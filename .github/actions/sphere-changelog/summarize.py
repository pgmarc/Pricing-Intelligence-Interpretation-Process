from enum import Enum
import json
import sys
from typing import Annotated, List, Optional
from uuid import UUID, uuid4

from google import genai
from pydantic import BaseModel, Field, TypeAdapter


class Group(str, Enum):
    features = 'features'
    fixes = 'fixes'
    docs = 'docs'
    refactor = 'refactor'
    chore = 'chore'
    other = 'other'

class Scope(str, Enum):
    harvey = 'harvey'
    mcp = 'mcp'
    prime = 'prime'
    csp = 'csp'
    amint = 'amint'
    ui = 'ui'

class Commit(BaseModel):
    id: str = Field(description="SHA256 ofa a commit.")
    message: str = Field(description="Description of the commit message according to the Conventional Commits spec.")
    group: Group = Field(description="Type of the commit.")
    scope: Annotated[Scope, Field(description="Scope of the commit according to the Conventional Commits spec.")] = None
    raw_message: str = Field(description="The raw message of the commit that follows Conventional Commits spec (i.e. <type>[optional scope]: <description>).")

class Release(BaseModel):
    version: str = Field(description="Release version of the software using SemVer.")
    timestamp: int = Field(description="Unix epoch of the release.")
    message: str = Field(description="Summary of the git tag of the release.")
    commit_id: str = Field(description="SHA256 of the tagged commit.")
    commits: List[Commit] = Field(description="List of commits that belongs to the release.")

class Change(BaseModel):
    """
    Expected structured output of the LLM
    """
    id: UUID = Field(description="Computed uuid4 of a summarized change by LLM.")
    message: str = Field(description="Description of the change summarized by LLM.")
    group: Group = Field(description="Type of the commit.")
    scope: Annotated[Scope, Field(description="Scope of the summarized commit.")] = None

adapter = TypeAdapter(List[Change])


def get_prompt(json_input: str):
	return f"""
	Objective: Given a JSON input summarize and/or merge commits messages in the following jq path `.commits` and
	clasify them as a `feat` or `fix`. Your goal is to generate as few entries as possible in order to get an overview of
	the features and fixes that were made during one software release to another.

	Rules:
	- If you merge or summarize two or more commits together create an UUID
	- If two descriptions are identical merge them into one. For example, `fix deployment` and `deployment is now working`
	- Commits types of type `feat` and `fix` must not be merged. For example `feat: iPricing actions on same column` and `fix: add-on names not printing in solutions`
	- You must not merge commits of different scope. For example, if scope is `feat(harvey)` and `feat(mcp)` do not merge them together.
	- You must not generate more messages than they were passed in the JSON input

	The input has the following JSON schema:
	```json
	{json.dumps(Release.model_json_schema())}
	```

	Here is the JSON input:
	```json
	{json_input}
	```
	"""

if __name__ == "__main__":
	"""
	The following models support structured output:
	- Gemini 3.1 Flash-Lite
	- Gemini 3.1 Pro Preview
	- Gemini 3.5 Flash
	- Gemini 3.1 Flash-Lite Preview
	- Gemini 2.5 Pro
	- Gemini 2.5 Flash
	- Gemini 2.5 Flash-Lite
	"""

	input_data = sys.stdin.read()
	client = genai.Client()
	response = client.models.generate_content(
    		model="gemini-2.5-flash-lite",
    		contents=get_prompt(input_data),
    		config={
        		"response_format": {"text": {"mime_type": "application/json", "schema": adapter.json_schema()}},
    		},

	summarized_changes = adapter.model_validate_json(response.text)
	print(json.dumps(summarized_changes))
