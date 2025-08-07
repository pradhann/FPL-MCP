# Fantasy Premier League MCP Server

This project provides a simple Model Context Protocol (MCP) server that
exposes a handful of tools for exploring Fantasy Premier League (FPL)
data. It follows the structure laid out in the tutorial blog, but
substitutes the original CSV/Parquet examples for live FPL API
endpoints. The goal is to make it easy to query player and team data
using natural language via Claude for Desktop or any other MCP client.

## Folder Layout

```
mix_server/
│
├── data/             # Local cache of FPL API responses
│
├── tools/            # MCP tool definitions
│   ├── __init__.py
│   ├── query_tools.py    # General player‐query tool
│   └── team_tools.py     # Team/fixture tools
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

* **General Query Tool**: The tool `query_fpl_players` accepts a
  flexible dictionary of filter conditions and returns a formatted
  table of players.  The supported comparison operators are
  documented in the function docstring so the LLM can construct
  appropriate arguments.

* **Team Tools**: A separate tool provides access to user‑specific
  information such as team picks for a given gameweek. You can
  configure your own `TEAM_ID` in `tools/team_tools.py`.

* **FastMCP**: The server is built using `FastMCP` from the
  `mcp` SDK. Since external package installation is unavailable in
  this environment, the `mcp` library is vendored into the
  repository via a shallow clone of the official SDK. See
  `mcp_sdk/` at the project root.

To run the server locally, add the absolute path to this directory
in your Claude configuration and start the server using `python
main.py`.  Ensure you have internet access so that the FPL API
requests succeed.