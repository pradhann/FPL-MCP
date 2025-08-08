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

# Use absolute imports rather than package-relative imports.  When this
# server is run via ``uv --directory`` or as a script, modules are
# imported from the top-level package (fpl_server).  Do not use
# leading dots for relative imports.
from utils import fpl_data  # type: ignore
from server import mcp  # type: ignore


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
        # Load player data with team names and positions.  This DataFrame
        # retains the ``element_type`` column (1–4 for GK, DEF, MID, FWD)
        # and converts ``selected_by_percent`` to float in
        # ``fpl_data.get_elements_df``.  We derive a price column
        # expressed in millions for easier filtering and display.
        df = fpl_data.get_elements_df()
        df["price_m"] = df["now_cost"] / 10.0
        # We'll present a useful subset of columns by default.
        # "element_type" is preserved so that callers can filter
        # numerically (1=GKP, 2=DEF, 3=MID, 4=FWD).  "position" holds
        # the string representation (GKP, DEF, MID, FWD).  Include
        # ``selected_by_percent`` for ownership queries.
        display_columns = [
            "id",
            "first_name",
            "second_name",
            "element_type",
            "position",
            "team_name",
            "price_m",
            "total_points",
            "minutes",
            "goals_scored",
            "assists",
            "yellow_cards",
            "red_cards",
            "selected_by_percent",
        ]
        # Ensure only available columns are selected (in case of API
        # changes).
        display_columns = [c for c in display_columns if c in df.columns]
    elif entity == "fixtures":
        # Load fixtures and map team IDs to names.  Rather than
        # merging and dropping the ``id`` column (which can cause
        # KeyError if ``id`` isn't present), use a mapping.
        df = fpl_data.get_fixtures_df()
        teams_df = fpl_data.get_teams_df()[["id", "name"]]
        team_map = dict(zip(teams_df["id"], teams_df["name"]))
        df["team_h_name"] = df["team_h"].map(team_map)
        df["team_a_name"] = df["team_a"].map(team_map)
        # Define default display columns.  Include the fixture id
        # (useful for debugging) and event (gameweek number).
        display_columns = [
            "id" if "id" in df.columns else None,
            "event" if "event" in df.columns else None,
            "kickoff_time" if "kickoff_time" in df.columns else None,
            "team_h_name",
            "team_a_name",
            "team_h_score" if "team_h_score" in df.columns else None,
            "team_a_score" if "team_a_score" in df.columns else None,
            "finished" if "finished" in df.columns else None,
        ]
        display_columns = [c for c in display_columns if c is not None]
    elif entity == "teams":
        df = fpl_data.get_teams_df()
        display_columns = [
            "id",
            "name",
            "short_name",
            "strength_attack_home" if "strength_attack_home" in df.columns else None,
            "strength_defence_home" if "strength_defence_home" in df.columns else None,
            "strength_attack_away" if "strength_attack_away" in df.columns else None,
            "strength_defence_away" if "strength_defence_away" in df.columns else None,
        ]
        display_columns = [c for c in display_columns if c is not None]
    else:
        raise ValueError(f"Unsupported entity: {entity}")

    # Validate filter keys before applying them.  Unknown keys
    # indicate either a mistake in the query or a missing column.  We
    # return a helpful error listing available fields.
    if filters:
        invalid = [col for col in filters if col not in df.columns]
        if invalid:
            available = ", ".join(sorted(df.columns))
            raise ValueError(
                f"Unknown filter field(s): {', '.join(invalid)}. Available fields: {available}"
            )
        df = _apply_filters(df, filters)

    # Validate sort column if provided
    if sort_by:
        if sort_by not in df.columns:
            available = ", ".join(sorted(df.columns))
            raise ValueError(
                f"Unknown sort field '{sort_by}'. Available fields: {available}"
            )
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

    # Select display columns in the defined order (if defined).  If
    # ``display_columns`` is not set (which should not happen), fall
    # back to all columns.
    if isinstance(locals().get("display_columns"), list) and display_columns:
        df = df[[col for col in display_columns if col in df.columns]]

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