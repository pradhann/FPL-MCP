"""
General-purpose MCP tools for querying Fantasy Premier League data.

These tools expose players, fixtures and player history in a
flexible way. Rather than having a separate tool for each
query, you can specify the ``entity`` to query and supply
filters, sort options and limits.  Additional helper tools
summarise team performance and return a player's detailed
gameweek history.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from utils import fpl_data
from server import mcp


def _apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Internal helper to apply comparison filters to a DataFrame.

    Args:
        df: The DataFrame to filter.
        filters: Mapping of column names to either a raw value or
            a dictionary specifying an operator (``eq``, ``lt``,
            ``lte``, ``gt``, ``gte``, ``contains``).

    Returns:
        The filtered DataFrame.
    """
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
            df = df[df[col] == condition]
    return df


@mcp.tool()
def query_fpl_data(
    entity: str,
    filters: Dict[str, Any],
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    top_n: Optional[int] = 20,
) -> str:
    """Query various FPL entities (players, fixtures, teams).

    Args:
        entity: The name of the dataset to query. Supported values
            are ``players`` (default), ``fixtures`` and ``teams``.
        filters: A mapping from column names to filter conditions.
            Values can be either a raw value (equality) or a dict
            specifying an operator.  See below for supported
            operators.
        sort_by: Column name to sort by. If None, a sensible
            default is used: ``total_points`` for players and
            ``kickoff_time`` for fixtures.
        sort_order: "asc" or "desc".
        top_n: Maximum number of rows to return. Use None for all.

    Returns:
        A string containing a formatted table of the query
        results. Columns depend on the entity:

        * **players**: id, first_name, second_name, position,
          team_name, price_m, total_points, minutes,
          goals_scored, assists, yellow_cards, red_cards.
        * **fixtures**: event, kickoff_time, team_h_name,
          team_a_name, team_h_score, team_a_score, finished.
        * **teams**: id, name, short_name, strength, etc.

    Example::

        query_fpl_data(
            entity="players",
            filters={"position": {"eq": "DEF"}, "yellow_cards": {"gt": 3}},
            sort_by="total_points",
            sort_order="desc",
            top_n=10,
        )

        query_fpl_data(
            entity="fixtures",
            filters={"team_h_name": {"contains": "United"}, "finished": {"eq": False}},
            sort_by="kickoff_time",
            sort_order="asc",
            top_n=5,
        )

    Supported operators in the ``filters`` dict:

    * ``eq`` – equality (default if no operator is specified)
    * ``lt`` – less than (numeric)
    * ``lte`` – less than or equal (numeric)
    * ``gt`` – greater than (numeric)
    * ``gte`` – greater than or equal (numeric)
    * ``contains`` – case-insensitive substring search (strings)
    """
    entity = entity.lower()
    if entity == "players":
        df = fpl_data.get_elements_df()
        # Add price in millions
        df["price_m"] = df["now_cost"] / 10.0
        # Rename team_name for clarity
        df = df.rename(columns={"team_name": "team_name"})
        # Select relevant columns
        df = df[
            [
                "id",
                "first_name",
                "second_name",
                "position",
                "team_name",
                "price_m",
                "total_points",
                "minutes",
                "goals_scored",
                "assists",
                "yellow_cards",
                "red_cards",
            ]
        ]
    elif entity == "fixtures":
        df = fpl_data.get_fixtures_df()
        teams_df = fpl_data.get_teams_df()[["id", "name"]]
        # Map team IDs to names
        df = df.merge(teams_df, left_on="team_h", right_on="id", how="left").rename(
            columns={"name": "team_h_name"}
        ).drop(columns=["id"])
        df = df.merge(teams_df, left_on="team_a", right_on="id", how="left").rename(
            columns={"name": "team_a_name"}
        ).drop(columns=["id"])
        # Keep useful columns
        df = df[
            [
                "event",
                "kickoff_time",
                "team_h_name",
                "team_a_name",
                "team_h_score",
                "team_a_score",
                "finished",
            ]
        ]
    elif entity == "teams":
        df = fpl_data.get_teams_df()
        # Select a subset of useful columns
        df = df[["id", "name", "short_name", "strength_attack_home", "strength_defence_home", "strength_attack_away", "strength_defence_away"]]
    else:
        raise ValueError(f"Unsupported entity: {entity}")

    # Apply filters
    if filters:
        df = _apply_filters(df, filters)

    # Apply sorting
    if sort_by:
        df = df.sort_values(by=sort_by, ascending=(sort_order == "asc"))
    else:
        # Apply sensible default sorting
        if entity == "players" and "total_points" in df.columns:
            df = df.sort_values(by="total_points", ascending=False)
        elif entity == "fixtures" and "kickoff_time" in df.columns:
            df = df.sort_values(by="kickoff_time", ascending=True)

    # Limit rows
    if top_n is not None:
        df = df.head(top_n)

    # Convert datetime columns to strings for display
    for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M")

    return df.to_string(index=False)


@mcp.tool()
def get_team_summary(team: str, last_n_games: int = 5) -> str:
    """Summarise a team's recent performance over the last N completed games.

    Args:
        team: Team name or ID. The name is case-insensitive and can be
            partial (e.g. "United" will match Manchester United). If an
            integer is provided, it is treated as the team ID.
        last_n_games: Number of completed games to include in the
            summary.

    Returns:
        A multi-line string reporting total games played, wins, draws,
        losses, goals scored, goals conceded and points accumulated.
    """
    # Resolve team ID
    try:
        team_id = int(team)
    except Exception:
        team_id = fpl_data.get_team_id_by_name(str(team))
    if team_id is None:
        return f"Team '{team}' not found."
    summary = fpl_data.compute_team_summary(team_id, last_n_games=last_n_games)
    # Get team name
    teams_df = fpl_data.get_teams_df()
    team_row = teams_df.loc[teams_df["id"] == team_id]
    if not team_row.empty:
        team_name = team_row.iloc[0]["name"]
    else:
        team_name = str(team_id)
    return (
        f"Summary for {team_name} (last {summary['games']} completed games):\n"
        f"Wins: {summary['wins']}, Draws: {summary['draws']}, Losses: {summary['losses']}\n"
        f"Goals scored: {summary['goals_scored']}, Goals conceded: {summary['goals_conceded']}\n"
        f"Total points: {summary['points']}"
    )


@mcp.tool()
def get_player_history(player: str, last_n_games: Optional[int] = None) -> str:
    """Return a player's gameweek-by-gameweek history for the current season.

    Args:
        player: Player name or ID. The name is case-insensitive and can
            be partial. If an integer is provided, it is treated as
            the element ID.
        last_n_games: Number of most recent gameweeks to include. If
            None, all completed gameweeks are returned.

    Returns:
        A formatted table with columns: round (gameweek), opponent team,
        minutes, goals_scored, assists, total_points, goals_conceded,
        yellow_cards and red_cards.
    """
    # Resolve player ID
    try:
        player_id = int(player)
    except Exception:
        player_id = fpl_data.get_player_id_by_name(str(player))
    if player_id is None:
        return f"Player '{player}' not found."
    history_df = fpl_data.get_player_history_df(player_id)
    if history_df.empty or history_df.shape[0] == 0:
        return f"No gameweek history available for player '{player}'."
    # Optionally restrict to last N games (history is chronological)
    if last_n_games is not None and last_n_games > 0:
        history_df = history_df.tail(last_n_games)
    # Map opponent team ID to name
    teams_df = fpl_data.get_teams_df()[["id", "name"]]
    history_df = history_df.merge(teams_df, left_on="opponent_team", right_on="id", how="left").rename(
        columns={"name": "opponent_team_name"}
    ).drop(columns=["id"])
    # Some columns might not exist if season hasn't started; use what is available
    cols = []
    for col in [
        "round",
        "opponent_team_name",
        "minutes",
        "goals_scored",
        "assists",
        "total_points",
        "goals_conceded",
        "yellow_cards",
        "red_cards",
    ]:
        if col in history_df.columns:
            cols.append(col)
    if not cols:
        return f"No relevant statistics available for player '{player}'."
    display_df = history_df[cols]
    # Sort by round ascending if present
    if "round" in display_df.columns:
        display_df = display_df.sort_values(by="round")
    return display_df.to_string(index=False)