"""
MCP tools for querying Fantasy Premier League players.

This module defines a single tool, ``query_fpl_players``, which
exposes a flexible interface for filtering players by arbitrary
conditions. The LLM should construct the ``filters`` argument
according to the documented format.
"""

from __future__ import annotations

from typing import Dict, Any, Optional

from utils import fpl_data
from server import mcp


@mcp.tool()
def query_fpl_players(filters: Dict[str, Any], top_n: Optional[int] = 20) -> str:
    """Query Fantasy Premier League players.

    Args:
        filters: A mapping describing filter conditions for the
            player table. Each key should be the name of a column in
            the FPL bootstrap elements table (e.g. ``now_cost``,
            ``element_type``, ``team``, ``first_name``, ``second_name``,
            ``total_points``). Values can either be a single value
            (interpreted as an equality check) or a dictionary with a
            single key specifying a comparison operator. Supported
            operators are:

            - ``eq``: equality (e.g. ``{"now_cost": {"eq": 55}}``)
            - ``lt``: strictly less than (numbers only)
            - ``lte``: less than or equal to (numbers only)
            - ``gt``: strictly greater than (numbers only)
            - ``gte``: greater than or equal to (numbers only)
            - ``contains``: case‑insensitive substring search (for text
              columns like ``first_name`` or ``second_name``)

            For example, to find all midfielders (position code ``4``)
            costing less than £8.0m, you would supply:

            ``filters = {"element_type": {"eq": 4}, "now_cost": {"lt": 80}}``

            To search for players whose last name contains "Silva":

            ``filters = {"second_name": {"contains": "silva"}}``

        top_n: The maximum number of players to return, sorted by
            ``total_points`` descending.  Set to ``None`` to
            return all matching players.

    Returns:
        A table (as a string) of players matching the filters. Columns
        include ``id``, ``first_name``, ``second_name``, ``position``,
        ``team_name``, ``price_m`` (current price in millions),
        ``total_points``, ``minutes`` and ``selected_by_percent``.
    """
    return fpl_data.query_players(filters=filters, top_n=top_n)
