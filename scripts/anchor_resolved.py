#!/usr/bin/env python3
"""anchor_resolved.py — OpenTimestamps anchor for resolved-but-unanchored predictions.

Two purposes:
1. RETROACTIVE: walk the canonical ledger, find resolved predictions without
   ots_anchored=True, write each to a content-stable JSON file, OTS-stamp it,
   and update the canonical's ots_anchored / ots_anchor fields.

   Retroactive anchoring is **chain-of-custody proof from this date forward**
   (i.e. "we did not edit this prediction record after this Bitcoin block"),
   NOT pre-registration proof. The methodology doc must reflect that distinction.

2. LOCK-TIME (when invoked with --lock-mode + --prediction-id): anchor a single
   prediction at the moment of lock. Intended to be called by the prediction
   creation pipeline (e.g. chorus_forecast.lock_prediction) on every new
   prediction so the ots_anchored flag is true at lock time, before resolution.

Usage:
    # Retroactive sweep
    python anchor_resolved.py --canonical ledger_canonical.json --out-dir ots_anchors/

    # Lock-time anchor
    python anchor_resolved.py --lock-mode --prediction-id pred_xyz123 \\
        --canonical ledger_canonical.json --out-dir ots_anchors/

After running: `ots upgrade ots_anchors/*.ots` once the OTS calendars publish
to a Bitcoin block (typically 1-3 hours later) to finalize the proofs.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def is_resolved_unanchored(pred: dict) -> bool:
    return (
        pred.get("status") == "resolved"
        and pred.get("brier_score") is not None
        and not pred.get("ots_anchored")
    )


def write_prediction_record(pred: dict, out_dir: Path) -> Path:
    """Write a stable JSON record for a single prediction.

    The record contains the fields that make the prediction's claim auditable
    after the fact: id, hash, prediction probability, locked_at, resolution
    criterion, resolved value, computed Brier. Stable key order so the SHA
    is deterministic across runs.
    """
    keep = [
        "canonical_id", "original_sha", "domain", "question",
        "resolution_criterion", "chorus_probability", "baseline_probability",
        "locked_at", "resolution", "resolution_date", "resolved_at",
        "brier_score", "in_headline", "temporal_class",
    ]
    record = {k: pred.get(k) for k in keep}
    cid = pred["canonical_id"]
    path = out_dir / f"{cid}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True))
    return path


def ots_stamp(file_path: Path) -> Path:
    """Run `ots stamp` on a file. Returns path to the .ots proof."""
    result = subprocess.run(
        ["ots", "stamp", str(file_path)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ots stamp failed: {result.stderr}")
    proof = file_path.with_suffix(file_path.suffix + ".ots")
    if not proof.exists():
        raise RuntimeError(f"ots stamp did not produce {proof}")
    return proof


def anchor_predictions(canonical_path: Path, out_dir: Path,
                       only_id: str | None = None) -> dict:
    """Anchor predictions and update the canonical's ots flags in place.

    If only_id is set, anchor that one prediction (lock-time mode); otherwise
    anchor every resolved-but-unanchored prediction (retroactive sweep).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger = json.loads(canonical_path.read_text())

    targets = []
    for p in ledger:
        if only_id is not None:
            if p.get("canonical_id") == only_id:
                targets.append(p)
        elif is_resolved_unanchored(p):
            targets.append(p)

    print(f"anchoring {len(targets)} predictions to {out_dir}/")
    anchored, errors = [], []
    for p in targets:
        cid = p["canonical_id"]
        try:
            record = write_prediction_record(p, out_dir)
            proof = ots_stamp(record)
            # Path relative to canonical for portability
            rel_proof = proof.relative_to(canonical_path.parent)
            p["ots_anchored"] = True
            p["ots_anchor"] = str(rel_proof)
            anchored.append(cid)
            print(f"  ✓ {cid} -> {rel_proof}")
        except Exception as e:
            errors.append({"canonical_id": cid, "error": str(e)})
            print(f"  ✗ {cid} -> {e}", file=sys.stderr)

    if anchored:
        canonical_path.write_text(json.dumps(ledger, indent=2))
        print(f"updated {canonical_path} with ots_anchored=True for {len(anchored)} records")

    return {"anchored": anchored, "errors": errors}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--lock-mode", action="store_true",
                    help="single-prediction anchor at lock time (requires --prediction-id)")
    ap.add_argument("--prediction-id", default=None)
    args = ap.parse_args()

    if args.lock_mode and not args.prediction_id:
        ap.error("--lock-mode requires --prediction-id")

    result = anchor_predictions(
        args.canonical, args.out_dir,
        only_id=args.prediction_id if args.lock_mode else None,
    )
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
