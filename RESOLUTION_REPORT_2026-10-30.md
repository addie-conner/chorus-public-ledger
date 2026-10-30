# Resolution report, 2026-10-30 (reconciliation, voids, overdue sports)

Branch `resolution-2026-10-30`, local only. Not pushed, not deployed.
Backups of every file written, all with the suffix `.bak.20261029T190657`:
- `~/chorus-public-ledger/ledger_canonical.json`
- `~/chorus/static/public_ledger/ledger_canonical.json`
- `~/chorus/static/public_ledger/predictions.json`
- `~/chorus/chorus_predictions.jsonl`
- `~/chorus/static/public_ledger/ledger_summary.json`
- `~/chorus/data/calibration/resolution_log.json`

## Result

- **Sports forward record, as of 2026-10-30:**
  - Directional hits: 101 of 126.
  - Brier 0.153 against 0.178 for the naive baselines, a skill score of +0.14.
  - Without the 41 World Cup rows locked after the 2026-06-11 kickoff: n=85, 69 right, 0.154 against 0.161, skill +0.04.
  - Where a pre-lock market price exists (18 rows), Chorus scores 0.121 against the market's 0.124, which is no edge.
  - The previous figure was 91 of 116, 0.163 against 0.190, skill +0.14 (+0.04 at n=75). All 10 newly resolved forward rows went the right way. The skill score did not change.
- **Resolved in this run:** 60 rows.
  - 10 sports rows: 9 from the Forbes 2026 NBA list, 1 from Wikipedia pageviews.
  - 50 ForecastBench rows. These are BWD (not forward) and stay outside every forward figure.
  - The auto-resolver found nothing it could resolve. Every outcome was looked up by hand against the source named on the row.
- **Carried into the source files:** the 68 resolutions from 2026-10-15 that existed only in this repo. They now live in `chorus_predictions.jsonl` and `predictions.json`.
- **Voided:** 41 rows under the pre-registered rule: 35 duplicates, 5 ill-formed questions, 1 unresolvable source.
- **Past due and still open (2-day grace):**
  - The 2026-10-15 public file had 298. The working ledger had 363 before this run (incl. 105 sports rows). After this run: 197.
  - Sports: 41 before, 30 after. Every remaining row is labeled with a reason category.
  - "Sports" here means the domains selected by `is_sport()` in the sports-record script.
- **Locked fields are unchanged:** question, probability, lock time, resolution criterion, resolution date, SHA and OTS receipt. Checked row by row against the backups, with 0 differences.

## How the ledger flows now (the fix)

The canonical ledger is rebuilt every day by `scripts/public_ledger_consolidate.py --write`. It reads three source files: `static/public_ledger/predictions.json`, `chorus_predictions.jsonl` and `manual_entries.json`.

The 2026-10-15 sweep was written by hand into this repo's copy only. The next rebuild would have dropped it, and so would any `lock_to_ledger.py` run with `push=True`. This run moves every hand edit to the source side:

1. **Outcomes** go into `~/chorus/data/resolutions_to_apply/` (`carry_public_2026_10_15.json`, `batch_2026_10_30.json`). They are applied by `apply_staged_resolutions.py`, which writes into the source files. The daily pipeline already runs this step, and it is idempotent.
2. **Curated public fields** go into `static/public_ledger/public_curations.json` (228 rows), created by `scripts/extract_public_curations.py`. The fields are:
   - RETRO class (11 rows)
   - per-row OTS anchor paths (139)
   - resolution values (147)
   - baseline Brier (78)
   - criterion notes (20)
   - the 10/15 resolution sources and dates

   The consolidation step applies them on every rebuild. It never overlays a locked field. Resolution-dependent fields are applied only to rows the sources already mark resolved.
3. **Draft dates:** the three 2026 draft rows keep their hashed `resolution_date` (2027-04-30). The sealed criterion date (2026-06-23) is stored separately in `resolution_date_corrected`, with a note. The sports-record script reads `resolution_date_corrected` where it is present.
4. **RETRO:** `classify_temporal` now honors RETRO, so those rows stay out of every forward figure. The headline counts only FWD.
5. **Voids** come from `static/public_ledger/voids_2026-10-30.json`. A void matches on id + question + resolution date and applies only to an open row.
6. **Awaiting-resolution labels** come from `static/public_ledger/awaiting_2026-10-30.json`. Past-due rows that are not listed there are labeled "not checked this run".
7. **Check:** `scripts/check_curations_preserved.py REBUILD REFERENCE` exits 1 on any lost field.
   - Run against the 2026-10-15 file on stable ids: 0 lost resolutions, 0 lost curated fields, 0 RETRO rows turned FWD.
   - The only changes are 60 open→resolved and 33 open→voided.
   - Rows whose ids change on every rebuild (`v1_unknown_*`) are matched by content. Of those, 11 open rows had already been resolved in the working ledger on 2026-10-03/04 (EIA and FRED weekly releases, sources on each row) but were never in the 10/15 public copy. The rebuild also has 44 rows that the 10/15 copy lacks: 27 resolved weekly EIA and claims rows, plus 17 open rows.

## Sports forward record (`scripts/sports_forward_record_2026_10_30.py`)

Same method as the 2026-10-15 script, with three changes:
- as-of date 2026-10-30
- `resolution_date_corrected` used where present
- last-year persistence entries for the 9 new Forbes NBA rows, from the Forbes 2025 list (API, list dated 2025-10-23)

| subset | n | directional hits | Chorus Brier | baseline Brier | baseline | skill |
|---|---|---|---|---|---|---|
| attention | 23 | 15 | 0.2542 | 0.2268 | constant hit-rate (in-sample) | -0.12 |
| Forbes valuations / pay lists | 22 | 21 | 0.0340 | 0.0415 | persistence; 0.5 where unchecked | +0.18 (see note) |
| outcomes / winners | 71 | 57 | 0.1516 | 0.2066 | market on 18, base rate on 53 | +0.27 |
| sponsorship / media | 10 | 8 | 0.1906 | 0.1600 | base rate 0.80 | -0.19 |
| **pooled, calendar excluded** | **126** | **101** | **0.1529** | **0.1778** | n-weighted subset baselines | **+0.14** |
| calendar checks (separate) | 8 | 8 | 0.0004 | n/a | n/a | n/a |
| pooled including calendar | 134 | | 0.1438 | | | |

- **Forbes:** on the 20 rows where last year's list was checked, every Chorus direction matches persistence, and the Brier is identical (0.0206 for both). Skill over persistence is zero. All of the +0.18 comes from the two rows scored against 0.5, as on 2026-10-15.
- **Outcomes against the market:** 18 rows, 0.1206 against 0.1236, unchanged.
- **World Cup rows locked after kickoff:** 41 rows (27 locked 2026-06-16, 14 locked 2026-06-14). Without them: n=85, 69 right, 0.1540 against 0.1609, skill +0.04. The outcomes subset becomes n=30, 0.1531 against 0.1982.
- **Draft subset:** the pageview row `pred_ba9e973e` (Finals top-3 by minutes, 2026 against 2025) falls into "outcomes" under the script's existing subset rules, because its domain is `nba_athlete_marketability`. It was not reclassified.
- **Misses:** 25, the same list as 2026-10-15. None of the 10 new rows missed.

## Spot checks against sources (all VERIFIED this run)

- **Forbes 2026 NBA list:** checked directly against the Forbes list API (`forbesapi/org/nba-valuations/2026`, list dated 2026-10-16) and the 2025 list (dated 2025-10-23).
- **`pred_ba9e973e`:** recomputed from the Wikimedia pageviews API and the Finals player-minutes tables (Wikipedia, citing NBA.com and Basketball-Reference). It is YES under three ways of combining the three players and with either window start.
- **ForecastBench:** all 50 matched to the public resolution set.
- **Carried 10/15 rows, rechecked:**
  - 9 attention rows against the Wikimedia API: all 9 outcomes reproduce.
  - The 8 NFL top-5 rows and Cowboys #1 against the Forbes NFL 2026 API: all agree.
- **Kyle Harrison:** the article `Kyle_Harrison` now returns a median of 5/day for 2026-09-28..10-04. The 10/15 note says 144/day, probably from a different article title. The outcome (NO, threshold 220) holds either way.

## Still open, by reason (sports, 30 rows)

| reason category | rows |
|---|---|
| criterion_needs_owner_decision | 8 Forbes NHL top-5 rows: no list titled 2026 (Forbes API `nhl-valuations/2026` returns 0 rows on 2026-10-30); the latest edition, titled 2025, came out 2025-12-11, before the lock |
| internal_computation_pending | 10 `wsl_judging_bias` rows: the criterion runs `wsl/analysis/bias_tests.py` on Chorus's own corpus; `wsl_brier_hook.py` has not produced an outcome |
| no_public_report_found | 3 upfront rows, NBA upfront ≥95% sold, Nielsen QI report, Geico/Honda/Discover NHL-TNT renewal, Hailey Van Lith Tier-1 deal (rechecked 2026-10-30). Absence of a report is not scored as NO |
| data_assembly_pending | 5 `cross_league_validated` attendance-residual rows (BWD, so not forward either way) |

The 167 non-sports past-due rows are labeled `not_checked_this_run`. Most of them have a criterion that only restates the question, with no named source. The largest groups:
- colorado_phonefree, 14 + 14 shadow
- earnings_sector_rate, 11
- fda_pdufa_scan, 11
- corporate_scan, 8
- cybersecurity, 8

## Voids

The rule file is `PREREG_resolution_run_2026-10-30.json`, sha256 `9788c0b49b2774339f130e7920a352083f1bb6e43167e91bf41f0fe2e34cdf05`. It was stamped with `ots stamp` (`.ots` beside it) before any void was selected.
- **V1 (duplicate)** compares the full question text, not a prefix. In 12 duplicate pairs the later copy carried a different probability from the keeper. The rule voids the later copy either way, because it looks only at the question text and lock time.
- **Schema-broken state_primary rows:** eight of the V1 voids are rows filed under `state_primary_2026` that have no question text, no probability and the placeholder id `pred_`. Their criterion field reads "Will Maxx Crosby play for New York Jets next?". The ninth copy, the keeper, stays open. It cannot be scored, because it has no probability.

## Problems for review before publishing

1. **Canon:** CH1 and CH4 in `~/groundline/reports/CLAIMS_CANON_2026-09-01.md` (C1l) still state n=116 / 91 / 0.163 vs 0.190 and Forbes n=13. The page now shows the 2026-10-30 figures. The canon needs an approved update first (edit the canon, then the surface).
2. **Prior-page sections not carried over:** the "Athlete & draft snapshot 2026-08-14 (superseded)" section and the macro-release line (CH6) were hand-written on the old page. Neither is produced by the render script, so neither is on the regenerated page. Both can be added back as rendered sections if wanted.
3. **OTS proof of the whole file:** `ledger_canonical.json.ots` was made against an older version of the file and does not verify against the current one. That was already true before this run (see `~/chorus/scripts/reanchor_ledger.py`). The per-row anchors in `ots_anchors/` are the real proofs. The verification protocol on the page still tells readers to run `ots verify ledger_canonical.json.ots`.
4. **Push hazard:** `~/chorus/scripts/lock_to_ledger.py` with `push=True` copies the working canonical over this repo's `ledger_canonical.json` and pushes to `main`. With the flow fix, that copy now carries the curations. It still pushes without review, and it copies whatever the last consolidation produced, so stale data can overwrite the public file. Recommendation: refuse to push unless `check_curations_preserved.py` passes against the current public file, or remove the auto-push.
5. **Daily pipeline commits:** `daily_ledger_pipeline.sh` auto-commits ledger files in `~/chorus` (on whatever branch is checked out) and tries `git push origin main`. The push currently fails on credentials.
### Sports and attention rows resolved in this run (10)

| canonical_id | question | lock | p | outcome | Brier | evidence and source |
|---|---|---|---|---|---|---|
| `pred_golden_state_warriors_finishes_in_top_5__8ad22773` | Golden State Warriors finishes in top 5 of NBA by valuation on the 2026 Forbes annual list | 2026-04-24 | 0.85 | YES | 0.0225 | Forbes NBA Team Valuations 2026 (list dated 2026-10-16): 1 Warriors $13.5B, 2 Knicks $12.6B, 3 Lakers $12.5B, 4 Clippers $7.8B, 5 Celtics $7.0B, 6 Bulls $6.7B, 7 Rockets $6.6B, 10 Heat $6.1B. Source: https://www.forbes.com/forbesapi/org/nba-valuations/2026/position/true.json?limit=40 (Forbes list API, list date 2026-10-16; article https://www.forbes.com/sites/justinteitelbaum/2026/10/16/the-most-valuable-nba-teams-2026/; checked 2026-10-30) |
| `pred_los_angeles_lakers_finishes_in_top_5_of__e1eaa1b2` | Los Angeles Lakers finishes in top 5 of NBA by valuation on the 2026 Forbes annual list | 2026-04-24 | 0.85 | YES | 0.0225 | Forbes NBA Team Valuations 2026 (list dated 2026-10-16): 1 Warriors $13.5B, 2 Knicks $12.6B, 3 Lakers $12.5B, 4 Clippers $7.8B, 5 Celtics $7.0B, 6 Bulls $6.7B, 7 Rockets $6.6B, 10 Heat $6.1B. Source: https://www.forbes.com/forbesapi/org/nba-valuations/2026/position/true.json?limit=40 (Forbes list API, list date 2026-10-16; article https://www.forbes.com/sites/justinteitelbaum/2026/10/16/the-most-valuable-nba-teams-2026/; checked 2026-10-30) |
| `pred_new_york_knicks_finishes_in_top_5_of_nba_ec211368` | New York Knicks finishes in top 5 of NBA by valuation on the 2026 Forbes annual list | 2026-04-24 | 0.85 | YES | 0.0225 | Forbes NBA Team Valuations 2026 (list dated 2026-10-16): 1 Warriors $13.5B, 2 Knicks $12.6B, 3 Lakers $12.5B, 4 Clippers $7.8B, 5 Celtics $7.0B, 6 Bulls $6.7B, 7 Rockets $6.6B, 10 Heat $6.1B. Source: https://www.forbes.com/forbesapi/org/nba-valuations/2026/position/true.json?limit=40 (Forbes list API, list date 2026-10-16; article https://www.forbes.com/sites/justinteitelbaum/2026/10/16/the-most-valuable-nba-teams-2026/; checked 2026-10-30) |
| `pred_los_angeles_clippers_finishes_in_top_5_o_b453d982` | Los Angeles Clippers finishes in top 5 of NBA by valuation on the 2026 Forbes annual list | 2026-04-24 | 0.85 | YES | 0.0225 | Forbes NBA Team Valuations 2026 (list dated 2026-10-16): 1 Warriors $13.5B, 2 Knicks $12.6B, 3 Lakers $12.5B, 4 Clippers $7.8B, 5 Celtics $7.0B, 6 Bulls $6.7B, 7 Rockets $6.6B, 10 Heat $6.1B. Source: https://www.forbes.com/forbesapi/org/nba-valuations/2026/position/true.json?limit=40 (Forbes list API, list date 2026-10-16; article https://www.forbes.com/sites/justinteitelbaum/2026/10/16/the-most-valuable-nba-teams-2026/; checked 2026-10-30) |
| `pred_boston_celtics_finishes_in_top_5_of_nba__06bbc0fc` | Boston Celtics finishes in top 5 of NBA by valuation on the 2026 Forbes annual list | 2026-04-24 | 0.85 | YES | 0.0225 | Forbes NBA Team Valuations 2026 (list dated 2026-10-16): 1 Warriors $13.5B, 2 Knicks $12.6B, 3 Lakers $12.5B, 4 Clippers $7.8B, 5 Celtics $7.0B, 6 Bulls $6.7B, 7 Rockets $6.6B, 10 Heat $6.1B. Source: https://www.forbes.com/forbesapi/org/nba-valuations/2026/position/true.json?limit=40 (Forbes list API, list date 2026-10-16; article https://www.forbes.com/sites/justinteitelbaum/2026/10/16/the-most-valuable-nba-teams-2026/; checked 2026-10-30) |
| `pred_chicago_bulls_finishes_in_top_5_of_nba_b_5ba7bc20` | Chicago Bulls finishes in top 5 of NBA by valuation on the 2026 Forbes annual list | 2026-04-24 | 0.15 | NO | 0.0225 | Forbes NBA Team Valuations 2026 (list dated 2026-10-16): 1 Warriors $13.5B, 2 Knicks $12.6B, 3 Lakers $12.5B, 4 Clippers $7.8B, 5 Celtics $7.0B, 6 Bulls $6.7B, 7 Rockets $6.6B, 10 Heat $6.1B. Source: https://www.forbes.com/forbesapi/org/nba-valuations/2026/position/true.json?limit=40 (Forbes list API, list date 2026-10-16; article https://www.forbes.com/sites/justinteitelbaum/2026/10/16/the-most-valuable-nba-teams-2026/; checked 2026-10-30) |
| `pred_houston_rockets_finishes_in_top_5_of_nba_1458d2af` | Houston Rockets finishes in top 5 of NBA by valuation on the 2026 Forbes annual list | 2026-04-24 | 0.15 | NO | 0.0225 | Forbes NBA Team Valuations 2026 (list dated 2026-10-16): 1 Warriors $13.5B, 2 Knicks $12.6B, 3 Lakers $12.5B, 4 Clippers $7.8B, 5 Celtics $7.0B, 6 Bulls $6.7B, 7 Rockets $6.6B, 10 Heat $6.1B. Source: https://www.forbes.com/forbesapi/org/nba-valuations/2026/position/true.json?limit=40 (Forbes list API, list date 2026-10-16; article https://www.forbes.com/sites/justinteitelbaum/2026/10/16/the-most-valuable-nba-teams-2026/; checked 2026-10-30) |
| `pred_miami_heat_finishes_in_top_5_of_nba_by_v_d79c4d23` | Miami Heat finishes in top 5 of NBA by valuation on the 2026 Forbes annual list | 2026-04-24 | 0.15 | NO | 0.0225 | Forbes NBA Team Valuations 2026 (list dated 2026-10-16): 1 Warriors $13.5B, 2 Knicks $12.6B, 3 Lakers $12.5B, 4 Clippers $7.8B, 5 Celtics $7.0B, 6 Bulls $6.7B, 7 Rockets $6.6B, 10 Heat $6.1B. Source: https://www.forbes.com/forbesapi/org/nba-valuations/2026/position/true.json?limit=40 (Forbes list API, list date 2026-10-16; article https://www.forbes.com/sites/justinteitelbaum/2026/10/16/the-most-valuable-nba-teams-2026/; checked 2026-10-30) |
| `pred_a8249447` | Golden State Warriors valuation grows ≥5% on Forbes 2026 NBA refresh | 2026-04-28 | 0.85 | YES | 0.0225 | Warriors $13.5B in 2026 vs $11.0B in 2025 = 1.227x (Forbes oneYearValueChange 23%), >= 1.05x. Source: https://www.forbes.com/forbesapi/org/nba-valuations/2026/position/true.json?limit=40 vs https://www.forbes.com/forbesapi/org/nba-valuations/2025/position/true.json?limit=40 (Forbes list API; 2026 list dated 2026-10-16, 2025 list dated 2025-10-23; checked 2026-10-30) |
| `pred_ba9e973e` | Median Wikipedia daily pageviews for top-3 NBA Finals 2026 players (top-3 by minutes played in Finals) exceeds the same metric for 2025 Finals top-3 players (calculated within 30 days post-Finals) | 2026-04-29 | 0.62 | YES | 0.1444 | Top-3 by Finals minutes 2026: Brunson 39.2, Wembanyama 39.2, Vassell 38.3 mpg (5 games, ended 2026-06-13); 2025: Gilgeous-Alexander 38.2, J. Williams 34.7, Nembhard 33.9 mpg (7 games, ended 2025-06-22). 30-day post-Finals median of combined daily views 22,623 (2026) vs 13,770 (2025); per-player medians sum 22,803 vs 12,857. YES under every aggregation and with the window starting on Finals day. Source: Wikipedia REST API per-article daily pageviews, en.wikipedia all-access/all-agents: https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{Jalen_Brunson,Victor_Wembanyama,Devin_Vassell}/daily/20260614/20260713 and /{Shai_Gilgeous-Alexander,Jalen_Williams,Andrew_Nembhard}/daily/20250623/20250722; minutes from https://en.wikipedia.org/wiki/2026_NBA_Finals and https://en.wikipedia.org/wiki/2025_NBA_Finals player statistics (NBA.com/Basketball-Reference cited); checked 2026-10-30 |

### ForecastBench rows resolved (50, all BWD, not forward)

All 50 were locked 2026-04-26, about six months after their 2025-11-02 resolution date, so they are BWD and never enter forward scoring. Outcomes come from the public ForecastBench resolution set for the 2025-10-26 round (https://github.com/forecastingresearch/forecastbench-datasets/blob/main/datasets/resolution_sets/2025-10-26_resolution_set.json, downloaded 2026-10-30), joined through the question ids in `~/chorus/outputs/forecastbench/2025-10-26_chorus_full_v10.json`. 49 of 50 agree with the outcome in that internal file; for the one that differs, the public resolution set is used. Outcomes: 8 YES, 42 NO; mean Brier 0.2052 (p as locked). Each row's `resolution_source` names its ForecastBench question id.

### Voided under PREREG_resolution_run_2026-10-30.json (41)

| rule | domain | question | note |
|---|---|---|---|
| V1_duplicate | existing_home_sales | Existing home sales higher MoM for March | duplicate of `5cf50d5003f6` |
| V1_duplicate | existing_home_sales | Existing home sales higher MoM for March | duplicate of `5cf50d5003f6` |
| V1_duplicate | existing_home_sales | Existing home sales higher MoM for March | duplicate of `5cf50d5003f6` |
| V1_duplicate | ez_cpi | Eurozone CPI hotter than consensus for March | duplicate of `3a45e7f61e83` |
| V1_duplicate | ez_cpi | Eurozone CPI hotter than consensus for March | duplicate of `3a45e7f61e83` |
| V1_duplicate | ez_cpi | Eurozone CPI hotter than consensus for March | duplicate of `3a45e7f61e83` |
| V1_duplicate | ez_cpi | Eurozone CPI hotter than consensus for March | duplicate of `3a45e7f61e83` |
| V1_duplicate | ez_cpi | Eurozone CPI hotter than consensus for March | duplicate of `3a45e7f61e83` |
| V1_duplicate | ez_cpi | Eurozone CPI hotter than consensus for March | duplicate of `3a45e7f61e83` |
| V1_duplicate | forecastbench | Will there be more than ten times as many fatalities in Turkmenistan for the 30 days before {resolution_date}  | duplicate of `pred_fb_da97b7ddfe29` |
| V1_duplicate | forecastbench | Will there be more 'Strategic developments' in Kenya for the 30 days before {resolution_date} compared to the  | duplicate of `pred_fb_b07a35d69694` |
| V1_duplicate | forecastbench | Will there be more than ten times as many 'Explosions/Remote violence' in Canada for the 30 days before {resol | duplicate of `pred_fb_6d639f5ead40` |
| V1_duplicate | forecastbench | Will there be more than ten times as many 'Violence against civilians' in Kosovo for the 30 days before {resol | duplicate of `pred_fb_848fde7e8a93` |
| V1_duplicate | forecastbench | Will there be more 'Protests' in Finland for the 30 days before {resolution_date} compared to the 30-day avera | duplicate of `pred_fb_ab9209eec18c` |
| V1_duplicate | forecastbench | Will there be more 'Violence against civilians' in Botswana for the 30 days before {resolution_date} compared  | duplicate of `pred_fb_9138b8ea137d` |
| V1_duplicate | forecastbench | Will there be more fatalities in French Polynesia for the 30 days before {resolution_date} compared to the 30- | duplicate of `pred_fb_ac35c4f2eb74` |
| V1_duplicate | forecastbench | Will there be more 'Explosions/Remote violence' in Democratic Republic of Congo for the 30 days before {resolu | duplicate of `pred_fb_a3f39a9cd4c1` |
| V1_duplicate | forecastbench | Will there be more 'Strategic developments' in Mozambique for the 30 days before {resolution_date} compared to | duplicate of `pred_fb_0c6c47da7321` |
| V1_duplicate | forecastbench | Will there be more than ten times as many 'Protests' in France for the 30 days before {resolution_date} compar | duplicate of `pred_fb_5520bfc3a8cd` |
| V1_duplicate | michigan_sentiment | Michigan Consumer Sentiment higher than prior month April 2026 | duplicate of `164377ad2cae` |
| V1_duplicate | michigan_sentiment | Michigan Consumer Sentiment higher than prior month April 2026 | duplicate of `164377ad2cae` |
| V1_duplicate | michigan_sentiment | Michigan Consumer Sentiment higher than prior month April 2026 | duplicate of `164377ad2cae` |
| V1_duplicate | michigan_sentiment | Michigan Consumer Sentiment higher than prior month April 2026 | duplicate of `164377ad2cae` |
| V1_duplicate | michigan_sentiment | Michigan Consumer Sentiment higher than prior month April 2026 | duplicate of `164377ad2cae` |
| V1_duplicate | michigan_sentiment | Michigan Consumer Sentiment higher than prior month April 2026 | duplicate of `164377ad2cae` |
| V1_duplicate | michigan_sentiment | Michigan Consumer Sentiment higher than prior month April 2026 | duplicate of `164377ad2cae` |
| V1_duplicate | michigan_sentiment | Michigan Consumer Sentiment higher than prior month April 2026 | duplicate of `164377ad2cae` |
| V1_duplicate | state_primary_2026 | (no question text, no probability; criterion field: "Will Maxx Crosby play for New York Jets next?") | duplicate of `pred_` |
| V1_duplicate | state_primary_2026 | (no question text, no probability; criterion field: "Will Maxx Crosby play for New York Jets next?") | duplicate of `pred_` |
| V1_duplicate | state_primary_2026 | (no question text, no probability; criterion field: "Will Maxx Crosby play for New York Jets next?") | duplicate of `pred_` |
| V1_duplicate | state_primary_2026 | (no question text, no probability; criterion field: "Will Maxx Crosby play for New York Jets next?") | duplicate of `pred_` |
| V1_duplicate | state_primary_2026 | (no question text, no probability; criterion field: "Will Maxx Crosby play for New York Jets next?") | duplicate of `pred_` |
| V1_duplicate | state_primary_2026 | (no question text, no probability; criterion field: "Will Maxx Crosby play for New York Jets next?") | duplicate of `pred_` |
| V1_duplicate | state_primary_2026 | (no question text, no probability; criterion field: "Will Maxx Crosby play for New York Jets next?") | duplicate of `pred_` |
| V1_duplicate | state_primary_2026 | (no question text, no probability; criterion field: "Will Maxx Crosby play for New York Jets next?") | duplicate of `pred_` |
| V2_ill_formed_question | primary_scan | Wisconsin D governor primary: TBD wins | ill-formed question |
| V2_ill_formed_question | primary_scan | Minnesota D governor primary: TBD wins | ill-formed question |
| V2_ill_formed_question | primary_scan | Michigan R senate primary: TBD wins | ill-formed question |
| V2_ill_formed_question | primary_scan | New Hampshire R senate primary: TBD wins | ill-formed question |
| V2_ill_formed_question | primary_scan | Maine R senate primary: TBD wins | ill-formed question |
| V3_unresolvable_source | nba_audience_trajectory | Top-3 NBA player Wikipedia 30-day median pageviews capture ≥40% of total NBA-player attention share, May 1-30  | unresolvable source |
