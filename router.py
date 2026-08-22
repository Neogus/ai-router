#!/usr/bin/env python3
"""
AI Router - a minimal CCR replacement with working Fusion support.

Architecture:
  Harness --(Anthropic or OpenAI format)--> this server
    /v1/messages          (Anthropic protocol - Claude Code)
    /v1/chat/completions  (OpenAI protocol - OpenCode, DeepSeek)

  --> looks up agent profile via auth token or header
  --> looks up provider, determines best endpoint
  --> translates format if harness protocol != provider protocol
  --> forwards to provider, streaming response back
  --> translates response back if needed

Run:
  python router.py                  # starts on 127.0.0.1:3459
  python router.py --port 3459      # explicit port
"""

import json
import os
import sys
import argparse
from pathlib import Path

from flask import Flask, request, Response
import requests

from translate import (
    anthropic_to_openai_messages,
    openai_to_anthropic_messages,
    anthropic_response_to_openai,
    openai_response_to_anthropic,
)

from dashboard import register_dashboard

BASE_DIR = Path(__file__).parent
PROVIDERS_DIR = BASE_DIR / "profiles" / "providers"
AGENTS_DIR = BASE_DIR / "profiles" / "agents"
HARNESSES_DIR = BASE_DIR / "profiles" / "harnesses"
ENV_FILE = BASE_DIR / ".env"
DEBUG_DIR = BASE_DIR / "debug"


def load_dotenv(path: Path) -> None:
    """Minimal .env loader."""
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_dotenv(ENV_FILE)

app = Flask(__name__)


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No such profile file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    """Save dict as JSON to path."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_agent_profile(name: str) -> dict:
    slug = name.strip().lower().replace(" ", "-")
    candidate = AGENTS_DIR / f"{slug}.json"
    if candidate.exists():
        return load_json(candidate)

    for path in AGENTS_DIR.glob("*.json"):
        data = load_json(path)
        if data.get("name", "").strip().lower() == name.strip().lower():
            return data

    raise FileNotFoundError(f"No agent profile found matching '{name}'")


def load_provider_profile(provider_name: str) -> dict:
    path = PROVIDERS_DIR / f"{provider_name}.json"
    provider = load_json(path)

    env_var = provider.get("api_key_env")
    if not env_var:
        raise ValueError(f"Provider '{provider_name}' has no 'api_key_env' field")

    api_key = os.environ.get(env_var)
    if not api_key:
        raise ValueError(
            f"Environment variable '{env_var}' is not set. "
            f"Add it to {ENV_FILE} or set it in your shell before starting the router."
        )

    provider["api_key"] = api_key
    return provider


def load_harness_profile(harness_name: str) -> dict:
    path = HARNESSES_DIR / f"{harness_name}.json"
    return load_json(path)


def extract_profile_name(req) -> str | None:
    """Extract agent profile name from request headers or query params."""
    if req.headers.get("X-Agent-Profile"):
        return req.headers["X-Agent-Profile"]
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):].strip()
    # Gemini API uses x-goog-api-key header or ?key= query parameter
    if req.headers.get("x-goog-api-key"):
        return req.headers["x-goog-api-key"].strip()
    if req.args.get("key"):
        return req.args["key"].strip()
    return req.headers.get("x-api-key", "").strip() or None


def apply_tool_filtering(body: dict, agent: dict, harness: dict, protocol: str) -> None:
    """Apply tool profile filtering to the request body.

    Tool profiles are now loaded from the harness config (not a global file).
    """
    tool_profile_name = agent.get("tool_profile", "full")
    tool_profiles = harness.get("tool_profiles", {})

    if not tool_profiles:
        return

    tool_profile = tool_profiles.get(tool_profile_name, {})
    tp_mode = tool_profile.get("mode", "keep_all")

    if protocol == "anthropic":
        tools_key = "tools"
        name_getter = lambda t: t.get("name", "")
    else:  # openai
        tools_key = "tools"
        name_getter = lambda t: t.get("function", {}).get("name", "")

    if tp_mode == "strip_all":
        body[tools_key] = []
    elif tp_mode == "whitelist":
        allowed = set(tool_profile.get("tools", []))
        body[tools_key] = [t for t in body.get(tools_key, []) if name_getter(t) in allowed]


def save_debug_tools(body: dict, harness_name: str, protocol: str) -> None:
    """Save tool names from the current request to a per-harness debug file.
    This allows the Discover button in the dashboard to read harness-specific tools."""
    if protocol == "anthropic":
        tools = body.get("tools", [])
        tool_names = [t.get("name", "") for t in tools if t.get("name")]
    elif protocol == "gemini":
        # Gemini format: tools[].functionDeclarations[].name
        tool_names = []
        for tool_group in body.get("tools", []):
            for fd in tool_group.get("functionDeclarations", []):
                if fd.get("name"):
                    tool_names.append(fd["name"])
    else:  # openai
        tools = body.get("tools", [])
        tool_names = [t.get("function", {}).get("name", "") for t in tools if t.get("function", {}).get("name")]

    if not tool_names:
        return

    DEBUG_DIR.mkdir(exist_ok=True)
    debug_path = DEBUG_DIR / f"tools_{harness_name}.json"
    try:
        save_json(debug_path, {"harness": harness_name, "tools": sorted(set(tool_names))})
    except Exception:
        pass


def auto_discover_tools(body: dict, harness: dict, harness_name: str, protocol: str) -> None:
    """Auto-capture: if harness.available_tools is empty, save tool names from the request."""
    if harness.get("available_tools"):
        return  # Already populated, skip

    if protocol == "anthropic":
        tools = body.get("tools", [])
        tool_names = [t.get("name", "") for t in tools if t.get("name")]
    else:  # openai
        tools = body.get("tools", [])
        tool_names = [t.get("function", {}).get("name", "") for t in tools if t.get("function", {}).get("name")]

    if not tool_names:
        return

    # Save discovered tools back to harness profile
    harness_path = HARNESSES_DIR / f"{harness_name}.json"
    try:
        harness_data = load_json(harness_path)
        harness_data["available_tools"] = sorted(set(tool_names))
        save_json(harness_path, harness_data)
        print(f"[AUTO-DISCOVER] Saved {len(tool_names)} tools for harness '{harness_name}': {tool_names}", file=sys.stderr)
    except Exception as e:
        print(f"[AUTO-DISCOVER] Failed to save tools for '{harness_name}': {e}", file=sys.stderr)


def determine_provider_endpoint(provider: dict, harness_protocol: str) -> tuple[str, str]:
    """Determine the best endpoint URL and what protocol it speaks.
    Returns (full_url, provider_protocol)."""
    endpoints = provider.get("endpoints", {})
    base_url = provider["base_url"].rstrip("/")

    # Prefer matching protocol (no translation needed)
    if harness_protocol in endpoints:
        return f"{base_url}{endpoints[harness_protocol]}", harness_protocol

    # Fall back to whatever endpoint is available
    for proto, path in endpoints.items():
        return f"{base_url}{path}", proto

    # Legacy fallback
    return f"{base_url}/v1/messages", "anthropic"


def build_forward_headers(provider: dict, provider_protocol: str, original_request) -> dict:
    """Build headers for the upstream request."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider['api_key']}",
    }

    if provider_protocol == "anthropic":
        headers["x-api-key"] = provider["api_key"]
        headers["anthropic-version"] = original_request.headers.get(
            "anthropic-version", "2023-06-01"
        )

    return headers


def forward_request(target_url: str, body: dict, headers: dict) -> requests.Response:
    """Send request to upstream provider."""
    return requests.post(
        target_url,
        json=body,
        headers=headers,
        stream=True,
        timeout=300,
    )


# Request log — circular buffer of recent requests for dashboard visibility
_request_log = []  # max 50 entries

def _save_request_log(agent_name, agent, final_model, original_model, target_url, protocol):
    import time
    entry = {
        "ts": time.strftime("%H:%M:%S"),
        "agent": agent_name,
        "harness": agent.get("harness", ""),
        "provider": agent.get("provider", ""),
        "model_from_harness": original_model,
        "model_sent": final_model,
        "target_url": target_url,
        "protocol": protocol,
    }
    _request_log.append(entry)
    if len(_request_log) > 50:
        _request_log.pop(0)


@app.route("/api/request-log")
def get_request_log():
    """Return recent request log entries (most recent first)."""
    from flask import jsonify
    return jsonify(list(reversed(_request_log)))



def handle_request(inbound_protocol: str):
    """Core request handler shared between Anthropic and OpenAI endpoints."""
    agent_name = extract_profile_name(request)
    if not agent_name:
        if inbound_protocol == "anthropic":
            return {"error": {"message": "Missing agent profile."}}, 400
        else:
            return {"error": {"message": "Missing agent profile.", "type": "invalid_request_error"}}, 400

    try:
        agent = load_agent_profile(agent_name)
    except FileNotFoundError as e:
        return {"error": {"message": str(e)}}, 404

    try:
        harness = load_harness_profile(agent["harness"])
    except FileNotFoundError:
        return {"error": {"message": f"Unknown harness '{agent.get('harness')}'"}}, 500

    try:
        provider = load_provider_profile(agent["provider"])
    except (FileNotFoundError, ValueError) as e:
        return {"error": {"message": str(e)}}, 500

    body = request.get_json(force=True)

    # Debug: incoming request
    if inbound_protocol == "anthropic":
        msg_chars = sum(len(str(m)) for m in body.get("messages", []))
        system_chars = (sum(len(str(s)) for s in body.get("system", []))
                       if isinstance(body.get("system"), list)
                       else len(str(body.get("system", ""))))
        tools_chars = sum(len(str(t)) for t in body.get("tools", []))
        tools_count = len(body.get("tools", []))
    else:
        msg_chars = sum(len(str(m)) for m in body.get("messages", []))
        system_chars = 0
        tools_chars = sum(len(str(t)) for t in body.get("tools", []))
        tools_count = len(body.get("tools", []))

    original_model = body.get("model", "(none)")
    print(f"[DEBUG] Inbound ({inbound_protocol}): agent={agent_name} harness={agent['harness']} "
          f"model_from_harness={original_model} → override_to={agent['model']}", file=sys.stderr)
    print(f"[DEBUG]   messages={msg_chars}c system={system_chars}c tools={tools_chars}c ({tools_count} defs)", file=sys.stderr)

    # Save per-harness debug tools (for Discover button in dashboard)
    save_debug_tools(body, agent["harness"], inbound_protocol)

    # Auto-discover tools for this harness (Option B from spec)
    auto_discover_tools(body, harness, agent["harness"], inbound_protocol)

    # Log: what the harness requested vs what we'll send
    print(f"[MODEL] '{original_model}' (harness) → '{agent['model']}' (agent profile override)", file=sys.stderr)


    # Override model
    body["model"] = agent["model"]

    # Cap max_tokens
    if agent.get("max_tokens"):
        if body.get("max_tokens", 0) > agent["max_tokens"]:
            body["max_tokens"] = agent["max_tokens"]

    # Apply tool filtering (from harness profile, not global file)
    apply_tool_filtering(body, agent, harness, inbound_protocol)

    # Inject Fusion plugin config (only for Anthropic inbound)
    if agent.get("fusion") and inbound_protocol == "anthropic":
        body["plugins"] = [agent["fusion"]]
        max_tokens_cap = agent.get("fusion_max_tokens", 1000)
        if body.get("max_tokens", 0) > max_tokens_cap:
            body["max_tokens"] = max_tokens_cap
        if agent.get("fusion_strip_tools", True):
            body["tools"] = []

    # Determine provider endpoint and whether translation is needed
    target_url, provider_protocol = determine_provider_endpoint(provider, inbound_protocol)
    needs_translation = (inbound_protocol != provider_protocol)

    # Translate request if needed
    if needs_translation:
        if inbound_protocol == "anthropic" and provider_protocol == "openai":
            body = anthropic_to_openai_messages(body)
        elif inbound_protocol == "openai" and provider_protocol == "anthropic":
            body = openai_to_anthropic_messages(body)

    # Debug: outbound
    tools_after = len(body.get("tools", []))
    print(f"[DEBUG] Outbound ({provider_protocol}): url={target_url} model={body.get('model')} tools={tools_after} translated={needs_translation}", file=sys.stderr)

    # Save to request log (for dashboard visibility)
    _save_request_log(agent_name, agent, body.get('model', ''), original_model, target_url, inbound_protocol)

    # Forward
    headers = build_forward_headers(provider, provider_protocol, request)
    upstream = forward_request(target_url, body, headers)

    # If translation needed on response AND not streaming, translate response
    if needs_translation and not body.get("stream"):
        try:
            response_data = upstream.json()
            if inbound_protocol == "anthropic" and provider_protocol == "openai":
                response_data = openai_response_to_anthropic(response_data)
            elif inbound_protocol == "openai" and provider_protocol == "anthropic":
                response_data = anthropic_response_to_openai(response_data)
            return Response(
                json.dumps(response_data),
                status=upstream.status_code,
                content_type="application/json",
            )
        except Exception as e:
            print(f"[ERROR] Response translation failed: {e}", file=sys.stderr)

    # Stream response back untouched (or if no translation needed)
    return Response(
        upstream.iter_content(chunk_size=1024),
        status=upstream.status_code,
        content_type=upstream.headers.get("content-type", "application/json"),
    )


@app.route("/v1/messages", methods=["POST"])
def messages():
    """Anthropic protocol endpoint (Claude Code)."""
    return handle_request("anthropic")


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """OpenAI protocol endpoint (OpenCode, DeepSeek harness)."""
    return handle_request("openai")


@app.route("/v1beta/models/<path:model_action>", methods=["POST"])
@app.route("/v1alpha/models/<path:model_action>", methods=["POST"])
def gemini_api(model_action):
    """Gemini native API endpoint (Gemini CLI).
    Handles: /v1beta/models/{model}:generateContent
    Captures tools for discovery, then translates to OpenAI and forwards."""
    agent_name = extract_profile_name(request)
    if not agent_name:
        return {"error": {"message": "Missing API key. Pass ?key=agent-slug", "code": 401}}, 401

    try:
        agent = load_agent_profile(agent_name)
    except FileNotFoundError as e:
        return {"error": {"message": str(e), "code": 404}}, 404

    try:
        harness = load_harness_profile(agent["harness"])
    except FileNotFoundError:
        return {"error": {"message": f"Unknown harness '{agent.get('harness')}'"}}, 500

    try:
        provider = load_provider_profile(agent["provider"])
    except (FileNotFoundError, ValueError) as e:
        return {"error": {"message": str(e)}}, 500

    body = request.get_json(force=True)

    # Extract model from URL (e.g. "gemini-2.5-flash:generateContent")
    gemini_model = model_action.split(":")[0] if ":" in model_action else model_action
    print(f"[DEBUG] Inbound (gemini): agent={agent_name} model_from_url={gemini_model} → override_to={agent['model']}", file=sys.stderr)

    # Save tools for discovery (Gemini format)
    save_debug_tools(body, agent["harness"], "gemini")
    auto_discover_tools(body, harness, agent["harness"], "gemini")

    # Translate Gemini → OpenAI format
    openai_messages = []
    # System instruction
    sys_inst = body.get("systemInstruction", {})
    if sys_inst and sys_inst.get("parts"):
        sys_text = " ".join(p.get("text", "") for p in sys_inst["parts"] if p.get("text"))
        if sys_text:
            openai_messages.append({"role": "system", "content": sys_text})

    # Contents → messages
    for content in body.get("contents", []):
        role = content.get("role", "user")
        openai_role = "assistant" if role == "model" else "user"
        parts = content.get("parts", [])
        text_parts = [p["text"] for p in parts if "text" in p]
        if text_parts:
            openai_messages.append({"role": openai_role, "content": " ".join(text_parts)})

    # Tools → OpenAI format
    openai_tools = []
    for tool_group in body.get("tools", []):
        for fd in tool_group.get("functionDeclarations", []):
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": fd.get("name", ""),
                    "description": fd.get("description", ""),
                    "parameters": fd.get("parameters", {}),
                }
            })

    openai_body = {
        "model": agent["model"],
        "messages": openai_messages,
    }
    if openai_tools:
        openai_body["tools"] = openai_tools

    # Apply tool filtering
    apply_tool_filtering(openai_body, agent, harness, "openai")

    # Forward to provider as OpenAI format
    target_url, provider_protocol = determine_provider_endpoint(provider, "openai")
    headers = build_forward_headers(provider, provider_protocol, request)

    tools_count = len(openai_body.get("tools", []))
    print(f"[DEBUG] Outbound (openai): url={target_url} model={openai_body['model']} tools={tools_count}", file=sys.stderr)
    _save_request_log(agent_name, agent, agent['model'], gemini_model, target_url, "gemini")

    upstream = forward_request(target_url, openai_body, headers)

    # Translate OpenAI response → Gemini streaming format
    # Gemini streaming API returns a JSON array of response objects
    is_streaming = "streamGenerateContent" in model_action
    try:
        resp_data = upstream.json()
        # Minimal translation: extract text from OpenAI response
        text_content = ""
        if resp_data.get("choices"):
            msg = resp_data["choices"][0].get("message", {})
            text_content = msg.get("content", "") or ""

        gemini_response = {
            "candidates": [{
                "content": {
                    "parts": [{"text": text_content}],
                    "role": "model"
                },
                "finishReason": "STOP",
            }],
            "usageMetadata": {
                "promptTokenCount": resp_data.get("usage", {}).get("prompt_tokens", 0),
                "candidatesTokenCount": resp_data.get("usage", {}).get("completion_tokens", 0),
                "totalTokenCount": resp_data.get("usage", {}).get("total_tokens", 0),
            },
            "modelVersion": agent["model"],
        }

        if is_streaming:
            # Gemini streaming format: SSE (data: {...}\n\n)
            sse_line = f"data: {json.dumps(gemini_response)}\n\n"
            return Response(
                sse_line,
                status=200,
                content_type="text/event-stream",
            )
        else:
            return Response(
                json.dumps(gemini_response),
                status=200,
                content_type="application/json",
            )
    except Exception as e:
        print(f"[ERROR] Gemini response translation failed: {e}", file=sys.stderr)
        return Response(
            upstream.content,
            status=upstream.status_code,
            content_type=upstream.headers.get("content-type", "application/json"),
        )



@app.route("/health", methods=["GET"])
def health():
    agents = [p.stem for p in AGENTS_DIR.glob("*.json")]
    providers = [p.stem for p in PROVIDERS_DIR.glob("*.json")]
    harnesses = [p.stem for p in HARNESSES_DIR.glob("*.json")]
    return {
        "status": "ok",
        "agents": agents,
        "providers": providers,
        "harnesses": harnesses,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3459)
    args = parser.parse_args()

    print(f"AI Router listening on http://{args.host}:{args.port}")
    print(f"Agent profiles: {[p.stem for p in AGENTS_DIR.glob('*.json')]}")
    print(f"Provider profiles: {[p.stem for p in PROVIDERS_DIR.glob('*.json')]}")
    print(f"Harness profiles: {[p.stem for p in HARNESSES_DIR.glob('*.json')]}")
    print(f"Endpoints: /v1/messages (Anthropic), /v1/chat/completions (OpenAI)")
    register_dashboard(app, BASE_DIR)
    print(f"Dashboard: http://{args.host}:{args.port}/ui")


    app.run(host=args.host, port=args.port, threaded=True)
