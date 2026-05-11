# Apply SCIP Batch 9 patch

Copy these files into the active app, preserving relative paths:

```text
notifications.py
main.py
App.jsx
liquidGlassTokens.css
frontend_contracts_batch9.ts
```

Then run:

```bash
python -m py_compile notifications.py main.py workflow.py account_action_queues.py
python smoke_batch9_notifications.py
npm install
npm run build
npm run dev
```

Batch 9 adds `/notifications` and `/notifications/digests`. It does not send external messages. Production delivery should be handled by a separate worker after RBAC and channel policy are approved.
