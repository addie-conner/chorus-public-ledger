# Chorus Prediction Methodology

## What we predict

Chorus generates probability estimates for events with verifiable outcomes:
- U.S. elections (governor, senate, presidential)
- Economic indicators (EIA petroleum, jobless claims)
- Financial markets (gold direction, FOMC decisions)
- FDA drug approvals
- Geopolitical events

We only predict events where the outcome can be independently verified by anyone.

## How predictions are generated

Each prediction combines multiple independent signals:

1. **Historical base rates** — how often similar events resolved YES in the past
2. **Leading indicators** — data that predicts outcomes before they happen (e.g., continuing claims trends predict initial claims)
3. **Prediction market prices** — current Polymarket/Kalshi prices as information aggregators
4. **Structural models** — fundamentals-based models (e.g., GDP + approval for presidential races)
5. **Calibration correction** — adjusting raw probabilities based on documented biases

No single signal dominates. The ensemble reduces error that any individual signal would produce.

## What calibration means

A "calibrated" forecaster is one whose stated probabilities match actual frequencies.

If you predict "70% chance" for 100 different events, and exactly 70 of them happen, your predictions are perfectly calibrated. If 85 happen, you're underconfident. If 55 happen, you're overconfident.

We measure calibration using the **Brier score**: the average squared error between predicted probability and actual outcome (0 or 1).

**Brier score = average of (predicted_probability - actual_outcome)^2**

- Perfect predictions: Brier = 0.000
- Coin flip on everything: Brier = 0.250
- Superforecasters: Brier = 0.050-0.100
- FiveThirtyEight (elections): Brier = 0.050-0.070

Lower is better. The theoretical minimum is 0 (impossible in practice for genuinely uncertain events).

## What we exclude and why

**Near-certainties (P < 5% or P > 95%):** Predicting that California will vote Democratic is not a real prediction. We exclude these from headline accuracy because they inflate the number without demonstrating forecasting skill.

**Garbage sources:** Some data sources (automated GDELT event detection, Facebook ad performance) were tested as prediction inputs but produced noise, not signal. These are excluded from the headline Brier score.

**Kalshi trivial markets:** Markets like "Will [specific person] leave Trump's cabinet first?" at 1% are near-certainties that pad accuracy. Excluded.

## The honest numbers

Our verified Brier scores (leave-one-cycle-out cross-validation on 587 races, 2008-2024):

| Race Type | N | FiveThirtyEight Raw | Chorus Calibrated | Improvement |
|-----------|---|---------------------|-------------------|-------------|
| Governor | 103 | 0.069 | 0.035 | +50% |
| Senate | 234 | 0.054 | 0.037 | +32% |
| Presidential | 250 | 0.042 | 0.041 | +4% |

**What this IS:** Chorus post-processing (calibration + safe seat compression + bias correction) applied to FiveThirtyEight's historical forecasts, validated with leave-one-cycle-out cross-validation.

**What this is NOT:** Independent Chorus forward predictions. Those begin resolving April 2, 2026.

## How to verify a prediction

Every Chorus prediction includes:
- A SHA-256 hash of the immutable fields (question, probability, timestamp)
- A Bitcoin timestamp (OpenTimestamps .ots file) proving the prediction existed before the outcome

To verify:
1. Check the prediction exists in `predictions.json` with the stated hash
2. Run `ots verify predictions.json.ots` to confirm the Bitcoin timestamp
3. After resolution: check that the outcome matches a verifiable public source

## The audit history

**March 31, 2026 — Brier score correction**

We originally reported a Brier score of 0.039 on 190 predictions ("538 + Kalshi").

On audit, we found:
- The actual computed number was 0.042, not 0.039
- 50 of the 190 predictions were trivial Kalshi near-certainties (P=0.01 on obvious outcomes) that padded the average
- The 2024 presidential outcomes were incorrectly coded (all 50 states as GOP wins, when Harris won 19 states)

After correction:
- 538-only (no Kalshi padding): 0.057 on 140 predictions
- Full corrected dataset: 0.053 on 727 election predictions
- Cross-validated with Chorus calibration: 0.038 on 587 predictions

We publish this correction because accuracy requires honesty about errors. A system that hides its mistakes cannot be trusted with its findings.

## Live vs backtested

The numbers above are backtested — they measure how well our methodology would have performed on historical data. Backtested numbers are always better than live numbers because:
1. You can't overfit to data you haven't seen
2. Historical data is cleaner than real-time data
3. You know which features matter after the fact

The live track record begins April 2, 2026. That is the number that matters long-term.
