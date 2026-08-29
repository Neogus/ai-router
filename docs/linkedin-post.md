# LinkedIn Post -- Release Announcement

**Copy-paste this as a LinkedIn feed post.**

---

I just open-sourced AI Router -- a local proxy service that lets you use any AI coding agent with any LLM provider.

The problem? Every AI coding tool (Claude Code, Aider, Gemini CLI, Goose...) is locked to its default API. Want to run Claude Code with a free Nemotron model? Or test Gemini CLI through OpenRouter? Normally impossible without deep config changes.

AI Router fixes this. It sits between your coding harness and the LLM provider, using each tool's own documented configuration options to:

-> Route API calls through a local proxy
-> Translate between 3 protocols (Anthropic, OpenAI, Gemini)
-> Override models on the fly
-> Filter tool definitions per profile
-> Stream responses back in the harness's native format

It runs as a Windows service (auto-starts on boot) with a CLI tool:

  ai-router launch "Claude Open Nemotron Free"
  ai-router launch "Gemini"
  ai-router ui

One command from any IDE terminal -- the agent launches in-place, fully configured.

Built with Python/Flask, includes a web dashboard, automatic harness discovery, and a one-script installer that handles everything (NSSM, PATH, credentials). Uses only documented env vars and standard HTTP APIs -- no reverse engineering or binary patching.

8 harnesses supported. 3 protocols translated. 30+ agent profiles ready to go.

Check it out: https://github.com/Neogus/ai-router

#OpenSource #AI #LLM #DeveloperTools #Python #AIEngineering #CodingAgents
