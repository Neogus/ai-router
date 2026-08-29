# AI Router — Setup Guide

Quick start for setting up AI Router on a fresh Windows machine.

---

## Step 1: Prerequisites

Install these before anything else:

| Requirement | Install |
|-------------|---------|
| **Windows 10/11** | — |
| **Python 3.8+** | [python.org](https://python.org) or `winget install Python.Python.3.12` |
| **Node.js LTS** | [nodejs.org](https://nodejs.org) or `winget install OpenJS.NodeJS.LTS` |

> Check both are on PATH: `python --version` and `node --version`

---

## Step 2: Clone the Repository

```powershell
git clone https://github.com/Neogus/ai-router.git
cd ai-router
```

---

## Step 3: Run the Installer

Open PowerShell **as Administrator**, then:

```powershell
.\install-service.ps1
```

This will automatically:
- Install Python dependencies (`flask`, `requests`)
- Create `.env` from the template
- Download NSSM (Windows service manager)
- Install and start the `AIRouter` Windows service on port **3459**
- Add the project folder to your PATH
- Prompt for your Windows password (so the service runs as your user)

---

## Step 4: Add API Keys

Edit `.env` in the project root and fill in the keys for providers you want to use:

```env
# Required for most agent profiles (free-tier models available)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional — only if using direct Anthropic access
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional — only if using Moonshot / Kimi models
MOONSHOT_API_KEY=your-moonshot-key-here

# Optional — only if using direct DeepSeek access
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
```

Where to get keys:
- **OpenRouter** — [openrouter.ai/keys](https://openrouter.ai/keys) (free tier available)
- **Anthropic** — [console.anthropic.com](https://console.anthropic.com)
- **Moonshot** — [platform.moonshot.cn](https://platform.moonshot.cn)
- **DeepSeek** — [platform.deepseek.com](https://platform.deepseek.com)

After editing, restart the service:

```powershell
ai-router restart
```

---

## Step 5: Install Coding Harnesses

Install whichever AI coding tools you want to use. You only need the ones you plan to launch.

```powershell
# Claude Code (most popular — works with all routed models)
npm install -g @anthropic-ai/claude-code --allow-scripts=@anthropic-ai/claude-code

# Aider (Python-based, great for OpenAI-compatible models)
pip install aider-chat

# Gemini CLI
npm install -g @google/gemini-cli

# DeepSeek Harness
npm install -g @deepseek-ai/dsh

# Goose (Block)
pip install goose-ai

# Codex — native only, no routing
npm install -g @openai/codex
```

Verify any installed harness:
```powershell
claude --version
aider --version
gemini --version
```

> You can also install harnesses from the web dashboard: `ai-router ui` → **Catalog** tab.

---

## Step 6: Launch an Agent

Open any terminal and run:

```powershell
# Launch by profile slug
ai-router launch claude-open-nemotron-free

# Launch by full name
ai-router launch "Claude Open GLM (Free)"

# See all available profiles
ai-router list
```

The agent launches **in your current terminal**, fully configured to route through the AI Router.

---

## Using the Dashboard

Open the web UI:

```powershell
ai-router ui
```

Or navigate to **http://127.0.0.1:3459/ui** in your browser.

From the dashboard you can:
- Browse and launch agent profiles
- Create or edit agents, harnesses, and providers
- Manage API keys
- View the live request log
- Discover tools for each harness
- Install new harnesses from the catalog

---

## CLI Quick Reference

| Command | What it does |
|---------|-------------|
| `ai-router launch <profile>` | Launch an agent in this terminal |
| `ai-router list` | List all agent profiles |
| `ai-router ui` | Open the web dashboard |
| `ai-router status` | Show service status |
| `ai-router start` | Start the service (admin) |
| `ai-router stop` | Stop the service (admin) |
| `ai-router restart` | Restart the service (admin) |
| `ai-router install` | Re-run the installer (admin) |

---

## Troubleshooting

**"ai-router" not recognized**
```powershell
# Refresh PATH in your current terminal
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
```

**Service won't start**
```powershell
# Check the logs
Get-Content .\logs\stderr.log -Tail 20

# Or run manually to see errors directly
python router.py --port 3459
```

**Harness binary not found**
```powershell
# Check if it's on PATH
where.exe claude
where.exe aider
```
Restart your terminal after installing a harness — PATH changes need a new session.

**Rate limit errors (429)**
Free-tier models on OpenRouter have aggressive rate limits. Wait and retry, switch to a different free model, or use a paid model.
