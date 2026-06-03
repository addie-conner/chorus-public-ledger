#!/usr/bin/env python3
"""resolve_political_2026_06_03.py — One-shot political resolution batch.

Resolves 13 predictions against authoritative web sources and VOIDS 13 that
referenced events or candidates that did not exist (authoring-time hallucination).

Touches three artifact files:
  - ~/chorus/static/public_ledger/predictions.json   (24 of 26 entries live here)
  - ~/chorus/chorus_predictions.jsonl                (2 of 26 entries live here)
  - ~/chorus-public-ledger/ledger_canonical.json     (downstream canonical view)

Plus appends to:
  - ~/chorus/data/calibration/resolution_log.json    (audit log)
  - ~/chorus/data/resolutions_to_apply/political_2026_06_03.json (staging archive)

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
STAGING = CHORUS / "data" / "resolutions_to_apply" / "political_2026_06_03.json"

# ---- Resolution map ---------------------------------------------------------
# Each entry: canonical_id -> {kind: "resolved"|"voided", ...}
# Resolved entries need actual (0 or 1) + source_url + evidence.
# Voided entries need void_reason + source_url + evidence.

RES = {
    # ---------- IOWA GOP GUBERNATORIAL PRIMARY (June 2 2026) ----------
    # Final results (>95% reporting):
    #   Lahn 37.65% (80,765), Feenstra 36.88% (79,113), Steen 14.49% (31,087),
    #   Sherman 7.03% (15,076), Andrews 3.59% (7,694)
    # Lahn cleared Iowa's 35% statutory threshold → outright nomination (no convention).
    "8f65e4b7ef4a": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://en.wikipedia.org/wiki/2026_Iowa_gubernatorial_election",
        "evidence": "Steen 14.49% (31,087/214,529) — below 25% threshold",
    },
    "0d5a943a6d53": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_Iowa_gubernatorial_election",
        "evidence": "Lahn 37.65% > Feenstra 36.88% (0.77pp margin)",
    },
    "179293d5fa15": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_Iowa_gubernatorial_election",
        "evidence": "Andrews 3.59% (7,694) — well below 10% threshold",
    },
    "18208151a09d": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://en.wikipedia.org/wiki/2026_Iowa_gubernatorial_election",
        "evidence": "Lahn won; Steen finished 3rd at 14.49%",
    },
    "27f7226e8fbb": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://en.wikipedia.org/wiki/2026_Iowa_gubernatorial_election",
        "evidence": "Lahn won; Steen finished 3rd at 14.49%",
    },
    "57b108750ae7": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_Iowa_gubernatorial_election",
        "evidence": "Lahn 37.65% cleared Iowa 35% statutory threshold → outright nomination at ballot (no convention required)",
        "criterion_note": "'Outright' interpreted as Iowa-law definition: cleared 35% threshold avoiding state convention nomination.",
    },

    # ---------- OTHER PRIMARIES & ELECTIONS ----------
    "552161305fa7": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://ballotpedia.org/United_States_Senate_election_in_Georgia,_2026",
        "evidence": "Ossoff ran unopposed in GA D primary, secured nomination",
    },
    "fa89356cca80": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.texastribune.org/2026/05/26/texas-john-cornyn-ken-paxton-us-senate-republican-primary-runoff/",
        "evidence": "Paxton 63.8% defeated Cornyn in 5/26 runoff (Trump endorsement week before); first incumbent TX Senator beaten in primary since 1970",
    },
    "f676c9884722": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.texastribune.org/2026/03/03/texas-greg-abbott-governor-republican-primary-lt-gov-dan-patrick/",
        "evidence": "Abbott (R) won 3/3 primary outright with >80% (~1.5M votes); no May runoff for governor",
        "criterion_note": "Resolution_date was 5/26 (runoff date), but Abbott cleared 50% on 3/3 so no runoff was held. R won the primary.",
    },

    # ---------- GEOPOLITICAL SCAN (May 2026) ----------
    "80dfea9551cb": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.aei.org/articles/china-taiwan-update-may-8-2026/",
        "evidence": "Only routine PLA joint combat readiness patrols May 1/6/19/25; no escalation incident",
    },
    "a8121ee2c82a": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://news.usni.org/2026/05/27/north-korea-tests-new-lightweight-launch-system-and-tactical-cruise-missiles",
        "evidence": "5/26: Hwasong-11D tactical ballistic + multi-purpose cruise missile launches from Jeongju toward Yellow Sea",
    },
    "f08bbccaa3fb": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://en.wikipedia.org/wiki/2026_Iran_war",
        "evidence": "US/Iran/Israel ceasefire 4/7-8 held through May; Operation Epic Fury concluded 5/5 with no major new escalation in May",
    },

    # ---------- VOIDED — event_did_not_occur ----------
    "eac12d8c44eb": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://ballotpedia.org/Texas%27_32nd_Congressional_District_election,_2026",
        "evidence": "No TX-32 special election. March 3 primary: Yarbrough won R nom outright after Binkley dropped 3/17; general 11/3",
    },
    "ee1420a06e60": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://mexiconewsdaily.com/news/preliminary-results-give-morena-at-least-10-of-15-seats-for-governor/",
        "evidence": "6/1/2026 was Mexican judicial elections (881 federal + 1,649 local positions); federal Chamber midterms in 2027",
    },
    "916cff5ff507": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://en.wikipedia.org/wiki/2025_New_Jersey_gubernatorial_election",
        "evidence": "NJ gov race was 2025 (Sherrill won general 11/2025); no 2026 NJ gov primary",
    },
    "f187be69c78e": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "evidence": "No 5/7 FOMC meeting; actual meeting was 4/28-29 (held 8-4)",
    },
    "cf1cbc389177": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "evidence": "No 5/7 FOMC meeting",
    },
    "28a123d3-ac5": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "evidence": "No 5/6 FOMC meeting",
    },
    "pred_583f357d": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "evidence": "No 5/6-7 FOMC meeting; 4/28-29 was actual",
    },
    "pred_e038ee1d": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "evidence": "No 5/6-7 FOMC meeting (this entry supersedes pred_583f357d but references same nonexistent meeting)",
    },
    "d8dcdc0b0894": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://ballotpedia.org/Ohio%27s_9th_Congressional_District_election,_2026",
        "evidence": "5/5/2026 was Ohio D primary (Kaptur incumbent seeking 23rd term), not a special election; general 11/3",
    },
    "9f37c1e5fcb7": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://mexiconewsdaily.com/mexico-elections-2024/mexico-governors-elections-puebla-tabasco-veracruz-yucatan/",
        "evidence": "Puebla gov race was 2024 (Armenta/Morena won 59%); no 2026 Puebla gubernatorial",
    },
    "0c37071d16d6": {
        "kind": "voided", "void_reason": "event_did_not_occur",
        "source_url": "https://mexiconewsdaily.com/mexico-elections-2024/mexico-election-results-morena-gubernatorial-races/",
        "evidence": "Referenced 9 gov races were 2024 cycle; 6/1/2026 in Mexico was judicial elections only",
    },

    # ---------- VOIDED — candidate_not_on_ballot ----------
    "e7584f1d0bad": {
        "kind": "voided", "void_reason": "candidate_not_on_ballot",
        "source_url": "https://ballotpedia.org/Texas_lieutenant_gubernatorial_election,_2026",
        "evidence": "Dan Patrick is Lt Gov incumbent; ran for Lt Gov re-election (won 3/3 primary), not governor",
    },
    "780092f99161": {
        "kind": "voided", "void_reason": "candidate_not_on_ballot",
        "source_url": "https://en.wikipedia.org/wiki/2026_California_gubernatorial_election",
        "evidence": "Karen Bass (LA Mayor) was not a candidate for CA governor; top-2 advancing are Becerra (D) and Hilton (R)",
    },

    # ---------- VOIDED — candidate_unspecified ----------
    "13d150791673": {
        "kind": "voided", "void_reason": "candidate_unspecified",
        "source_url": "https://en.wikipedia.org/wiki/2026_United_States_Senate_election_in_Iowa",
        "evidence": "Prediction said 'TBD wins' with no named candidate; Hinson won R primary 6/2 (open seat after Ernst retirement)",
    },
}


def brier(p, actual):
    return round((float(p) - float(actual)) ** 2, 6)


def patch_v1(p, r, kind_now):
    """Mutate a v1 (predictions.json) entry in place. Returns 'resolved'|'voided'|'skip'."""
    if p.get("status") in ("resolved", "voided"):
        return "skip"
    if r["kind"] == "resolved":
        prob = float(p.get("chorus_probability") or p.get("p_yes") or 0.5)
        actual = float(r["actual"])
        b = brier(prob, actual)
        base = brier(0.5, actual)
        bss = round(1 - (b / base), 6) if base > 0 else 0.0
        p["status"] = "resolved"
        p["resolution"] = actual
        p["resolved_at"] = NOW
        p["brier_score"] = b
        p["baseline_brier"] = base
        p["brier_skill_score"] = bss
        p["resolution_source"] = r["source_url"]
        p["resolution_value"] = r["evidence"][:200]
        if "criterion_note" in r:
            p["criterion_note"] = r["criterion_note"]
        return "resolved"
    else:
        p["status"] = "voided"
        p["voided_at"] = NOW
        p["void_reason"] = r["void_reason"]
        p["void_source"] = r["source_url"]
        p["void_evidence"] = r["evidence"][:200]
        return "voided"


def patch_v2(p, r):
    """Mutate a v2 (chorus_predictions.jsonl) entry in place. v2 has different key names."""
    if p.get("status") in ("resolved", "voided"):
        return "skip"
    if r["kind"] == "resolved":
        prob = float(p.get("predicted_prob") or p.get("chorus_probability") or 0.5)
        actual = float(r["actual"])
        b = brier(prob, actual)
        base = brier(0.5, actual)
        p["status"] = "resolved"
        p["resolution"] = actual
        p["resolved_at"] = NOW
        p["brier_score"] = b
        p["baseline_brier"] = base
        p["resolution_source"] = r["source_url"]
        p["resolution_value"] = r["evidence"][:200]
        return "resolved"
    else:
        p["status"] = "voided"
        p["voided_at"] = NOW
        p["void_reason"] = r["void_reason"]
        p["void_source"] = r["source_url"]
        p["void_evidence"] = r["evidence"][:200]
        return "voided"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()
    write = args.commit and args.confirm
    if args.commit and not args.confirm:
        print("ERROR: --commit requires --confirm (intentional friction)", file=sys.stderr)
        sys.exit(2)

    # Load all four
    v1 = json.loads(V1.read_text())
    v2_lines = V2.read_text().splitlines()
    v2 = [json.loads(l) for l in v2_lines if l.strip()]
    canon = json.loads(CANONICAL.read_text())
    canon_int = json.loads(CANONICAL_INTERNAL.read_text())

    by_v1 = {e.get("id") or e.get("canonical_id"): e for e in v1}
    by_v2 = {e.get("prediction_id"): e for e in v2}
    by_canon = {e["canonical_id"]: e for e in canon}
    by_canon_int = {e.get("canonical_id"): e for e in canon_int if e.get("canonical_id")}

    # Drive everything from the canonical map (it has authoritative IDs + original_id).
    results = []
    audit = []
    for cid, r in RES.items():
        cn = by_canon.get(cid)
        if not cn:
            audit.append(f"MISSING_FROM_CANONICAL: {cid}")
            continue
        src = cn.get("source_file", "?")
        oid = cn.get("original_id") or cid

        if src.endswith("chorus_predictions.jsonl"):
            target = by_v2.get(oid)
            if not target:
                audit.append(f"MISSING_FROM_V2: {oid}")
                continue
            outcome = patch_v2(target, r)
            patch_v2(cn, r)  # mirror to public canonical
            ci = by_canon_int.get(cid)
            if ci: patch_v2(ci, r)  # mirror to internal canonical
        elif src.endswith("predictions.json"):
            target = by_v1.get(oid) or by_v1.get(cid)
            if not target:
                audit.append(f"MISSING_FROM_V1: {oid}")
                continue
            outcome = patch_v1(target, r, r["kind"])
            patch_v1(cn, r, r["kind"])  # mirror to public canonical
            ci = by_canon_int.get(cid)
            if ci: patch_v1(ci, r, r["kind"])  # mirror to internal canonical
        else:
            audit.append(f"UNKNOWN_SOURCE: {cid} src={src}")
            continue

        results.append({
            "canonical_id": cid,
            "domain": cn.get("domain"),
            "question": (cn.get("question") or "")[:120],
            "prob": cn.get("chorus_probability"),
            "outcome": outcome,
            "kind": r["kind"],
            "actual": r.get("actual"),
            "void_reason": r.get("void_reason"),
            "brier": cn.get("brier_score") if r["kind"] == "resolved" else None,
            "source_url": r["source_url"],
        })

    # ---- Print plan ----
    resolved = [x for x in results if x["kind"] == "resolved"]
    voided = [x for x in results if x["kind"] == "voided"]
    print(f"\n{'COMMIT' if write else 'DRY-RUN'} — political resolution batch 2026-06-03\n")
    print(f"Total to apply: {len(results)} (resolved={len(resolved)} voided={len(voided)})")
    print(f"Audit issues:   {len(audit)}")
    for a in audit:
        print(f"  ! {a}")

    print(f"\n=== RESOLVED ({len(resolved)}) ===")
    print(f"{'BRIER':>7s}  {'p':>5s}  {'act':>3s}  domain                            question")
    for x in resolved:
        print(f"{x['brier']:7.4f}  {x['prob']:5.2f}  {int(x['actual']):>3d}  {(x['domain'] or '')[:32]:32s}  {x['question'][:80]}")
    if resolved:
        mean_b = sum(x["brier"] for x in resolved) / len(resolved)
        hc = [x for x in resolved if abs(x["prob"] - 0.5) > 0.2]
        hc_b = (sum(x["brier"] for x in hc) / len(hc)) if hc else 0
        print(f"\nbatch mean Brier (n={len(resolved)}): {mean_b:.4f}")
        if hc:
            print(f"HC subset (|p-.5|>.2, n={len(hc)}): {hc_b:.4f}")

    print(f"\n=== VOIDED ({len(voided)}) ===")
    for x in voided:
        print(f"  [{x['void_reason']:30s}]  p={x['prob']:.2f}  {x['question'][:80]}")

    if not write:
        print(f"\n(dry-run — pass --commit --confirm to write)")
        return

    # ---- Backup + write ----
    for path in (V1, V2, CANONICAL, CANONICAL_INTERNAL):
        bk = path.with_suffix(path.suffix + f".bak.{NOW[:10]}")
        if not bk.exists():
            shutil.copy2(path, bk)
            print(f"backup: {bk.name}")

    V1.write_text(json.dumps(v1, indent=2))
    V2.write_text("\n".join(json.dumps(e) for e in v2) + "\n")
    CANONICAL.write_text(json.dumps(canon, indent=2))
    CANONICAL_INTERNAL.write_text(json.dumps(canon_int, indent=2))

    # Append to audit log
    RESLOG.parent.mkdir(parents=True, exist_ok=True)
    log = json.loads(RESLOG.read_text()) if RESLOG.exists() else []
    for x in results:
        log.append({
            "id": x["canonical_id"],
            "domain": x["domain"],
            "question": x["question"],
            "probability": x["prob"],
            "outcome": x.get("actual"),
            "void_reason": x.get("void_reason"),
            "brier": x.get("brier"),
            "source": x["source_url"],
            "resolved_at": NOW,
            "applied_via": "resolve_political_2026_06_03.py",
        })
    RESLOG.write_text(json.dumps(log, indent=2))

    # Archive staging file
    STAGING.parent.mkdir(parents=True, exist_ok=True)
    STAGING.write_text(json.dumps(results, indent=2))

    print(f"\nWROTE:")
    print(f"  {V1} ({len(v1)} entries)")
    print(f"  {V2} ({len(v2)} entries)")
    print(f"  {CANONICAL} ({len(canon)} entries)")
    print(f"  {RESLOG} (+{len(results)} log rows)")
    print(f"  {STAGING} (staging archive)")
    print(f"\nNext: python3 ~/chorus/scripts/render_political_dashboard.py")


if __name__ == "__main__":
    main()
