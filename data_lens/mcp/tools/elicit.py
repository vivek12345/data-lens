"""
MCP tool for eliciting information from the user.

This module demonstrates:
- @mcp.tool decorator usage
- Context injection for user information
- Structured error handling
"""

from fastmcp import Context, FastMCP
from pydantic import BaseModel


class UserInfo(BaseModel):
    name: str
    age: int


def register_elicit_tool(mcp: FastMCP):
    """Register elicitation tool with the MCP instance."""

    @mcp.tool(
        name="collect_user_info",
        description="Collect user information through interactive prompts.",
        tags={"user-info"},
        meta={"version": "1.0", "author": "engineering-team"},
    )
    async def collect_user_info(ctx: Context) -> str:
        """Collect user information through interactive prompts."""
        result = await ctx.elicit(
            message="Please provide your information", response_type=UserInfo
        )

        if result.action == "accept":
            user = result.data
            return f"Hello {user.name}, you are {user.age} years old"
        elif result.action == "decline":
            return "Information not provided"
        else:  # cancel
            return "Operation cancelled"
