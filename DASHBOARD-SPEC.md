# Dashboard Agent Editor - Improvement Spec

## Location
/mnt/c/Users/grabino/PycharmProjects/pythonProject/ai-router/dashboard.py

## Current State
- Dashboard works at http://127.0.0.1:3459/ui
- Agent form editor exists (editAgentForm / openAgentFormModal functions in the inline JS)
- /api/openrouter-models endpoint returns 421 models from OpenRouter API
- /api/form-options returns harnesses, providers, tool_profiles

## Required Changes

### 1. Provider-aware model list
- When user selects a provider in the agent editor, fetch models FOR THAT PROVIDER
- Currently only showing a handful (openrouter/free, openrouter/beta, etc.) — the `<datalist>` is not being populated
- Fix: auto-load models when provider dropdown changes, not via manual button
- Each provider should have its own model list endpoint or the OpenRouter endpoint should filter

### 2. Strip provider prefix from model display
- Instead of showing "openrouter/fusion" show just "fusion"
- The full model ID (with provider prefix) should still be stored in the JSON
- Display: short name. Value saved: full ID
- Example: display "nemotron-3-ultra-550b-a55b:free" but save "nvidia/nemotron-3-ultra-550b-a55b:free"

### 3. Model version selector
- Some models have multiple versions (e.g., claude-sonnet-4, claude-sonnet-5)
- Group models by base name, show versions in a secondary dropdown
- If only 1 version exists, hide the version dropdown

### 4. Auto-activate Fusion when fusion model selected
- Remove the Fusion checkbox
- When user selects model "fusion" (openrouter/fusion), automatically show the Fusion panel config (judge model + analysis models)
- When any other model is selected, hide Fusion config and set fusion: null

### 5. Harnesses section should be editable
- Currently harnesses are read-only in the UI
- Add edit/create/delete capabilities (same as agents/providers)
- Fields: name, binary (path to executable), launch_mode, speaks_protocol, env_map, config_template, extra_args

### 6. "Load OpenRouter models" button fix
- The button calls loadModelList() which populates a `<datalist>` with id="af-model-list"
- Issue: the datalist may not be showing all options due to browser limits on datalist size (421 items)
- Consider: replace with a searchable `<select>` or a text input with dropdown suggestions (limit to top 50 matches as user types)

## Technical Notes
- All HTML/CSS/JS is inline in DASHBOARD_HTML raw string in dashboard.py
- The JS uses template literals with ${} for dynamic content in openAgentFormModal()
- API endpoints available: /api/openrouter-models, /api/form-options, /api/agents, /api/providers
- The `_orModels` variable caches the full model list client-side after first load
