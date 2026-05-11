# SCIP Batch 17 — Backend / Frontend Contracts

## Contract
`roadmap.v1.batch17`

## Routes
- `GET /roadmap/summary`
- `GET /roadmap/12-month`
- `GET /roadmap/okr-tree`
- `GET /roadmap/ownership-map`
- `GET /roadmap/release-train`
- `GET /roadmap/benefits`
- `GET /roadmap/steering-pack`
- `GET /roadmap/monthly-calendar`
- `GET /roadmap/templates`
- `GET /roadmap/validation`

## UI placement
These routes are governance L5 outputs. They may be linked from Narratives → Roadmap or from MIS/QCG/Admin governance evidence. They must not appear as a new Arrival card.

## Frontend rules
- Do not compute roadmap scores or financial metrics in the client.
- Display server-provided roadmap status, owners, gates, and benefits.
- Keep dense roadmap tables on solid evidence surfaces.
- Preserve Liquid Glass for rails, navigation, context chips, and transient drawers only.
