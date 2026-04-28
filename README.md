# Chorus — Public Prediction Ledger

SHA-locked, OpenTimestamps-anchored ledger of forward predictions with resolved Brier scores.

**Live page:** [chorus public ledger](./index.html) (rendered via GitHub Pages)

## What this is

Every Chorus forward prediction — locked publicly *before* the resolution event — recorded with:

- A `sha256` hash of the immutable prediction fields (question, probability, locked timestamp, resolution criterion)
- Resolution source named at lock time (FRED, BLS, ICE, ESPN, government release, etc.)
- Resolved Brier score after the event

The full ledger file is anchored to the Bitcoin blockchain via OpenTimestamps, providing tamper-proof timestamps independent of GitHub.

## Headline

Forward, single-prediction, deduplicated, in-headline-domains: see [`ledger_summary.json`](./ledger_summary.json) and the [rendered index](./index.html).

## Verification protocol

Anyone can verify any prediction in three steps:

1. **Hash check.** For any entry, confirm the `sha256` field matches a SHA-256 hash of the immutable fields.
2. **Bitcoin timestamp.** Run `ots verify ledger_canonical.json.ots` against `ledger_canonical.json` to confirm the file existed before any resolution event.
3. **Independent resolution.** Cross-check the entry's `resolution_source` against the cited public source — never against Chorus's own data.

```bash
pip install opentimestamps-client
ots verify ledger_canonical.json.ots
```

## What this is NOT

- **Not a list of every prediction Chorus has ever generated internally.** Research scratchwork is excluded. The full ledger contains only locked, public-facing predictions.
- **Not cherry-picked.** Every locked forward prediction is in the ledger regardless of outcome. The headline number restricts scope to publishable sub-domains and explicitly excludes pastcasting / cross-validation / aggregate batch claims (those are reported separately as backward-validation).
- **Not a guarantee.** Brier scores describe calibration over resolved predictions; they describe the past, not the future.

## Schema

Each entry in `ledger_canonical.json` has:

| Field | Description |
|---|---|
| `canonical_id` | Stable identifier across schema migrations |
| `original_id`, `original_sha` | Identifier and hash from the source file (preserves backward verifiability) |
| `source_file` | Which Chorus internal file the entry originated from |
| `domain` | Raw domain (e.g. `corporate_earnings`, `labor_claims`) |
| `headline_domain` | Combined sub-domain for headline reporting (set on forward singles only) |
| `temporal_class` | `FWD` (forward), `BWD` (logged at resolution time), `AGG` (backward-validation aggregate), `UNKNOWN` |
| `question`, `resolution_criterion` | What's being predicted, in falsifiable form |
| `chorus_probability` | The locked probability estimate |
| `baseline_probability` | Naive baseline used for edge calculation (where applicable) |
| `locked_at`, `resolution_date`, `resolved_at` | Timestamps |
| `resolution`, `resolution_source` | The actual outcome and where it was sourced |
| `brier_score` | $(p - actual)^2$, where lower is better |
| `audit_flags` | Transparency markers: `missing_sha256`, `no_ots_anchor`, `duplicate_of:<id>`, `resolution_overdue`, etc. |

## Audit flags

The headline number includes only entries clean on all flags. Other entries appear in the full ledger but are excluded from the headline number — flagged transparently for the reader to inspect.

## Methodology

See [`methodology.md`](./methodology.md) for the 8-gate forecasting methodology and the explicit distinction between forward predictions and backward-calculated cross-validation work.
