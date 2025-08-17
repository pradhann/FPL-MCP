"""
Configure the FastMCP server instance.

This module creates a shared `FastMCP` server named ``fpl_mcp`` and
imports tool modules so that their decorated functions are
registered.  It adjusts ``sys.path`` at runtime to locate the
vendored MCP SDK (cloned under ``mcp_sdk/src`` at the repository
root).

You typically do not run this module directly. Instead, use
``python main.py`` which imports the server and calls ``mcp.run()``.
"""

from __future__ import annotations

import sys
from pathlib import Path


# -----------------------------------------------------------------------------
# Make the vendored `mcp` package importable.
# We assume the repository root contains a directory named `mcp_sdk/src`.

current_dir = Path(__file__).resolve().parent
repo_root = current_dir.parent
mcp_sdk_path = repo_root / "mcp_sdk" / "src"
if mcp_sdk_path.exists() and str(mcp_sdk_path) not in sys.path:
    sys.path.insert(0, str(mcp_sdk_path))

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore[attr-defined]
except ImportError as e:
    raise ImportError(
        "Failed to import FastMCP. Ensure that the `mcp_sdk` folder "
        "exists at the project root and contains the MCP SDK."
    ) from e


# Create the shared MCP server instance.
mcp = FastMCP("fpl_mcp")


# Import tools so that their decorators and prompts register functions
# with the server.  Use absolute imports rather than package-relative
# ones so that the code works when run from the project root.
# pylint: disable=unused-import
# Import tool modules so their decorated functions register with the server.
from tools import query_tools  # noqa: F401
from tools import team_tools  # noqa: F401
from tools import general_tools  # noqa: F401
from tools import prompts  # noqa: F401
from tools import video_tools  # noqa: F401
from tools import transcript_tools  # noqa: F401
from tools import expert_tools

# Authentication and transfer tools
# Authentication and transfer tools have been removed.  They were
# experimental and are no longer part of this project.  To avoid
# import errors, we do not import them here.

# The imported modules register their tools and prompts via
# decorators.  No further action is required here.
