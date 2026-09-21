"""Exercise dependency failure and graceful shutdown against the Compose stack."""

import json
import subprocess

from smoke import request


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True)


def main():
    try:
        docker("compose", "stop", "feature-cache")
        assert request("http://127.0.0.1:8010", "/health")[0] == 200
        status, body = request("http://127.0.0.1:8010", "/ready")
        assert status == 503 and body["error"]["code"] == "NOT_READY"
        print("Dependency outage: liveness=200, readiness=503")
    finally:
        docker("compose", "up", "-d", "--no-build", "--wait")

    before = docker("compose", "logs", "--no-color", "rasheed-api")
    docker("compose", "stop", "rasheed-api")
    after = docker("compose", "logs", "--no-color", "rasheed-api")
    assert after.count('"event": "service_stopped"') > before.count('"event": "service_stopped"'), (
        "Lifespan cleanup did not finish"
    )
    container = docker("compose", "ps", "-a", "-q", "rasheed-api").strip()
    state = json.loads(docker("inspect", container))[0]["State"]
    # Uvicorn re-raises captured SIGTERM after cleanup: 128 + 15 is normal.
    assert state["ExitCode"] in (0, 143), state
    assert not state["OOMKilled"], state
    print(f"Graceful shutdown: cleanup completed, exit={state['ExitCode']}, OOM=false")


if __name__ == "__main__":
    main()
