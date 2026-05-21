def capitalize:
	(.[:1] | ascii_upcase) + .[1:];

[ .[] | select(.version != null) |
	{
		version: .version | ltrimstr("v"),
		timestamp: .timestamp | todateiso8601,
		message,
		commit_id,
		commits: [ .commits[] | select(.merge_commit == false) |
					{
						id,
						message: .message | capitalize,
						group,
						scope,
						raw_message
					}
			]
        }
]
