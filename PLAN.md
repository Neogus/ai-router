# AI Router - Multi-Harness + Protocol Translation Plan

## Phase 1: Protocol Translation Layer
- [ ] Add Anthropic→OpenAI translator (messages, tools, tool_calls, responses)
- [ ] Add OpenAI→Anthropic translator (reverse)
- [ ] Update provider profiles to declare supported endpoints
- [ ] Router picks best endpoint and translates if needed

## Phase 2: OpenAI Inbound Endpoint
- [ ] Add `/v1/chat/completions` Flask route (accepts OpenAI format from harnesses)
- [ ] Reuse same agent/provider lookup logic
- [ ] Apply same tool_profile filtering

## Phase 3: Install & Configure Harnesses
- [ ] Install OpenCode (`npm i -g opencode`)
- [ ] Install DeepSeek harness (`dsh`)
- [ ] Update `router-launch.ps1` to support all three harnesses
- [ ] Create agent profiles using opencode/deepseek harnesses

## Phase 4: NSSM Service + Web UI (later)
- [ ] Wrap router in NSSM service
- [ ] Web dashboard for config management

---

## Format Translation Reference

### Anthropic → OpenAI

| Anthropic | OpenAI |
|-----------|--------|
| top-level `system` | `{"role": "system", "content": "..."}` message |
| `messages[].content` (array of blocks) | `messages[].content` (string or array) |
| `{"type": "tool_use", "name", "input"}` | `tool_calls: [{"type": "function", "function": {"name", "arguments"}}]` |
| `{"role": "user", content: [{"type": "tool_result"}]}` | `{"role": "tool", "tool_call_id", "content"}` |
| `tools[].input_schema` | `tools[].function.parameters` |
| `max_tokens` | `max_tokens` |
| Response: `{"content": [...], "stop_reason"}` | Response: `{"choices": [{"message": {...}, "finish_reason"}]}` |

### OpenAI → Anthropic

Reverse of above.
