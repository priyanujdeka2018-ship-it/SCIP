# SCIP - Sobha Collections Intelligence Platform

Release branch scaffold for `release/go-live-rc1`.

This package creates the corrected repository structure and preserves the Batch 0-17 upload map. It intentionally does not include live R-series Excel workbooks or unverified runtime overlays from batch upgrade packs.

## Data rule

Do not commit live `.xlsx` source files to this public repository. Keep only `data/.gitkeep` in GitHub. Upload R-series source workbooks to Render/staging storage.

## Runtime rule

Batch 13 is the cumulative runtime baseline. Batches 14-17 are overlays. Batch 0-12 artifacts remain as product history, lineage, contracts, smoke tests, and governance references.

See `README_UPLOAD_FIRST.md` and `UPLOAD_MAP_RELEASE_GO_LIVE_RC1.md`.
