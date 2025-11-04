"""
Main MCP Server Instance

This module creates and configures the single FastMCP instance used throughout
the application. All tools, resources, and prompts from other modules are
registered with this instance via registration functions.

Organization:
- Tools are defined in app/mcp/tools/ modules
- Resources are defined in app/mcp/resources/ modules
- Prompts are defined in app/mcp/prompts/ modules

Each module provides a registration function that accepts the mcp instance
and registers its functionality.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from data_lens.database.connection import DatabaseContext, DatabaseState
from data_lens.mcp.prompts import register_report_prompts
from data_lens.mcp.resources import register_database_resources
# Import and call registration functions (NO circular imports!)
from data_lens.mcp.tools import (register_elicit_tool, register_mysql_tools,
                                 register_progress_tool,
                                 register_visualization_tools)
from data_lens.utils.logger import get_logger

from .middleware import TagBasedMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def mcp_lifespan(app) -> AsyncIterator[DatabaseContext]:
    """
    Lifespan manager for FastMCP that provides DatabaseContext to tools.
    This supports two modes:
    1. HTTP mode: Reuses existing database pool from app.state (combined lifespan)
    2. stdio mode: Creates its own database connection (standalone mode for Claude Desktop)
    """
    logger.info("🚀 Starting combined lifespan...")

    # Initialize database state
    db_state = DatabaseState()
    try:
        await db_state.initialize()
        logger.info("✓ Database initialized for app")
        yield DatabaseContext(pool=db_state.pool)
    finally:
        logger.info("🛑 Shutting down combined lifespan...")
        await db_state.cleanup()
        logger.info("✓ Combined cleanup completed")


# Create the single FastMCP instance used throughout the application
mcp = FastMCP(
    name="MySQL Analytics Server",
    instructions=(
        "A powerful server for MySQL database analytics with SSH tunnel support. "
        "Use this server to execute read-only SQL queries, visualize data with graphs, "
        "and inspect database schemas securely."
    ),
    lifespan=mcp_lifespan,
)

# Add middleware
mcp.add_middleware(TagBasedMiddleware())

# Register all tools, resources, and prompts
register_mysql_tools(mcp)
register_visualization_tools(mcp)
register_elicit_tool(mcp)
register_progress_tool(mcp)
register_database_resources(mcp)
register_report_prompts(mcp)

logger.info("✓ All tools, resources, and prompts registered")
