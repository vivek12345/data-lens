"""
Tag-based middleware for access control.

This middleware demonstrates:
- Custom middleware implementation in FastMCP
- Tag-based access control for tools
- Runtime tool inspection
- Error handling with ToolError
"""

from logging import getLogger

from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext

logger = getLogger(__name__)


class TagBasedMiddleware(Middleware):
    """
    Middleware that enforces tag-based access control on tools.

    Features:
    - Blocks tools marked with 'private' tag
    - Checks if tools are enabled
    - Can be extended to implement role-based access control (RBAC)

    Usage:
        mcp.add_middleware(TagBasedMiddleware())
    """

    def __init__(self):
        """Initialize the middleware."""
        super().__init__()
        logger.info("TagBasedMiddleware initialized")

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """
        Intercept tool calls to enforce access control.

        Args:
            context: Middleware context containing tool information
            call_next: Next middleware or tool handler in the chain

        Returns:
            Result from the tool or raises ToolError if access denied
        """
        if context.fastmcp_context:
            logger.info(f"Checking access for tool: {context.message.name}")

            try:
                # Get the tool object to check its metadata
                tool = await context.fastmcp_context.fastmcp.get_tool(
                    context.message.name
                )

                # Check if this tool has a "private" tag
                if "private" in tool.tags:
                    logger.warning(
                        f"Access denied: Tool '{tool.name}' is marked as private"
                    )
                    raise ToolError(
                        f"Access denied: Tool '{tool.name}' is private and requires authentication"
                    )

                # Check if tool is enabled
                if not tool.enabled:
                    logger.warning(f"Tool '{tool.name}' is currently disabled")
                    raise ToolError(f"Tool '{tool.name}' is currently disabled")

                logger.info(f"Access granted for tool: {tool.name} (tags: {tool.tags})")

            except ToolError:
                # Re-raise ToolErrors
                raise
            except Exception as e:
                # Log unexpected errors
                logger.error(f"Error in tag middleware: {e}")
                raise ToolError(f"Middleware error: {str(e)}")

        # Call the next middleware or the actual tool
        return await call_next(context)
