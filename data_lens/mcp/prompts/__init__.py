"""
MCP prompts for common database tasks.

This package contains modules with prompt registration functions.
Each module provides a registration function that accepts the MCP instance
and registers its prompts.
"""

from .report_prompts import register_report_prompts

__all__ = ["register_report_prompts"]
