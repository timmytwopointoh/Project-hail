#!/usr/bin/env python3
"""Manual one-request Gemini connectivity test (never logs the key)."""
import json
import os
import sys

from gemini_client import GeminiError, generate


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY is not configured. Add it under GitHub Actions secrets.")
        return 2
    try:
        result = generate(
            "Reply with exactly: VEILBOUND_GEMINI_READY",
            retries=1,
        )
    except (GeminiError, ValueError) as err:
        print("Gemini connection failed: " + str(err))
        return 1
    if result is None or "VEILBOUND_GEMINI_READY" not in result["text"]:
        print("Gemini returned an unexpected health-check response.")
        return 1
    # Diagnostic usage only; no actual source code or private secrets.
    print(json.dumps({"status": "connected",
                      "provider": "Google Gemini",
                      "model": result["model"],
                      "usage": result["usage"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
