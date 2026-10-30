#!/usr/bin/env python3
"""Sports forward record, as of 2026-10-31. Read-only. Same method as sports_forward_record_2026_10_15.py; changes: TODAY, resolution_date_corrected is used where present (sealed criterion date; the hashed resolution_date is kept), and PERSIST covers the 2026 Forbes NBA rows resolved 2026-10-30. 2026-10-31 copy: only TODAY changed.

Sports scope: resolved rows in ledger_canonical.json whose domain is sports, plus the
demo-arc and 2026 NBA draft staging files. Forward only: temporal_class == FWD, no
duplicate_of flag, resolution_date already passed, lock date before the outcome.

Baselines (stated per subset):
  attention   constant forecaster at the subset's realized hit rate (in-sample; generous
              to the baseline) -> Brier = r(1-r)
  forbes      last-year persistence: same confidence level as the Chorus call, direction
              taken from the prior-year Forbes list; 0.5 where no prior-year list was checked
  outcomes    pre-lock market price where the ledger stores one (baseline_probability);
              otherwise in-sample base rate
  media       in-sample base rate
  calendar    reported separately; near-certain schedule checks, excluded from pooled skill
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TODAY = "2026-10-31"

ATT_IDS = {"pred_e78785dc", "pred_0f65936b", "pred_4969ec96"}
MEDIA_IDS = {"pred_d4efe957", "pred_7d8d18b2", "pred_d30afe71", "pred_12332624", "pred_2ed61a40",
             "pred_bbcb580a", "pred_42cca4f1", "pred_d837d5f2", "pred_e91d9ef2", "pred_c545859d"}
CAL_IDS = {"pred_nfl_2026_season_kickoff_september", "pred_mlb_2026_all_star_game_july",
           "pred_us_open_tennis_2026_starts_aug", "pred_wimbledon_2026_singles_finals_july",
           "pred_tour_de_france_2026_starts_july", "pred_open_championship_golf_2026_july",
           "pred_nba_summer_league_2026_held", "pred_wc_2026_final_played_on_2026_07_19"}
# prior-year direction for persistence (1 = was true on the prior-year Forbes list)
PERSIST = {
    # Forbes NFL 2025 list (forbesapi nfl-valuations/2025): top 5 Cowboys, Rams, Giants, Patriots, 49ers
    "pred_dallas_cowboys_finishes_in_top_5_of_nfl__4c7062ef": 1, "pred_los_angeles_rams_finishes_in_top_5_of_nf_9b49cf25": 1,
    "pred_new_york_giants_finishes_in_top_5_of_nfl_ff2ae647": 1, "pred_new_england_patriots_finishes_in_top_5_o_75ddbeb3": 1,
    "pred_san_francisco_49ers_finishes_in_top_5_of_3ac98ed3": 1, "pred_philadelphia_eagles_finishes_in_top_5_of_75a353c7": 0,
    "pred_chicago_bears_finishes_in_top_5_of_nfl_b_f190a0ee": 0, "pred_new_york_jets_finishes_in_top_5_of_nfl_b_9d3cec67": 0,
    "pred_1bd02c9d": 1,          # Cowboys #1 in 2025
    "pred_5f44f5eb": 1,          # Forbes soccer 2025: Real Madrid #1 $6.75B > Man Utd #2 $6.6B
    "pred_aa330d75": 1,          # Ronaldo #1 in 2025 ("fourth year in a row" in the 2026 article)
    # Forbes NBA 2025 list (forbesapi nba-valuations/2025, dated 2025-10-23): top 5 Warriors, Lakers, Knicks, Clippers, Celtics;
    # Bulls #6, Rockets #7, Heat #8. Warriors grew 25% in 2025 (>= 5%).
    "pred_golden_state_warriors_finishes_in_top_5__8ad22773": 1, "pred_los_angeles_lakers_finishes_in_top_5_of__e1eaa1b2": 1,
    "pred_new_york_knicks_finishes_in_top_5_of_nba_ec211368": 1, "pred_los_angeles_clippers_finishes_in_top_5_o_b453d982": 1,
    "pred_boston_celtics_finishes_in_top_5_of_nba__06bbc0fc": 1, "pred_chicago_bulls_finishes_in_top_5_of_nba_b_5ba7bc20": 0,
    "pred_houston_rockets_finishes_in_top_5_of_nba_1458d2af": 0, "pred_miami_heat_finishes_in_top_5_of_nba_by_v_d79c4d23": 0,
    "pred_a8249447": 1,
}
SPORT_PREFIX = ("sports_", "nba_", "nhl_", "athlete_valuation", "forward_qi", "cross_league", "macro_conditional_sponsorship",
                "wsl_", "sports_attention")


def is_sport(r):
    return r["domain"].startswith(SPORT_PREFIX) or r["domain"] in {"athlete_marketability_signal"}


def subset(r):
    cid, dom = r["canonical_id"], r["domain"]
    if cid in CAL_IDS:
        return "calendar"
    if cid in ATT_IDS or dom in {"sports_attention_short_fuse", "athlete_marketability_signal"} or "Wikipedia 7-day median" in r["question"]:
        return "attention"
    if cid in MEDIA_IDS or dom == "macro_conditional_sponsorship":
        return "media"
    if dom in {"sports_valuations", "sports_valuation", "athlete_valuation"}:
        return "forbes"
    return "outcomes"


def load():
    rows = [r for r in json.loads((REPO / "ledger_canonical.json").read_text()) if is_sport(r)]
    for f in ["staging_2026-06-28_demo_arc_locks.json", "staging_2026_nba_draft_2026-06-08.json"]:
        rows += [r for r in json.loads((REPO / f).read_text()) if r.get("canonical_id")]
    return rows


def fwd(rows):
    out, excluded = [], []
    for r in rows:
        if r.get("status") != "resolved" or r.get("resolution") is None:
            continue
        rd = str(r.get("resolution_date_corrected") or r.get("resolution_date") or "")[:10]
        why = None
        if r.get("temporal_class") != "FWD":
            why = f"temporal_class={r.get('temporal_class')}"
        elif any(f.startswith("duplicate_of") for f in r.get("audit_flags", [])):
            why = "duplicate"
        elif rd > TODAY:
            why = f"resolved before its resolution date ({rd})"
        if why:
            excluded.append((r, why))
        else:
            out.append(r)
    return out, excluded


def o(r):
    v = r["resolution"]
    return 1.0 if v in (True, 1, 1.0) else 0.0


def stats(rs, sub):
    n = len(rs)
    if not n:
        return None
    ps = [r["chorus_probability"] for r in rs]
    os_ = [o(r) for r in rs]
    brier = sum((p - y) ** 2 for p, y in zip(ps, os_)) / n
    hits = sum(1 for p, y in zip(ps, os_) if (p > 0.5 and y == 1) or (p < 0.5 and y == 0))
    rate = sum(os_) / n
    if sub == "forbes":
        bs = []
        for r, p, y in zip(rs, ps, os_):
            if r["canonical_id"] in PERSIST:
                conf = max(p, 1 - p)
                bp = conf if PERSIST[r["canonical_id"]] else 1 - conf
            else:
                bp = 0.5
            bs.append((bp - y) ** 2)
        base, label = sum(bs) / n, "persistence (prior-year list; 0.5 where unchecked)"
    elif sub == "outcomes":
        bs = [((r["baseline_probability"] if r.get("baseline_probability") is not None else rate) - y) ** 2 for r, y in zip(rs, os_)]
        nm = sum(1 for r in rs if r.get("baseline_probability") is not None)
        base, label = sum(bs) / n, f"market price on {nm} rows, in-sample base rate on {n - nm}"
    elif sub == "attention":
        base, label = rate * (1 - rate), "constant hit-rate (in-sample)"
    else:
        base, label = rate * (1 - rate), "in-sample base rate"
    return dict(n=n, hits=hits, brier=brier, base=base, bss=(1 - brier / base) if base else None, label=label, rate=rate)


def main():
    rows = load()
    f, ex = fwd(rows)
    subs = {}
    for r in f:
        subs.setdefault(subset(r), []).append(r)
    res = {}
    for k in ["attention", "forbes", "outcomes", "media", "calendar"]:
        res[k] = stats(subs.get(k, []), k)
    # pooled excluding calendar: n-weighted average of subset baselines
    pool = [r for k in ["attention", "forbes", "outcomes", "media"] for r in subs.get(k, [])]
    n = len(pool)
    pb = sum(res[k]["brier"] * res[k]["n"] for k in ["attention", "forbes", "outcomes", "media"]) / n
    pbase = sum(res[k]["base"] * res[k]["n"] for k in ["attention", "forbes", "outcomes", "media"]) / n
    ph = sum(res[k]["hits"] for k in ["attention", "forbes", "outcomes", "media"])
    res["pooled_ex_calendar"] = dict(n=n, hits=ph, brier=pb, base=pbase, bss=1 - pb / pbase, label="n-weighted subset baselines")
    allr = pool + subs.get("calendar", [])
    ab = sum((r["chorus_probability"] - o(r)) ** 2 for r in allr) / len(allr)
    res["pooled_incl_calendar"] = dict(n=len(allr), brier=ab)
    # market-priced rows only
    mk = [r for r in subs.get("outcomes", []) if r.get("baseline_probability") is not None]
    res["market_priced_only"] = dict(n=len(mk),
                                     brier=sum((r["chorus_probability"] - o(r)) ** 2 for r in mk) / len(mk),
                                     market=sum((r["baseline_probability"] - o(r)) ** 2 for r in mk) / len(mk))
    dates = sorted(r["locked_at"][:10] for r in pool)
    rdates = sorted(str(r["resolution_date"])[:10] for r in pool)
    res["lock_range"] = [dates[0], dates[-1]]
    res["resolution_range"] = [rdates[0], rdates[-1]]
    res["excluded"] = [(r["canonical_id"], r["question"][:70], why) for r, why in ex]
    res["misses"] = [(subset(r), r["question"][:90], r["chorus_probability"], o(r)) for r in pool
                     if not ((r["chorus_probability"] > 0.5 and o(r) == 1) or (r["chorus_probability"] < 0.5 and o(r) == 0))]
    # Sensitivity outputs (reported in RESOLUTION_REPORT_2026-10-15.md, now computed here):
    # 1) World Cup rows locked after the 2026-06-11 kickoff (in-play locks) removed.
    wc = lambda r: r["domain"].startswith("sports_worldcup_2026") and r["locked_at"][:10] >= "2026-06-11"
    kept = {k: [r for r in subs.get(k, []) if not wc(r)] for k in ["attention", "forbes", "outcomes", "media"]}
    ks = {k: stats(v, k) for k, v in kept.items() if v}
    kn = sum(x["n"] for x in ks.values())
    kb = sum(x["brier"] * x["n"] for x in ks.values()) / kn
    kbase = sum(x["base"] * x["n"] for x in ks.values()) / kn
    res["ex_worldcup_post_kickoff"] = dict(n_excluded=sum(1 for r in pool if wc(r)), n=kn,
                                           hits=sum(x["hits"] for x in ks.values()), brier=kb, base=kbase,
                                           bss=1 - kb / kbase, outcomes=ks.get("outcomes"))
    # 2) Forbes rows where the prior-year list was checked: Chorus vs persistence.
    fp = [r for r in subs.get("forbes", []) if r["canonical_id"] in PERSIST]
    if fp:
        pb = []
        for r in fp:
            conf = max(r["chorus_probability"], 1 - r["chorus_probability"])
            pb.append(((conf if PERSIST[r["canonical_id"]] else 1 - conf) - o(r)) ** 2)
        res["forbes_persistence_checked"] = dict(
            n=len(fp), chorus=sum((r["chorus_probability"] - o(r)) ** 2 for r in fp) / len(fp),
            persistence=sum(pb) / len(fp),
            same_direction=sum(1 for r in fp if (r["chorus_probability"] > 0.5) == bool(PERSIST[r["canonical_id"]])))
    res["as_of"] = TODAY
    json.dump(res, sys.stdout, indent=1, default=str)


if __name__ == "__main__":
    main()
