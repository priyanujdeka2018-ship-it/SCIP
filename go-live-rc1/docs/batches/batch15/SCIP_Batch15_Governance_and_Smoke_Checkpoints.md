# SCIP Batch 15 Governance and Smoke Checkpoints

## Governance checkpoints

- Adoption analytics must not create a third Arrival door.
- All adoption events must include correlation ID.
- Sensitive values must be redacted before storage.
- Actor and session IDs must be hashed.
- Role values must exclude Entity Head.
- World values must be only Live Pulse or Narratives.
- Optimization recommendations must preserve the Liquid Glass two-door model.
- Frontend may display server-provided metrics only.
- Adoption dashboards are governance briefs, not dashboard-first product navigation.

## Smoke checkpoints

1. Seed adoption events.
2. Verify all events include correlation IDs.
3. Verify sensitive keys are redacted.
4. Verify no event uses `entity_head`.
5. Verify no event uses a world other than `live_pulse` or `narratives`.
6. Verify all required adoption metrics are present.
7. Verify dashboards are marked `not_arrival_door`.
8. Verify optimization backlog recommendations include Liquid Glass guardrails.
9. Verify App fetches `/adoption/summary`, `/adoption/dashboards`, and `/adoption/backlog`.
10. Verify no frontend adoption conversion calculation is introduced.
