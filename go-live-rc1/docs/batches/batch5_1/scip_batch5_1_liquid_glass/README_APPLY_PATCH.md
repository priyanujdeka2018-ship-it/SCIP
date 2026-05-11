# Apply SCIP Batch 5.1 patch

1. Copy `App.jsx` into the frontend source directory, replacing the Batch 5 `App.jsx`.
2. Copy `liquidGlassTokens.css` into the same directory as `App.jsx`.
3. Ensure `main.jsx` still imports `App.jsx`.
4. Keep the existing Batch 5 backend files unless you want to use the copies in this pack.
5. Run:

```bash
npm install
npm run build
npm run dev
```

6. Verify:

- `/` or app load shows only Live Pulse and Narratives.
- Live Pulse shows Current Signal, Month Movement, Risk & Action.
- Narratives shows Story, Portfolio, Dues, Advance, Roadmap.
- Cards show reporting basis.
- Show evidence opens lineage.
- Forecast assumptions are visible.
- Quickball blocks untrusted answers.
