"""
Entry point for running the FPL MCP server.

To start the server, run this module directly. It simply imports
the shared server instance from ``server.py`` and calls its
``run()`` method.  When running via Claude for Desktop, your
configuration should specify something akin to::

    "command": "python",
    "args": ["main.py"]

or use a tool like ``uv run`` if you have ``uv`` installed. The
server blocks until it is terminated by the client.
"""

from __future__ import annotations

from server import mcp


if __name__ == "__main__":
    mcp.run()
