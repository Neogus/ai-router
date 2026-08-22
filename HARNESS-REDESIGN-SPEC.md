# Harness & Tool Profile Architecture Redesign

## Current Structure (wrong)
```
profiles/
  tool-profiles.json          ← GLOBAL, hardcoded Claude Code tools
  harnesses/
    claude-code.json          ← just launch config
    opencode.json
    deepseek-harness.json
```

## Desired Structure
```
profiles/
  harnesses/
    claude-code.json          ← launch config + available_tools + tool_profiles
    opencode.json
    deepseek-harness.json
```

Each harness.json should contain:
```json
{
  "name": "claude-code",
  "binary": "claude",
  "binary_path": "",
  "launch_mode": "env",
  "speaks_protocol": "anthropic",
  "env_map": {
    "base_url": "ANTHROPIC_BASE_URL",
    "auth_token": "ANTHROPIC_AUTH_TOKEN"
  },
  "extra_args": [],

  "available_tools": [
    "PowerShell", "Read", "Write", "Edit", "Grep", "Glob",
    "Agent", "AskUserQuestion", "WebSearch", "WebFetch",
    "Workflow", "DesignSync", "CronCreate", "CronDelete", "CronList",
    "EnterPlanMode", "ExitPlanMode", "EnterWorktree", "ExitWorktree",
    "NotebookEdit", "ReportFindings", "ScheduleWakeup", "SendMessage",
    "Skill", "TaskOutput", "TaskStop"
  ],

  "tool_profiles": {
    "full": {
      "description": "All tools",
      "mode": "keep_all"
    },
    "coding": {
      "description": "Essential coding tools",
      "mode": "whitelist",
      "tools": ["PowerShell", "Read", "Write", "Edit", "Grep", "Glob",
               "Agent", "WebSearch", "WebFetch", "AskUserQuestion",
               "TaskOutput", "TaskStop", "SendMessage"]
    },
    "minimal": {
      "description": "File ops + shell only",
      "mode": "whitelist",
      "tools": ["PowerShell", "Read", "Write", "Edit", "Grep", "Glob"]
    },
    "none": {
      "description": "Strip all tools",
      "mode": "strip_all"
    }
  }
}
```

## Changes Required

### 1. Router changes (router.py)
- Load tool profiles from harness profile instead of global file
- `apply_tool_filtering()` should look up `agent.harness` → harness profile → tool_profiles
- Delete global `profiles/tool-profiles.json` (migrated into harness profiles)

### 2. Dashboard: Harness Config UI (custom form, NOT generic JSON editor)
- Binary name + path input
- Launch mode dropdown (env, config_file, config_file_plus_env)
- Protocol dropdown (anthropic, openai)
- Env map: key-value pairs editor (add/remove rows)
- Extra args: list editor
- **Available Tools**: list showing all tools this harness provides
  - "Discover" button that captures tools from a live request (or manual entry)
- **Tool Profiles**: create/edit/delete profiles by selecting from available_tools
  - Checkboxes for each available tool
  - Profile name + description
  - Mode selector (keep_all, whitelist, strip_all)

### 3. Dashboard: Agent Editor
- When harness is selected, tool_profile dropdown should update to show
  only profiles available for THAT harness
- Different harnesses = different tool profile options

### 4. Discovery endpoint
- POST /api/harnesses/<slug>/discover-tools
- Captures tools from the next request through that harness
- Or: read from debug_last_request.json per harness

## How to discover tools per harness
Option A: Manual - list them in the harness config
Option B: Auto-capture - router saves tool names seen per harness to the profile
Option C: First-request capture - on first request from a harness, save tool list

Best approach: Option B (auto-capture) + manual override in the UI
- Router already has debug output showing tool names
- Add logic: if request comes in and harness.available_tools is empty, save the tool names
