"""Reproducible client-side latency sample. Run against an already-ready service."""

import argparse
import concurrent.futures
import json
import math
import time

from smoke import request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    payload = json.dumps(
        {
            "gpa": 3.5,
            "monthly_household_income_sar": 4000.0,
            "household_size": 4,
            "transcript_present": True,
            "income_proof_present": True,
        }
    ).encode()

    def measure(_):
        started = time.perf_counter()
        status, _ = request(args.base_url, "/v1/predict", payload)
        return (time.perf_counter() - started) * 1000, status

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(measure, range(args.requests)))
    elapsed = time.perf_counter() - started
    times = sorted(t for t, _ in results)
    print(
        json.dumps(
            {
                "requests": args.requests,
                "concurrency": args.concurrency,
                "p50_ms": round(times[math.ceil(len(times) * 0.5) - 1], 3),
                "p99_ms": round(times[math.ceil(len(times) * 0.99) - 1], 3),
                "requests_per_second": round(args.requests / elapsed, 2),
                "errors": sum(status != 200 for _, status in results),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
