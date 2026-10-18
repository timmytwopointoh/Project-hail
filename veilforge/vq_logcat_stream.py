#!/usr/bin/env python3
"""Persistent, bounded Android logcat telemetry for genuine emulator QA.

One subscriber records all filtered output to disk; bounded RAM cursors detect
fresh frame markers and sticky GLES failures. A startup sentinel confirms the
subscriber is attached before a renderer is launched. No frame is synthesized.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
import subprocess
import threading
import time
import uuid

FAILURE_MARKERS = ("GL_ERROR", "LOAD_FAIL", "ASSET_NOT_FOUND")


class LogcatEvents:
    """Thread-safe event window; overrun and fatal diagnostics fail closed."""

    def __init__(self, capacity=8192, *, reject_wrong_pack=False):
        if capacity < 1:
            raise ValueError("Logcat capacity must be positive")
        self._cv = threading.Condition()
        self._lines = deque(maxlen=capacity)
        self._seq = 0
        self._fatal = None
        self._ended = False
        self._reject_wrong_pack = reject_wrong_pack

    def record(self, line):
        with self._cv:
            self._seq += 1
            self._lines.append((self._seq, line))
            if self._fatal is None:
                if any(marker in line for marker in FAILURE_MARKERS):
                    self._fatal = "Android GLES failure: " + line[-1800:]
                elif (self._reject_wrong_pack
                      and "GLTF_LOADED actual_scene=true" in line
                      and "models=10 nodes=11" not in line):
                    self._fatal = "Renderer imported unexpected mesh pack: " + line[-1800:]
            self._cv.notify_all()

    def _check_health(self):
        if self._fatal is not None:
            raise RuntimeError(self._fatal)
        if self._ended:
            raise RuntimeError("Android logcat subscriber ended unexpectedly")

    def mark(self):
        with self._cv:
            self._check_health()
            return self._seq

    def assert_healthy(self):
        with self._cv:
            self._check_health()

    def finish(self):
        with self._cv:
            self._ended = True
            self._cv.notify_all()

    def wait_for(self, predicate, *, since, timeout):
        if not isinstance(since, int) or since < 0:
            raise ValueError("Logcat cursor must be nonnegative")
        end = time.monotonic() + timeout
        with self._cv:
            while True:
                self._check_health()
                if self._lines and since < self._lines[0][0] - 1:
                    raise RuntimeError("Android logcat cursor expired; evidence may be lost")
                for sequence, line in self._lines:
                    if sequence > since and predicate(line):
                        return line
                remaining = end - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("No matching Android logcat event before deadline")
                self._cv.wait(remaining)


class LogcatStream:
    """Single append-only ADB process with full durable file and bounded RAM."""

    def __init__(self, path, *, reject_wrong_pack=False, capacity=8192,
                 startup_timeout=20, startup_probe_interval=.75):
        if startup_timeout <= 0 or startup_probe_interval <= 0:
            raise ValueError("Logcat startup timeouts must be positive")
        self.path = Path(path)
        self.events = LogcatEvents(capacity, reject_wrong_pack=reject_wrong_pack)
        self._startup_timeout = startup_timeout
        self._startup_probe_interval = startup_probe_interval
        self._proc = None
        self._thread = None
        self._file = None

    def _await_subscriber(self):
        """Echo a real device nonce until the async logcat reader observes it.

        ADB may finish `shell log` before `adb logcat` subscribes; a single
        marker is therefore lossy. No simulated events or log-dump fallback:
        only a nonce actually consumed by the live subscriber unlocks capture.
        """
        nonce = "VQ_LOGCAT_ATTACHED_" + uuid.uuid4().hex
        deadline = time.monotonic() + self._startup_timeout
        probes = 0
        while True:
            self.events.assert_healthy()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"Android logcat subscriber did not echo nonce after "
                    f"{probes} real ADB probes")
            subprocess.run(
                ["adb", "shell", "log", "-p", "i", "-t", "VEILFORGE_PROBE", nonce],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=min(15, remaining), check=True)
            probes += 1
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                continue
            try:
                self.events.wait_for(
                    lambda line: nonce in line, since=0,
                    timeout=min(self._startup_probe_interval, remaining))
                return
            except TimeoutError:
                # Only absence of this specific nonce is transient. A closed
                # subscriber, cursor overrun or sticky GLES error still fails.
                continue

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("w", encoding="utf-8", buffering=1)
        try:
            self._proc = subprocess.Popen(
                ["adb", "logcat", "-v", "brief", "-s", "VEILFORGE_PROBE:I", "*:S"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self._thread = threading.Thread(target=self._consume, daemon=True)
            self._thread.start()
            # Real device echo must reach this live reader before any
            # camera launch. Retry a lost startup probe, not a failed gate.
            self._await_subscriber()
            return self
        except BaseException:
            self.close()
            raise

    def _consume(self):
        try:
            for raw in iter(self._proc.stdout.readline, b""):
                line = raw.decode("utf-8", "replace").rstrip("\r\n")
                self._file.write(line + "\n")
                self.events.record(line)
        finally:
            self.events.finish()

    def mark(self):
        return self.events.mark()

    def wait_for(self, predicate, *, since, timeout):
        return self.events.wait_for(predicate, since=since, timeout=timeout)

    def assert_healthy(self):
        self.events.assert_healthy()

    def close(self):
        if self._proc is not None:
            if self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
                    self._proc.wait(timeout=5)
            if self._thread is not None:
                self._thread.join(timeout=5)
            if self._proc.stdout is not None:
                self._proc.stdout.close()
            self._proc = None
        if self._file is not None:
            self._file.close()
            self._file = None

    def __exit__(self, exc_type, exc, tb):
        self.close()
