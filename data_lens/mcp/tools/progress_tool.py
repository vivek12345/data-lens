"""
MCP tool for reporting progress.

This module demonstrates:
- @mcp.tool decorator usage
- Context injection for progress reporting
- Structured error handling
"""

from typing import Any

from fastmcp import Context, FastMCP


def register_progress_tool(mcp: FastMCP):
    """Register progress reporting tool with the MCP instance."""

    @mcp.tool(
        name="process_data",
        description="Process data from a resource with progress reporting.",
        tags={"data-processing"},
        meta={"version": "1.0", "author": "engineering-team"},
    )
    async def process_data(data_uri: str, ctx: Context) -> dict[str, Any]:
        """Process data from a resource with progress reporting."""
        await ctx.info(f"Processing data from {data_uri}")

        # Read a resource
        resource = await ctx.read_resource(data_uri)
        data = resource[0].content if resource else ""

        # Report progress
        await ctx.report_progress(progress=50, total=100)

        # Example request to the client's LLM for help
        # Try to use ctx.sample, but fall back to a simple summary if not available
        try:
            summary = await ctx.sample(f"Summarize this in 10 words: {data[:200]}")
        except Exception as e:
            ctx.error(f"ctx.sample() not available: {e}")
            # Create a simple summary instead
            preview = data[:200].strip()
            line_count = data.count("\n")
            summary = f"Data preview: {preview[:50]}... ({line_count} lines)"

        await ctx.report_progress(progress=100, total=100)
        return {
            "length": len(data),
            "summary": summary,
            "preview": data[:500] if len(data) > 500 else data,
        }
