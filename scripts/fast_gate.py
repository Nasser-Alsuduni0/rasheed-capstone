"""Enforce the course's 60-second fast test gate, including process startup."""

import subprocess
import sys
import time

started = time.perf_counter()
try:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "not slow",
            "--cov",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "-q",
        ],
        timeout=60,
        check=False,
    )
except subprocess.TimeoutExpired:
    raise SystemExit("Fast test gate exceeded 60 seconds") from None
print(f"FAST_GATE_SECONDS={time.perf_counter() - started:.3f}", flush=True)
raise SystemExit(result.returncode)
