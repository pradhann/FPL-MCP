"""
Reusable prompts to guide the language model when using the FPL MCP tools.

These prompts explain how to construct filter dictionaries, list valid
fields for each entity, and highlight common mistakes (such as using
string values for numeric comparisons).  They are registered with
FastMCP via the ``@mcp.prompt()`` decorator.  When queried,
Claude can consult this guidance before attempting to call a tool.
"""

from __future__ import annotations

# Import the shared MCP server.  Absolute import ensures this works
# both when run as a package (python -m fpl_server.tools.prompts) and
# as a script (python tools/prompts.py) from the fpl_server directory.
from server import mcp  # type: ignore


@mcp.prompt()
def fpl_query_guidance() -> str:
    """
    Guidance on using FPL query tools.

    This prompt should be read by the language model before making a
    call to ``query_fpl_data`` or ``get_team_summary`` or
    ``get_player_history``.  It provides a quick reference for
    constructing filter dictionaries and choosing valid field names.

    For ``query_fpl_data``:

    - The ``entity`` parameter must be one of ``"players"``,
      ``"fixtures"`` or ``"teams"``.  This selects which dataset
      to query.

    - For **players**, you can filter on any of these fields (case
      sensitive): ``id``, ``first_name``, ``second_name``,
      ``element_type`` (1=GKP, 2=DEF, 3=MID, 4=FWD), ``position``
      ("GKP", "DEF", "MID", "FWD"), ``team_name``, ``price_m`` (float
      cost in millions), ``total_points``, ``minutes``, ``goals_scored``,
      ``assists``, ``yellow_cards``, ``red_cards``, and
      ``selected_by_percent`` (float).  Use numeric comparison
      operators (e.g. ``{"gte": 100}``) for numeric fields and
      ``{"contains": "united"}`` for substring matches on strings.

    - For **fixtures**, valid fields include ``id`` (fixture ID),
      ``event`` (gameweek number), ``kickoff_time`` (date/time),
      ``team_h_name``, ``team_a_name``, ``team_h_score``,
      ``team_a_score`` and ``finished`` (True/False).  To find
      upcoming fixtures, filter on ``{"finished": {"eq": False}}``.
      Use ``contains`` on ``team_h_name`` or ``team_a_name`` to
      match team names.

    - For **teams**, you can filter on ``id``, ``name``,
      ``short_name``, ``strength_attack_home``, ``strength_defence_home``,
      ``strength_attack_away`` and ``strength_defence_away``.

    - The ``filters`` argument should be a dictionary mapping field
      names to either a single value (equality) or a dictionary with
      a single key specifying an operator: ``eq``, ``lt``, ``lte``,
      ``gt``, ``gte`` or ``contains``.  Numeric comparisons (``lt``,
      ``gt``, etc.) only work on numeric fields.

    - ``sort_by`` must be a valid field name and ``sort_order`` must
      be either ``"asc"`` or ``"desc"``.  If omitted, sensible
      defaults are used (players sorted by ``total_points`` and
      fixtures sorted by ``kickoff_time``).

    For ``get_team_summary`` and ``get_player_history``, supply
    either a team or player name (partial matching is allowed) or
    their numeric IDs.  ``last_n_games`` limits the number of
    completed gameweeks to consider.

    Examples:

    .. code-block:: json

        {
          "entity": "players",
          "filters": {
            "position": {"eq": "DEF"},
            "yellow_cards": {"gte": 5},
            "total_points": {"gte": 100}
          },
          "sort_by": "total_points",
          "sort_order": "desc",
          "top_n": 10
        }

        {
          "entity": "fixtures",
          "filters": {
            "team_h_name": {"contains": "Arsenal"},
            "finished": {"eq": false}
          },
          "sort_by": "kickoff_time",
          "sort_order": "asc",
          "top_n": 5
        }

    """
    return (
        "Use `query_fpl_data` with the appropriate `entity` ('players', 'fixtures' or 'teams') and "
        "supply a `filters` dictionary mapping field names to conditions. Valid operators are eq, lt, "
        "lte, gt, gte and contains. Fields for players include id, first_name, second_name, "
        "element_type (1=GKP, 2=DEF, 3=MID, 4=FWD), position (GKP, DEF, MID, FWD), team_name, price_m, "
        "total_points, minutes, goals_scored, assists, yellow_cards, red_cards and selected_by_percent. "
        "Fields for fixtures include id, event, kickoff_time, team_h_name, team_a_name, team_h_score, "
        "team_a_score and finished. Fields for teams include id, name, short_name and strength_* fields. "
        "Ensure numeric comparisons use numbers (e.g. 25.0 for selected_by_percent)."
    )