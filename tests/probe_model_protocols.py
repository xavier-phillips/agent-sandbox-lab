"""Bounded synthetic tool-call checks for an OpenAI-compatible inference route.

No agent code runs here. The key comes from one environment variable and is
never printed. Test both APIs: a chat-only success cannot qualify Responses.
"""

import argparse
import json
import os
import time
import urllib.error
import urllib.request


PARAMETERS = {
    "type": "object",
    "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
    "required": ["a", "b"],
    "additionalProperties": False,
}
PROMPT = "Call probe_sum with a=2 and b=3. After receiving its result, reply with exactly 5."


def post(base, path, key, body, timeout):
    request = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def probe_chat(send, model):
    tool = {"type": "function", "function": {"name": "probe_sum", "parameters": PARAMETERS}}
    messages = [{"role": "user", "content": PROMPT}]
    first = send("/chat/completions", {
        "model": model, "messages": messages, "tools": [tool],
        "tool_choice": {"type": "function", "function": {"name": "probe_sum"}},
        "max_tokens": 512,
    })
    message = first["choices"][0]["message"]
    calls = message.get("tool_calls", [])
    assert len(calls) == 1, "expected one native tool call"
    call = calls[0]
    assert call["function"]["name"] == "probe_sum", "wrong tool"
    assert json.loads(call["function"]["arguments"]) == {"a": 2, "b": 3}, "wrong arguments"
    messages += [message, {"role": "tool", "tool_call_id": call["id"], "content": '{"sum":5}'}]
    second = send("/chat/completions", {
        "model": model, "messages": messages, "tools": [tool],
        "tool_choice": "none", "max_tokens": 512,
    })
    assert second["choices"][0]["message"].get("content", "").strip() == "5", "tool result not consumed"
    return {"returned_model": first.get("model"), "native_call": True, "tool_result_consumed": True}


def probe_responses(send, model):
    tool = {"type": "function", "name": "probe_sum", "parameters": PARAMETERS}
    initial = [{"role": "user", "content": PROMPT}]
    first = send("/responses", {
        "model": model, "input": initial, "tools": [tool],
        "tool_choice": {"type": "function", "name": "probe_sum"},
        "max_output_tokens": 512, "store": False,
    })
    assert first.get("status") == "completed", "incomplete response"
    calls = [item for item in first.get("output", []) if item.get("type") == "function_call"]
    assert len(calls) == 1, "expected one Responses function call"
    call = calls[0]
    assert call["name"] == "probe_sum", "wrong tool"
    assert json.loads(call["arguments"]) == {"a": 2, "b": 3}, "wrong arguments"
    continued = initial + first["output"] + [
        {"type": "function_call_output", "call_id": call["call_id"], "output": '{"sum":5}'}
    ]
    second = send("/responses", {
        "model": model, "input": continued, "tools": [tool],
        "tool_choice": "none", "max_output_tokens": 512, "store": False,
    })
    assert second.get("status") == "completed", "incomplete continuation"
    text = "".join(part.get("text", "") for item in second.get("output", [])
                   if item.get("type") == "message" for part in item.get("content", [])
                   if part.get("type") == "output_text")
    assert text.strip() == "5", "Responses tool result not consumed"
    return {"returned_model": first.get("model"), "native_call": True, "tool_result_consumed": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="API root including /v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key-env", default="OMNIROUTE_API_KEY")
    parser.add_argument("--timeout", type=float, default=45)
    args = parser.parse_args()
    key = os.environ.get(args.api_key_env)
    if not key:
        parser.error("API key environment variable is empty")
    send = lambda path, body: post(args.base_url, path, key, body, args.timeout)
    results = []
    for name, check in [("chat_completions", probe_chat), ("responses", probe_responses)]:
        started = time.monotonic()
        try:
            detail = check(send, args.model)
            result = {"api": name, "pass": True, **detail}
        except urllib.error.HTTPError as error:
            result = {"api": name, "pass": False, "http_status": error.code}
        except (AssertionError, KeyError, TypeError, ValueError, OSError) as error:
            result = {"api": name, "pass": False, "error_type": type(error).__name__}
            if isinstance(error, AssertionError):
                result["reason"] = str(error)
        result["seconds"] = round(time.monotonic() - started, 2)
        results.append(result)
        print(json.dumps(result), flush=True)
    return 0 if all(result["pass"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
