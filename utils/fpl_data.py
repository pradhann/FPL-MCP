"""
Utility functions for fetching and querying Fantasy Premier League data.

This module encapsulates calls to the public FPL API and
provides Pandas DataFrames representing players, teams and
positions. It also implements a simple query mechanism that
allows filtering and sorting the player table based on
user-supplied conditions.

Because this environment does not have access to PyPI, the MCP
SDK is vendored into the repository.  See README.md for details.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests


# Base URL for the Fantasy Premier League API
FPL_BASE_URL = "https://fantasy.premierleague.com/api"

# Directory where cached data lives
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _download_json(endpoint: str) -> Dict[str, Any]:
    """Download JSON data from the given FPL API endpoint.

    Args:
        endpoint: Path relative to the API base, e.g.
            "/bootstrap-static/".

    Returns:
        The decoded JSON object.
    """
    url = FPL_BASE_URL + endpoint
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_bootstrap_data(force_refresh: bool = False) -> Dict[str, Any]:
    """Retrieve the FPL bootstrap static dataset.

    The bootstrap data contains the core tables used by the FPL
    site: players (elements), teams, positions (element_types),
    events, etc. To speed up repeated queries, this function caches
    the response on disk.

    Args:
        force_refresh: If True, always download fresh data from
            the API. Otherwise, use the cached file if present.

    Returns:
        A dictionary containing the bootstrap data.
    """
    cache_path = DATA_DIR / "bootstrap_static.json"
    if not force_refresh and cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    data = _download_json("/bootstrap-static/")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    # Additionally cache individual top-level keys for convenience
    for key, value in data.items():
        # Skip simple numeric keys or None
        filename = f"{key}.json"
        path = DATA_DIR / filename
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(value, f)
        except Exception:
            # Some values may not be serializable (e.g. None) – ignore
            pass
    return data


def get_elements_df(force_refresh: bool = False) -> pd.DataFrame:
    """Return a DataFrame containing all players (elements).

    The resulting DataFrame includes a few extra columns mapping
    numeric IDs to human-friendly names (team_name and position).

    Args:
        force_refresh: If True, bypass the cache and fetch fresh
            bootstrap data.

    Returns:
        A Pandas DataFrame with player information.
    """
    data = get_bootstrap_data(force_refresh=force_refresh)
    elements = pd.DataFrame(data["elements"])
    teams_df = pd.DataFrame(data["teams"])[["id", "name"]].rename(
        columns={"id": "team", "name": "team_name"}
    )
    positions_df = pd.DataFrame(data["element_types"])[
        ["id", "singular_name_short"]
    ].rename(columns={"id": "element_type", "singular_name_short": "position"})
    # Merge to add team_name and position
    elements = elements.merge(teams_df, on="team", how="left")
    elements = elements.merge(positions_df, on="element_type", how="left")
    return elements


def get_teams_df(force_refresh: bool = False) -> pd.DataFrame:
    """Return a DataFrame of teams.

    Args:
        force_refresh: If True, fetch fresh bootstrap data.

    Returns:
        DataFrame with id, name, short_name and other team info.
    """
    data = get_bootstrap_data(force_refresh=force_refresh)
    return pd.DataFrame(data["teams"])


def get_element_types_df(force_refresh: bool = False) -> pd.DataFrame:
    """Return a DataFrame of element types (positions).

    Args:
        force_refresh: If True, fetch fresh bootstrap data.

    Returns:
        DataFrame with id, singular_name_short and other fields.
    """
    data = get_bootstrap_data(force_refresh=force_refresh)
    return pd.DataFrame(data["element_types"])


def get_player_detail(player_id: int) -> Dict[str, Any]:
    """Fetch detailed statistics for a single player.

    Args:
        player_id: The element ID of the player.

    Returns:
        A JSON dictionary representing the player's history and
        upcoming fixtures.
    """
    endpoint = f"/element-summary/{player_id}/"
    return _download_json(endpoint)

def get_fixtures_df(force_refresh: bool = False) -> pd.DataFrame:
    """Return a DataFrame containing all fixtures for the season.

    The returned DataFrame includes the home and away team IDs, the
    final scores (if finished), and the kickoff time.  To speed up
    repeated queries the raw JSON is cached in the ``data`` folder.

    Args:
        force_refresh: If True, download fresh fixtures data even if
            a cache file exists.

    Returns:
        A Pandas DataFrame with columns such as ``id``, ``event``,
        ``kickoff_time``, ``team_h``, ``team_h_score``, ``team_a``,
        ``team_a_score``, and ``finished``.
    """
    cache_path = DATA_DIR / "fixtures.json"
    if not force_refresh and cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = _download_json("/fixtures/")
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    # Convert to DataFrame
    df = pd.DataFrame(data)
    # Ensure kickoff_time is datetime for sorting; errors='coerce' handles None
    if "kickoff_time" in df.columns:
        df["kickoff_time"] = pd.to_datetime(df["kickoff_time"], errors="coerce")
    return df


def get_player_history_df(player_id: int) -> pd.DataFrame:
    """Return a DataFrame of a player's gameweek history for the current season.

    This pulls the ``history`` field from ``element-summary/{player_id}/``
    and returns it as a DataFrame.  Each row represents a single
    gameweek with stats such as goals, assists, minutes, yellow
    cards and total points.

    Args:
        player_id: The element ID of the player.

    Returns:
        A DataFrame with columns including ``round``, ``minutes``,
        ``goals_scored``, ``assists``, ``yellow_cards``,
        ``red_cards``, ``total_points``, ``goals_conceded``, etc.
    """
    data = get_player_detail(player_id)
    history = data.get("history", [])
    df = pd.DataFrame(history)
    return df


def get_team_id_by_name(team_name: str) -> Optional[int]:
    """Return the team ID corresponding to a case-insensitive team name.

    Args:
        team_name: Team name (e.g. "Manchester United" or "MAN UTD").

    Returns:
        The team ID if found, otherwise None.
    """
    teams = get_teams_df()
    # Normalize names: remove punctuation and casefold
    normalized = team_name.strip().casefold()
    # Attempt exact match on full name or short name
    for _, row in teams.iterrows():
        if row["name"].casefold() == normalized or row.get("short_name", "").casefold() == normalized:
            return int(row["id"])
    # Fallback to partial match: return the first team whose name contains the query
    for _, row in teams.iterrows():
        if normalized in row["name"].casefold() or normalized in row.get("short_name", "").casefold():
            return int(row["id"])
    return None


def get_player_id_by_name(name: str) -> Optional[int]:
    """Return the element ID corresponding to a player's full or partial name.

    The search is case-insensitive and matches either the player's
    first_name or second_name, or the combination of both.

    Args:
        name: Player name (full or partial).

    Returns:
        The player ID if found, otherwise None.
    """
    df = get_elements_df()
    name = name.strip().casefold()
    # Try exact match on full name
    for _, row in df.iterrows():
        full = f"{row['first_name']} {row['second_name']}".casefold()
        if full == name:
            return int(row["id"])
    # Try partial match on any name component
    for _, row in df.iterrows():
        if name in row["first_name"].casefold() or name in row["second_name"].casefold():
            return int(row["id"])
    return None


def compute_team_summary(team: int, last_n_games: int = 5) -> Dict[str, Any]:
    """Compute a summary of a team's recent performance.

    This examines completed fixtures involving the specified team and
    returns aggregate statistics for the most recent ``last_n_games``.

    Args:
        team: Team ID.
        last_n_games: Number of completed games to include.

    Returns:
        A dictionary with keys ``games``, ``wins``, ``draws``, ``losses``,
        ``goals_scored``, ``goals_conceded`` and ``points``. If the
        team has not played any completed games, the dictionary will
        contain zeros.
    """
    fixtures = get_fixtures_df()
    # Filter completed fixtures involving this team
    mask = (
        fixtures["finished"].fillna(False).astype(bool)
        & ((fixtures["team_h"] == team) | (fixtures["team_a"] == team))
    )
    team_fixtures = fixtures[mask].copy()
    # Sort by kickoff_time descending (most recent first)
    if "kickoff_time" in team_fixtures.columns:
        team_fixtures.sort_values(by="kickoff_time", ascending=False, inplace=True)
    else:
        # fallback to event id if no kickoff_time
        team_fixtures.sort_values(by="event", ascending=False, inplace=True)
    # Take last N games
    team_fixtures = team_fixtures.head(last_n_games)
    summary = {
        "games": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_scored": 0,
        "goals_conceded": 0,
        "points": 0,
    }
    for _, row in team_fixtures.iterrows():
        summary["games"] += 1
        if row["team_h"] == team:
            goals_for, goals_against = row.get("team_h_score", 0), row.get("team_a_score", 0)
        else:
            goals_for, goals_against = row.get("team_a_score", 0), row.get("team_h_score", 0)
        summary["goals_scored"] += int(goals_for or 0)
        summary["goals_conceded"] += int(goals_against or 0)
        # Determine result
        if goals_for > goals_against:
            summary["wins"] += 1
            summary["points"] += 3
        elif goals_for == goals_against:
            summary["draws"] += 1
            summary["points"] += 1
        else:
            summary["losses"] += 1
    return summary


def query_players(
    filters: Dict[str, Any],
    top_n: Optional[int] = 20,
    force_refresh: bool = False,
) -> str:
    """Return a formatted table of players matching the provided filters.

    This function provides a thin query layer over the FPL players
    DataFrame. Filters can be specified as equality conditions or
    comparison operations. The available comparison operators are:

    - ``eq``: equal to (the default if only a raw value is supplied)
    - ``lt``: strictly less than
    - ``lte``: less than or equal to
    - ``gt``: strictly greater than
    - ``gte``: greater than or equal to
    - ``contains``: case‐insensitive substring match (for text columns)

    Examples::

        # Players costing less than £8.0m (cost is stored in tenths)
        filters = {"now_cost": {"lt": 80}}

        # Midfielders (position code 4) from team id 1 with at least 100 total points
        filters = {
            "element_type": {"eq": 4},
            "team": {"eq": 1},
            "total_points": {"gte": 100},
        }

        # Players whose second_name contains "Silva"
        filters = {"second_name": {"contains": "silva"}}

    Args:
        filters: Mapping of column names to either a single value
            (interpreted as equality) or a dictionary specifying a
            comparison operator.
        top_n: Limit the number of players returned. If None,
            return all matching rows.
        force_refresh: If True, refresh the bootstrap cache before
            querying.

    Returns:
        A string containing the filtered players formatted as a
        table. Columns include ``id``, ``first_name``, ``second_name``,
        ``position``, ``team_name``, ``now_cost`` (price in tenths of
        millions), ``total_points``, ``minutes`` and
        ``selected_by_percent``.
    """
    df = get_elements_df(force_refresh=force_refresh)
    # Apply filters
    for col, condition in filters.items():
        if isinstance(condition, dict):
            for op, value in condition.items():
                if op == "eq":
                    df = df[df[col] == value]
                elif op == "lt":
                    df = df[df[col] < value]
                elif op == "lte":
                    df = df[df[col] <= value]
                elif op == "gt":
                    df = df[df[col] > value]
                elif op == "gte":
                    df = df[df[col] >= value]
                elif op == "contains":
                    df = df[df[col].astype(str).str.contains(str(value), case=False, na=False)]
                else:
                    raise ValueError(f"Unsupported operator: {op}")
        else:
            # Equality check
            df = df[df[col] == condition]

    # Sort by total_points descending then by now_cost ascending
    if "total_points" in df.columns:
        df = df.sort_values(by=["total_points", "now_cost"], ascending=[False, True])

    if top_n is not None:
        df = df.head(top_n)

    # Select and rename columns for display
    display_columns = [
        "id",
        "first_name",
        "second_name",
        "position",
        "team_name",
        "now_cost",
        "total_points",
        "minutes",
        "selected_by_percent",
    ]
    # Some older seasons may not have selected_by_percent; guard
    cols_available = [c for c in display_columns if c in df.columns]
    display_df = df[cols_available].copy()
    # Convert cost to £m for readability
    if "now_cost" in display_df.columns:
        display_df.loc[:, "price_m"] = display_df["now_cost"] / 10.0
        display_df.drop(columns=["now_cost"], inplace=True)
        # Move price_m after team_name
        cols = [
            "id",
            "first_name",
            "second_name",
            "position",
            "team_name",
            "price_m",
        ] + [c for c in display_df.columns if c not in {"id", "first_name", "second_name", "position", "team_name", "price_m"}]
        display_df = display_df[cols]

    return display_df.to_string(index=False)