# resolve_demo_arc_picks.py — usage

Auto-scores the 22 demo-arc high-conviction picks against their Wikipedia threshold
as resolution dates pass. Default = dry-run. Two flags required to actually write.

## When to run

After any structural-event window passes (NBA Draft Week, MLB All-Star Week, NCAA
football opening week, Heisman ceremony, etc). The script checks for entries whose
`resolution_date <= today + grace_days` (default grace = 2 days).

Next scheduled resolutions (as of 2026-05-27):

| Date       | Athlete         | p     | Event                              |
|------------|-----------------|-------|------------------------------------|
| 2026-06-29 | RJ Luis Jr.     | 0.70  | 2026 NBA Draft Week                |
| 2026-07-18 | Bryce Eldridge  | 0.75  | MLB All-Star Week (Future Stars)   |
| 2026-07-18 | Volpe / Wood / Stewart / McGonigle | 0.72–0.77 | MLB All-Star Week 2026 |
| 2026-07-25 | Citron / Miles  | 0.70–0.78 | WNBA All-Star Week              |
| 2026-08-22 | Kobbie Mainoo   | 0.75  | 2026-27 Premier League open week   |
| 2026-08-29 | Hezly Rivera    | 0.73  | U.S. Gymnastics Championships 2026 |
| 2026-09-05 | Klubnik / Allar | 0.72  | NCAA football season opening week  |
| 2026-09-08 | Kasatkina       | 0.78  | 2026 US Open women's singles       |
| 2026-10-04 | Kyle Harrison   | 0.72  | MLB postseason / Wild Card race    |
| 2026-10-17 | CJ Carr         | 0.75  | Notre Dame marquee October game    |
| 2026-10-27 | Stephon Castle  | 0.72  | 2026-27 NBA opening week           |
| 2026-11-21 | Sam Leavitt     | 0.70  | LSU-Alabama rivalry week 2026      |
| 2026-12-12 | Jeremiah Smith  | 0.70  | Heisman ceremony week              |
| 2027-03-05 | Travis Bazzana  | 0.70  | 2027 MLB Spring Training           |
| 2027-04-12 | Hidalgo / Fudd  | 0.75  | NCAA Women's Final Four 2027       |
| 2027-07-11 | Lily Yohannes   | 0.71  | FIFA Women's World Cup 2027        |

## Run modes

```bash
# Dry-run (default): show what would resolve. Safe.
python3 scripts/resolve_demo_arc_picks.py

# Adjust grace window (resolve everything due within N days of today)
python3 scripts/resolve_demo_arc_picks.py --grace-days 7

# Actually write to ledger — requires BOTH flags
python3 scripts/resolve_demo_arc_picks.py --commit --confirm
```

The `--commit --confirm` combo is intentional friction. The script will never push
to git — it prints the suggested git commands instead, for manual review.

## Pre-flight checks

```bash
# Before running with --commit, always:
git -C /Users/addieconner/chorus-public-ledger status
git -C /Users/addieconner/chorus-public-ledger log -3 --oneline
```

The repo is touched by parallel sessions. Confirm no other changes are staged.

## What it does per entry

1. Parses the question text:
   `"{Athlete} Wikipedia 7-day median exceeds {N}/day during {event} ({YYYY-MM-DD} through {YYYY-MM-DD})"`
2. Pulls daily pageviews for the slug over the window from the Wikipedia REST API.
3. Computes the median over the full window (typically 7 days).
4. ABOVE direction: median >= threshold → resolution=True. BELOW direction: median <= threshold → True.
5. Computes Brier = (1−p)² if resolved else p².
6. Updates the entry in-place: `status="resolved"`, `resolved_at`, `resolution`, `brier_score`, `resolution_source`.

## What it doesn't do

- Doesn't push to git (prints the commands instead).
- Doesn't re-score entries already marked `status="resolved"`.
- Doesn't touch entries outside the 22-pick cohort (filters by `source_file`).
- Doesn't handle questions with non-ISO date windows (a small number of pre-call
  backward-validation entries use natural-language date ranges; those get skipped
  with an "unparseable" flag and need manual resolution).

## Failure modes

- Wikipedia API 404 (slug doesn't exist or got renamed) → entry skipped, logged.
- Wikipedia API HTTP error → entry skipped, logged.
- Question shape doesn't match the regex → entry skipped, manual review needed.

Any skipped entry stays `status="open"` — re-run later or resolve manually.
