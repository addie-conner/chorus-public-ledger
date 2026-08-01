#!/usr/bin/env python3
"""audit_ledger.py — read-only audit of the canonical ledger.

Surfaces two ledger-hygiene gaps:

1. OVERDUE & UNRESOLVED: status == "open" but resolution_date has passed.
   These need a resolution outcome appended (or status moved to "void" if
   the underlying market/data feed never resolved).

2. EMPTY MODEL_INPUTS on OPEN entries: status == "open" and model_inputs
   is {}. These are publish-readiness gaps — the prediction has no
   attributed signal stack, so it cannot be cited under the RA-validated
   banner. Either backfill model_inputs from the originating run, or
   delete / mark provisional.

Read-only. Prints reports to stdout. Does NOT mutate the ledger.
The companion mutation step lives in anchor_resolved.py and a future
resolve_overdue.py (intentionally separate so concurrent Claude sessions
on this repo do not race on writes).

Usage:
    python scripts/audit_ledger.py
    python scripts/audit_ledger.py --canonical ledger_canonical.json
    python scripts/audit_ledger.py --high-conviction-only
    python scripts/audit_ledger.py --domain conservation_deforestation
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

CONVICTION_PUBLISH_GATE = 0.20  # |p - 0.5| > 0.20 per feedback_conviction_filter_publish_gate


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def conviction(pred: dict) -> float | None:
    p = pred.get("chorus_probability")
    if p is None:
        return None
    return abs(p - 0.5)


def is_open(pred: dict) -> bool:
    return pred.get("status") == "open"


def days_overdue(pred: dict, now: datetime) -> int | None:
    rd = parse_iso(pred.get("resolution_date"))
    if rd is None:
        return None
    if rd.tzinfo is None:
        rd = rd.replace(tzinfo=timezone.utc)
    delta = (now - rd).days
    return delta if delta > 0 else None


def has_empty_stack(pred: dict) -> bool:
    return not pred.get("model_inputs") and not pred.get("data_sources_used")


def s(v) -> str:
    return "" if v is None else str(v)


def fmt_row(cols: list[str], widths: list[int]) -> str:
    return "  ".join(s(c).ljust(w)[:w] for c, w in zip(cols, widths))


def is_scaffold(pred: dict) -> bool:
    """Backtest/scaffold rows ingested without a locked probability — exclude
    from the actionable overdue list, count separately."""
    return pred.get("chorus_probability") is None


def report_overdue(preds: list[dict], now: datetime) -> None:
    rows, scaffold = [], 0
    for p in preds:
        if not is_open(p):
            continue
        d = days_overdue(p, now)
        if d is None:
            continue
        if is_scaffold(p):
            scaffold += 1
            continue
        rows.append((d, p))
    rows.sort(key=lambda x: -x[0])

    print(f"\n=== OVERDUE & UNRESOLVED — locked predictions ({len(rows)}) ===")
    print(f"    (also: {scaffold} scaffold/stub rows with null probability, not shown)")
    if not rows:
        print("  (none)")
        return
    widths = [14, 24, 12, 6, 60]
    print(fmt_row(["canonical_id", "domain", "resolves", "days", "question"], widths))
    print("-" * sum(widths))
    for d, p in rows:
        print(fmt_row([
            s(p.get("canonical_id"))[:14],
            s(p.get("domain"))[:24],
            s(p.get("resolution_date"))[:10],
            str(d),
            s(p.get("question"))[:60],
        ], widths))


def report_empty_stack(preds: list[dict], high_conv_only: bool) -> None:
    rows = []
    for p in preds:
        if not is_open(p) or is_scaffold(p):
            continue
        if not has_empty_stack(p):
            continue
        c = conviction(p)
        if high_conv_only and (c is None or c <= CONVICTION_PUBLISH_GATE):
            continue
        rows.append((c if c is not None else -1, p))
    rows.sort(key=lambda x: -x[0])

    label = "EMPTY MODEL_INPUTS — OPEN"
    if high_conv_only:
        label += f" — conviction>{CONVICTION_PUBLISH_GATE}"
    print(f"\n=== {label} ({len(rows)}) ===")
    if not rows:
        print("  (none)")
        return
    widths = [14, 24, 6, 6, 60]
    print(fmt_row(["canonical_id", "domain", "p", "|conv|", "question"], widths))
    print("-" * sum(widths))
    for c, p in rows:
        prob = p.get("chorus_probability")
        print(fmt_row([
            s(p.get("canonical_id"))[:14],
            s(p.get("domain"))[:24],
            f"{prob:.2f}" if prob is not None else "-",
            f"{c:.2f}" if c >= 0 else "-",
            s(p.get("question"))[:60],
        ], widths))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canonical", type=Path,
                    default=Path(__file__).resolve().parent.parent / "ledger_canonical.json")
    ap.add_argument("--high-conviction-only", action="store_true",
                    help="empty-stack report: only entries with |p-0.5| > 0.20 (publish-gate)")
    ap.add_argument("--domain", type=str, default=None,
                    help="restrict both reports to a single domain")
    args = ap.parse_args()

    preds = json.loads(args.canonical.read_text())
    if args.domain:
        preds = [p for p in preds if p.get("domain") == args.domain]

    now = datetime.now(timezone.utc)
    n_total = len(preds)
    n_open = sum(1 for p in preds if is_open(p))
    print(f"ledger: {args.canonical}")
    print(f"as of:  {now.isoformat(timespec='seconds')}")
    print(f"scope:  {n_total} entries, {n_open} open" + (f" [domain={args.domain}]" if args.domain else ""))

    report_overdue(preds, now)
    report_empty_stack(preds, args.high_conviction_only)


if __name__ == "__main__":
    main()
