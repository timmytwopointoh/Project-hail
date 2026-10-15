"""Hermetic Gemini REST-contract checks; no paid API calls or real secrets."""
import importlib.util
import io
import json
import os
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/gemini_client.py"
SPEC = importlib.util.spec_from_file_location("gemini_client", SCRIPT)
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)

class FakeHTTP:
    def __init__(self, payload):
        self.payload = io.BytesIO(json.dumps(payload).encode("utf-8"))
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def read(self, count=None):
        return self.payload.read(count)

def valid_response(text='{"summary":"ok","edits":[],"risks":[]}'):
    return {
        "modelVersion": "gemini-3.8-flash",
        "candidates": [{"finishReason": "STOP",
                        "content": {"parts": [{"text": text}]}}],
        "usageMetadata": {"promptTokenCount": 123, "candidatesTokenCount": 45,
                          "totalTokenCount": 168},
    }

class GeminiClientTests(unittest.TestCase):
    def test_no_key_skips_network(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(client.generate("check"))
            self.assertNotIn("GEMINI_API_KEY", os.environ)

    def test_authenticated_structured_patch_request_and_usage(self):
        calls = []
        def transport(req, timeout=None):
            calls.append((req, timeout))
            return FakeHTTP(valid_response())
        secret = "testing-secret-never-print-me"
        with patch.dict(os.environ, {"GEMINI_API_KEY": secret, "GEMINI_MODEL": "gemini-3.8-flash"}):
            answer = client.generate("Fix the swing", structured=True, transport=transport)
            self.assertNotIn("GEMINI_API_KEY", os.environ)
        self.assertEqual(1, len(calls))
        req, timeout = calls[0]
        self.assertEqual(90, timeout)
        self.assertTrue(req.full_url.endswith("gemini-3.8-flash:generateContent"))
        self.assertNotIn(secret, req.full_url)
        self.assertEqual(secret, req.get_header("X-goog-api-key"))
        payload = json.loads(req.data)
        schema = payload["generationConfig"]["responseFormat"]["text"]
        self.assertEqual("application/json", schema["mimeType"])
        self.assertEqual(["summary", "edits", "risks"], schema["schema"]["required"])
        self.assertEqual(168, answer["usage"]["totalTokenCount"])
        self.assertEqual("gemini-3.8-flash", answer["model"])

    def test_vision_picture_encoded_without_external_upload(self):
        data = b"\xff\xd8\xff\xda jpeg fixture"
        body = client.request_body("Describe frame", [data])
        part = body["contents"][0]["parts"][1]
        self.assertEqual("image/jpeg", part["inline_data"]["mime_type"])
        self.assertEqual(data, __import__("base64").b64decode(part["inline_data"]["data"]))
        self.assertNotIn("responseFormat", body["generationConfig"])

    def test_retries_transient_http_then_succeeds(self):
        attempts, sleeps = [], []
        def transport(req, timeout=None):
            attempts.append(1)
            if len(attempts) == 1:
                raise urllib.error.HTTPError(req.full_url, 429, "rate limit", {}, io.BytesIO(b""))
            return FakeHTTP(valid_response("done"))
        result = client.generate("retry", api_key="fixture", retries=2,
                                 sleeper=sleeps.append, transport=transport)
        self.assertEqual("done", result["text"])
        self.assertEqual(2, len(attempts))
        self.assertEqual([1], sleeps)

    def test_fails_closed_on_bad_key_error_without_retry_or_leak(self):
        attempts = []
        def transport(req, timeout=None):
            attempts.append(1)
            raise urllib.error.HTTPError(req.full_url, 401, "secret-value", {}, None)
        with self.assertRaises(client.GeminiError) as ctx:
            client.generate("bad auth", api_key="secret-value", transport=transport)
        self.assertEqual(1, len(attempts))
        self.assertEqual("Gemini API returned HTTP 401", str(ctx.exception))
        self.assertNotIn("secret-value", str(ctx.exception))

    def test_reject_truncated_or_blocked_results(self):
        for response in [
            {"candidates": [{"finishReason": "MAX_TOKENS",
                             "content": {"parts": [{"text": "{}"}]}}]},
            {"promptFeedback": {"blockReason": "SAFETY"}, "candidates": []},
            {"candidates": [{"finishReason": "STOP",
                             "content": {"parts": []}}]},
        ]:
            with self.assertRaises(client.GeminiError):
                client.parse_response(response, "gemini-3.8-flash")

    def test_reject_bad_models_oversized_or_invalid_configuration(self):
        with self.assertRaises(ValueError):
            client.generate("x", api_key="fixture", model="../traversal")
        with self.assertRaises(ValueError):
            client.generate("x", api_key="fixture", retries=999)
        with self.assertRaises(ValueError):
            client.request_body("x" * 90001)
        with self.assertRaises(ValueError):
            client.request_body("frame", [b"x" * 2_000_001])

if __name__ == "__main__":
    unittest.main()
