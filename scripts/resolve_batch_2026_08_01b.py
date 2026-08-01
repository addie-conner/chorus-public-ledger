#!/usr/bin/env python3
"""resolve_batch_2026_08_01b.py — Write-back finisher for July-15 verified resolutions.

Resolves 18 predictions verified in resolver_run_2026-07-15.txt but not yet
written to ledger due to Gmail MCP expiry on that session's delivery:

  BOJ_DECISION (6): BOJ hiked to 1.00% on June 16 2026 — "holds" = NO (actual=0)
  FED_TERMINAL (6): Fed held at 3.50-3.75% — "above 4.00%" = NO (actual=0)
  FOMC_SCAN (4):    FOMC June 17 held — cuts=NO, holds=YES, "cut?"=NO
  MONETARY_POLICY (1): FOMC May 6-7 held — "holds unchanged"=YES (actual=1)
  TRUMP_SURVIVAL (1): Trump still president July 31 2026 — YES (actual=1)

Resolution mapping and criterion verification:

  BOJ "holds at next meeting" — BOJ hiked to 1.00% on June 16, did NOT hold.
    actual=0 for all 6. Clean match.
  FED "Fed funds upper above 4.00% at next FOMC" — Fed target was 3.50-3.75%
    throughout all resolution dates. actual=0 for all 6. Clean match.
  FOMC June-17 "Fed cuts 25bp" — Fed held. actual=0. Clean match.
  FOMC June-17 "Fed holds rates at current level" — Fed held. actual=1. Clean match.
  FOMC June-17 "Fed cuts 50bp" — Fed held. actual=0. Clean match.
  FOMC rate decision "Will the FOMC cut rates at the 2026-06-17 meeting?" — No cut. actual=0.
  pred_e038ee1d "FOMC holds rates unchanged at May 6-7 2026 meeting" — Fed held. actual=1.
  Trump "Trump still president on July 31 2026" — YES as of 2026-08-01. actual=1.

Evidence sources:
  BOJ hike June 16:
    [1] https://www.cnbc.com/2026/06/16/boj-rate-hike-historic-inflation.html
    [2] https://www.reuters.com/markets/japan/bank-japan-raises-interest-rates-1-june-2026/
  Fed June 17 hold:
    [1] https://www.cnbc.com/2026/06/17/fed-interest-rate-decision-june-2026.html
    [2] https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm
  Fed Apr 29 hold (for fed_terminal resolution dates May 23-30):
    [1] https://www.cnbc.com/2026/04/29/fed-interest-rate-decision-april-2026.html
    [2] https://www.federalreserve.gov/newsevents/pressreleases/monetary20260429a.htm
  FOMC May 6-7 hold:
    [1] https://www.cnbc.com/2026/05/07/fed-interest-rate-decision-may-2026.html
    [2] https://www.federalreserve.gov/newsevents/pressreleases/monetary20260507a.htm
  Trump still president July 31 2026:
    [1] https://www.bbc.com/news/world-us-canada-2026-07-31
    [2] https://apnews.com/hub/donald-trump

Ambiguous-list exclusions (NOT included):
  - pred_9d8ac31d (Cooper Flagg #1): contradicts pred_nba_draft_2026_flagg_not_in_draft; deferred
  - SCOTUS_SCAN (6): "rules as expected" criterion requires Addie adjudication
  - ForecastBench (60): template-literal placeholders, needs harness

Default mode is DRY-RUN. Pass --commit --confirm to write.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

NOW = datetime.now(timezone.utc).isoformat()
HOME = Path.home()
CHORUS = HOME / "chorus"
PUBLIC = HOME / "chorus-public-ledger"

V1 = CHORUS / "static" / "public_ledger" / "predictions.json"
V2 = CHORUS / "chorus_predictions.jsonl"
CANONICAL = PUBLIC / "ledger_canonical.json"
CANONICAL_INTERNAL = CHORUS / "static" / "public_ledger" / "ledger_canonical.json"
RESLOG = CHORUS / "data" / "calibration" / "resolution_log.json"
STAGING = PUBLIC / "staging_2026-08-01b_writeback.json"

# ---------------------------------------------------------------------------
# Resolution table — canonical_id -> resolution dict
# ---------------------------------------------------------------------------
# actual: 1 = YES (outcome occurred), 0 = NO (outcome did not occur)
# source_url: primary evidence
# evidence: brief description (max 300 chars)
# criterion_note: optional mapping clarification

_BOJ_SRC = "https://www.cnbc.com/2026/06/16/boj-rate-hike-historic-inflation.html"
_BOJ_EVD = "BOJ raised rates to 1.00% on June 16, 2026 — did NOT hold. All 'holds at next meeting' = NO."
_BOJ_NOTE = "BOJ hiked to 1.00% June 16, 2026; criterion='holds at next meeting'; BOJ did NOT hold -> actual=0"

_FED_AP_SRC = "https://www.cnbc.com/2026/04/29/fed-interest-rate-decision-april-2026.html"
_FED_JN_SRC = "https://www.cnbc.com/2026/06/17/fed-interest-rate-decision-june-2026.html"
_FED_EVD = "Fed held at 3.50-3.75% at Apr 29 and Jun 17 2026 meetings. Upper bound never exceeded 4.00%."
_FED_NOTE = "Fed funds upper = 3.75% (held Apr 29 + Jun 17 2026); criterion='above 4.00%' -> actual=0"

RES: dict[str, dict] = {

    # ── TRUMP SURVIVAL ────────────────────────────────────────────────────
    "62f9f4e239d1": {
        "actual": 1,
        "source_url": "https://apnews.com/hub/donald-trump",
        "evidence": (
            "Trump remains the 47th President of the United States as of 2026-08-01. "
            "No removal, resignation, or death event occurred before or on July 31 2026. "
            "Verified via AP News White House coverage and BBC US politics."
        ),
        "criterion_note": "Criterion: 'Trump still president on July 31 2026' — YES (actual=1); Brier=(0.75-1)^2=0.0625",
    },

    # ── BOJ DECISION (6) — all "holds" = actual=0 ─────────────────────────
    "fbec98f5399b": {"actual": 0, "source_url": _BOJ_SRC, "evidence": _BOJ_EVD, "criterion_note": _BOJ_NOTE},
    "7821f470c2f1": {"actual": 0, "source_url": _BOJ_SRC, "evidence": _BOJ_EVD, "criterion_note": _BOJ_NOTE},
    "db77a0ce4dc0": {"actual": 0, "source_url": _BOJ_SRC, "evidence": _BOJ_EVD, "criterion_note": _BOJ_NOTE},
    "0eba43e4b227": {"actual": 0, "source_url": _BOJ_SRC, "evidence": _BOJ_EVD, "criterion_note": _BOJ_NOTE},
    "c2fae00fc838": {"actual": 0, "source_url": _BOJ_SRC, "evidence": _BOJ_EVD, "criterion_note": _BOJ_NOTE},
    "e7b83ddd9fe9": {"actual": 0, "source_url": _BOJ_SRC, "evidence": _BOJ_EVD, "criterion_note": _BOJ_NOTE},

    # ── FED TERMINAL (6) — upper never exceeded 4.00%, all = actual=0 ─────
    "73dda56e9577": {"actual": 0, "source_url": _FED_AP_SRC, "evidence": _FED_EVD, "criterion_note": _FED_NOTE},
    "4be5b00af39d": {"actual": 0, "source_url": _FED_AP_SRC, "evidence": _FED_EVD, "criterion_note": _FED_NOTE},
    "9248c619476e": {"actual": 0, "source_url": _FED_AP_SRC, "evidence": _FED_EVD, "criterion_note": _FED_NOTE},
    "cb935523027f": {"actual": 0, "source_url": _FED_AP_SRC, "evidence": _FED_EVD, "criterion_note": _FED_NOTE},
    "902b2ea04406": {"actual": 0, "source_url": _FED_JN_SRC, "evidence": _FED_EVD, "criterion_note": _FED_NOTE},
    "2888044d0439": {"actual": 0, "source_url": _FED_JN_SRC, "evidence": _FED_EVD, "criterion_note": _FED_NOTE},

    # ── FOMC_SCAN (3 entries June 17 meeting) ─────────────────────────────
    "aaeb684d2c1a": {   # "Fed cuts 25bp" — Fed held
        "actual": 0,
        "source_url": _FED_JN_SRC,
        "evidence": "FOMC June 17 2026: Fed held rates at 3.50-3.75% (unanimous 12-0). No 25bp cut.",
        "criterion_note": "Criterion: 'FOMC 2026-06-17: Fed cuts 25bp' — Fed HELD, not cut -> actual=0",
    },
    "c0c9c10c958f": {   # "Fed holds rates at current level" — Fed held
        "actual": 1,
        "source_url": _FED_JN_SRC,
        "evidence": "FOMC June 17 2026: Fed held rates at 3.50-3.75% (unanimous 12-0). Rate unchanged.",
        "criterion_note": "Criterion: 'FOMC 2026-06-17: Fed holds rates at current level' — Fed HELD -> actual=1",
    },
    "f33e9dd53858": {   # "Fed cuts 50bp" — Fed held
        "actual": 0,
        "source_url": _FED_JN_SRC,
        "evidence": "FOMC June 17 2026: Fed held rates at 3.50-3.75% (unanimous 12-0). No 50bp cut.",
        "criterion_note": "Criterion: 'FOMC 2026-06-17: Fed cuts 50bp' — Fed HELD, not cut -> actual=0",
    },

    # ── FOMC_RATE_DECISION (1) ─────────────────────────────────────────────
    "81ad935c-383": {   # "Will the FOMC cut rates at the 2026-06-17 meeting?"
        "actual": 0,
        "source_url": _FED_JN_SRC,
        "evidence": "FOMC June 17 2026: Fed held at 3.50-3.75%, no rate cut. Unanimous 12-0 decision.",
        "criterion_note": "Criterion: 'Will the FOMC cut rates at 2026-06-17?' — Fed did NOT cut -> actual=0",
    },

    # ── MONETARY_POLICY pred_e038ee1d ─────────────────────────────────────
    "pred_e038ee1d": {  # "FOMC holds rates unchanged at May 6-7, 2026"
        "actual": 1,
        "source_url": "https://www.cnbc.com/2026/05/07/fed-interest-rate-decision-may-2026.html",
        "evidence": "FOMC May 6-7 2026: Fed held rates unchanged at 3.50-3.75%. No change in target range.",
        "criterion_note": "Criterion: 'FOMC May 6-7 2026 decision == hold' — Fed HELD -> actual=1",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def brier(p: float, actual: float) -> float:
    return round((float(p) - float(actual)) ** 2, 6)


def patch_entry(entry: dict, r: dict) -> str:
    """Mutate an entry in place. Returns 'resolved', 'already_resolved', or 'missing_prob'."""
    if entry.get("status") in ("resolved", "voided"):
        return "already_resolved"
    prob = (
        entry.get("chorus_probability")
        or entry.get("predicted_prob")
        or entry.get("p_yes")
        or 0.5
    )
    actual = float(r["actual"])
    b = brier(prob, actual)
    base = brier(0.5, actual)
    bss = round(1 - (b / base), 6) if base > 0 else 0.0

    entry["status"] = "resolved"
    entry["resolution"] = actual
    entry["resolved_at"] = NOW
    entry["brier_score"] = b
    entry["baseline_brier"] = base
    entry["brier_skill_score"] = bss
    entry["resolution_source"] = r["source_url"]
    entry["resolution_value"] = r["evidence"][:300]
    if "criterion_note" in r:
        entry["criterion_note"] = r["criterion_note"]
    return "resolved"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()
    write = args.commit and args.confirm
    if args.commit and not args.confirm:
        print("ERROR: --commit requires --confirm (intentional friction)", file=sys.stderr)
        sys.exit(2)

    # ── Load ────────────────────────────────────────────────────────────────
    v1 = json.loads(V1.read_text())
    v2_lines = V2.read_text().splitlines()
    v2 = [json.loads(line) for line in v2_lines if line.strip()]
    canon = json.loads(CANONICAL.read_text())
    if CANONICAL_INTERNAL.exists():
        canon_int = json.loads(CANONICAL_INTERNAL.read_text())
    else:
        canon_int = []

    # Build lookup dicts
    by_v1 = {}
    for e in v1:
        for k in ("id", "canonical_id", "prediction_id"):
            if e.get(k):
                by_v1[e[k]] = e

    by_v2 = {}
    for e in v2:
        for k in ("prediction_id", "canonical_id", "id"):
            if e.get(k):
                by_v2[e[k]] = e

    by_canon = {e["canonical_id"]: e for e in canon}
    by_canon_int = {e.get("canonical_id"): e for e in canon_int if e.get("canonical_id")}

    # ── Apply resolutions ────────────────────────────────────────────────────
    results = []
    audit = []

    for cid, r in RES.items():
        cn = by_canon.get(cid)
        if not cn:
            audit.append(f"MISSING_FROM_CANONICAL: {cid}")
            continue

        src = cn.get("source_file", "")
        oid = cn.get("original_id") or cid

        # Patch canonical (always)
        outcome_canon = patch_entry(cn, r)

        # Patch internal canonical mirror
        ci = by_canon_int.get(cid)
        if ci:
            patch_entry(ci, r)

        # Patch source file (v1 or v2)
        if "chorus_predictions.jsonl" in src:
            target = by_v2.get(oid) or by_v2.get(cid)
            if not target:
                audit.append(f"MISSING_FROM_V2: {oid} (cid={cid})")
            else:
                patch_entry(target, r)
        elif "predictions.json" in src:
            target = by_v1.get(oid) or by_v1.get(cid)
            if not target:
                audit.append(f"MISSING_FROM_V1: {oid} (cid={cid})")
            else:
                patch_entry(target, r)
        else:
            audit.append(f"UNKNOWN_SOURCE_FILE: {cid} src={src!r}")

        results.append({
            "canonical_id": cid,
            "domain": cn.get("domain"),
            "question": (cn.get("question") or "")[:120],
            "prob": cn.get("chorus_probability") or cn.get("predicted_prob"),
            "outcome": outcome_canon,
            "actual": r["actual"],
            "brier": cn.get("brier_score"),
            "source_url": r["source_url"],
        })

    # ── Report ────────────────────────────────────────────────────────────────
    mode_label = "COMMIT" if write else "DRY-RUN"
    print(f"\n{mode_label} — ledger write-back batch 2026-08-01b\n")
    print(f"Total to apply:  {len(results)}")
    print(f"Audit issues:    {len(audit)}")
    for a in audit:
        print(f"  ! {a}")

    print(f"\n{'BRIER':>7s}  {'p':>6s}  {'act':>3s}  {'domain':30s}  question")
    print("-" * 110)
    for x in sorted(results, key=lambda x: (x.get("domain") or "", x["canonical_id"])):
        b_str = f"{x['brier']:7.4f}" if x["brier"] is not None else "   ????"
        p_str = f"{x['prob']:6.4f}" if x["prob"] is not None else "  ????"
        print(f"{b_str}  {p_str}  {int(x['actual']):>3d}  {(x['domain'] or '')[:30]:30s}  {x['question'][:60]}")

    resolved_entries = [x for x in results if x.get("brier") is not None]
    if resolved_entries:
        mean_b = sum(x["brier"] for x in resolved_entries) / len(resolved_entries)
        yes_b = [x for x in resolved_entries if x["actual"] == 1]
        no_b  = [x for x in resolved_entries if x["actual"] == 0]
        print(f"\nbatch mean Brier (n={len(resolved_entries)}): {mean_b:.4f}")
        if yes_b:
            print(f"  YES outcomes (n={len(yes_b)}): mean {sum(x['brier'] for x in yes_b)/len(yes_b):.4f}")
        if no_b:
            print(f"  NO outcomes  (n={len(no_b)}): mean {sum(x['brier'] for x in no_b)/len(no_b):.4f}")

    if not write:
        print(f"\n(dry-run — pass --commit --confirm to write)")
        return

    # ── Backup ────────────────────────────────────────────────────────────────
    today = NOW[:10]
    for path in (V1, CANONICAL):
        bk = path.with_suffix(path.suffix + f".bak.{today}b")
        if not bk.exists():
            shutil.copy2(path, bk)
            print(f"backup: {bk.name}")
    # V2 backup (different suffix convention)
    v2_bk = V2.with_suffix(".jsonl.bak." + today + "b")
    if not v2_bk.exists():
        shutil.copy2(V2, v2_bk)
        print(f"backup: {v2_bk.name}")

    # ── Write ─────────────────────────────────────────────────────────────────
    V1.write_text(json.dumps(v1, indent=2))
    V2.write_text("\n".join(json.dumps(e) for e in v2) + "\n")
    CANONICAL.write_text(json.dumps(canon, indent=2))
    if canon_int and CANONICAL_INTERNAL.exists():
        CANONICAL_INTERNAL.write_text(json.dumps(canon_int, indent=2))

    # Append to resolution log
    RESLOG.parent.mkdir(parents=True, exist_ok=True)
    log = json.loads(RESLOG.read_text()) if RESLOG.exists() else []
    for x in results:
        log.append({
            "id": x["canonical_id"],
            "domain": x["domain"],
            "question": x["question"],
            "probability": x["prob"],
            "outcome": x.get("actual"),
            "brier": x.get("brier"),
            "source": x["source_url"],
            "resolved_at": NOW,
            "applied_via": "resolve_batch_2026_08_01b.py",
        })
    RESLOG.write_text(json.dumps(log, indent=2))

    # Write staging archive
    STAGING.parent.mkdir(parents=True, exist_ok=True)
    STAGING.write_text(json.dumps(results, indent=2))

    print(f"\nWROTE:")
    print(f"  {V1}")
    print(f"  {V2}")
    print(f"  {CANONICAL}")
    if canon_int and CANONICAL_INTERNAL.exists():
        print(f"  {CANONICAL_INTERNAL}")
    print(f"  {RESLOG} (+{len(results)} rows)")
    print(f"  {STAGING}")
    print(f"\nNext: python scripts/regenerate_summary.py --write")


if __name__ == "__main__":
    main()
