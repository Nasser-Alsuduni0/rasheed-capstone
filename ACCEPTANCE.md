# Capstone acceptance evidence

This maps the mandatory project requirements, deliverables, and pass conditions
to inspectable evidence. Passing tests does not mean the educational policy is
suitable for real scholarship decisions.

| Requirement | Evidence |
| --- | --- |
| src layout, separate domain/service/adapters/api | src/rasheed; four import-linter contracts in pyproject.toml |
| Protocol dependency injection | service/interfaces.py; bootstrap.py; fake test adapters |
| Required Make targets | Makefile: install/test/lint/image/smoke |
| Strict POST /v1/predict and trace envelope | api/schemas.py; integration/test_api.py; 43 malformed JSON payloads |
| Startup-only load/warmup; live vs ready | api/app.py lifespan; bootstrap.py; import-time I/O regression test |
| Container ≤500 MB, non-root, healthcheck, shutdown | Dockerfile; BENCHMARKS.md; scripts/operations_check.py |
| Real health-gated supporting service | Redis in docker-compose.yml; readiness and outage checks |
| Three test levels; real-model behavioural tests | tests/unit, integration, behavioural; session-scoped real_model |
| Invariance, directional, full golden decisions | tests/behavioural; tests/golden and provenance README |
| Branch coverage ≥80%; fast gate ≤60 s | pytest-cov branch config; scripts/fast_gate.py timeout; CI coverage artifact |
| Sequential delivery pipeline and main-only SHA publish | .github/workflows/ci.yml; exact tested Docker image transferred between jobs |
| One approval, required checks, no force-push | scripts/branch-protection.json; live GitHub branch settings after bootstrap |
| Typed fail-fast settings; no secret history | config.py; Gitleaks history and directory CI jobs |
| Structured privacy-safe trace-linked logs | logging_config.py; JSON log privacy integration test |
| Original implemented and tested extension | Explained outcomes: reasons, missing documents, next steps |
| Repository and meaningful milestones | Public GitHub repository and incremental commit history |
| Ten-minute reproduction and five-minute presentation | README.md; DEMO.md |
| Real numbers and five decisions | BENCHMARKS.md; DECISIONS.md |

Public repository: https://github.com/Nasser-Alsuduni0/rasheed-capstone

CI evidence: https://github.com/Nasser-Alsuduni0/rasheed-capstone/actions/workflows/ci.yml

The initial bootstrap is committed and pushed by the owner before enabling branch
protection. Subsequent main changes must go through reviewed, passing pull
requests. A local test run is not represented as a remote CI run, and generated
image tags are not claimed until the publish job succeeds.

## Red-flag safeguards

- No claimed dataset, trained-model accuracy, or learned probability.
- Golden files specify reviewed expected behavior; no auto-update snapshot script.
- No production latest tag. Full commit SHA tags, optionally deployment digests.
- Tests exercise public seams; no private helper imports or inflated coverage scope.
- No credentials, applicant identities, or document contents in source or logs.
- Benchmark numbers are measured locally and labeled with conditions.
- The live presentation and an independent future PR approval require real people;
  neither is fabricated by automation.
