. | {
	version: .version | ltrimstr("v"),
	release_date: .timestamp | todateiso8601,
	description: .message,
	commit_id,
	sections: (
		.commits
		| group_by(.scope)
		| map({
			name: .[0].scope,
			features: map(select(.raw_message | startswith("feat")) | { id, message }),
			fixes: map(select(.raw_message | startswith("fix")) | { id, message })
		      })
	)
}
