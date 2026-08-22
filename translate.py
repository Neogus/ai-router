"""
Protocol translation between Anthropic and OpenAI message formats.

Used by the router to bridge harnesses that speak one protocol
with providers that speak another.
"""

import json
import uuid


def anthropic_to_openai_messages(body: dict) -> dict:
    """Convert an Anthropic /v1/messages request body to OpenAI /v1/chat/completions format."""
    openai_body = {}

    # Model
    openai_body["model"] = body.get("model", "")

    # Max tokens
    if body.get("max_tokens"):
        openai_body["max_tokens"] = body["max_tokens"]

    # Temperature
    if body.get("temperature") is not None:
        openai_body["temperature"] = body["temperature"]

    # Top-p
    if body.get("top_p") is not None:
        openai_body["top_p"] = body["top_p"]

    # Stream
    if body.get("stream") is not None:
        openai_body["stream"] = body["stream"]

    # Messages: system prompt becomes a system message
    messages = []
    system = body.get("system")
    if system:
        if isinstance(system, str):
            messages.append({"role": "system", "content": system})
        elif isinstance(system, list):
            # Anthropic system can be list of content blocks
            text_parts = []
            for block in system:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block["text"])
            messages.append({"role": "system", "content": "\n".join(text_parts)})

    # Convert each message
    for msg in body.get("messages", []):
        converted = _convert_anthropic_message_to_openai(msg)
        if isinstance(converted, list):
            messages.extend(converted)
        else:
            messages.append(converted)

    openai_body["messages"] = messages

    # Tools
    tools = body.get("tools", [])
    if tools:
        openai_body["tools"] = [_convert_anthropic_tool_to_openai(t) for t in tools]

    # Tool choice
    if body.get("tool_choice"):
        tc = body["tool_choice"]
        if isinstance(tc, dict) and tc.get("type") == "tool":
            openai_body["tool_choice"] = {
                "type": "function",
                "function": {"name": tc.get("name", "")}
            }
        elif tc == "auto":
            openai_body["tool_choice"] = "auto"
        elif tc == "any":
            openai_body["tool_choice"] = "required"

    return openai_body


def openai_to_anthropic_messages(body: dict) -> dict:
    """Convert an OpenAI /v1/chat/completions request body to Anthropic /v1/messages format."""
    anthropic_body = {}

    # Model
    anthropic_body["model"] = body.get("model", "")

    # Max tokens (required for Anthropic)
    anthropic_body["max_tokens"] = body.get("max_tokens", 4096)

    # Temperature
    if body.get("temperature") is not None:
        anthropic_body["temperature"] = body["temperature"]

    # Top-p
    if body.get("top_p") is not None:
        anthropic_body["top_p"] = body["top_p"]

    # Stream
    if body.get("stream") is not None:
        anthropic_body["stream"] = body["stream"]

    # Messages: extract system message, convert the rest
    messages = []
    system_parts = []

    for msg in body.get("messages", []):
        if msg["role"] == "system":
            system_parts.append(msg.get("content", ""))
        elif msg["role"] == "tool":
            # Tool results in OpenAI format → Anthropic tool_result
            messages.append(_convert_openai_tool_result_to_anthropic(msg))
        elif msg["role"] == "assistant" and msg.get("tool_calls"):
            messages.append(_convert_openai_assistant_tool_calls_to_anthropic(msg))
        else:
            messages.append(_convert_openai_message_to_anthropic(msg))

    if system_parts:
        anthropic_body["system"] = "\n".join(system_parts)

    anthropic_body["messages"] = messages

    # Tools
    tools = body.get("tools", [])
    if tools:
        anthropic_body["tools"] = [_convert_openai_tool_to_anthropic(t) for t in tools]

    # Tool choice
    if body.get("tool_choice"):
        tc = body["tool_choice"]
        if isinstance(tc, dict) and tc.get("type") == "function":
            anthropic_body["tool_choice"] = {
                "type": "tool",
                "name": tc.get("function", {}).get("name", "")
            }
        elif tc == "auto":
            anthropic_body["tool_choice"] = {"type": "auto"}
        elif tc == "required":
            anthropic_body["tool_choice"] = {"type": "any"}

    return anthropic_body


def anthropic_response_to_openai(response: dict) -> dict:
    """Convert an Anthropic response to OpenAI chat completion format."""
    content_blocks = response.get("content", [])

    # Build the message
    message = {"role": "assistant"}
    text_parts = []
    tool_calls = []

    for block in content_blocks:
        if isinstance(block, dict):
            if block.get("type") == "text":
                text_parts.append(block["text"])
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id", f"call_{uuid.uuid4().hex[:24]}"),
                    "type": "function",
                    "function": {
                        "name": block["name"],
                        "arguments": json.dumps(block.get("input", {}))
                    }
                })

    message["content"] = "\n".join(text_parts) if text_parts else None
    if tool_calls:
        message["tool_calls"] = tool_calls

    # Map stop_reason
    stop_reason = response.get("stop_reason", "end_turn")
    finish_reason_map = {
        "end_turn": "stop",
        "tool_use": "tool_calls",
        "max_tokens": "length",
        "stop_sequence": "stop",
    }
    finish_reason = finish_reason_map.get(stop_reason, "stop")

    # Build OpenAI response
    openai_response = {
        "id": response.get("id", f"chatcmpl-{uuid.uuid4().hex[:24]}"),
        "object": "chat.completion",
        "model": response.get("model", ""),
        "choices": [{
            "index": 0,
            "message": message,
            "finish_reason": finish_reason,
        }],
        "usage": {
            "prompt_tokens": response.get("usage", {}).get("input_tokens", 0),
            "completion_tokens": response.get("usage", {}).get("output_tokens", 0),
            "total_tokens": (
                response.get("usage", {}).get("input_tokens", 0) +
                response.get("usage", {}).get("output_tokens", 0)
            ),
        }
    }

    return openai_response


def openai_response_to_anthropic(response: dict) -> dict:
    """Convert an OpenAI chat completion response to Anthropic format."""
    choice = response.get("choices", [{}])[0]
    message = choice.get("message", {})

    content = []

    # Text content
    if message.get("content"):
        content.append({"type": "text", "text": message["content"]})

    # Tool calls
    for tc in message.get("tool_calls", []):
        func = tc.get("function", {})
        try:
            input_data = json.loads(func.get("arguments", "{}"))
        except json.JSONDecodeError:
            input_data = {"raw": func.get("arguments", "")}

        content.append({
            "type": "tool_use",
            "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:24]}"),
            "name": func.get("name", ""),
            "input": input_data,
        })

    # Map finish_reason
    finish_reason = choice.get("finish_reason", "stop")
    stop_reason_map = {
        "stop": "end_turn",
        "tool_calls": "tool_use",
        "length": "max_tokens",
        "content_filter": "end_turn",
    }
    stop_reason = stop_reason_map.get(finish_reason, "end_turn")

    usage = response.get("usage", {})

    anthropic_response = {
        "id": response.get("id", f"msg_{uuid.uuid4().hex[:24]}"),
        "type": "message",
        "role": "assistant",
        "content": content,
        "model": response.get("model", ""),
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
    }

    return anthropic_response


# --- Internal helpers ---

def _convert_anthropic_message_to_openai(msg: dict):
    """Convert a single Anthropic message to OpenAI format."""
    role = msg.get("role", "user")
    content = msg.get("content")

    if role == "assistant":
        result = {"role": "assistant"}
        if isinstance(content, str):
            result["content"] = content
            return result
        elif isinstance(content, list):
            text_parts = []
            tool_calls = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block["text"])
                    elif block.get("type") == "tool_use":
                        tool_calls.append({
                            "id": block.get("id", f"call_{uuid.uuid4().hex[:24]}"),
                            "type": "function",
                            "function": {
                                "name": block["name"],
                                "arguments": json.dumps(block.get("input", {}))
                            }
                        })
            result["content"] = "\n".join(text_parts) if text_parts else None
            if tool_calls:
                result["tool_calls"] = tool_calls
            return result
        result["content"] = str(content) if content else ""
        return result

    elif role == "user":
        if isinstance(content, str):
            return {"role": "user", "content": content}
        elif isinstance(content, list):
            # Check for tool_result blocks
            tool_results = []
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "tool_result":
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": block.get("tool_use_id", ""),
                            "content": _extract_text_from_content(block.get("content", ""))
                        })
                    elif block.get("type") == "text":
                        text_parts.append(block["text"])
                    elif block.get("type") == "image":
                        text_parts.append("[image]")

            if tool_results and not text_parts:
                return tool_results
            elif tool_results and text_parts:
                return tool_results + [{"role": "user", "content": "\n".join(text_parts)}]
            else:
                return {"role": "user", "content": "\n".join(text_parts) if text_parts else ""}

    return {"role": role, "content": str(content) if content else ""}


def _convert_openai_message_to_anthropic(msg: dict) -> dict:
    """Convert a single OpenAI message to Anthropic format."""
    role = msg.get("role", "user")
    content = msg.get("content", "")

    if role == "assistant":
        if isinstance(content, str) and content:
            return {"role": "assistant", "content": [{"type": "text", "text": content}]}
        return {"role": "assistant", "content": [{"type": "text", "text": content or ""}]}

    return {"role": role, "content": content if content else ""}


def _convert_openai_assistant_tool_calls_to_anthropic(msg: dict) -> dict:
    """Convert an OpenAI assistant message with tool_calls to Anthropic format."""
    content = []
    if msg.get("content"):
        content.append({"type": "text", "text": msg["content"]})

    for tc in msg.get("tool_calls", []):
        func = tc.get("function", {})
        try:
            input_data = json.loads(func.get("arguments", "{}"))
        except json.JSONDecodeError:
            input_data = {"raw": func.get("arguments", "")}

        content.append({
            "type": "tool_use",
            "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:24]}"),
            "name": func.get("name", ""),
            "input": input_data,
        })

    return {"role": "assistant", "content": content}


def _convert_openai_tool_result_to_anthropic(msg: dict) -> dict:
    """Convert an OpenAI tool result message to Anthropic format."""
    return {
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": msg.get("tool_call_id", ""),
            "content": msg.get("content", ""),
        }]
    }


def _convert_anthropic_tool_to_openai(tool: dict) -> dict:
    """Convert an Anthropic tool definition to OpenAI format."""
    return {
        "type": "function",
        "function": {
            "name": tool.get("name", ""),
            "description": tool.get("description", ""),
            "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
        }
    }


def _convert_openai_tool_to_anthropic(tool: dict) -> dict:
    """Convert an OpenAI tool definition to Anthropic format."""
    func = tool.get("function", {})
    return {
        "name": func.get("name", ""),
        "description": func.get("description", ""),
        "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
    }


def _extract_text_from_content(content) -> str:
    """Extract plain text from Anthropic content (string or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)
