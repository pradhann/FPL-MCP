"""
MCP tools for working with a specific FPL team.

These tools allow you to inspect the current or historical picks
for a given Fantasy Premier League team. To use them, you must
provide your own `TEAM_ID` below. The default value is set to
``4118472`` as provided by the user.

Note that the FPL API exposes some endpoints without requiring
authentication. However, certain information may be limited or
subject to rate limits. These tools make best‑effort queries and
format the results in a human‑readable manner.
"""

from __future__ import annotations

from typing import Dict, Any

import requests

# Absolute imports so that this module can be run from the project
# root using uv or python without a package context.  Avoid leading
# dots for relative imports.
from utils import fpl_data  # type: ignore
from server import mcp  # type: ignore

# Team ID to query. Update this value if you wish to inspect a different team.
TEAM_ID: int = 4118472


def _fetch_team_event_picks(team_id: int, gw: int) -> Dict[str, Any]:
    """Fetch the picks for a team in a given gameweek.

    Args:
        team_id: FPL entry/team identifier.
        gw: Gameweek number (1–38).

    Returns:
        JSON dictionary containing picks and chip usage.
    """
    endpoint = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gw}/picks/"
    resp = requests.get(endpoint)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def get_team_picks(gw: int) -> str:
    """Retrieve the squad picks for the configured team in a specific gameweek.

    Args:
        gw: The gameweek number (1 through 38). Use the current
            gameweek to see your latest picks.

    Returns:
        A formatted listing of players selected for that gameweek,
        including captaincy and multiplier information. The output
        includes each player's position, team, price and total
        points to aid in analysis.

    Example:

        ``get_team_picks(3)``

    ````
    Team picks for GW3:
    ============================================
    Position  Player               Team     Price   Pts  Mult  C/V
    ------------------------------------------------------------
    GK        Ederson             MCI      5.5    12    1      
    DEF       Alexander-Arnold    LIV      8.0    15    2      C
    ...
    ````
    """
    data = _fetch_team_event_picks(TEAM_ID, gw)
    picks = data.get("picks", [])
    # Load elements DataFrame to map ids to names and positions
    elements_df = fpl_data.get_elements_df()
    # Create mapping of element id to row for quick lookup
    elements_df = elements_df.set_index("id")

    # Build table rows
    rows = []
    for pick in picks:
        elem_id = pick.get("element")
        player = elements_df.loc.get(elem_id)
        if player is None:
            # Skip unknown IDs
            continue
        pos_short = player["position"]
        name = f"{player['first_name']} {player['second_name']}"
        team_name = player["team_name"]
        price_m = player["now_cost"] / 10.0
        points = player["total_points"]
        mult = pick.get("multiplier", 1)
        is_cap = "C" if pick.get("is_captain", False) else ("V" if pick.get("is_vice_captain", False) else "")
        rows.append({
            "Position": pos_short,
            "Player": name,
            "Team": team_name,
            "Price": price_m,
            "Pts": points,
            "Mult": mult,
            "C/V": is_cap,
        })
    if not rows:
        return f"No picks found for team {TEAM_ID} in gameweek {gw}."
    # Sort by position order: GK, DEF, MID, FWD then by multiplier descending
    order = {"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3}
    rows.sort(key=lambda r: (order.get(r["Position"], 99), -r["Mult"]))
    # Build header and table string
    header = f"Team picks for GW{gw} (team {TEAM_ID}):\n"
    header += "Position  Player                        Team               Price  Pts  Mult  C/V\n"
    header += "-----------------------------------------------------------------------------\n"
    lines = []
    for r in rows:
        lines.append(
            f"{r['Position']:<8} {r['Player']:<28} {r['Team']:<18} {r['Price']:<5.1f} {r['Pts']:<4} {r['Mult']:<4} {r['C/V']}"
        )
    return header + "\n".join(lines)