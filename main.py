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

# Import the shared MCP server instance.  Use an absolute import so
# that the module can be executed directly (``python main.py``) or via
# uv (``uv run main.py``) without relying on package-relative imports.
from server import mcp  # type: ignore


if __name__ == "__main__":
    mcp.run()