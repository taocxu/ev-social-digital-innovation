# Public Repository Rules

**Repository**: `taocxu/ev-social-digital-innovation`
**URL**: https://github.com/taocxu/ev-social-digital-innovation

## Core Principles

1. **Read-only and dry-run by default.** Never modify, overwrite, or delete source files without explicit user confirmation.
2. **Copy-only reorganisation.** Use `shutil.copy2` (or equivalent); never move or rename originals.
3. **SHA-256 verification.** Verify every copied file against its source before reporting success.
4. **No automatic deletion.** Do not delete source files or intermediate records without explicit user approval.
5. **No credential handling.** This repository does not store, process, or transmit credentials, tokens, or secrets.
6. **No force push.** Use `--force-with-lease` only when explicitly authorised for public history cleanup.
7. **No automatic uploads.** Never push to GitHub or any remote without explicit user instruction.

## Workflow Rules

- Default to dry-run. Actual execution requires both `--execute` and a confirmation flag.
- Preserve duplicate entities. SHA-256 identical files from different source directories are all copied.
- Windows file system constraints: no reserved filenames, no invalid characters, max path length 220 characters.
- Office temporary files (starting with `~$`) are excluded from copy operations.
- After every copy operation, verify source and target SHA-256. Stop on any mismatch.

## Repository Boundaries

- `control/scripts/` — Reusable governance tooling (MIT licensed).
- `research_outputs/` — Final curated research outputs (author copyright reserved).
- **Do not commit**: inventories, classification maps, execution logs, config.json, or any file containing absolute local paths.

## Push Rules

1. Can create local commits without restriction.
2. Only push when explicitly requested by the user.
3. Never force push (unless explicitly authorised).
4. Never change repository visibility without explicit user approval.
5. Never upload excluded research materials.
6. Before each push, check staged files, remote URL, and credentials.
