"""
MCP resources for database information.

This package contains modules with resource registration functions.
Each module provides a registration function that accepts the MCP instance
and registers its resources.
"""

from .database_resources import register_database_resources

__all__ = ["register_database_resources"]
