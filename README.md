# File Friend CLI (`ff`)

Upload large files from any host to File Friend, resume interrupted transfers,
and hand the resulting verified reference to an MCP tool. Download, inspect,
and delete files with the same command-line application.

The CLI uses the separately versioned
[Python SDK](https://github.com/jmazzahacks/byteforge-mcp-file-friend-api-python).
Hosts need the CLI and access to a File Friend server; they do not need the
backend, PostgreSQL, Docker, or a local File Friend server.

## Install on a host

Requires Linux or macOS (the SDK uses Unix `fcntl` locks), Git, and
[uv](https://docs.astral.sh/uv/getting-started/installation/).
Native Windows is not supported; use a Linux environment such as WSL.
`uv` can provision Python 3.13 and keeps the application isolated from system
Python packages. No system-wide pip installation is needed.

```bash
uv tool install --python 3.13 --exclude-newer '7 days' \
  'git+https://github.com/jmazzahacks/byteforge-mcp-file-friend-cli.git'
uv tool update-shell
```

Open a new shell after updating PATH, then check:

```bash
ff --help
```

For reproducible provisioning, append `@<reviewed-full-commit-sha>` to the Git
URL. Install under the account that will run uploads. Scheduled jobs should use
the absolute `ff` path reported by `command -v ff` and set their environment
explicitly.

If a previous installation of `byteforge-mcp-file-friend-api-python` supplied
`ff`, remove that old CLI installation from your tool environment first. Keep
SDK installations needed by Python applications in their own environments.
Upgrading those applications to SDK 0.0.3 removes their legacy CLI entry point.

## Configure

In Bash, set the server origin (no `/api` suffix) and read the token without echoing it:

```bash
export FF_SERVER_URL='https://ff.mazza.vc'
read -r -s -p 'File Friend token: ' FF_TOKEN
export FF_TOKEN
printf '\n'
```

The token must have upload/delete access granted by the server administrator.
The server must already be provisioned and reachable. These instructions do not
install or deploy a server. HTTPS is required except for loopback development.

Alternatively, create `~/.config/ff/config.toml`:

```toml
server_url = "https://ff.mazza.vc"
# token = "..."
# cache_dir = "/path/to/private/resume-cache"
# max_bytes = 53687091200
```

Protect this file with mode `0600` if it contains a token. Environment variables
`FF_SERVER_URL`, `FF_TOKEN`, `FF_CACHE_DIR`, and `FF_MAX_BYTES` override file settings.
Status and download requests do not send the admin token.

## Upload and share a reference

```bash
umask 077
ff upload ./report.pdf --ttl 24h > report.reference.json
```

Successful upload prints a JSON reference only after the server verifies the
file. Supply that reference to a compatible MCP tool. Treat its ID and URL as
secrets: anyone possessing a live reference may read the file.

Interrupted upload? Run the same command again. The SDK checks the source hash,
size, and upload options before resuming. Preserve the cache and run as the same
user. If the source changed and you intentionally want a new upload, use
`--restart`.

For a slow or large upload, increase the deadline:

```bash
ff upload ./archive.tar --ttl 48h --timeout 14400 --chunk-size 64M > archive.reference.json
```

Timeout is seconds; its default is 3600. Chunk size defaults to 64 MiB.
TTL supports `s`, `m`, `h`, and `d`; chunk size supports binary `K`, `M`, `G`,
and `T` suffixes. Server policy and available capacity still bound uploads.
The client size limit defaults to 50 GiB and can be set with `FF_MAX_BYTES`.

## Download, inspect, and delete

Replace `FILE_ID` with the ID from the reference; the corresponding download URL
is also accepted. Quote URLs in shell commands.

```bash
ff info 'FILE_ID'
ff download 'FILE_ID' -o ./received-report.pdf
ff rm 'FILE_ID'
```

Downloads resume from partial files, verify the full SHA-256, and replace the
output only after verification. Keep the partial and lock files to resume.
Deletion requires the admin token and acknowledges deletion intent; physical
cleanup may finish asynchronously. Administrators share deletion authority.

JSON goes to stdout; progress and errors go to stderr. Exit code `0` means
success, `1` means failure (including a gone/expired file), and `130` means
interrupted. Argument errors use argparse's exit code `2`.

## Upgrade or uninstall

```bash
uv tool upgrade --exclude-newer '7 days' byteforge-mcp-file-friend-cli
uv tool uninstall byteforge-mcp-file-friend-cli
```

For deployments pinned to a commit, install the newly reviewed Git URL with
`uv tool install --force --python 3.13 --exclude-newer '7 days' URL`.
Uninstalling the application does not remove your configuration or resume cache.

## Local development

Use a root virtual environment created with `uv venv --allow-existing --python 3.13 .`, preserving
and restoring `.gitignore` if recreating it. Activate it with `source bin/activate`.
Third-party build and test dependencies are hash locked, retaining the existing
seven-day release-age gate. First-party dependencies use public immutable Git
revisions in `pyproject.toml`.

```bash
source bin/activate
uv pip install --require-hashes -r dev-requirements.txt -r build-requirements.txt
uv pip install --no-build-isolation .
python -m pytest
ruff check src tests
ff --help
```

Tests run against an installed wheel and local fixtures. No production server is
needed or authorized for testing. Refresh lockfiles using `uv pip compile
--generate-hashes --exclude-newer '7 days' -c dev-requirements.txt
dev-requirements.in -o dev-requirements.txt` (and the equivalent build lock command).
Do not hand-edit generated lockfiles or add sibling editable dependencies.

## Validation

All seven CLI tests pass against installed SDK/CLI wheels, including entry-point
ownership, upload/download options, interruption handling and local HTTP status
checks. The SDK separately validates transfer/resume behavior.

## License and attribution

MIT. Created by Jason Byteforge ([@jmazzahacks](https://github.com/jmazzahacks)).
