"""
MCP tools for database operations.

This package contains modules with tool registration functions:
- mysql: Database query and schema inspection tools
- visualization: Data visualization and charting tools

Each module provides a registration function that accepts the MCP instance
and registers its tools.
"""

from .elicit import register_elicit_tool
from .mysql import register_mysql_tools
from .progress_tool import register_progress_tool
from .visualization import register_visualization_tools

__all__ = [
    "register_mysql_tools",
    "register_visualization_tools",
    "register_elicit_tool",
    "register_progress_tool",
]
