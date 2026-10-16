"""Hermetic private inference tests. No Ollama install, model download or API key."""
import importlib.util
import io
import json
import os
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "scripts/local_ai.py"
SPEC = importlib.util.spec_from_file_location("veilbound_local_ai", PATH)
ai = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ai)

class FakeHTTP:
    def __init__(self, body):
        self.content = io.BytesIO(json.dumps(body).encode("utf-8"))
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, maxbytes): return self.content.read(maxbytes)

def answer(text='{"summary":"ok","edits":[],"risks":[]}'):
    return {"response": text, "done": True, "done_reason": "stop",
            "prompt_eval_count": 60, "eval_count": 29, "total_duration": 10000}

class LocalAITests(unittest.TestCase):
    def test_loopback_only_and_structured_code_contract(self):
        calls = []
        def transport(request, timeout):
            calls.append((request, timeout))
            return FakeHTTP(answer())
        with patch.dict(os.environ, {"VEILBOUND_LOCAL_MODEL": "qwen2.5-coder:1.5b"}):
            result = ai.generate("Improve Java combat", structured=True, transport=transport)
        req, timeout = calls[0]
        self.assertEqual("http://127.0.0.1:11434/api/generate", req.full_url)
        self.assertEqual(300, timeout)
        payload = json.loads(req.data)
        self.assertFalse(payload["stream"])
        self.assertEqual("qwen2.5-coder:1.5b", payload["model"])
        self.assertEqual(["summary", "edits", "risks"], payload["format"]["required"])
        self.assertEqual("VEILBOUND local inference", result["provider"])
        self.assertEqual(29, result["usage"]["eval_count"])
        self.assertEqual("application/json", req.get_header("Content-type"))
        self.assertNotIn("authorization", repr(req.headers).lower())
        self.assertNotIn("google", repr(req.headers).lower())

    def test_rejects_images_until_true_local_vision_model_exists(self):
        with self.assertRaisesRegex(ValueError, "Image review"):
            ai.generate("Inspect", photos=[b"fake image"], transport=lambda *a, **k: None)

    def test_text_only_will_not_claim_to_have_seen_images(self):
        body = ai.make_request("Telemetry only")
        self.assertIsNone(body["format"])
        self.assertNotIn("images", body)

    def test_limits_and_bad_model_names(self):
        for prompt in ("", "x" * 28001):
            with self.assertRaises(ValueError):
                ai.make_request(prompt)
        for name in ("../../passwd", "bad model; rm -rf", "x" * 112):
            with self.assertRaises(ValueError):
                ai.make_request("okay", model=name)

    def test_missing_server_fails_closed_not_silently_skipped(self):
        def transport(req, timeout):
            raise urllib.error.URLError("private information")
        with self.assertRaises(ai.LocalModelError) as e:
            ai.generate("source", transport=transport)
        self.assertIn("localhost", str(e.exception).replace("Local Ollama", "localhost"))

    def test_incomplete_results_rejected(self):
        for response in ({"response": "ok", "done": False},
                         {"response": "", "done": True},
                         {"response": "ok", "done": True, "done_reason": "length"},
                         {"done": True}):
            with self.assertRaises(ai.LocalModelError):
                ai.parse_response(response, "qwen2.5-coder:1.5b")

    def test_valid_response_has_no_external_api_credentials(self):
        req = ai.make_request("Fix the animation", structured=True)
        self.assertEqual(req["keep_alive"], "2m")
        self.assertEqual(req["options"]["num_thread"], 2)
        self.assertLessEqual(req["options"]["num_ctx"], 8192)

if __name__ == "__main__":
    unittest.main()
