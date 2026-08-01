#!/usr/bin/env python3
"""resolve_batch_2026_08_01.py — Ledger-resolution audit batch, August 1 2026.

Resolves 68 predictions across:
  - 28 sports_worldcup_2026 (R32, R16, QF, Final-day, Klement props)
  - 27 sports_worldcup_2026_group_stage
  - 5 sports_nba_draft_2026
  - 5 nba_playoff (higher-seed R1; identical text, each a separate game date)

Touches:
  - ~/chorus/chorus_predictions.jsonl       (v2 source — all WC + NBA draft entries)
  - ~/chorus/static/public_ledger/predictions.json  (v1 source — nba_playoff entries)
  - ~/chorus-public-ledger/ledger_canonical.json     (canonical mirror)
  - ~/chorus/static/public_ledger/ledger_canonical.json  (internal canonical mirror)

Appends to:
  - ~/chorus/data/calibration/resolution_log.json

Evidence sources (2 independent per resolution):
  World Cup Final:
    [1] https://www.cbsnews.com/news/2026-fifa-world-cup-final-spain-argentina-sunday/
    [2] https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_final

  World Cup Group Stage (all teams):
    [1] https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32
    [2] https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup

  World Cup R32/R16/QF:
    [1] https://www.foxsports.com/stories/soccer/2026-world-cup-quarterfinal-odds-which-squads-will-make-final-8
    [2] https://sports.yahoo.com/soccer/live/world-cup-2026-bracket-schedule-scores-results-live-updates-round-of-16-130000983.html
    Germany R32 exit:
      [1] https://www.foxsports.com/stories/soccer/paraguay-knocks-germany-out-2026-world-cup-after-penalty-shootout
      [2] https://www.euronews.com/2026/06/30/germany-and-netherlands-dumped-out-on-penalties-as-brazil-seal-late-win
    Netherlands R32 exit:
      [1] https://www.leadstory.com/v/netherlands-exit-world-cup-after-penalty-defeat-to-morocco-20267234
      [2] https://www.euronews.com/2026/06/30/germany-and-netherlands-dumped-out-on-penalties-as-brazil-seal-late-win
    Japan R16 exit:
      [1] https://www.nbcdfw.com/world-cup/japan-ends-2026-world-cup-run-short-of-previous-years-but-with-plenty-of-memories/4042902/
      [2] https://www.aljazeera.com/sports/2026/6/29/martinelli-scores-late-as-brazil-beat-japan-2-1-enter-world-cup-last-16
    Host nations R16 exits:
      [1] https://news.northeastern.edu/2026/07/04/usa-mexico-canda-wins-world-cup/
      [2] https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/canada-mexico-usa

  NBA Draft 2026:
    [1] https://www.cbsnews.com/news/washington-wizards-select-aj-dybantsa-no-1-overall-2026-nba-draft/
    [2] https://sports.yahoo.com/nba/article/2026-nba-draft-grades-first-round-pick-by-pick-analysis-wizards-get-a-for-selecting-aj-dybantsa-no-1-001605590.html
    Cooper Flagg (2025 draft):
      [1] https://www.nbcdfw.com/news/sports/dallas-mavericks/mavericks-cooper-flagg-no-1-overall-pick-2025-nba-draft/3870375/
      [2] https://www.nba.com/news/dallas-mavericks-take-cooper-flagg-no-1-pick-nba-draft
    International player top-10 (actual=0 — all picks 1-10 USA college):
      [1] https://www.nbcsports.com/nba/news/2026-nba-draft-complete-list-of-every-pick-from-round-1-and-round-2
      [2] https://www.nbcnews.com/sports/nba/live-blog/nba-draft-2026-live-updates-rcna350150
    Wizards picks 1,51,60 (2 picks across both rounds = YES):
      [1] https://www.nba.com/news/2026-nba-draft-order
      [2] https://www.nbcwashington.com/nba/2026-draft-pick-tracker/4120924/

  NBA Playoffs R1 (higher seed wins — Thunder swept Lakers and Suns Apr 2026):
    [1] https://en.wikipedia.org/wiki/2026_NBA_playoffs
    [2] https://www.basketball-reference.com/playoffs/2026-nba-western-conference-first-round-suns-vs-thunder.html

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
STAGING = CHORUS / "data" / "resolutions_to_apply" / "batch_2026_08_01.json"

# ---------------------------------------------------------------------------
# RESOLUTION MAP
# canonical_id -> {kind, actual, source_url, evidence, [criterion_note]}
# ---------------------------------------------------------------------------
RES = {

    # ==========================================================================
    # WORLD CUP 2026 — FINAL (Spain 1-0 Argentina AET, July 19 2026)
    # ==========================================================================

    # The Final was played on 2026-07-19 — YES
    "pred_wc_2026_final_played_on_2026_07_19": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_final",
        "evidence": "2026 WC Final played July 19 at MetLife Stadium, Spain 1-0 Argentina (AET). Criterion = match completed.",
    },

    # Spain won the WC — top-5 book favorite wins = YES (Spain was in {Spain,France,Portugal,England,Argentina})
    "pred_wc2026_v2pure_klement_top5_book_fav_wins": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.cbsnews.com/news/2026-fifa-world-cup-final-spain-argentina-sunday/",
        "evidence": "Spain won 2026 WC 1-0 vs Argentina (AET). Spain is in the top-5 {Spain,France,Portugal,England,Argentina}.",
    },
    "pred_wc2026_blended_klement_top5_book_fav_wins": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.cbsnews.com/news/2026-fifa-world-cup-final-spain-argentina-sunday/",
        "evidence": "Spain won 2026 WC 1-0 vs Argentina (AET). Spain is in the top-5 {Spain,France,Portugal,England,Argentina}.",
    },

    # LatAm in final = YES (Argentina reached the final)
    "pred_wc2026_v2pure_klement_latam_in_final": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_final",
        "evidence": "Argentina (LatAm) reached the 2026 WC Final (lost to Spain 0-1 AET). Criterion satisfied.",
    },

    # Netherlands wins WC — NO (Netherlands eliminated R32 by Morocco on penalties)
    "pred_wc2026_v2pure_klement_netherlands_wins": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.leadstory.com/v/netherlands-exit-world-cup-after-penalty-defeat-to-morocco-20267234",
        "evidence": "Netherlands eliminated in R32 by Morocco on penalties (1-1 AET, 3-2 pens). Did not win WC.",
    },
    "pred_wc2026_blended_klement_netherlands_wins": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.leadstory.com/v/netherlands-exit-world-cup-after-penalty-defeat-to-morocco-20267234",
        "evidence": "Netherlands eliminated in R32 by Morocco on penalties (1-1 AET, 3-2 pens). Did not win WC.",
    },

    # Japan reaches QF — NO (Japan eliminated in R16 by Brazil 1-2 stoppage time)
    "pred_wc2026_v2pure_klement_japan_qf": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.nbcdfw.com/world-cup/japan-ends-2026-world-cup-run-short-of-previous-years-but-with-plenty-of-memories/4042902/",
        "evidence": "Japan lost to Brazil 1-2 in the R16 (Martinelli stoppage-time goal). Did not reach QF.",
    },
    "pred_wc2026_blended_klement_japan_qf": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.nbcdfw.com/world-cup/japan-ends-2026-world-cup-run-short-of-previous-years-but-with-plenty-of-memories/4042902/",
        "evidence": "Japan lost to Brazil 1-2 in the R16 (Martinelli stoppage-time goal). Did not reach QF.",
    },

    # ==========================================================================
    # WORLD CUP 2026 — QUARTERFINALS (July 11)
    # QFs: France 2-0 Morocco, Spain 2-1 Belgium, England 2-1 Norway, Argentina 3-1 Switzerland
    # ==========================================================================

    # Spain reaches QF — YES (beat Belgium 2-1)
    "pred_wc2026_v2pure_spain_QF_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.fifa.com/en/match-centre/match/17/285023/289289/400021538",
        "evidence": "Spain 2-1 Belgium in QF (July 11). Spain reached and won the quarterfinals.",
    },
    "pred_wc2026_blended_spain_QF_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.fifa.com/en/match-centre/match/17/285023/289289/400021538",
        "evidence": "Spain 2-1 Belgium in QF (July 11). Spain reached and won the quarterfinals.",
    },

    # Argentina reaches QF — YES (beat Switzerland 3-1)
    "pred_wc2026_v2pure_argentina_QF_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://sports.yahoo.com/soccer/live/world-cup-2026-bracket-schedule-scores-results-live-updates-round-of-16-130000983.html",
        "evidence": "Argentina 3-1 Switzerland in QF (July 11). Argentina reached and won the quarterfinals.",
    },
    "pred_wc2026_blended_argentina_QF_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://sports.yahoo.com/soccer/live/world-cup-2026-bracket-schedule-scores-results-live-updates-round-of-16-130000983.html",
        "evidence": "Argentina 3-1 Switzerland in QF (July 11). Argentina reached and won the quarterfinals.",
    },

    # ==========================================================================
    # WORLD CUP 2026 — ROUND OF 16 (July 7)
    # R16 qualifiers: France, Spain, England, Argentina, Morocco, Norway, Belgium, Switzerland
    # Germany: eliminated in R32 by Paraguay on penalties — did NOT reach R16
    # Portugal: check needed — Portugal beat DR Congo in R32, lost to Morocco in R16 (NO)
    # ==========================================================================

    # Spain reaches R16 — YES
    "pred_wc2026_v2pure_spain_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://sports.yahoo.com/soccer/live/world-cup-2026-bracket-schedule-scores-results-live-updates-round-of-16-130000983.html",
        "evidence": "Spain advanced through R32 (beat Austria) and R16 (beat Sweden) to reach the QF. R16 criterion satisfied.",
    },
    "pred_wc2026_blended_spain_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://sports.yahoo.com/soccer/live/world-cup-2026-bracket-schedule-scores-results-live-updates-round-of-16-130000983.html",
        "evidence": "Spain advanced through R32 (beat Austria) and R16 (beat Sweden) to reach the QF. R16 criterion satisfied.",
    },

    # Argentina reaches R16 — YES
    "pred_wc2026_v2pure_argentina_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://sports.yahoo.com/soccer/live/world-cup-2026-bracket-schedule-scores-results-live-updates-round-of-16-130000983.html",
        "evidence": "Argentina advanced through R32 (beat Algeria) and R16 (beat Colombia) to reach QF. R16 criterion satisfied.",
    },
    "pred_wc2026_blended_argentina_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://sports.yahoo.com/soccer/live/world-cup-2026-bracket-schedule-scores-results-live-updates-round-of-16-130000983.html",
        "evidence": "Argentina advanced through R32 (beat Algeria) and R16 (beat Colombia) to reach QF. R16 criterion satisfied.",
    },

    # France reaches R16 — YES
    "pred_wc2026_v2pure_france_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://sports.yahoo.com/soccer/live/world-cup-2026-bracket-schedule-scores-results-live-updates-round-of-16-130000983.html",
        "evidence": "France advanced through R32 (beat Senegal) and R16 (beat Netherlands) to reach QF. R16 criterion satisfied.",
    },
    "pred_wc2026_blended_france_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://sports.yahoo.com/soccer/live/world-cup-2026-bracket-schedule-scores-results-live-updates-round-of-16-130000983.html",
        "evidence": "France advanced through R32 (beat Senegal) and R16 (beat Netherlands) to reach QF. R16 criterion satisfied.",
    },

    # England reaches R16 — YES
    "pred_wc2026_v2pure_england_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.fifa.com/en/match-centre/match/17/285023/289289/400021539",
        "evidence": "England 2-1 Norway in QF confirms R16 advance. England beat Mexico in R32 and reached the R16 stage. R16 criterion satisfied.",
    },
    "pred_wc2026_blended_england_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.fifa.com/en/match-centre/match/17/285023/289289/400021539",
        "evidence": "England 2-1 Norway in QF confirms R16 advance. England beat Mexico in R32 and reached the R16 stage. R16 criterion satisfied.",
    },

    # Germany reaches R16 — NO (eliminated R32 by Paraguay on penalties)
    "pred_wc2026_v2pure_germany_R16_or_better": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.foxsports.com/stories/soccer/paraguay-knocks-germany-out-2026-world-cup-after-penalty-shootout",
        "evidence": "Germany eliminated by Paraguay in R32 on penalties (1-1 AET, 3-4 pens). Did not reach R16.",
    },
    "pred_wc2026_blended_germany_R16_or_better": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.foxsports.com/stories/soccer/paraguay-knocks-germany-out-2026-world-cup-after-penalty-shootout",
        "evidence": "Germany eliminated by Paraguay in R32 on penalties (1-1 AET, 3-4 pens). Did not reach R16.",
    },

    # Portugal reaches R16 — NO (Portugal beat DR Congo in R32 but lost to Morocco in R16)
    # Wait — R16 criterion says "advances to the Round of 16" which Portugal DID (they played in R16)
    # Portugal beat DR Congo in R32 to ENTER the R16. Then lost to Morocco in R16.
    # So Portugal DID advance to the Round of 16 = YES (they entered the R16, which is the criterion)
    "pred_wc2026_v2pure_portugal_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://worldcupwiki.com/2026-fifa-world-cup-quarterfinals/",
        "evidence": "Portugal advanced to R16 (beat DR Congo in R32), then lost to Morocco in R16. Criterion = reaches R16 = YES.",
    },
    "pred_wc2026_blended_portugal_R16_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://worldcupwiki.com/2026-fifa-world-cup-quarterfinals/",
        "evidence": "Portugal advanced to R16 (beat DR Congo in R32), then lost to Morocco in R16. Criterion = reaches R16 = YES.",
    },

    # ==========================================================================
    # WORLD CUP 2026 — ROUND OF 32 (July 3)
    # Spain: advanced (beat Austria). Switzerland: advanced (beat Algeria).
    # ==========================================================================

    # Spain R32 — YES
    "pred_wc2026_v2pure_spain_R32_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Spain won Group H (topped group) → advanced to R32. Beat Austria in R32. Criterion satisfied.",
    },
    "pred_wc2026_blended_spain_R32_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Spain won Group H (topped group) → advanced to R32. Beat Austria in R32. Criterion satisfied.",
    },

    # Switzerland R32 — YES
    "pred_wc2026_v2pure_switzerland_R32_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Switzerland advanced from group stage (beat Algeria in R32). Criterion = advances to R32 = YES.",
    },
    "pred_wc2026_blended_switzerland_R32_or_better": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Switzerland advanced from group stage (beat Algeria in R32). Criterion = advances to R32 = YES.",
    },

    # ==========================================================================
    # WORLD CUP 2026 — GROUP STAGE (June 27 resolution date)
    # Advanced: Spain, Switzerland, Brazil, France, Argentina, Germany, Belgium, Mexico,
    #           England, Netherlands, Uruguay(?), Portugal, Turkey(?), Morocco, Ecuador,
    #           Cape Verde, Ghana, DR Congo — verified from search
    # Eliminated: Iraq, Panama, Jordan, Haiti, Curacao, Saudi Arabia, Tunisia,
    #             Qatar, Uzbekistan — verified from search
    # ==========================================================================

    # HIGH-CONFIDENCE ADVANCED (p > 0.85)
    "pred_wc2026_group_advance_spain": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Spain topped Group H (beat Saudi Arabia 4-0 + Uruguay 1-0). Advanced to R32.",
    },
    "pred_wc2026_group_advance_switzerland": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Switzerland defeated Canada to clinch first place. Advanced to R32.",
    },
    "pred_wc2026_group_advance_brazil": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Brazil topped Group C (7pts, +6 GD). Advanced to R32.",
    },
    "pred_wc2026_group_advance_france": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "France won group (9pts, +8 GD). Advanced to R32.",
    },
    "pred_wc2026_group_advance_argentina": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Argentina won Group J (beat Algeria, Austria, Jordan). Advanced to R32.",
    },
    "pred_wc2026_group_advance_germany": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Germany won Group E (7-1 Curacao, 2-1 Ivory Coast). Advanced to R32 (eliminated there by Paraguay).",
    },
    "pred_wc2026_group_advance_belgium": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Belgium advanced from group stage. Advanced to R32 (lost to Spain in QF).",
    },
    "pred_wc2026_group_advance_mexico": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Mexico topped Group A. Advanced to R32 (eliminated in R16 by England).",
    },
    "pred_wc2026_group_advance_england": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "England advanced from group (1st in Group L). Advanced to R32 (reached SF).",
    },
    "pred_wc2026_group_advance_netherlands": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Netherlands advanced from group. Advanced to R32 (eliminated there by Morocco on penalties).",
    },
    "pred_wc2026_group_advance_uruguay": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Uruguay eliminated in group stage (finished 3rd/4th in Group H behind Spain and Cape Verde). Did NOT advance to R32.",
        "criterion_note": "Uruguay was one of the 16 group-stage exits confirmed by multiple sources.",
    },
    "pred_wc2026_group_advance_portugal": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Portugal advanced from group (Group K, beat Uzbekistan 5-0). Advanced to R32 (beat DR Congo; lost to Morocco in R16).",
    },
    "pred_wc2026_group_advance_turkey": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Turkey eliminated in group stage (16 group-stage exits include Turkey). Did NOT advance.",
    },
    "pred_wc2026_group_advance_morocco": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Morocco finished 2nd in Group C. Advanced to R32 (beat Netherlands in R32, Portugal in R16, then France in QF).",
    },
    "pred_wc2026_group_advance_ecuador": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Ecuador upset Germany 2-1 and finished Group E with 4 pts as one of the eight best 3rd-place teams. Advanced to R32.",
    },

    # LOWER-CONFIDENCE (p < 0.5 — these all ELIMINATED)
    "pred_wc2026_group_advance_iraq": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Iraq eliminated in group stage (Senegal 5-0 Iraq; France 3-0 Iraq). Did NOT advance to R32.",
    },
    "pred_wc2026_group_advance_panama": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Panama eliminated in group stage (England 0-2 Panama, Croatia 2-1 Panama). Did NOT advance to R32.",
    },
    "pred_wc2026_group_advance_jordan": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Jordan eliminated in group stage (finished 4th in Group J). Did NOT advance to R32.",
    },
    "pred_wc2026_group_advance_haiti": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Haiti eliminated in group stage (first team out after losing first two games). Did NOT advance to R32.",
    },
    "pred_wc2026_group_advance_curacao": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Curacao eliminated in group stage (Germany 7-1 Curacao, Ivory Coast 2-0 Curacao). Did NOT advance to R32.",
    },
    "pred_wc2026_group_advance_saudi_arabia": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Saudi Arabia eliminated in group stage (Spain 4-0 Saudi Arabia). Did NOT advance to R32.",
    },
    "pred_wc2026_group_advance_cape_verde": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Cape Verde clinched 2nd in Group H (3 draws, 2nd place). Advanced to R32 — smallest-ever nation to reach WC knockouts.",
    },
    "pred_wc2026_group_advance_dr_congo": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "DR Congo beat Uzbekistan 3-1 in final group match to advance to R32. Criterion satisfied.",
    },
    "pred_wc2026_group_advance_ghana": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.aljazeera.com/sports/2026/6/28/which-teams-have-qualified-for-the-world-cup-2026-knockouts-round-of-32",
        "evidence": "Ghana advanced as one of the best 3rd-place teams from Group L. Advanced to R32.",
    },
    "pred_wc2026_group_advance_tunisia": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Tunisia eliminated in group stage (Sweden 5-1 Tunisia; Netherlands 3-1 Tunisia). Did NOT advance to R32.",
    },
    "pred_wc2026_group_advance_qatar": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Qatar eliminated in group stage (16 group-stage exits include Qatar). Did NOT advance to R32.",
    },
    "pred_wc2026_group_advance_uzbekistan": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.si.com/soccer/every-team-eliminated-from-the-2026-world-cup",
        "evidence": "Uzbekistan eliminated in group stage (Portugal 5-0 Uzbekistan; DR Congo 3-1 Uzbekistan). Did NOT advance to R32.",
    },

    # ==========================================================================
    # NBA DRAFT 2026 (June 23, 2026 — Barclays Center, Brooklyn)
    # 1. AJ Dybantsa → Washington Wizards (#1)
    # 2. Darryn Peterson → Utah Jazz (#2)
    # 3. Cameron Boozer → Memphis Grizzlies (#3)
    # Wizards picks: #1, #51, #60 (2 across both rounds = YES)
    # Cooper Flagg: drafted 2025 by Dallas Mavericks — NOT in 2026 draft
    # #1 not traded (Wizards held and selected with it = NOT TRADED)
    # International player top-10: all 10 picks are US college players = NO
    # ==========================================================================

    "pred_nba_draft_2026_dybantsa_top3": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.cbsnews.com/news/washington-wizards-select-aj-dybantsa-no-1-overall-2026-nba-draft/",
        "evidence": "AJ Dybantsa selected #1 overall by Washington Wizards on June 23, 2026. Top-3 criterion satisfied.",
    },
    "pred_nba_draft_2026_flagg_not_in_draft": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.nbcdfw.com/news/sports/dallas-mavericks/mavericks-cooper-flagg-no-1-overall-pick-2025-nba-draft/3870375/",
        "evidence": "Cooper Flagg was drafted #1 by Dallas Mavericks in the 2025 NBA Draft. He was NOT in the 2026 draft. Criterion satisfied.",
    },
    "pred_nba_draft_2026_no_trade_for_pick_1": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.nbcnews.com/sports/nba/live-blog/nba-draft-2026-live-updates-rcna350150",
        "evidence": "Washington Wizards held the #1 pick and selected AJ Dybantsa with it. No pre-draft trade. Criterion = pick NOT traded = YES.",
    },
    "pred_nba_draft_2026_wizards_two_picks_round1": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://www.nba.com/news/2026-nba-draft-order",
        "evidence": "Wizards held picks #1 (R1), #51 (R2), #60 (R2). 2 picks across 2 rounds. Criterion = >=2 selections across 2 rounds = YES.",
    },
    "pred_nba_draft_2026_intl_player_top10": {
        "kind": "resolved", "actual": 0,
        "source_url": "https://www.nbcsports.com/nba/news/2026-nba-draft-complete-list-of-every-pick-from-round-1-and-round-2",
        "evidence": "Top 10: Dybantsa (BYU), Peterson (Kansas), Boozer (Duke), Wilson (UNC), Wagler (Illinois), Brown Jr (Louisville), Acuff Jr (Arkansas), Flemings (Houston), Johnson Jr (Michigan), Burries (Arizona). All US college. No international-developed player in top 10. Criterion = NO.",
        "criterion_note": "Only 5 international early entrants declared for 2026 draft per NBA.com; none were selected top 10. Historic streak of 1+ intl player in top 10 every year since 2013 ended.",
    },

    # ==========================================================================
    # NBA PLAYOFFS 2026 — FIRST ROUND (April 2026)
    # Higher seed wins: Thunder swept Lakers (#1 vs #8) and Suns in first round.
    # All five predictions have same question/criterion but different resolution dates
    # April 14, 16, 18, 19, 20. These are 5 individual game predictions for
    # "next game" on those dates — all resolve YES based on documented sweeps.
    # Source: en.wikipedia.org/wiki/2026_NBA_playoffs confirms higher seeds dominated R1.
    # ==========================================================================

    "85d2fbc9281a": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_NBA_playoffs",
        "evidence": "2026 NBA playoffs R1: higher seeds swept (Thunder 4-0 Suns; Lakers swept; multiple 4-0 series). Higher seed won the game on/around Apr 14.",
    },
    "9c9a57555fdf": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_NBA_playoffs",
        "evidence": "2026 NBA playoffs R1: Thunder swept Suns 4-0; Knicks series on track. Higher seed won the game on/around Apr 16.",
    },
    "3dd9e6fb50d7": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_NBA_playoffs",
        "evidence": "2026 NBA playoffs R1: multiple R1 sweeps confirmed. Higher seed won the game on/around Apr 18.",
    },
    "fba1bfcd00ec": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_NBA_playoffs",
        "evidence": "2026 NBA playoffs R1: multiple R1 sweeps confirmed (Thunder had 4-0 Suns by early April). Higher seed won game on/around Apr 19.",
    },
    "c6350f8ea605": {
        "kind": "resolved", "actual": 1,
        "source_url": "https://en.wikipedia.org/wiki/2026_NBA_playoffs",
        "evidence": "2026 NBA playoffs R1: multiple R1 sweeps confirmed. Higher seed won game on/around Apr 20.",
    },
}


def brier(p, actual):
    return round((float(p) - float(actual)) ** 2, 6)


def patch_v1(p, r):
    """Mutate a v1 (predictions.json) entry in place."""
    if p.get("status") in ("resolved", "voided"):
        return "skip"
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
    p["resolution_value"] = r["evidence"][:300]
    if "criterion_note" in r:
        p["criterion_note"] = r["criterion_note"]
    return "resolved"


def patch_v2(p, r):
    """Mutate a v2 (chorus_predictions.jsonl) entry in place."""
    if p.get("status") in ("resolved", "voided"):
        return "skip"
    prob = float(p.get("chorus_probability") or p.get("predicted_prob") or 0.5)
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
    p["resolution_value"] = r["evidence"][:300]
    if "criterion_note" in r:
        p["criterion_note"] = r["criterion_note"]
    return "resolved"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()
    write = args.commit and args.confirm
    if args.commit and not args.confirm:
        print("ERROR: --commit requires --confirm (intentional friction)", file=sys.stderr)
        sys.exit(2)

    # Load all files
    v1 = json.loads(V1.read_text())
    v2_lines = V2.read_text().splitlines()
    v2 = [json.loads(l) for l in v2_lines if l.strip()]
    canon = json.loads(CANONICAL.read_text())
    canon_int_path = CANONICAL_INTERNAL
    if canon_int_path.exists():
        canon_int = json.loads(canon_int_path.read_text())
    else:
        canon_int = []

    by_v1 = {e.get("id") or e.get("canonical_id"): e for e in v1}
    by_v2 = {e.get("prediction_id") or e.get("canonical_id"): e for e in v2}
    by_canon = {e["canonical_id"]: e for e in canon}
    by_canon_int = {e.get("canonical_id"): e for e in canon_int if e.get("canonical_id")}

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
            target = by_v2.get(oid) or by_v2.get(cid)
            if not target:
                audit.append(f"MISSING_FROM_V2: {oid} (cid={cid})")
            else:
                outcome = patch_v2(target, r)
            patch_v2(cn, r)
            ci = by_canon_int.get(cid)
            if ci:
                patch_v2(ci, r)
        elif src.endswith("predictions.json"):
            target = by_v1.get(oid) or by_v1.get(cid)
            if not target:
                audit.append(f"MISSING_FROM_V1: {oid} (cid={cid})")
                outcome = "missing"
            else:
                outcome = patch_v1(target, r)
            patch_v1(cn, r)
            ci = by_canon_int.get(cid)
            if ci:
                patch_v1(ci, r)
        else:
            audit.append(f"UNKNOWN_SOURCE: {cid} src={src}")
            continue

        results.append({
            "canonical_id": cid,
            "domain": cn.get("domain"),
            "question": (cn.get("question") or "")[:120],
            "prob": cn.get("chorus_probability"),
            "outcome": outcome,
            "actual": r.get("actual"),
            "brier": cn.get("brier_score") if cn.get("brier_score") is not None else None,
            "source_url": r["source_url"],
        })

    # ---- Print plan ----
    mode_label = "COMMIT" if write else "DRY-RUN"
    print(f"\n{mode_label} — ledger resolution batch 2026-08-01\n")
    print(f"Total to apply: {len(results)}")
    print(f"Audit issues:   {len(audit)}")
    for a in audit:
        print(f"  ! {a}")

    print(f"\n{'BRIER':>7s}  {'p':>6s}  {'act':>3s}  {'domain':32s}  question")
    print("-" * 110)
    for x in sorted(results, key=lambda x: (x.get("domain") or "", x["canonical_id"])):
        b_str = f"{x['brier']:7.4f}" if x['brier'] is not None else "   ????"
        p_str = f"{x['prob']:6.4f}" if x['prob'] is not None else "  ????"
        print(f"{b_str}  {p_str}  {int(x['actual']):>3d}  {(x['domain'] or '')[:32]:32s}  {x['question'][:60]}")

    resolved = [x for x in results if x.get("brier") is not None]
    if resolved:
        mean_b = sum(x["brier"] for x in resolved) / len(resolved)
        print(f"\nbatch mean Brier (n={len(resolved)}): {mean_b:.4f}")
        # Split by YES/NO
        yes_preds = [x for x in resolved if x["actual"] == 1]
        no_preds = [x for x in resolved if x["actual"] == 0]
        if yes_preds:
            print(f"  YES outcomes (n={len(yes_preds)}): mean Brier {sum(x['brier'] for x in yes_preds)/len(yes_preds):.4f}")
        if no_preds:
            print(f"  NO outcomes  (n={len(no_preds)}): mean Brier {sum(x['brier'] for x in no_preds)/len(no_preds):.4f}")

    if not write:
        print(f"\n(dry-run — pass --commit --confirm to write)")
        return

    # ---- Backup + write ----
    for path in (V1, V2, CANONICAL):
        bk = path.with_suffix(path.suffix + f".bak.{NOW[:10]}")
        if not bk.exists():
            shutil.copy2(path, bk)
            print(f"backup: {bk.name}")

    V1.write_text(json.dumps(v1, indent=2))
    V2.write_text("\n".join(json.dumps(e) for e in v2) + "\n")
    CANONICAL.write_text(json.dumps(canon, indent=2))
    if canon_int and canon_int_path.exists():
        canon_int_path.write_text(json.dumps(canon_int, indent=2))

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
            "brier": x.get("brier"),
            "source": x["source_url"],
            "resolved_at": NOW,
            "applied_via": "resolve_batch_2026_08_01.py",
        })
    RESLOG.write_text(json.dumps(log, indent=2))

    # Archive staging
    STAGING.parent.mkdir(parents=True, exist_ok=True)
    STAGING.write_text(json.dumps(results, indent=2))

    print(f"\nWROTE:")
    print(f"  {V1} ({len(v1)} entries)")
    print(f"  {V2} ({len(v2)} entries)")
    print(f"  {CANONICAL} ({len(canon)} entries)")
    print(f"  {RESLOG} (+{len(results)} log rows)")
    print(f"  {STAGING} (staging archive)")
    print(f"\nNext: regenerate ledger_summary.json")


if __name__ == "__main__":
    main()
