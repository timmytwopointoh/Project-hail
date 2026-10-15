#!/usr/bin/env python3
"""Minimal, testable Gemini REST client for VEILBOUND's isolated worker farm.

Uses Google's generateContent REST API with per-call JSON mode, bounded
transient-error retries, timeouts and non-sensitive usage metadata. The model
never receives a GitHub credential, and API keys are never included in URLs,
saved artifacts, errors or subprocesses.
"""
import base64
import json
import os
import re
import time
import urllib.error
import urllib.request

DEFAULT_MODEL = "gemini-3.8-flash"
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models/"
TRANSIENT_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 2   # At most three billable request attempts per worker.
MAX_JSON_BYTES = 1_500_000

# This guides the provider, but every response is ALSO validated locally.
CODE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "edits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "find": {"type": "string"},
                    "replace": {"type": "string"},
                },
                "required": ["path", "find", "replace"],
            },
        },
        "risks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "edits", "risks"],
}

class GeminiError(RuntimeError):
    """Safe error message: never includes raw responses or secret credentials."""


def request_body(prompt, pictures=None, *, json_schema=None):
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Nonempty prompt required")
    if len(prompt) > 90000:
        raise ValueError("Prompt exceeds configured source budget")
    parts = [{"text": prompt}]
    for jpg in pictures or []:
        if not isinstance(jpg, bytes) or len(jpg) > 2_000_000:
            raise ValueError("Each JPEG must be bytes and under 2MB")
        parts.append({"inline_data": {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(jpg).decode("ascii"),
        }})
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"candidateCount": 1, "maxOutputTokens": 8192},
    }
    if json_schema is not None:
        body["generationConfig"]["responseFormat"] = {
            "text": {"mimeType": "application/json", "schema": json_schema}
        }
    return body


def parse_response(response, model):
    if not isinstance(response, dict):
        raise GeminiError("Gemini returned a malformed response envelope")
    choices = response.get("candidates")
    if not isinstance(choices, list) or not choices:
        feedback = response.get("promptFeedback") or {}
        block = feedback.get("blockReason", "no candidate") if isinstance(feedback, dict) else "no candidate"
        raise GeminiError("Gemini generated no candidate: " + str(block)[:60])
    candidate = choices[0]
    if not isinstance(candidate, dict):
        raise GeminiError("Gemini generated an invalid candidate")
    finish = candidate.get("finishReason", "")
    if finish not in ("STOP", ""):
        raise GeminiError("Gemini stopped without a complete response: " + str(finish)[:40])
    content = candidate.get("content")
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        raise GeminiError("Gemini returned no text parts")
    answer = "\n".join(p.get("text", "") for p in parts
                       if isinstance(p, dict) and isinstance(p.get("text"), str))
    if not answer.strip():
        raise GeminiError("Gemini returned an empty text response")
    usage = response.get("usageMetadata") or {}
    if not isinstance(usage, dict):
        usage = {}
    usage_safe = {}
    for key in ("promptTokenCount", "candidatesTokenCount", "totalTokenCount",
                "thoughtsTokenCount"):
        number = usage.get(key)
        if isinstance(number, int) and number >= 0:
            usage_safe[key] = number
    return {
        "text": answer, "model": str(response.get("modelVersion") or model)[:100],
        "usage": usage_safe,
    }


def generate(prompt, pictures=None, *, structured=False, api_key=None,
             model=None, retries=MAX_RETRIES, sleeper=time.sleep, transport=None):
    # Consume the key so subsequent Java compiler/test subprocesses cannot
    # accidentally inherit GEMINI_API_KEY from this Python process.
    key = api_key if api_key is not None else os.environ.pop("GEMINI_API_KEY", "")
    if not key:
        return None
    name = model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL
    if not MODEL_PATTERN.fullmatch(name):
        raise ValueError("Unsupported Gemini model name")
    if not isinstance(retries, int) or not 0 <= retries <= MAX_RETRIES:
        raise ValueError("Gemini retry count exceeds policy")
    payload = request_body(prompt, pictures,
                           json_schema=CODE_SCHEMA if structured else None)
    request = urllib.request.Request(
        API_ROOT + name + ":generateContent",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    call = transport or urllib.request.urlopen
    for attempt in range(retries + 1):
        try:
            with call(request, timeout=90) as response:
                raw = response.read(MAX_JSON_BYTES + 1)
            if len(raw) > MAX_JSON_BYTES:
                raise GeminiError("Gemini response exceeds size limit")
            parsed = json.loads(raw)
            return parse_response(parsed, name)
        except urllib.error.HTTPError as err:
            if err.code in TRANSIENT_CODES and attempt < retries:
                sleeper(min(2 ** attempt, 4))
                continue
            raise GeminiError("Gemini API returned HTTP " + str(err.code)) from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < retries:
                sleeper(min(2 ** attempt, 4))
                continue
            raise GeminiError("Gemini network request failed after retries") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise GeminiError("Gemini API returned malformed JSON") from None
    raise GeminiError("Gemini request did not complete")
