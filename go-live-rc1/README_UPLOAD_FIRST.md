# Upload this first - release/go-live-rc1

This zip creates the corrected SCIP release branch structure. Extract/upload directly into the repository root on branch `release/go-live-rc1`.

## What this scaffold includes

- Corrected capital `Backend/` structure.
- Root `src/` frontend structure.
- Batch history folders for Batch 0 through Batch 17.
- `data/.gitkeep` only, with `.gitignore` blocking workbook commits.
- Available loose docs/config/build files from the current workspace.
- Upload map and release instructions.

## What this scaffold intentionally does not include

- Live `.xlsx` source files.
- Batch upgrade zip runtime code not currently present in this workspace.
- Unverified replacements for `Backend/main.py`, `src/App.jsx`, or migrations.

Next step after uploading this scaffold: apply the batch packs in the order documented in `UPLOAD_MAP_RELEASE_GO_LIVE_RC1.md`.
