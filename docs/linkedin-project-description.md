# LinkedIn Project Description

**Use this in the "Projects" section body on LinkedIn.**

---

**AI Router — Multi-Protocol LLM Proxy for AI Coding Agents**

AI Router is a local Windows service that acts as a configurable proxy between AI coding agents and LLM providers. It enables developers to use any coding harness (Claude Code, Aider, Gemini CLI, DeepSeek, Goose) with any model provider — swapping models, filtering tools, and translating protocols in real-time, all through each tool's own documented configuration options.

**The Problem:**
Each AI coding tool is locked to its default provider. Want to test Claude Code with a free model? Impossible without modifying configs. Want to compare how different models handle the same coding task across different agents? You'd need to reconfigure each tool manually every time.

**The Solution:**
AI Router uses each harness's documented environment variables and standard HTTP endpoints to redirect API calls through a local proxy. The proxy translates protocols, overrides the model, and forwards to the provider of your choice — all using your own API keys.

**Key Technical Features:**

- Multi-protocol translation engine (Anthropic, OpenAI, Google Gemini) — each harness speaks its native protocol while the router translates on the fly

- Automatic tool discovery — probes each harness to capture its tool definitions, enabling per-profile tool filtering

- NSSM Windows service with CLI launcher — persistent background service that auto-starts on boot, controlled via ai-router commands from any terminal

- Agent profile system — define harness + provider + model + tool profile combinations as reusable configurations

- Web dashboard for real-time monitoring — request log, harness catalog, one-click installation, tool discovery UI

**Architecture:**
Harness → AI Router (localhost:3459) → Protocol Translation → Model Override → Tool Filtering → Provider (OpenRouter, Anthropic, DeepSeek, etc.)

**Tech Stack:** Python (Flask), PowerShell, NSSM, REST APIs, SSE streaming, JSON protocol translation

**Supported Harnesses:** Claude Code, Aider, Gemini CLI, DeepSeek Harness, Goose, OpenCode, Codex, Amp

This project uses only publicly documented environment variables and standard HTTP APIs. It does not reverse-engineer, decompile, or modify any third-party software. All trademarks are property of their respective owners.

**GitHub:** https://github.com/Neogus/ai-router
