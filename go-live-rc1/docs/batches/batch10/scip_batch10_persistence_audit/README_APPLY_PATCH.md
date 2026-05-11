# Apply SCIP Batch 10 Patch

1. Copy backend files into the backend service directory:

```text
persistence.py
main.py
migrations/001_batch10_persistence.sql
```

2. Copy frontend files into the frontend app directory:

```text
App.jsx
liquidGlassTokens.css
```

3. Run smoke test locally:

```bash
python smoke_batch10_persistence_audit.py
```

4. Start backend and seed persistence:

```bash
uvicorn main:app --reload
curl -X POST "http://localhost:8000/persistence/seed?reset=true"
```

5. Export audit packs:

```bash
curl -o audit.json "http://localhost:8000/audit/export?format=json"
curl -o audit.csv "http://localhost:8000/audit/export?format=csv"
```

6. Run frontend build locally:

```bash
npm install
npm run build
npm run dev
```

## Production hardening note

The patch uses SQLite to keep the package portable. Before production, port the schema to the approved database engine, add RBAC, enable authenticated actor identity, and move delivery-channel status into a controlled worker.
