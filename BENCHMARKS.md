# Measured benchmarks

Measured locally on 22 September 2026 (Asia/Riyadh), Windows + Docker Desktop,
Linux containers, Docker Engine 29.8.0, CPython 3.12.13, one Uvicorn worker.
Host: Intel Core i7-10750H (6 cores / 12 logical processors), 15.78 GiB RAM.
These are actual observations, not performance guarantees or CI measurements.

| Check | Observed result | Method |
| --- | --- | --- |
| First uncached image build | 40.76 s | Docker build wall time; includes base/frontend downloads |
| Warm build after one source-line edit | 6.22 s | Added package version line; dependency/model layers visibly CACHED |
| Final local image size | 220,457,345 bytes (220.46 MB decimal) | docker image inspect rasheed-capstone:dev --format '{{.Size}}' |
| Recreation to first successful /ready | 4.880 s | python scripts/startup_time.py; Redis already healthy |
| Full suite | 111 passed, 3.68 s pytest time | pytest --cov; all three levels, after Redis retry fix |
| Fast suite | 90 passed, 21 deselected; 4.46 s pytest time | python scripts/fast_gate.py |
| Fast gate end-to-end wall time | 14.338 s | Includes interpreter/test/coverage process overhead; limit 60 s |
| Real-model behavioural suite | 21 passed, 0.30 s | pytest -m slow |
| Full branch-aware core coverage | 100% | domain/service/api; 234 statements, 28 branches |
| Fast-only branch-aware coverage | 99.62% | Same core scope; limit 80% |
| Malformed live HTTP requests | 43/43 rejected with 4xx | python scripts/smoke.py |
| Load sample | 1,000 requests, concurrency 10, 0 errors | python scripts/benchmark.py |
| Client latency p50 / p99 | 65.688 / 109.379 ms | Nearest-rank quantiles of completed requests |
| Throughput | 140.26 requests/s | Total requests / batch wall time |
| Runtime identity | appuser, UID 10001 | docker compose exec -T rasheed-api id |
| Dependency outage | /health 200, /ready 503 | Real Redis stop and recovery |
| Graceful shutdown | Cleanup completed; exit 143; not OOM-killed | SIGTERM, service_stopped event and container state |

The warm build also replaced the Python base tag with its resolved digest, which
reused the same local base. Docker's first context transfer was 35.33 kB.
Image size is the local uncompressed size, not compressed registry transfer size.

An earlier run before the Redis timeout hardening measured 111 tests in 4.41 s,
image size 220,457,107 bytes, p50/p99 63.970/111.969 ms, and 142.10 requests/s
with zero errors. The table reports the final remeasurement where repeated;
the initial build/startup/fast-gate timings are retained as measured observations.
Gitleaks found no leaks in the pre-publication full-history and directory scans.

The load client uses a new HTTP connection per request on localhost through
Docker Desktop networking. Results include client scheduling, transport, API,
model, and synchronous Redis counting. No requests are excluded as warm-up;
the service was already ready. This is a modest smoke load, not capacity planning.

## Reproduce

Run from the repository root; Python scripts require only the standard library.

```sh
docker compose up --build -d --wait
python scripts/smoke.py
python scripts/benchmark.py --requests 1000 --concurrency 10
python scripts/startup_time.py
python scripts/operations_check.py
docker compose up -d --wait
docker image inspect rasheed-capstone:dev --format '{{.Size}}'
```

For cold-build timing, use a clean builder/cache and explicitly state whether base
downloads are included. Do not delete a shared machine's Docker cache just to
reproduce this number. For warm timing, make a one-line source comment/version
edit, time docker build, and check its CACHED lines; restore or commit the edit.

Test timings depend on filesystem cache, machine load, and instrumentation.
CI uploads its own coverage artifact; it does not substitute local timings.

## Remote CI cross-check

[Initial green main run 35659835859](https://github.com/Nasser-Alsuduni0/rasheed-capstone/actions/runs/35659835859)
on a GitHub-hosted Ubuntu runner measured the fast gate at **3.722 s wall time**
(90 passed in 1.45 s, 99.62% core branch-aware coverage). The slow suite passed
21 tests in 0.09 s. All 43 malformed live requests, real Redis outage/recovery,
non-root identity, image-size limit, and graceful cleanup checks passed.
The tested image was published and subsequently pulled locally without credentials;
its identity is recorded in [RELEASE.md](RELEASE.md).
