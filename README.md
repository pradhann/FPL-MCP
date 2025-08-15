# Fantasy Premier League MCP Server

This project provides a simple Model Context Protocol (MCP) server that
exposes a handful of tools for exploring Fantasy Premier League (FPL)
data. It follows the structure laid out in the tutorial blog, but
substitutes the original CSV/Parquet examples for live FPL API
endpoints. The goal is to make it easy to query player and team data
using natural language via Claude for Desktop or any other MCP client.

---

## Usage

To run the server locally:

1. **Run the server**

   ```bash
   python main.py
   ```

2. **Claude Desktop configuration**
   Add the following to your Claude configuration file (`claude_desktop_config.json` or equivalent), replacing `/path/to/fpl_server` with the absolute path to your local `fpl_server` directory:

   ```json
   {
     "mcpServers": {
       "fpl-server": {
         "command": "python3",
         "args": [
           "/path/to/fpl_server/main.py"
         ],
         "env": {
           "PYTHONPATH": "/path/to/fpl_server"
         }
       }
     }
   }
   ```

3. **Check in Claude Desktop**
   Restart Claude Desktop and verify that the `fpl-server` MCP server appears in the connected servers list.

## Folder Layout

```
fpl_server/
│
├── data/             # Local cache of FPL API responses
│
├── tools/            # MCP tool definitions
│   ├── __init__.py
│   ├── query_tools.py      # Legacy player-only query tool (v1)
│   ├── general_tools.py    # General querying of players, fixtures, teams; team/player summaries
│   └── team_tools.py       # Team picks tool (manager-specific)
│
├── utils/            # Reusable logic for data fetching and querying
│   ├── __init__.py
│   └── fpl_data.py
│
├── server.py         # Defines the shared FastMCP server instance
├── main.py           # Entry point to run the server
└── README.md         # This file
```

### Key Concepts

* **Data Fetching and Caching**: The module `utils/fpl_data.py` wraps
  calls to the Fantasy Premier League API. It downloads the
  bootstrap static dataset on demand and caches it to the `data/`
  folder. Other helper functions provide easy access to players,
  teams and positions as Pandas DataFrames.

* **General Query Tools**: Version 2 introduces a more flexible tool
  `query_fpl_data` (found in ``tools/general_tools.py``).  It
  accepts an ``entity`` parameter (``players``, ``fixtures`` or
  ``teams``) plus a dictionary of filters, optional sort criteria
  and a limit.  This enables complex queries such as "find
  defenders with the most yellow cards and at least 50 points",
  "list upcoming fixtures for United", or "rank teams by home
  attacking strength" without defining a separate tool for each
  question.  The original `query_fpl_players` remains for
  backwards compatibility.

* **Team & Player History Tools**: Additional tools in
  ``general_tools.py`` summarise a team's recent performance
  (`get_team_summary`) and provide a player's gameweek-by-gameweek
  history (`get_player_history`).  These build on the fixtures and
  element-summary endpoints to deliver ready-made summaries.  A
  separate team picks tool (`get_team_picks` in ``team_tools.py``)
  exposes your chosen squad for a specific gameweek.

* **FastMCP**: The server is built using `FastMCP` from the
  `mcp` SDK. Since external package installation is unavailable in
  this environment, the `mcp` library is vendored into the
  repository via a shallow clone of the official SDK. See
  `mcp_sdk/` at the project root.

To run the server locally, add the absolute path to this directory
in your Claude configuration and start the server using either
`python main.py` or, if you are using [`uv`](https://github.com/astral-sh/uv),
`uv run main.py`.  The Claude desktop configuration should specify
the `fpl_server` entry as shown in your JSON snippet.  Ensure you
have internet access so that the FPL API requests succeed.
