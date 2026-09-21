"""Measure recreation-to-readiness with the supporting service already healthy."""

import http.client
import subprocess
import time
import urllib.error
import urllib.request

subprocess.run(["docker", "compose", "rm", "--stop", "--force", "rasheed-api"], check=True)
started = time.perf_counter()
subprocess.run(["docker", "compose", "up", "--detach", "--no-build", "rasheed-api"], check=True)
while time.perf_counter() - started < 60:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8010/ready", timeout=2) as response:
            if response.status == 200:
                print(f"TIME_TO_READY_SECONDS={time.perf_counter() - started:.3f}")
                break
    except (urllib.error.URLError, TimeoutError, http.client.RemoteDisconnected):
        pass
    time.sleep(0.1)
else:
    raise SystemExit("Readiness timeout")
