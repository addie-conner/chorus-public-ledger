# Resolution report, 2026-10-31 (2026 NBA draft rows)

Branch `resolution-2026-10-31`, local only. Not pushed, not deployed. Run label 2026-10-31; the machine clock read 2026-10-30 UTC, which is what the OpenTimestamps receipts will show.

Backups of every file written carry the suffix `.bak.20261031T195329`.

## Result

- **Sports forward record, as of 2026-10-31** (`scripts/sports_forward_record_2026_10_31.py`, same method as 2026-10-30; only the as-of date changed):
  - Directional hits: 101 of 127.
  - Brier 0.156 against 0.177 for the naive baselines, skill +0.12.
  - Without the 41 World Cup rows locked after the 2026-06-11 kickoff: n=86, 69 right, 0.158 against 0.161, skill +0.02.
  - Where a pre-lock market price exists (18 rows): 0.121 against 0.124, no edge. Unchanged.
  - Previous figure (2026-10-30): 101 of 126, 0.153 against 0.178, skill +0.14 (+0.04 at n=85).
- The one newly scored row is a miss, so the pooled skill fell from +0.14 to +0.12.

| subset | n | right | Chorus Brier | baseline | skill |
|---|---|---|---|---|---|
| outcomes / winners | 72 | 57 | 0.1563 | 0.2053 | +0.24 (was +0.27, n=71) |
| attention | 23 | 15 | 0.2542 | 0.2268 | -0.12 (unchanged) |
| sponsorship / media | 10 | 8 | 0.1906 | 0.1600 | -0.19 (unchanged) |
| Forbes lists | 22 | 21 | 0.0340 | 0.0415 | +0.18, 0 over persistence on 20 rows (unchanged) |
| **pooled, calendar excluded** | **127** | **101** | **0.1555** | **0.1773** | **+0.12** |

## Changes

1. **Resolved YES:** `pred_nba26_nba26_wiz_r2`, "Wizards use R2 pick #51 to draft Nigerian-heritage OR DMV-local prospect", p 0.30, Brier 0.49.
   - Washington traded #51 (to Orlando) and #60 (to Milwaukee) in a three-team trade and received #46, Felix Okpara. Okpara is one of the four players named in the criterion, so the trade-up branch is met.
   - Sources: nba.com/news/magic-wizards-bucks-trade-2026-nba-draft (updated 2026-06-25) and en.wikipedia.org/wiki/2026_NBA_draft (second round 2026-06-24). Both were checked on 2026-10-30.
   - Staged in `~/chorus/data/resolutions_to_apply/batch_2026_10_31.json` and applied by `apply_staged_resolutions.py`.
   - The locked resolution_date 2027-04-30 is kept. The draft-night date 2026-06-24 is stored as `resolution_date_corrected`, the same treatment as the three draft-order rows.
2. **Voided:** `pred_nba26_nba26_d4`, "Wizards 8+ nationally televised regular-season games", p 0.85.
   - The criterion counts "ABC/ESPN/TNT/NBA TV" broadcasts, and TNT no longer carries NBA games.
   - The 2026-10-30 rule did not cover the row: it applies only to past-due rows, and its V3 list is closed. A dated addendum came first: `PREREG_resolution_run_2026-10-30_addendum_2026-10-31.json`, sha256 `f7d4ea016f6cb2479b4551c59044151967411b943071cbf7f7383c85426f4491`, with an `.ots` stamp beside it. It adds rule V4 and states that it was written after the schedule was public.
   - Criterion note: "Would likely have resolved YES on intent (10+ national games per Yahoo Sports 2026-08-13 / 2026-09-03); voided rather than scored on a reinterpreted criterion."
3. **Not RETRO, left open:** `pred_nba26_nba26_3`, "Cameron Boozer signs major footwear deal by 2026-12-31", locked 2026-06-08.
   - The locked criterion already names the Jordan Brand NIL deal and counts only a pro contract.
   - Sneaker News (2026-05-21) shows Boozer in the Jordan Triangle rollout but uses no contract language.
   - HoopsHype (2026-06-23; syndicated on Yahoo 2026-06-24) says he "landed a shoe deal with Jordan Brand earlier this year", without saying whether that is the NIL deal or a pro deal.
   - Neither source shows a pro deal public before the lock, so the row is not marked RETRO. It still needs a ruling at resolution on whether a pro contract was ever announced.
4. **Upgraded OpenTimestamps receipts:** 13 rows (`pred_nba26_nba26_{3,d3,d4,draft_1,w1..w9}`).
   - For each row, `ots info` reports a file sha256 equal to `shasum -a 256` of the anchored JSON.
   - Each JSON matches its ledger row on question, probability, lock time, criterion and original_sha.
   - Each receipt carries Bitcoin attestations in blocks 953687 (2026-06-14T20:19:15Z), 953697 (21:49:28Z) and 953699 (22:00:24Z). Each was checked against the block merkle root from blockstream.info.
   - Mismatches: 0. The pending receipts are kept as `.ots.pending-2026-10-31`.
   - The rows now carry `ots_anchor`, `anchored_by: bitcoin block 953697 (2026-06-14T21:49:28Z)`, the attestation list and a note, all through `public_curations.json`.
   - The anchors were made 2026-06-14, six days after the 2026-06-08 lock and before the 2026-06-23 draft.
   - `wiz_r2` has no per-row anchor.

## Checks

- `check_curations_preserved.py` comparing the rebuild against the 2026-10-30 public file: 32 differences, all expected. They are wiz_r2 resolved, d4 voided with its note, and ots_anchor/ots_anchored on the 13 rows. No resolution or curated field was lost.
- A field-by-field diff over all 1,034 rows found changes only on those 14 rows. After the copy, the check against the rebuild exits 0.
- Locked fields (question, probability, locked_at, original_sha, resolution_date) are unchanged.
- The whole-file stamp `ledger_canonical.json.ots` covers sha256 `53de16c0…c49d`. The prior receipt is kept as `ledger_canonical.json.ots.2026-10-30`.
- The renderer now produces the macro-release line and the verification text that were hand-edited into the 2026-10-30 page, so they survive a re-render.

## Canon edits needed (not made)

- CH1 in `~/groundline/reports/CLAIMS_CANON_2026-09-01.md` (line 367) still says n=126, 101 right, 0.153 against 0.178, +0.14 (+0.04 at n=85). The new figures are n=127, 101 right, 0.156 against 0.177, +0.12 (+0.02 at n=86, 0.158 against 0.161), resolved by 2026-10-31.
- CH2, CH3, CH4 and CH5 are unchanged.
