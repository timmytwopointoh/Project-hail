#!/usr/bin/env python3
"""VEILBOUND's self-hosted coding brain: local Ollama and open-weight models.

Only the loopback endpoint is allowed. Nothing is sent to Gemini or another
remote inference API. The model is an independently released open-weight
foundation model; task planning, tool boundaries, testing and promotion rules
are VEILBOUND's own implementation.
"""
import json
import os
import re
import urllib.error
import urllib.request

DEFAULT_MODEL = "qwen2.5-coder:1.5b"
API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,110}$")
MAX_INPUT_CHARS = 28000
MAX_RESPONSE_BYTES = 500000
CODE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "edits": {"type": "array", "items": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "find": {"type": "string"},
                           "replace": {"type": "string"}},
            "required": ["path", "find", "replace"]}},
        "risks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "edits", "risks"],
}

class LocalModelError(RuntimeError):
    """Privacy-preserving, safe-to-print inference error."""


def make_request(prompt, *, structured=False, model=None):
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_INPUT_CHARS:
        raise ValueError("Empty or oversized local AI request")
    model = model or os.environ.get("VEILBOUND_LOCAL_MODEL") or DEFAULT_MODEL
    if not isinstance(model, str) or not MODEL_PATTERN.fullmatch(model):
        raise ValueError("Invalid locally installed model name")
    return {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": CODE_SCHEMA if structured else None,
        "options": {
            "temperature": 0.15,
            "num_ctx": 8192,
            "num_predict": 1536 if structured else 360,
            "num_thread": 2,
        },
        "keep_alive": "2m",
    }


def parse_response(obj, model):
    if not isinstance(obj, dict) or not isinstance(obj.get("response"), str):
        raise LocalModelError("The local model returned no text")
    if obj.get("done") is not True:
        raise LocalModelError("Local inference did not complete")
    if obj.get("done_reason") not in ("stop", None):
        raise LocalModelError("Local inference ended prematurely")
    answer = obj["response"].strip()
    if not answer:
        raise LocalModelError("The local model generated empty text")
    tokens = {}
    for key in ("prompt_eval_count", "eval_count", "total_duration"):
        number = obj.get(key)
        if isinstance(number, int) and number >= 0:
            tokens[key] = number
    return {"text": answer, "model": model,
            "usage": tokens, "provider": "VEILBOUND local inference"}


def generate(prompt, photos=None, *, structured=False, model=None,
             transport=None, timeout=300):
    # The coding model is text-only. Never silently claim to inspect pixels.
    if photos:
        raise ValueError("Image review requires a separately approved local vision model")
    payload = make_request(prompt, structured=structured, model=model)
    selected = payload["model"]
    if payload["format"] is None:
        del payload["format"]
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST")
    call = transport or urllib.request.urlopen
    try:
        with call(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise LocalModelError("Local inference result exceeds safety limit")
        return parse_response(json.loads(raw), selected)
    except urllib.error.HTTPError as exc:
        raise LocalModelError("Local inference returned HTTP " + str(exc.code)) from None
    except (urllib.error.URLError, OSError, TimeoutError):
        raise LocalModelError("Local Ollama unavailable: start the local model service") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise LocalModelError("Local model returned invalid JSON envelope") from None
