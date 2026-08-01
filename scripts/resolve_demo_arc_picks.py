#!/usr/bin/env python3
"""resolve_demo_arc_picks.py — score the 22 demo-arc HC predictions as they resolve.

Scope: high-conviction (chorus_probability >= 0.70) entries from these source files,
all of which use Wikipedia-pageview threshold resolution against a structural-event
window (NBA Draft Week, MLB All-Star Week, NCAA football opening, etc):

  cap2_breakout_2026_05_26.jsonl
  cap2_cohort_expansion_2026_05_26.jsonl
  cap2_multisource_v3_2026_05_26.jsonl
  cap2_broadscan_2026_05_27.jsonl
  cap2_brunson_maxey_demo_2026_05_27.jsonl
  cap2_demo_wave2_2026_05_27.jsonl

Each entry's question is shaped like:
  "{Athlete} Wikipedia 7-day median exceeds {N}/day during {event} ({YYYY-MM-DD} through {YYYY-MM-DD})"

(or "stays below" for the rare BELOW-direction entry).

Algorithm:
  1. For each candidate to resolve (resolution_date <= today + grace), parse the slug,
     threshold, direction, and window from the question text.
  2. Pull daily Wikipedia pageviews for the window from the REST API.
  3. Compute 7-day median over the window. (If window is 7 days, that's the full window
     median. Some windows are longer — we still take the full-window median, which is
     a reasonable approximation of "7-day median during this period.")
  4. ABOVE direction: median >= threshold  -> resolution = True.
     BELOW direction: median <= threshold  -> resolution = True.
  5. brier = (1-p)^2 if resolution else p^2.

DRY-RUN BY DEFAULT. Pass --commit AND --confirm to write back to the ledger.
Never auto-pushes — prints the suggested git commands.

Concurrency note: chorus-public-ledger is touched by parallel sessions. Always
`git status` before --commit, and prefer staging the change manually.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median

LEDGER = Path("/Users/addieconner/chorus-public-ledger/ledger_canonical.json")
# Additional staging files whose entries should also be considered for resolution.
# Each lives at the repo root and is read/written independently of the canonical ledger.
STAGING_FILES = [
    Path("/Users/addieconner/chorus-public-ledger/staging_2026_nba_draft_2026-06-08.json"),
    Path("/Users/addieconner/chorus-public-ledger/staging_2026-06-08_avi_v2_findings.json"),
    Path("/Users/addieconner/chorus-public-ledger/staging_2026-06-28_demo_arc_locks.json"),
]
COHORT_SOURCE_FILES = {
    "cap2_breakout_2026_05_26.jsonl",
    "cap2_cohort_expansion_2026_05_26.jsonl",
    "cap2_multisource_v3_2026_05_26.jsonl",
    "cap2_broadscan_2026_05_27.jsonl",
    "cap2_brunson_maxey_demo_2026_05_27.jsonl",
    "cap2_demo_wave2_2026_05_27.jsonl",
    "staging_2026_nba_draft_2026-06-08.json",
    "staging_2026-06-08_avi_v2_findings.json",
    "staging_2026-06-28_demo_arc_locks.json",
}
HC_THRESHOLD = 0.70
# Staging-file entries are admitted to the resolution queue regardless of HC threshold —
# the threshold gates the original demo-arc cohort, not standalone forward locks.
STAGING_HC_THRESHOLD = 0.0
RESOLUTION_SOURCE = "Wikipedia REST API per-article daily pageviews"
USER_AGENT = "Chorus-Resolution-Monitor/2026.05.27 (addieconner@gmail.com)"

QUESTION_RE = re.compile(
    r"^(?P<athlete>.+?) Wikipedia 7-day median "
    r"(?P<direction>exceeds|stays below|below) "
    r"(?P<threshold>[\d,]+)/day during (?P<event>.+?) "
    r"\((?P<window_start>\d{4}-\d{2}-\d{2}) through (?P<window_end>\d{4}-\d{2}-\d{2})\)"
)


def parse_question(q: str) -> dict | None:
    m = QUESTION_RE.match(q.strip())
    if not m:
        return None
    return {
        "athlete": m["athlete"],
        "direction": "below" if "below" in m["direction"] else "above",
        "threshold": int(m["threshold"].replace(",", "")),
        "event": m["event"],
        "window_start": date.fromisoformat(m["window_start"]),
        "window_end": date.fromisoformat(m["window_end"]),
    }


def extract_slug(entry: dict) -> str | None:
    """Pull the Wikipedia slug. Prefer the explicit slug in model_inputs.scenario;
    fall back to the resolution_criterion text which embeds the slug in quotes."""
    scenario = (entry.get("model_inputs") or {}).get("scenario") or {}
    slug = scenario.get("wiki_slug")
    if slug:
        return slug
    rc = entry.get("resolution_criterion") or ""
    m = re.search(r"pageviews for '([^']+)'", rc)
    if m:
        return m["1"] if False else m.group(1)
    return None


def wiki_encode_slug(slug: str) -> str:
    return urllib.parse.quote(unicodedata.normalize("NFC", slug), safe="%")


def fetch_pageviews(slug: str, start: date, end: date) -> list[dict] | None:
    """Daily pageviews for slug over [start, end] inclusive."""
    enc = wiki_encode_slug(slug)
    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia/all-access/all-agents/{enc}/daily/"
        f"{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data.get("items", [])
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)}


def resolve_one(entry: dict) -> dict | None:
    """Returns a resolution dict or None if cannot resolve (with reason printed)."""
    q = entry.get("question") or ""
    parsed = parse_question(q)
    if not parsed:
        print(f"  [skip] {entry['canonical_id']}: question shape unparseable")
        return None

    slug = extract_slug(entry)
    if not slug:
        print(f"  [skip] {entry['canonical_id']}: no slug")
        return None

    items = fetch_pageviews(slug, parsed["window_start"], parsed["window_end"])
    if isinstance(items, dict) and items.get("_error"):
        print(f"  [skip] {entry['canonical_id']}: wikipedia api {items['_error']}")
        return None
    if not items:
        print(f"  [skip] {entry['canonical_id']}: no pageview items")
        return None

    views = [it["views"] for it in items]
    window_median = median(views)
    threshold = parsed["threshold"]
    direction = parsed["direction"]

    if direction == "above":
        resolved = window_median >= threshold
    else:
        resolved = window_median <= threshold

    p = entry["chorus_probability"]
    brier = (1 - p) ** 2 if resolved else p ** 2

    return {
        "canonical_id": entry["canonical_id"],
        "athlete": parsed["athlete"],
        "direction": direction,
        "threshold": threshold,
        "window_median": round(window_median, 1),
        "resolution": bool(resolved),
        "brier": round(brier, 4),
        "chorus_probability": p,
        "window_start": parsed["window_start"].isoformat(),
        "window_end": parsed["window_end"].isoformat(),
        "data_points": len(views),
    }


def apply_resolution_to_entry(entry: dict, r: dict, now_iso: str) -> None:
    entry["status"] = "resolved"
    entry["resolved_at"] = now_iso
    entry["resolution"] = r["resolution"]
    entry["brier_score"] = r["brier"]
    entry["resolution_source"] = RESOLUTION_SOURCE
    flags = entry.get("audit_flags") or []
    entry["audit_flags"] = [f for f in flags if f != "resolution_overdue"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--commit", action="store_true",
                    help="Actually write resolutions to the ledger (default: dry-run).")
    ap.add_argument("--confirm", action="store_true",
                    help="Required alongside --commit to actually persist changes.")
    ap.add_argument("--grace-days", type=int, default=2,
                    help="Resolve entries with resolution_date <= today + grace_days.")
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    args = ap.parse_args()

    today = date.today()
    cutoff = today + timedelta(days=args.grace_days)
    print(f"=== resolve_demo_arc_picks · today={today} · cutoff={cutoff} ===")

    # Load canonical + each staging file. `sources[path]` is the parsed JSON list
    # for that file; resolutions are written back to the file the entry came from.
    sources: dict[Path, list] = {args.ledger: json.loads(args.ledger.read_text())}
    for sp in STAGING_FILES:
        if sp.exists():
            sources[sp] = json.loads(sp.read_text())

    candidates: list[tuple[dict, Path]] = []
    for path, entries in sources.items():
        is_staging = path != args.ledger
        threshold = STAGING_HC_THRESHOLD if is_staging else HC_THRESHOLD
        for e in entries:
            if (
                e.get("source_file") in COHORT_SOURCE_FILES
                and e.get("status") == "open"
                and e.get("chorus_probability", 0) >= threshold
            ):
                candidates.append((e, path))
    print(f"Candidate open entries: {len(candidates)} "
          f"(canonical + {sum(1 for p in sources if p != args.ledger)} staging file(s))")

    due: list[tuple[dict, Path]] = []
    upcoming: list[tuple[date, dict, Path]] = []
    for e, path in candidates:
        rd_str = e.get("resolution_date")
        if not rd_str:
            continue
        try:
            rd = date.fromisoformat(rd_str[:10] if len(rd_str) > 10 else rd_str)
        except ValueError:
            continue
        if rd <= cutoff:
            due.append((e, path))
        else:
            upcoming.append((rd, e, path))

    print(f"Due for resolution (resolution_date <= {cutoff}): {len(due)}")
    if not due:
        upcoming.sort(key=lambda x: x[0])
        print("\nUpcoming resolutions (top 8):")
        for rd, e, path in upcoming[:8]:
            athlete = parse_question(e.get("question") or "")
            athlete_name = athlete["athlete"] if athlete else "?"
            days = (rd - today).days
            tag = "[stage]" if path != args.ledger else "[canon]"
            print(f"  {rd}  ({days:+d} days)  {tag} {athlete_name:<22}  p={e['chorus_probability']:.2f}  {e['canonical_id']}")
        print("\nNo entries to resolve today. Exiting cleanly.")
        return 0

    # Resolve each one (rate-limited)
    resolutions: list[tuple[dict, Path, dict]] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for entry, path in due:
        time.sleep(1.0)  # courtesy rate-limit on Wikipedia
        r = resolve_one(entry)
        if r is None:
            continue
        resolutions.append((entry, path, r))
        marker = "YES" if r["resolution"] else "NO "
        print(f"  [{marker}] {r['athlete']:<22} median={r['window_median']:<7} thr={r['threshold']:<7} brier={r['brier']:.4f}")

    if not resolutions:
        print("\nNo resolvable entries (all parseable but couldn't fetch data). Exiting.")
        return 0

    yes_n = sum(1 for _, _, r in resolutions if r["resolution"])
    no_n = len(resolutions) - yes_n
    mean_brier = sum(r["brier"] for _, _, r in resolutions) / len(resolutions)
    print(f"\nSummary: {len(resolutions)} resolved · {yes_n} YES · {no_n} NO · mean Brier={mean_brier:.4f}")

    if not args.commit:
        print("\n[DRY-RUN] No ledger changes written. Re-run with --commit --confirm to persist.")
        return 0

    if not args.confirm:
        print("\n[GUARD] --commit passed without --confirm. Refusing to write. Pass both flags to persist.")
        return 1

    # Persist — group writes by source file (canonical + each staging)
    for entry, _path, r in resolutions:
        apply_resolution_to_entry(entry, r, now_iso)
    modified_paths = {p for _, p, _ in resolutions}
    for p in modified_paths:
        p.write_text(json.dumps(sources[p], indent=2))
        n = sum(1 for _, sp, _ in resolutions if sp == p)
        print(f"Wrote {n} resolution(s) to {p}")

    print("\nNext steps — run manually:")
    repo = args.ledger.parent
    print(f"  git -C {repo} status")
    files_arg = " ".join(p.name for p in modified_paths)
    print(f"  git -C {repo} add {files_arg}")
    n_word = "resolutions" if len(resolutions) != 1 else "resolution"
    print(f"  git -C {repo} commit -m 'Resolve {len(resolutions)} {n_word} {today.isoformat()}'")
    print(f"  git -C {repo} push origin main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
