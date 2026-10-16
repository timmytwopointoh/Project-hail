#!/usr/bin/env python3
"""Proof of actual inference, not a mocked provider-free unit test."""
import argparse
import json
import sys
from pathlib import Path

from local_ai import LocalModelError, generate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5-coder:0.5b")
    parser.add_argument("--out", type=Path, default=Path("inspection_output/local-ai-smoke"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    prompt = (
        "You are the VEILBOUND local coding assistant. Return JSON using the "
        "specified schema. This is a connectivity smoke test, NOT a request to "
        "edit real game source. Set summary to a brief statement that the "
        "local model is online, edits to an empty array, risks to an empty "
        "array. Do not include markdown or code fences."
    )
    try:
        response = generate(prompt, structured=True, model=args.model, timeout=250)
        proposal = json.loads(response["text"])
        if not isinstance(proposal, dict) or not isinstance(proposal.get("summary"), str):
            raise ValueError("Missing required AI summary")
        if proposal.get("edits") != [] or proposal.get("risks") != []:
            raise ValueError("Smoke model proposed changes or risks unexpectedly")
        report = {"result": "passed", "actual_local_inference": True,
                  "model": response["model"], "usage": response["usage"],
                  "zero_api_keys_used": True, "no_source_edited": True,
                  "summary": proposal["summary"][:250]}
    except (LocalModelError, ValueError) as exc:
        report = {"result": "failed", "actual_local_inference": False,
                  "reason": str(exc)[:300]}
    (args.out / "real_local_ai_smoke.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "passed" else 1

if __name__ == "__main__":
    sys.exit(main())
