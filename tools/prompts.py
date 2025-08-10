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


@mcp.prompt()
def video_summary_guidance() -> str:
    """
    Guidance for summarising FPL YouTube videos.

    This prompt tells the language model how and when to use the
    ``summarise_fpl_youtube`` tool.  When a user provides a YouTube
    link to a Fantasy Premier League podcast, preview or analysis
    video and asks for a summary, recommended players or insights,
    call the ``summarise_fpl_youtube`` tool with the ``url``
    parameter set to the full video URL.

    The tool returns a dictionary with four keys:

    - ``summary`` (str): A concise overall summary (about 600
      characters) covering the main talking points.  It prioritises
      sentences containing FPL keywords such as player names,
      captaincy, fixtures and rotation.

    - ``players`` (list): Up to ten of the most frequently
      mentioned players.  Each entry has ``player_name`` and
      ``reasoning`` fields.  Reasoning combines transcript lines
      mentioning price, minutes, rotation, fixtures, etc., and
      includes the player's FPL price and position.

    - ``main_points`` (list): A list of broader topics discussed
      during the video (e.g. "Captaincy", "Differentials", "Fixtures
      Analysis").  Each entry has ``topic`` and ``summary`` fields
      summarising the key points from the transcript.

    - ``video_id`` (str): The YouTube video ID for reference.

    Example call:

    .. code-block:: json

        {
          "url": "https://www.youtube.com/watch?v=DFlm3_EIbko"
        }

    You generally do not need to present the ``video_id`` to the
    user unless they explicitly ask for it.  Use ``summary`` and
    ``main_points`` to answer high-level questions about the video's
    content, and use ``players`` to provide actionable
    recommendations or insights.
    """
    return (
        "When given a YouTube link to an FPL-related podcast or video and asked to summarise or "
        "extract recommendations, use the `summarise_fpl_youtube` tool. Pass the full URL in the "
        "`url` parameter. The tool returns a concise overall 'summary' of the video, a list of up "
        "to ten recommended players with reasoning (including their price and position), and a list "
        "of broader 'main_points' topics with brief summaries. It also returns the video ID for reference."
    )


@mcp.prompt()
def transcript_summary_guidance() -> str:
    """
    Guidance on summarising raw YouTube transcripts for FPL analysis.

    When you call ``fetch_youtube_transcript`` with a YouTube URL,
    you'll receive a raw transcript as plain text.  This transcript
    likely contains filler words (e.g. "uh", "you know"), greetings
    and irrelevant chatter.  To extract actionable information for
    Fantasy Premier League (FPL), follow these steps:

    1. **Clean the text**: Ignore or remove obvious filler phrases and
       pleasantries.  Focus on sentences that mention player names,
       prices, positions, fixtures, minutes, rotation, captaincy,
       differentials, chip strategies (wildcard, bench boost, free hit)
       and other FPL‑relevant topics.

    2. **Identify players**: Cross‑reference names in the transcript
       against the list of Premier League players.  For each player
       discussed, note why they were mentioned (e.g. "cheap enabler",
       "minutes risk", "captaincy option", "great upcoming fixtures").

    3. **Extract themes**: Group the discussion into high‑level topics
       such as Captaincy, Fixtures Analysis, Differentials, Rotation,
       Chip Strategy, Goalkeepers, etc.  Summarise the key points
       raised under each theme in one or two sentences.

    4. **Compose a summary**: Write a short paragraph (3–5 sentences)
       that captures the overall narrative of the video.  Mention the
       main themes and the standout recommendations without going into
       exhaustive detail.

    5. **Answer questions**: If the user asks specific questions
       about the video (e.g. "Who did they recommend as captain?"),
       search the transcript for relevant lines and summarise those
       answers using the context you extracted.

    By following this guidance, you can turn a raw transcript into
    meaningful FPL insights that include recommended players, their
    rationale (price, minutes, fixtures, etc.), and high‑level
    strategic advice.
    """
    return "To summarise a raw YouTube transcript for FPL, ignore filler and focus on lines that mention players, prices, minutes, rotation, fixtures, captaincy, differentials or chip strategies.  Extract the players mentioned and note why they were discussed.  Group the discussion into themes such as Captaincy, Fixtures Analysis, Differentials, Rotation and Chip Strategy, and summarise each in one or two sentences.  Finally write a concise paragraph capturing the overall narrative of the video.  Use the transcript context to answer follow‑up questions about recommendations or strategies."
