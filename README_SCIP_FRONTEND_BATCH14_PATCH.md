# SCIP Frontend Batch 14 Netlify Patch

Purpose: restore the root-level Vite/Netlify frontend shell and overlay Batch 14 Product UAT UI files.

Files included:
- package.json
- vite.config.js
- netlify.toml
- index.html
- src/main.jsx
- src/App.jsx
- src/liquidGlassTokens.css

Source selection:
- src/App.jsx and src/liquidGlassTokens.css from scip_batch14_rollout_uat_signoff.zip
- package.json, vite.config.js, src/main.jsx from loose Vite shell files
- index.html created for root-level Vite app
- netlify.toml corrected for root-level build: no FRONTEND/Src base

Netlify settings:
- Production branch: release
- Base directory: blank
- Build command: npm install && npm run build
- Publish directory: dist
