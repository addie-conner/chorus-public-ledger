#!/usr/bin/env python3
"""Resolution sweep 2026-10-15: overdue sports rows in ledger_canonical.json.

Rules (sealed, not changed here):
  - Lock text, probabilities, thresholds and lock dates are never edited.
  - brier = (p - outcome)^2, outcome in {0,1}, p = chorus_probability as locked.
  - If the outcome (or the list it comes from) was public before locked_at, the row
    is marked temporal_class = "RETRO" with an audit flag, and kept (not deleted).
    RETRO rows are excluded from forward scoring.
  - Rows whose outcome cannot be established from a public source stay open.

Also annotates the 6 demo-arc staging rows resolved today by
scripts/resolve_demo_arc_picks.py (sealed Wikipedia REST all-access/all-agents rule)
with the window median and the API URL.

Dry-run by default; --write persists. Never pushes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "ledger_canonical.json"
STAGING = REPO / "staging_2026-06-28_demo_arc_locks.json"
TODAY = "2026-10-15T00:00:00+00:00"

# id -> (outcome, temporal, source, pub_date, value_note)
R = {}


def add(i, outcome, src, pub, note, temporal="FWD"):
    R[i] = (outcome, temporal, src, pub, note)


# ---- sports_scan (locked 2026-03-29; baseline_probability = market price in scripts/scan_sports_2026.py)
WC = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"
add("aa9136cf715e", 0, WC + " ; https://www.foxsports.com/stories/soccer/2026-world-cup-bracket-semifinals-final-matchups", "2026-07-15",
    "Semifinals Spain-France, Argentina-England; no host nation (USA/MEX/CAN) reached the semifinals.")
for i, team, won in [("57932270444d", "USA", 0), ("cfe2700a0e2c", "Germany", 0), ("b28cdd92b045", "Brazil", 0),
                     ("90ca2e61f600", "Spain", 1), ("01e8025da9c8", "Argentina", 0), ("add53d867679", "England", 0),
                     ("0e2aa37658bc", "France", 0)]:
    add(i, won, WC + " ; https://abcnews.com/GMA/Culture/spain-argentina-win-2026-world-cup/story?id=134824556", "2026-07-19",
        f"Spain beat Argentina 1-0 a.e.t. in the final on 2026-07-19. {team} {'won' if won else 'did not win'}.")
NBAF = "https://en.wikipedia.org/wiki/2026_NBA_Finals ; https://www.nba.com/news/jalen-brunson-wins-bill-russell-trophy-as-2026-nba-finals-mvp"
for i, team in [("47a1319a0e6d", "Spurs"), ("8491311f2fbc", "Thunder"), ("9b65d85094c8", "Nuggets"), ("0271385f0724", "Celtics")]:
    add(i, 0, NBAF, "2026-06-13", f"Knicks beat Spurs 4-1 (Game 5, 2026-06-13). {team} did not win.")
SCF = "https://en.wikipedia.org/wiki/2026_Stanley_Cup_Final ; https://www.nhl.com/news/carolina-hurricanes-vegas-golden-knights-stanley-cup-final-game-6-recap-june-14-2026"
add("bf0768e67ba2", 1, SCF, "2026-06-14", "Hurricanes beat Golden Knights 4-2, clinched 2026-06-14.")
add("75ed41af12fb", 0, SCF, "2026-06-14", "Hurricanes won; Avalanche did not.")
add("a2f80896aef0", 0, SCF, "2026-06-14", "Hurricanes won; Lightning did not.")
SL = ("AO: https://ausopen.com/articles/news/major-milestone-alcaraz-completes-slam-set-ao-2026-title ; "
      "RG: https://www.olympics.com/en/news/french-open-2026-mens-singles-final-alexander-zverev-flavio-cobolli-live-updates-results ; "
      "W: https://www.olympics.com/en/news/wimbledon-2026-jannik-sinner-alexander-zverev-mens-singles-final-resuls ; "
      "USO: https://en.wikipedia.org/wiki/2026_US_Open_%E2%80%93_Men%27s_singles")
add("df34e67e737b", 0, SL, "2026-09-13", "2026 men's Slams: Alcaraz (AO), Zverev (RG), Sinner (W), Zverev (USO). Sinner won 1.")
add("983073a32116", 0, SL, "2026-09-13", "Djokovic won 0 Slams in 2026 (lost AO final, lost USO R1).")

# ---- Forbes team lists (sports_valuations, locked 2026-04-24)
NFL = "https://www.forbes.com/sites/justinteitelbaum/2026/09/09/the-nfls-most-valuable-teams-2026/ (syndicated https://sports.yahoo.com/articles/nfl-most-valuable-teams-2026-103000891.html)"
NFLN = "Forbes 2026 NFL: 1 Cowboys $17B, 2 Rams $13.5B, 3 Giants $12B, 4 Patriots $10.6B, 5 49ers $10.5B; Jets #7, Eagles #9, Bears #12."
for i in ["pred_dallas_cowboys_finishes_in_top_5_of_nfl__4c7062ef", "pred_los_angeles_rams_finishes_in_top_5_of_nf_9b49cf25",
          "pred_new_york_giants_finishes_in_top_5_of_nfl_ff2ae647", "pred_new_england_patriots_finishes_in_top_5_o_75ddbeb3",
          "pred_san_francisco_49ers_finishes_in_top_5_of_3ac98ed3"]:
    add(i, 1, NFL, "2026-09-09", NFLN)
for i in ["pred_philadelphia_eagles_finishes_in_top_5_of_75a353c7", "pred_chicago_bears_finishes_in_top_5_of_nfl_b_f190a0ee",
          "pred_new_york_jets_finishes_in_top_5_of_nfl_b_9d3cec67"]:
    add(i, 0, NFL, "2026-09-09", NFLN)
add("pred_1bd02c9d", 1, NFL, "2026-09-09", "Cowboys #1 at $17B.")

MLB = "https://www.forbes.com/sites/justinteitelbaum/2026/03/20/baseballs-most-valuable-teams-2026/ (syndicated https://ca.sports.yahoo.com/news/baseball-most-valuable-teams-2026-103000807.html)"
MLBN = ("Forbes 2026 MLB, published 2026-03-20 (before the 2026-04-24 lock): 1 Yankees $8.5B, 2 Dodgers $7.8B, 3 Red Sox $5.25B, "
        "4 Cubs $5.0B, 5 Giants $4.05B; Mets #6, Phillies #7, Braves #8.")
for i in ["pred_new_york_yankees_finishes_in_top_5_of_ml_9903b60e", "pred_los_angeles_dodgers_finishes_in_top_5_of_53a44aca",
          "pred_boston_red_sox_finishes_in_top_5_of_mlb__547f180d", "pred_chicago_cubs_finishes_in_top_5_of_mlb_by_27dd3f54",
          "pred_san_francisco_giants_finishes_in_top_5_o_88449f91"]:
    add(i, 1, MLB, "2026-03-20", MLBN, "RETRO")
for i in ["pred_new_york_mets_finishes_in_top_5_of_mlb_b_76134d83", "pred_philadelphia_phillies_finishes_in_top_5__a97c452e",
          "pred_atlanta_braves_finishes_in_top_5_of_mlb__c71a2dd7"]:
    add(i, 0, MLB, "2026-03-20", MLBN, "RETRO")
add("pred_b9794481", 1, MLB, "2026-03-20",
    "Yankees +4% ($8.2B to $8.5B) vs median +12% across 30 teams. List published 2026-03-20, before the 2026-04-28 lock.", "RETRO")
add("pred_3406b00f", 1, MLB, "2026-03-20",
    "Dodgers $7.8B. List published 2026-03-20, before the 2026-04-28 lock.", "RETRO")
add("pred_5f44f5eb", 1,
    "https://www.forbes.com/sites/justinteitelbaum/2026/05/29/the-worlds-most-valuable-soccer-teams-2026/ (republished https://www.forbes.com.au/news/sport/ranking-worlds-most-valuable-soccer-teams-2026/)",
    "2026-05-29", "Real Madrid #1 $9.5B vs Manchester United #3 $7.2B.")

ATH = ("https://www.forbes.com/sites/brettknight/2026/05/22/the-worlds-10-highest-paid-athletes-2026/ ; "
       "https://www.forbes.com/sites/brettknight/2026/05/22/inside-the-41-billion-haul-by-2026s-50-highest-paid-athletes/")
add("pred_aa330d75", 1, ATH, "2026-05-22", "Ronaldo #1 at $300M.")
add("pred_9430cff3", 1, ATH, "2026-05-22", "NBA in top 10: LeBron James #4, Stephen Curry #6, Kevin Durant #9 (3).")
add("pred_9df9e26d", 0, ATH, "2026-05-22", "Saquon Barkley not in the top 50 (#50 = Jannik Sinner, $54.6M).")

# ---- NBA / media / sponsorship (locked 2026-04-28/29)
add("pred_9d8ac31d", 0, "https://en.wikipedia.org/wiki/2026_NBA_draft ; https://www.aljazeera.com/sports/2026/6/24/nba-draft-2026-aj-dybantsa-no-1-pick-washington-wizards",
    "2026-06-23", "No. 1 pick 2026 = AJ Dybantsa (Washington). Cooper Flagg was the 2025 No. 1 pick and was not in the 2026 draft (premise error in the lock).")
add("pred_e9511166", 1, "https://en.wikipedia.org/wiki/2026_NBA_draft", "2026-06-23", "No. 2 pick = Darryn Peterson (Utah).")
add("pred_e78785dc", 1, "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/Jalen_Brunson/daily/20260613/20260620",
    "2026-06-14", "Finals MVP Jalen Brunson; daily views 2026-06-14 = 1,350,798 (>= 50,000 on 7 of 8 days 06-13..06-20).")
add("pred_0f65936b", 0, "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/Cooper_Flagg/daily/20260620/20260630",
    "2026-06-26", "Cooper_Flagg views on 2026-06-25 = 4,238 (window max 8,323 on 06-24).")
add("pred_4969ec96", 0, "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/Caitlin_Clark/daily/20260501/20260531 ; opener date https://www.thehoosiernetwork.com/article/2026/05/indiana-fever-dallas-wings-caitlin-clark-returns-paige-bueckers",
    "2026-05-10", "Fever opener (home) 2026-05-09 vs Dallas; Caitlin_Clark views that day = 11,427 (May max 11,908).")
add("pred_e91d9ef2", 1, "https://espnpressroom.com/us/press-releases/2026/06/abcs-most-watched-nba-finals-game-1-since-2018-with-average-audience-of-nearly-17m-viewers-16-93m/",
    "2026-06-04", "ABC aired Game 1 (2026-06-03).")
add("pred_60303dca", 1, "https://www.nba.com/news/suns-thunder-2026-playoffs-game-4-takeaways", "2026-04-28",
    "Only sweep: Thunder 4-0 Suns, Game 4 on 2026-04-27, before the 2026-04-29 lock.", "RETRO")
add("pred_e2333d1e", 1, "https://www.nba.com/news/2025-26-all-nba-teams-announced ; https://en.wikipedia.org/wiki/2026_NBA_Finals",
    "2026-05-24", "All-NBA First Team includes Victor Wembanyama (Spurs, 2026 finalist). Announced 2026-05-24, after lock.")
add("pred_c545859d", 1, "https://en.wikipedia.org/wiki/2026_NBA_Finals (attendance from page wikitext)", "2026-06-13",
    "Attendance G1 18,835, G2 19,014, G3 19,812, G4 19,812, G5 18,984; every game >= 18,000.")
add("pred_d837d5f2", 0, "https://bleacherreport.com/articles/25508133-cooper-flagg-unveils-signature-logo-new-balance-new-photo-ahead-2026-27-nba-season",
    "2026-10", "Flagg remains a New Balance athlete (deal signed 2024); no Nike or Adidas deal reported 2026-06-25..07-25.")
add("pred_d4efe957", 1, "https://pr.nba.com/2026-nba-finals-viewership", "2026-06-16", "Series average 20.6M (Nielsen Big Data + Panel).")
add("pred_7d8d18b2", 1, "https://www.nba.com/news/nba-finals-2026-spurs-knicks-game-1-viewership", "2026-06-06", "Game 1 16.93M.")
add("pred_d30afe71", 0, "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ICSA ; https://pr.nba.com/2026-nba-finals-viewership",
    "2026-10-01", "Joint event false: ICSA Q3 2026 average 203,462 (< 250K) and Finals average 20.6M (> 11.0M).")
add("pred_12332624", 1, "https://espnpressroom.com/press-release/espn-delivers-most-watched-stanley-cup-final-since-2019-capping-its-most-watched-stanley-cup-playoffs-ever/",
    "2026-06-16", "2026 Stanley Cup Final on ABC averaged 5.2M over six games.")
add("pred_2ed61a40", 1, "https://sports.yahoo.com/articles/knicks-spurs-finals-begins-red-220701887.html (Sportico)", "2026-06-05",
    "Average in-game unit about $800,000 per 30-second spot.")
add("pred_bbcb580a", 1, "https://bleacherreport.com/articles/25445663-warriors-reportedly-land-record-jersey-patch-sponsorship-agreement-ahead-2026-27-nba-season ; https://www.sportico.com/business/sponsorship/2026/warriors-sign-record-jersey-patch-deal-with-iren-1234937113/",
    "2026-06-25", "Warriors x Iren patch for 2026-27 at more than $50M/yr.")
add("pred_42cca4f1", 1, "https://bleacherreport.com/articles/25445663-warriors-reportedly-land-record-jersey-patch-sponsorship-agreement-ahead-2026-27-nba-season",
    "2026-06-25", "Iren >$50M/yr, reported as a record; prior Warriors/Rakuten deal ~$20M/yr; Knicks deal reported >$20M/yr. >=1.10x is inferred from reported values, not a published comparison.")

# ---- calendar checks (locked 2026-06-16)
add("pred_nfl_2026_season_kickoff_september", 1, "https://www.nfl.com/news/seahawks-to-kick-off-2026-nfl-regular-season-on-wednesday-sept-9-in-seattle", "2026-09-09", "Kickoff 2026-09-09.")
add("pred_mlb_2026_all_star_game_july", 1, "https://en.wikipedia.org/wiki/2026_Major_League_Baseball_All-Star_Game", "2026-07-14", "Played 2026-07-14.")
add("pred_us_open_tennis_2026_starts_aug", 1, "https://en.wikipedia.org/wiki/2026_US_Open_%E2%80%93_Men%27s_singles", "2026-08-30", "Main draw began 2026-08-30.")
add("pred_wimbledon_2026_singles_finals_july", 1, "https://www.aljazeera.com/sports/2026/7/11/noskova-defeats-muchova-in-wimbledon-final-to-record-first-grand-slam-title", "2026-07-12", "Ladies' final 07-11, Gentlemen's final 07-12.")
add("pred_tour_de_france_2026_starts_july", 1, "https://www.barcelona.cat/mobilitat/en/mobility-impacts-tour-france-2026/4-july-stage-1-time-trial", "2026-07-04", "Stage 1 TTT Barcelona 2026-07-04.")
add("pred_open_championship_golf_2026_july", 1, "https://en.wikipedia.org/wiki/2026_Open_Championship", "2026-07-19", "Final round 2026-07-19.")
add("pred_nba_summer_league_2026_held", 1, "https://www.nba.com/news/2026-nba-summer-league-what-to-watch-key-dates", "2026-07-19", "Las Vegas Summer League 2026-07-09..07-19.")

DEMO_MEDIANS = {
    "demo_arc_2026-06-28_008": ("Kobbie_Mainoo", 1117), "demo_arc_2026-06-28_009": ("Hezly_Rivera", 128),
    "demo_arc_2026-06-28_010": ("Cade_Klubnik", 985), "demo_arc_2026-06-28_011": ("Drew_Allar", 913),
    "demo_arc_2026-06-28_012": ("Daria_Kasatkina", 521), "demo_arc_2026-06-28_013": ("Kyle_Harrison", 144),
}


def main(write: bool) -> int:
    d = json.loads(LEDGER.read_text())
    by = {r["canonical_id"]: r for r in d}
    missing = [i for i in R if i not in by]
    if missing:
        print("MISSING ids:", missing)
        return 1
    for i, (o, tc, src, pub, note) in R.items():
        r = by[i]
        assert r["status"] == "open", i
        p = r["chorus_probability"]
        r["status"] = "resolved"
        r["resolution"] = float(o)
        r["resolved_at"] = TODAY
        r["resolution_source"] = f"{src} (published {pub})"
        r["resolution_value"] = note
        r["brier_score"] = round((p - o) ** 2, 6)
        bp = r.get("baseline_probability")
        if bp is not None:
            r["baseline_brier"] = round((bp - o) ** 2, 6)
        flags = [f for f in r.get("audit_flags", []) if f != "resolution_overdue"]
        flags.append("resolved_2026-10-15_sweep")
        if tc == "RETRO":
            r["temporal_class"] = "RETRO"
            flags.append(f"retro:outcome_public_{pub}_before_lock_{r['locked_at'][:10]}")
        r["audit_flags"] = flags
        print(f"{'RETRO' if tc == 'RETRO' else 'FWD  '} o={o} p={p} brier={r['brier_score']:.4f}  {r['question'][:80]}")
    st = json.loads(STAGING.read_text())
    for e in st:
        cid = e.get("canonical_id")
        if cid in DEMO_MEDIANS:
            slug, med = DEMO_MEDIANS[cid]
            ws = e["model_inputs"]["window_start"].replace("-", "")
            we = e["model_inputs"]["window_end"].replace("-", "")
            e["resolution_value"] = f"window median {med}/day vs threshold {e['model_inputs']['threshold']}"
            e["resolution_source"] = ("Wikipedia REST API per-article daily pageviews "
                                      f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{slug}/daily/{ws}/{we}")
    print(f"{len(R)} ledger rows; 6 staging annotations")
    if write:
        LEDGER.write_text(json.dumps(d, indent=2))
        STAGING.write_text(json.dumps(st, indent=2))
        print("written")
    else:
        print("[dry-run]")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
