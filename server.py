#!/usr/bin/env python3
"""
FastMCP Data Lens Server with SSH Tunnel Support

This server demonstrates all major FastMCP features:
1. Resources: Expose database information via URIs
2. Tools: Execute queries, inspect schema, create visualizations
3. Prompts: Generate report and query templates
4. Lifespan Management: Handle database connections and SSH tunnels
5. Middleware: Tag-based access control
6. Context: Share state across requests
7. Modular Organization: Tools, resources, and prompts organized by feature

Features:
- SSH tunnel support for secure remote connections
- Connection pooling for performance
- Read-only query enforcement for security
- Data visualization with matplotlib
- Comprehensive error handling and logging
- Clean, modular architecture with single MCP instance
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import uvicorn

# Import the main MCP instance (all tools/resources/prompts are auto-registered)
from data_lens.mcp.mcp import mcp, auth_provider
from data_lens.config import settings
from data_lens.database import DatabaseState, DatabaseContext
from data_lens.utils.logger import get_logger, setup_logging

from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from starlette.applications import Starlette
from starlette.routing import Mount

# Configure logging with our custom logger
setup_logging()
logger = get_logger(__name__)

MCP_PATH = "/mcp"
# Define CORS middleware for HTTP mode
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=[
            "mcp-protocol-version",
            "mcp-session-id",
            "Authorization",
            "Content-Type",
        ],
        expose_headers=["mcp-session-id"],
    )
]

# Create ASGI application for MCP
mcp_app = mcp.http_app(middleware=middleware, path=MCP_PATH)

# Define MCP path and get well-known auth routes
if auth_provider:
    well_known_routes = auth_provider.get_well_known_routes(mcp_path=MCP_PATH)
else:
    well_known_routes = []

app = Starlette(
    routes=[
        *well_known_routes,  # Auth well-known routes (/.well-known/*, /auth/*)
        Mount("/", app=mcp_app),
        # Add other routes as needed
    ],
    lifespan=mcp_app.lifespan,
)

def main():
    """
    Main entry point for the server.
    
    Supports two modes:
    1. Claude Desktop (stdio): MCP native protocol
    2. HTTP Server: REST API for other clients
    """
    if settings.TRANSPORT_MODE == "stdio":
        # Run in stdio mode for Claude Desktop
        logger.info("Running in STDIO mode for Claude Desktop")
        mcp.run()
    elif settings.TRANSPORT_MODE == "http":
        # Run as HTTP server
        logger.info(f"Running HTTP server on {settings.SERVER_HOST}:{settings.SERVER_PORT}")
        uvicorn.run(
            app,
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT
        )


if __name__ == "__main__":
    main()

