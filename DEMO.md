# Five-minute capstone demonstration

Prepare before the timer: start Docker Desktop, run
`docker compose up --build -d --wait`, activate the Python environment, and open
the README, Swagger, and the repository Actions page. Use synthetic inputs only.

## 0:00–0:45 — Problem and boundaries

“Rasheed screens scholarship applications into accept, review, or reject.
It combines merit and financial need using an explicitly versioned rule artifact.
It is an educational screening aid, not a trained probability model or final
scholarship authority.”

Show `models/MODEL_CARD.md` and the README formula.

## 0:45–1:30 — Healthy, contained deployment

```sh
docker compose ps
docker compose exec -T rasheed-api id
docker image inspect rasheed-capstone:dev --format '{{.Size}}'
```

Point out both healthy services, appuser, the measured image size, and /ready
healthcheck. Redis has no host port; the API binds localhost.

## 1:30–2:30 — Prediction and original extension

In http://localhost:8010/docs, call POST /v1/predict with:

```json
{"gpa":3.5,"monthly_household_income_sar":4000.0,"household_size":4,"transcript_present":true,"income_proof_present":true}
```

Show accept, score 0.84875, model/policy versions, and trace ID.
Set income_proof_present=false and repeat: review, missing-document reason,
and actionable next steps. Call GET /v1/statistics; explain that these are request
counts, not unique applicants. Submit household_size=0: safe 422 envelope.

## 2:30–3:30 — Architecture and real tests

Show bootstrap and the service Protocols, then:

```sh
python scripts/fast_gate.py
python -m pytest -m slow -q
```

Explain unit/integration/behavioural levels, ≥80% branch coverage, the
session-scoped real_model fixture, directional tests, and hand-reviewed golden
expectations. Do not regenerate golden data during the presentation.

## 3:30–4:30 — Delivery evidence

Open the latest green main Actions run: lint/secrets → tests → real image smoke
→ GHCR publish. Show the full-SHA image reference, protected main requiring an
approval/checks, and the meaningful commit history.
Open BENCHMARKS.md and distinguish measured results from future guarantees.

## 4:30–5:00 — Trade-offs and next steps

Briefly cover privacy-first logs, Redis failure returning 503, and why transparent
rules were chosen instead of fabricated training results. Production next steps:
institution-approved policy, fairness evaluation, authentication/TLS/rate limits,
durable auditing and idempotency. The presenter must understand these trade-offs,
not merely replay commands.

Optional after the timed demo:
`python scripts/operations_check.py`, then `docker compose up -d --wait`.
This demonstrates live/readiness separation and graceful shutdown.
