# AI Router - Dashboard Debug Context

## Project Location
/mnt/c/Users/grabino/PycharmProjects/pythonProject/ai-router

## The Problem
The dashboard at http://127.0.0.1:3459/ui loads the HTML/CSS but JavaScript is broken.
Status section shows empty, sidebar links don't work. Likely a JS syntax error in dashboard.py's inline DASHBOARD_HTML string.

## Key Files
- `dashboard.py` - contains inline HTML/CSS/JS (DASHBOARD_HTML variable ~990 lines) + Flask API routes
- `router.py` - imports dashboard via `from dashboard import register_dashboard`

## How to Test
```bash
cd /mnt/c/Users/grabino/PycharmProjects/pythonProject/ai-router
export $(grep -v '^#' .env | xargs)
python3 router.py --port 3459
# Then open http://127.0.0.1:3459/ui
# Check browser console (F12) for JS errors
```

## Architecture
- Dashboard is a single-page app served at /ui
- REST APIs at /api/agents, /api/providers, /api/harnesses, /api/tool-profiles, /api/keys, /api/status, /api/launch/<slug>, /api/form-options, /api/openrouter-models
- JS uses `loaders.status()` on init, `nav()` for section switching
- Agent editing has both form-based (editAgentForm) and raw JSON (editItem) modes

## What to Debug
1. Open browser dev tools (F12) → Console tab to see the JS error
2. The error is likely in the DASHBOARD_HTML JavaScript section (lines 232-717 of dashboard.py)
3. Common issues: missing semicolons, unclosed functions, template literal escaping problems in the raw string
