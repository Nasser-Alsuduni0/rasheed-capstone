# Five engineering decisions

## 1. Transparent, versioned rules rather than an unvalidated learned model

There is no approved labelled scholarship dataset in this project. A JSON scoring
artifact gives reproducible, inspectable behavior without inventing training
accuracy. The merit/need weights and thresholds are educational assumptions.
Missing documents force review before the GPA rejection rule so incomplete cases
are not silently treated as final decisions. Trade-off: these rules are not a
validated fairness or student-success model; real deployment needs institutional
policy approval, data governance, and outcome evaluation.

## 2. Pure domain and Protocol-based composition

Domain dataclasses and policy contain no FastAPI/Pydantic/Redis dependency.
Service orchestrates two Protocols; bootstrap selects adapters at lifespan startup.
Four import-linter contracts make the boundaries executable. The alternative,
passing HTTP models through the whole system, is shorter initially but couples
policy to transport. Trade-off: explicit mapping and factories add a few files,
while enabling real HTTP tests with cheap deterministic fake dependencies.

## 3. Actionable explanations with a deliberately small privacy surface

The extension returns reason codes, missing-document lists, and next steps,
not just a score. We accept no identity fields or document contents and log only
opaque trace IDs/status/duration. Safe error envelopes omit internal exceptions.
The alternative—logging payloads and raw exceptions—is easier to debug but
exposes applicant information. Trade-off: debugging needs reproducible synthetic
cases; scores are guidance and humans remain responsible for final awards.

## 4. Redis aggregates with explicit readiness and failure semantics

Redis provides an actual supporting service for aggregate decision counters.
Only three counters are stored; no per-applicant records or deduplication keys.
Readiness depends on Redis; liveness does not. If counting fails, the API returns
503 instead of pretending the complete operation succeeded. Failure latency
is bounded by socket and Compose DNS timeouts; automatic Redis retries are disabled
so an increment is not silently replayed after an ambiguous connection failure.
Trade-off: availability is coupled to Redis, counters are ephemeral, and client
retries can count an application
twice. Durable, exactly-once accounting would require a different data model and
idempotency design, which the demo does not claim to provide.

## 5. Test the release artifact and require reviewed changes

Hash-pinned Python dependencies, a digest-pinned Python base, non-root/read-only
runtime, full-history Gitleaks, and SHA-pinned CI actions reduce ambiguity.
Fast tests enforce branch coverage and a 60-second limit; session-scoped real-model
tests check directional/invariance properties and independently reviewed golden
decisions. CI builds once, exercises the real Compose stack, then publishes that
same image only from main. Reviewed PRs and required checks protect main after
initial bootstrap. Trade-off: stricter updates require deliberate lock, golden,
and compatibility review; a commit tag is traceable but deployment by digest is
stronger than assuming registry tags cannot be overwritten.
