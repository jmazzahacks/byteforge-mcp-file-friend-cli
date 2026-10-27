# File Friend CLI

Owns the `ff` application and shell configuration/output only. Transfer logic
belongs to byteforge-mcp-file-friend-api-python. Preserve CLI arguments, FF_*
settings, resume caches and reference JSON. Use public immutable Git dependency
pins, never sibling path dependencies. The SDK version used for release must no
longer expose an ff entry point. Python 3.13+, Unix, MIT/public under jmazzahacks.

Read README.md for installation and validation. Root venv: source bin/activate.
Run tests against installed wheels using local fixtures only. Do not commit
without Jason's approval. Never modify projects outside this workspace.
