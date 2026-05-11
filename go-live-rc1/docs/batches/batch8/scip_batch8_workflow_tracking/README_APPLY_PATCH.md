# Apply SCIP Batch 8 Patch

Copy these files into the active SCIP app repository after reviewing:

- `workflow.py` -> backend root
- `main.py` -> backend root
- `App.jsx` -> frontend app source path used by Vite
- `liquidGlassTokens.css` -> frontend style path used by App.jsx
- `frontend_contracts_batch8.ts` -> frontend contracts/types directory if used

Then run:

```bash
python -m py_compile workflow.py main.py
uvicorn main:app --reload
```

Frontend:

```bash
npm install
npm run build
npm run dev
```

Smoke check:

```bash
python smoke_batch8_workflow_tracking.py
```

Expected result:

```text
overall_passed = true
```
