#!/usr/bin/env python3
"""regenerate_summary.py — Regenerate ledger_summary.json from ledger_canonical.json.

Reads the public-facing ledger_canonical.json and produces a fresh
ledger_summary.json using the same schema as the existing file.

Methodology: forward, single-prediction, deduplicated, in-headline-domain
entries are the headline figure. All other resolved forward singles are
reported in the full-transparency section.

Usage:
    python scripts/regenerate_summary.py                # dry-run (print only)
    python scripts/regenerate_summary.py --write        # write ledger_summary.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CANONICAL = REPO / "ledger_canonical.json"
SUMMARY = REPO / "ledger_summary.json"

NOW = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"

# These HEADLINE_DOMAIN_MAP + HEADLINE_DOMAINS mirror the consolidate script's definitions
HEADLINE_DOMAIN_MAP = {
    "earnings_sector_rate": "corporate_earnings",
    "earnings_largecap":    "corporate_earnings",
    "labor_claims":         "macro_indicators",
    "jobless_claims":       "macro_indicators",
    "ism_scan":             "macro_indicators",
    "eia_natgas":           "macro_indicators",
    "global_latam":         "latin_america",
    "latam_scan":           "latin_america",
}

HEADLINE_DOMAINS = {
    "corporate_earnings",
    "macro_indicators",
    "international_political",
    "latin_america",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="Write ledger_summary.json (default: dry-run)")
    args = ap.parse_args()

    ledger = json.loads(CANONICAL.read_text())
    print(f"canonical: {CANONICAL} ({len(ledger)} entries)")

    # Partition
    resolved    = [e for e in ledger if e.get("status") == "resolved"]
    voided      = [e for e in ledger if e.get("status") == "voided"]
    open_       = [e for e in ledger if e.get("status") == "open"]
    pre_reg     = [e for e in ledger if e.get("status") == "pre_registered"]

    # Forward, single-prediction, deduplicated (no duplicate_of flag)
    def is_duplicate(e: dict) -> bool:
        return any(f.startswith("duplicate_of:") for f in e.get("audit_flags", []))

    def is_fwd(e: dict) -> bool:
        return e.get("temporal_class") == "FWD"

    def is_bwd(e: dict) -> bool:
        tc = e.get("temporal_class", "")
        return tc in ("BWD", "AGG")

    def has_brier(e: dict) -> bool:
        return e.get("brier_score") is not None

    def is_overdue(e: dict) -> bool:
        return "resolution_overdue" in e.get("audit_flags", [])

    forward_singles = [
        e for e in resolved
        if is_fwd(e) and not is_duplicate(e) and not is_bwd(e) and has_brier(e)
    ]
    backward_validation = [
        e for e in resolved
        if is_bwd(e) and not is_duplicate(e)
    ]
    backward_logged = [
        e for e in resolved
        if is_bwd(e) and is_duplicate(e)
    ]
    duplicates = [e for e in ledger if is_duplicate(e)]
    overdue = [e for e in open_ if is_overdue(e)]

    # Headline: forward singles in headline domains, in_headline=True
    headline_entries = [e for e in forward_singles if e.get("in_headline")]
    headline_briers = [e["brier_score"] for e in headline_entries]
    headline_n = len(headline_briers)
    headline_mean = round(sum(headline_briers) / headline_n, 4) if headline_briers else None

    # Headline by domain (group by headline_domain)
    by_headline_domain: dict[str, list[dict]] = defaultdict(list)
    for e in headline_entries:
        hd = e.get("headline_domain") or HEADLINE_DOMAIN_MAP.get(e.get("domain", ""), e.get("domain", "unknown"))
        by_headline_domain[hd].append(e)

    headline_domain_summary = {}
    for hd, entries in sorted(by_headline_domain.items()):
        bs = [e["brier_score"] for e in entries]
        headline_domain_summary[hd] = {
            "n": len(bs),
            "mean_brier": round(sum(bs) / len(bs), 4),
            "best": round(min(bs), 4),
            "worst": round(max(bs), 4),
            "predictions": [
                {
                    "q": e.get("question", "")[:80],
                    "p": e.get("chorus_probability"),
                    "actual": e.get("resolution"),
                    "brier": e.get("brier_score"),
                }
                for e in sorted(entries, key=lambda x: -(x.get("chorus_probability") or 0))
            ],
        }

    # All forward brier
    brier_scores = [e["brier_score"] for e in forward_singles]
    all_fwd_mean = round(sum(brier_scores) / len(brier_scores), 4) if brier_scores else None

    # By domain
    by_domain: dict[str, list[float]] = defaultdict(list)
    for e in forward_singles:
        by_domain[e.get("domain", "unknown")].append(e["brier_score"])

    domain_means = {
        d: {
            "n": len(s),
            "mean_brier": round(sum(s) / len(s), 4),
            "best": round(min(s), 4),
            "worst": round(max(s), 4),
            "in_headline": HEADLINE_DOMAIN_MAP.get(d, d) in HEADLINE_DOMAINS,
        }
        for d, s in sorted(by_domain.items(), key=lambda kv: -len(kv[1]))
    }

    # By year
    by_year: dict[str, list[float]] = defaultdict(list)
    for e in forward_singles:
        year = (e.get("resolved_at") or "")[:4]
        if year:
            by_year[year].append(e["brier_score"])
    year_means = {
        y: {"n": len(s), "mean_brier": round(sum(s) / len(s), 4)}
        for y, s in sorted(by_year.items())
    }

    # Audit flag counts
    flag_counts = Counter(
        f for e in ledger for f in e.get("audit_flags", [])
    ).most_common(20)

    summary = {
        "generated_at": NOW,
        "totals": {
            "total_entries": len(ledger),
            "resolved": len(resolved),
            "forward_singles": len(forward_singles),
            "backward_validation": len(backward_validation),
            "backward_logged": len(backward_logged),
            "open": len(open_),
            "overdue": len(overdue),
            "duplicates_tagged": len(duplicates),
            "voided": len(voided),
            "pre_registered": len(pre_reg),
            "ots_anchored": sum(1 for e in ledger if e.get("ots_anchored")),
        },
        "headline_brier_FORWARD_ONLY": {
            "scope": "Forward, single-prediction, deduplicated, in-headline-domain only. Excludes pastcasting/cross-validation/aggregate batch claims and weak/exploratory domains.",
            "n": headline_n,
            "mean_brier": headline_mean,
            "best": round(min(headline_briers), 4) if headline_briers else None,
            "worst": round(max(headline_briers), 4) if headline_briers else None,
            "interpretation": "Lower=better. 0.05-0.10 = superforecaster tier; 538 elections ~0.05-0.07; coin-flip = 0.25.",
        },
        "headline_by_domain": headline_domain_summary,
        "all_forward_brier": {
            "scope": "All forward, single, deduplicated predictions across all domains (full transparency).",
            "n": len(brier_scores),
            "mean_brier": all_fwd_mean,
            "best": round(min(brier_scores), 4) if brier_scores else None,
            "worst": round(max(brier_scores), 4) if brier_scores else None,
        },
        "backward_validation": {
            "scope": "Pastcasting / cross-validation / aggregate batch claims. NOT forward predictions. Methodology evidence only.",
            "entries": [
                {
                    "question": e.get("question"),
                    "domain": e.get("domain"),
                    "n_underlying": (e.get("model_inputs") or {}).get("n_personas") if isinstance(e.get("model_inputs"), dict) else None,
                    "brier": e.get("brier_score"),
                    "notes": e.get("resolution_source"),
                }
                for e in backward_validation
            ],
        },
        "by_domain_FORWARD_ONLY": domain_means,
        "by_year_FORWARD_ONLY": year_means,
        "audit_flag_counts": flag_counts,
    }

    # Print summary
    hb = summary["headline_brier_FORWARD_ONLY"]
    t = summary["totals"]
    print(f"\nLEDGER SUMMARY — {NOW}")
    print(f"Total entries: {t['total_entries']}  |  Resolved: {t['resolved']}  |  Open: {t['open']}  |  Voided: {t['voided']}")
    print(f"Forward singles: {t['forward_singles']}  |  Overdue: {t['overdue']}")
    print()
    print("HEADLINE (forward, deduplicated, in-headline-domain):")
    print(f"  n={hb['n']}, mean Brier={hb['mean_brier']}, best={hb['best']}, worst={hb['worst']}")
    print()
    afb = summary["all_forward_brier"]
    print(f"ALL FORWARD (transparency): n={afb['n']}, mean Brier={afb['mean_brier']}")
    print()
    print("BY DOMAIN (forward only):")
    for d, s in domain_means.items():
        hl = " [headline]" if s["in_headline"] else ""
        print(f"  {d:35s} n={s['n']:3d}  mean={s['mean_brier']:.4f}{hl}")

    if args.write:
        SUMMARY.write_text(json.dumps(summary, indent=2))
        print(f"\nWROTE {SUMMARY} ({SUMMARY.stat().st_size/1024:.1f} KB)")
    else:
        print("\n(dry-run — pass --write to commit ledger_summary.json)")


if __name__ == "__main__":
    main()
