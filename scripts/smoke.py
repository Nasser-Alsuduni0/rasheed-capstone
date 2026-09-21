"""Exercise a live service, including the entire malformed-file corpus."""

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def request(base, path, payload=None):
    data = None if payload is None else payload
    req = urllib.request.Request(
        base + path, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    args = parser.parse_args()
    for path in ("/health", "/ready"):
        status, body = request(args.base_url, path)
        assert status == 200 and body["error"] is None, (path, status)
    status, body = request(
        args.base_url, "/v1/predict", (ROOT / "payloads/valid.json").read_bytes()
    )
    assert status == 200 and body["data"]["decision"] == "accept", body
    assert body["data"]["reason_codes"] and body["trace_id"]
    corpus = sorted((ROOT / "payloads/malformed").glob("*.json"))
    assert len(corpus) >= 40
    for path in corpus:
        status, body = request(args.base_url, "/v1/predict", path.read_bytes())
        assert 400 <= status < 500, (path.name, status)
        assert body["error"]["code"] == "INVALID_REQUEST"
    status, body = request(args.base_url, "/v1/statistics")
    assert status == 200 and body["data"]["accept"] >= 1
    print(
        f"SMOKE_OK: valid prediction, health, readiness, statistics, {len(corpus)} malformed files"
    )


if __name__ == "__main__":
    main()
