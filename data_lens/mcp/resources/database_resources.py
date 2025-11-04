"""
MCP resources for exposing database information.

This module demonstrates:
- @mcp.resource decorator usage
- URI-based resource naming
- MIME type specification
- Context access for database operations
- Resource metadata with tags
"""

from fastmcp import Context, FastMCP
from mysql.connector import Error

from data_lens.config import db_config, settings
from data_lens.database.connection import DatabaseContext
from data_lens.utils.logger import get_logger

logger = get_logger(__name__)


def register_database_resources(mcp: FastMCP):
    """Register database information resources with the MCP instance."""

    @mcp.resource(
        uri="mysql://schema/database",
        name="Database Information",
        description="Get overall database information including all tables and their row counts.",
        mime_type="text/plain",
        tags={"database", "schema"},
        meta={"version": "1.0", "author": "engineering-team"},
    )
    async def get_database_info(ctx: Context) -> str:
        """
        Get overall database information including all tables and their row counts.

        This resource provides a quick overview of:
        - Database name and version
        - Connection type (SSH Tunnel or Direct)
        - List of all tables with statistics

        Returns:
            Formatted text with database information
        """
        logger.debug(f"Database context: {ctx.request_context}")
        db_ctx: DatabaseContext = ctx.request_context.lifespan_context
        connection = db_ctx.pool.get_connection()

        try:
            cursor = connection.cursor(dictionary=True)

            # Get database info
            cursor.execute("SELECT DATABASE() as db_name, VERSION() as version")
            db_info = cursor.fetchone()

            # Get all tables with row counts and size information
            cursor.execute(
                """
                SELECT 
                    TABLE_NAME,
                    TABLE_ROWS,
                    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS size_mb,
                    ENGINE,
                    TABLE_COLLATION
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
            """,
                (db_config.DB_NAME,),
            )

            tables = cursor.fetchall()

            cursor.close()
            connection.close()

            # Format the information
            info = f"Database: {db_info['db_name']}\n"
            info += f"MySQL Version: {db_info['version']}\n"
            info += (
                f"Connection: {'SSH Tunnel' if settings.USE_SSH_TUNNEL else 'Direct'}\n"
            )
            info += f"Total Tables: {len(tables)}\n\n"

            if tables:
                info += "Tables:\n"
                info += f"{'Table':<30} {'Rows':>12} {'Size (MB)':>12} {'Engine':<10} Collation\n"
                info += "-" * 90 + "\n"

                for table in tables:
                    info += (
                        f"{table['TABLE_NAME']:<30} "
                        f"{table['TABLE_ROWS']:>12,} "
                        f"{table['size_mb']:>12} "
                        f"{table['ENGINE']:<10} "
                        f"{table['TABLE_COLLATION']}\n"
                    )

            await ctx.info("✓ Database information retrieved successfully")
            return info

        except Error as e:
            await ctx.error(f"✗ Failed to retrieve database info: {e}")
            return f"Error retrieving database info: {e}"
