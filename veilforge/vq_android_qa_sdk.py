#!/usr/bin/env python3
"""Shared fail-closed Android GLES capture/evidence contract (M34-10).

Factory and M30 keep their distinct renderer/shader requirements. This module
centralizes the *presented pixel* gate and independent PNG integrity audit.
A JSON assertion is never trusted without re-opening the actual screenshot.
"""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import re

MIN_FOREGROUND = 0.0015
MIN_CONTRAST = 3.0
MAX_MODAL = 0.70
MAX_CAPTURE_BYTES = 25 * 1024 * 1024


def frame_is_trusted(score):
    """The same conservative framebuffer policy for factory and M30."""
    return (
        isinstance(score, dict)
        and score.get("renderer_background_confirmed") is True
        and isinstance(score.get("foreground_fraction"), (int, float))
        and score["foreground_fraction"] >= MIN_FOREGROUND
        and isinstance(score.get("channel_stddev"), (int, float))
        and score["channel_stddev"] >= MIN_CONTRAST
        and isinstance(score.get("modal_overlay_fraction"), (int, float))
        and score["modal_overlay_fraction"] < MAX_MODAL
    )


def evidence_png(root, relative_name, expected_sha256, reported_metrics):
    """Reopen and verify an Android screenshot rather than trusting JSON metrics.

    Only normal, in-root PNG paths are accepted. Recompute all screenshot
    foreground, compositor-background and modal metrics independently.
    Caller is responsible for checking expected camera/asset/role identity.
    """
    if not isinstance(relative_name, str) or not relative_name or "\\" in relative_name or "\x00" in relative_name:
        raise ValueError("Unsafe screenshot path")
    path = PurePosixPath(relative_name)
    if path.is_absolute() or any(part in ("..", ".") for part in relative_name.split("/")) or not path.parts:
        raise ValueError("Unsafe screenshot path")
    root = Path(root).resolve()
    target = root.joinpath(*path.parts)
    if not target.resolve().is_relative_to(root) or target.is_symlink():
        raise ValueError("Screenshot escapes evidence directory")
    if not target.is_file():
        raise ValueError("Missing screenshot file")
    size = target.stat().st_size
    if size < 1000 or size > MAX_CAPTURE_BYTES:
        raise ValueError("Screenshot byte length outside allowed range")
    if not isinstance(expected_sha256, str) or re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256) is None:
        raise ValueError("Invalid screenshot digest")
    data = target.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256.lower():
        raise ValueError("Screenshot SHA256 mismatch")
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Screenshot is not a PNG")
    try:
        from PIL import Image
        from android_visual_qa import metrics
        with Image.open(target) as opened:
            if opened.format != "PNG":
                raise ValueError("Screenshot is not PNG encoded")
            frame = opened.convert("RGB")
        if min(frame.size) < 240 or max(frame.size) < 450:
            raise ValueError("Screenshot dimensions too small")
        actual = metrics(frame)
    except (OSError, ValueError, RuntimeError) as error:
        raise ValueError("Unreadable or invalid PNG pixels: " + str(error)) from error
    if not frame_is_trusted(actual):
        raise ValueError("Actual PNG pixels fail GLES/background/foreground/modal gate")
    if not frame_is_trusted(reported_metrics):
        raise ValueError("Reported screenshot metrics fail trusted-frame gate")
    if reported_metrics.get("dimensions") != actual["dimensions"]:
        raise ValueError("Reported screenshot dimensions mismatch")
    for key, tolerance in (
        ("foreground_fraction", .00002),
        ("channel_stddev", .002),
        ("modal_overlay_fraction", .00002),
    ):
        if abs(reported_metrics[key] - actual[key]) > tolerance:
            raise ValueError("Reported screenshot pixel metrics mismatch: " + key)
    return actual
