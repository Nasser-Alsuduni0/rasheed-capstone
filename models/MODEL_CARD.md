# Rasheed rules model 1.0.0

Intended use: an educational scholarship-screening prototype with invented,
documented thresholds. This is not a calibrated probability or trained ML model.
No real applicant data, labels, or statistical accuracy claims are used.

Score = 0.65 * GPA / 4 + 0.35 * (1 - min(income_per_person / 5000, 1)).
Weights are nonnegative and sum to one; the score is bounded in [0, 1].
Higher GPA or lower per-person income cannot reduce it. Document completeness
is handled by the business policy, separately from the model.

Complete applications with GPA < 2 are rejected with an explanation. Otherwise
score >= 0.70 accepts, score >= 0.45 goes to review, and a lower score rejects.
Any missing document overrides these outcomes and goes to review.

Limitations: document flags are self-reported; records are not authenticated;
there is no fairness validation, real-world calibration, or award guarantee.
The brief permits lightweight/rule-based decisions. Institutional thresholds,
verification and appeals require separate validation before real-world use.

Change control: version the model and policy; inspect changed predictions
and justify each golden-file update in a reviewed pull request. Tests must never
regenerate the golden file automatically.
