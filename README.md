# AI Router

**A local proxy service that routes AI coding agents through any LLM provider with protocol translation, model override, and tool filtering.**

AI Router sits between your coding harnesses (Claude Code, Aider, Gemini CLI, DeepSeek, Goose, etc.) and LLM providers (OpenRouter, Anthropic, DeepSeek), letting you swap models, filter tools, and use free-tier models — all without reconfiguring each tool.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Your IDE Terminal                                                │
│                                                                   │
│  ai-router launch "Claude Open Nemotron Free"                    │
│       │                                                           │
│       ▼                                                           │
│  ┌──────────┐    ┌─────────────────────────────────────────┐     │
│  │  Claude   │───▶│  AI Router (localhost:3459)              │     │
│  │  Code     │◀───│                                         │     │
│  └──────────┘    │  1. Identify agent (Bearer token)        │     │
│                  │  2. Load profile (harness + provider)     │     │
│                  │  3. Override model                        │     │
│                  │  4. Filter tools                         │     │
│                  │  5. Translate protocol if needed          │     │
│                  │  6. Forward to provider                   │     │
│                  └────────────────┬──────────────────────────┘     │
│                                   │                               │
└───────────────────────────────────┼───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  OpenRouter / Anthropic / etc  │
                    │  (nvidia/nemotron, glm, etc)   │
                    └───────────────────────────────┘
```

## Supported Harnesses

| Harness | Protocol | Routable | Native |
|---------|----------|----------|--------|
| Claude Code | Anthropic | ✅ | ✅ |
| Aider | OpenAI | ✅ | ✅ |
| Gemini CLI | Gemini native | ✅ | ✅ |
| DeepSeek (dsh) | OpenAI | ✅ | ✅ |
| Goose | OpenAI | ✅ | ✅ |
| OpenCode | OpenAI | ✅ | ✅ |
| Codex | OpenAI (proprietary) | ❌ | ✅ |
| Amp | Anthropic (Sourcegraph) | ❌ | ✅ |

**Routable** = can redirect through the router to any provider
**Native** = can launch with its own default API (no routing)

---

## Installation

### Prerequisites

- **Windows 10/11**
- **Python 3.8+** installed and on PATH
- **Administrator privileges** for service installation

### Quick Install

```powershell
# 1. Clone the repository
git clone https://github.com/Neogus/ai-router.git
cd ai-router

# 2. Run the installer (as Administrator)
.\install-service.ps1
```

The installer will:
1. Detect Python and install requirements (Flask, Requests)
2. Create `.env` from template (you fill in API keys later)
3. Create `~/.gemini/settings.json` for Gemini CLI support
4. Download NSSM (service manager) if not present
5. Install and start the Windows service
6. Prompt for Windows credentials (for user-context execution)
7. Add the project directory to your PATH

### Post-Install: Add API Keys

Edit `.env` in the project root:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
```

Then restart the service:
```powershell
ai-router restart    # (from an admin terminal)
```

### Install Harnesses

Install whichever AI coding tools you want to use:

```powershell
npm install -g @anthropic-ai/claude-code    # Claude Code
pip install aider-chat                       # Aider
npm install -g @google/gemini-cli           # Gemini CLI
npm install -g @deepseek-ai/dsh            # DeepSeek Harness
npm install -g @openai/codex               # Codex (native only)
npm install -g @anthropic-ai/amp           # Amp (native only)
```

Or use the dashboard to install harnesses: `ai-router ui` → Catalog tab.

---

## CLI Reference

### Basic Usage

```powershell
ai-router <command> [arguments]
```

### Commands

| Command | Description |
|---------|-------------|
| `ai-router launch <profile>` | Launch an agent in the current terminal |
| `ai-router ui` | Open the web dashboard in browser |
| `ai-router status` | Show service status and health |
| `ai-router list` | List all available agent profiles |
| `ai-router start` | Start the service (requires admin) |
| `ai-router stop` | Stop the service (requires admin) |
| `ai-router restart` | Restart the service (requires admin) |
| `ai-router install` | Run the installer (elevates to admin) |
| `ai-router help` | Show help |

### Launch Examples

```powershell
# Launch by profile name (with model routing)
ai-router launch "Claude Open Nemotron Free"
ai-router launch "Aider Open Nemotron Free"
ai-router launch "Gemini (Nemotron Free)"

# Launch by slug
ai-router launch claude-open-nemotron-free
ai-router launch aider-open-nemotron-free

# Launch native (uses harness's own API key, no routing)
ai-router launch "Claude Code"
ai-router launch "Gemini"
ai-router launch "Codex"

# Short form (first word treated as profile if not a command)
ai-router "Aider Open Nemotron Free"
```

### Service Control (requires admin terminal)

```powershell
# Open admin PowerShell, then:
ai-router restart
ai-router stop
ai-router start
```

---

## Web Dashboard

Access at: **http://127.0.0.1:3459/ui**

The dashboard provides:
- **Agent Profiles** — Create/edit agent configurations
- **Harness Editor** — Configure binary paths, protocols, tool profiles
- **Harness Catalog** — Install new harnesses with one click
- **Tool Discovery** — Auto-detect tools for each harness
- **Request Log** — See all requests flowing through the router
- **API Keys** — Manage provider credentials

---

## Concepts

### Agent Profile

An agent profile defines HOW a harness connects:

```json
{
  "name": "Claude Open Nemotron Free",
  "harness": "claude-code",
  "provider": "openrouter",
  "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
  "tool_profile": "coding"
}
```

- **harness** — which coding tool to launch
- **provider** — where to send API requests
- **model** — override the model (harness thinks it's using Claude, but gets Nemotron)
- **tool_profile** — filter which tools to expose

### Native Profiles

Native profiles launch harnesses with their own APIs (no routing):

```json
{
  "name": "Claude Code",
  "harness": "claude-code",
  "provider": "native",
  "native": true,
  "model": ""
}
```

### Harness Config

Defines how to launch and communicate with a coding tool:

```json
{
  "name": "Aider",
  "binary": "aider",
  "speaks_protocol": "openai",
  "env_map": {
    "base_url": "OPENAI_API_BASE",
    "auth_token": "OPENAI_API_KEY"
  },
  "extra_args": ["--model", "openai/{{model}}"]
}
```

### Provider Config

Defines an LLM API endpoint:

```json
{
  "name": "openrouter",
  "base_url": "https://openrouter.ai/api",
  "api_key_env": "OPENROUTER_API_KEY",
  "endpoints": {
    "openai": "/v1/chat/completions",
    "anthropic": "/v1/messages"
  }
}
```

---

## Protocol Support

The router handles three API protocols:

| Protocol | Endpoint | Used By |
|----------|----------|---------|
| Anthropic | `/v1/messages` | Claude Code |
| OpenAI | `/v1/chat/completions` | Aider, DeepSeek, Goose, OpenCode |
| Gemini | `/v1beta/models/{model}:generateContent` | Gemini CLI |

Protocol translation happens automatically when a harness speaks one protocol but the provider expects another.

---

## Tool Filtering

Each harness declares its available tools. Tool profiles control which tools are exposed:

| Profile | Behavior |
|---------|----------|
| `full` | Pass all tools through |
| `coding` | Essential coding tools only (Read, Write, Edit, Grep, Shell) |
| `minimal` | File operations + shell only |
| `none` | Strip all tools |

---

## File Structure

```
ai-router/
├── router.py              # Main proxy server
├── dashboard.py           # Web dashboard (Flask)
├── translate.py           # Protocol translation
├── ai-router.ps1          # CLI tool (PowerShell)
├── ai-router.cmd          # CLI wrapper (batch)
├── install-service.ps1    # Service installer
├── .env                   # API keys (not in git)
├── .env.example           # Template for API keys
├── requirements.txt       # Python dependencies
├── profiles/
│   ├── agents/            # Agent profiles
│   ├── harnesses/         # Harness configurations
│   └── providers/         # Provider endpoints
├── debug/                 # Runtime debug files
├── logs/                  # Service logs
└── tools/                 # NSSM (downloaded during install)
```

---

## Troubleshooting

### Service won't start

```powershell
# Check logs
Get-Content .\logs\stderr.log -Tail 20

# Test manually
python router.py --port 3459
```

### "ai-router" not recognized

```powershell
# Refresh PATH in current terminal
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
```

### 429 Rate Limit errors

Free-tier models on OpenRouter have aggressive rate limits. Options:
- Wait and retry (Claude Code retries automatically)
- Switch to a different free model
- Use a paid model for no limits

### Harness not found

```powershell
# Check if binary is on PATH
where.exe claude
where.exe aider
where.exe gemini
```

The router auto-discovers binaries in common locations (`AppData\Roaming\npm`, `AppData\Roaming\Python\Scripts`, etc.).

### Admin required for service control

Service start/stop/restart requires admin. Either:
- Open an admin terminal
- Or use: `Start-Process powershell -Verb RunAs -ArgumentList "-Command ai-router restart"`

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check |
| `GET /api/status` | Service status (agent/harness/provider counts) |
| `GET /api/request-log` | Recent request log |
| `GET /api/launch/<slug>` | Get launch config for an agent |
| `POST /api/launch/<slug>` | Launch agent in new terminal window |
| `GET /api/form-options` | Form dropdowns (harnesses, providers) |
| `GET /api/harnesses/catalog` | Available harness catalog |
| `POST /api/harnesses/<slug>/discover-tools` | Auto-discover tools |
| `POST /api/harnesses/install` | Install a harness |

---

## License

**AGPL-3.0** — Free to use, study, and modify. If you distribute or deploy it commercially, you must release your source code under the same license.


See [LICENSE](LICENSE) for full terms.

---

## Disclaimer

AI Router is an independent, open-source project. It is **not affiliated with, endorsed by, or sponsored by** Anthropic, OpenAI, Google, NVIDIA, Sourcegraph, Block, or any other company whose products or services are referenced in this project.

All product names, trademarks, and registered trademarks (including but not limited to Claude, Anthropic, OpenAI, Gemini, DeepSeek, Codex, Goose, and Amp) are the property of their respective owners and are used here solely for identification and interoperability purposes.

This tool routes API requests using **publicly documented environment variables and standard HTTP APIs**. It does not reverse-engineer, decompile, or modify any third-party software.

**Users are solely responsible for:**
- Obtaining and using their own API keys
- Complying with each provider's Terms of Service and Usage Policies
- Ensuring their use of this tool does not violate any applicable agreements

This software is provided "as is", without warranty of any kind. See the [LICENSE](LICENSE) for full terms.
