"""
MCP tools for executing SQL queries and managing MySQL databases.

This module demonstrates:
- @mcp.tool decorator usage via registration functions
- Context injection for database access
- Read-only query enforcement for security
- Structured error handling
"""

from typing import Any

from fastmcp import Context, FastMCP
from mysql.connector import Error

from data_lens.database import DatabaseContext, is_read_only_query
from data_lens.utils.logger import get_logger

logger = get_logger(__name__)


def register_mysql_tools(mcp: FastMCP):
    """Register MySQL database tools with the MCP instance."""

    @mcp.tool(
        name="execute_query",
        description="Execute a read-only SQL query and return results in tabular format.",
        tags={"private", "read-only", "database"},
        meta={"version": "1.0", "author": "engineering-team"},
    )
    async def execute_query(query: str, ctx: Context) -> dict[str, Any]:
        """
        Execute a read-only SQL query and return results.

        Only SELECT, SHOW, DESCRIBE, and EXPLAIN queries are allowed.
        This is a security measure to prevent data modification.

        Args:
            query: SQL query to execute (read-only only)

        Returns:
            Query results with columns and rows

        Example:
            {
                "success": True,
                "columns": ["id", "name", "email"],
                "rows": [
                    {"id": 1, "name": "John", "email": "john@example.com"},
                    ...
                ],
                "row_count": 10
            }
        """
        if not is_read_only_query(query):
            logger.warning(f"Blocked non-read-only query attempt: {query[:100]}...")
            return {
                "success": False,
                "error": "Only read-only queries (SELECT, SHOW, DESCRIBE, EXPLAIN) are allowed.",
            }

        # Get connection from pool via context
        db_ctx: DatabaseContext = ctx.request_context.lifespan_context
        connection = db_ctx.pool.get_connection()

        try:
            logger.info(f"Executing query: {query[:100]}...")
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)

            results = cursor.fetchall()
            columns = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )

            cursor.close()

            await ctx.info(f"✓ Query executed successfully: {query[:100]}...")
            logger.info(f"Query returned {len(results)} rows")

            return {
                "success": True,
                "columns": columns,
                "rows": results,
                "row_count": len(results),
            }
        except Error as e:
            await ctx.error(f"✗ Failed to execute query: {str(e)}")
            logger.error(f"Query execution failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            connection.close()

    @mcp.tool(
        name="list_tables",
        description="List all tables in the currently connected database.",
        tags={"database", "schema"},
        meta={"version": "1.0", "author": "engineering-team"},
    )
    async def list_tables(ctx: Context) -> dict[str, Any]:
        """
        List all tables in the currently connected database.

        Returns:
            List of table names and count

        Example:
            {
                "success": True,
                "tables": ["users", "orders", "products"],
                "count": 3
            }
        """
        db_ctx: DatabaseContext = ctx.request_context.lifespan_context
        connection = db_ctx.pool.get_connection()

        try:
            logger.debug("Listing database tables")
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()

            await ctx.info(f"✓ Listed {len(tables)} tables")
            logger.info(f"Found {len(tables)} tables in database")

            return {"success": True, "tables": tables, "count": len(tables)}
        except Error as e:
            await ctx.error(f"✗ Failed to list tables: {e}")
            logger.error(f"Failed to list tables: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            connection.close()

    @mcp.tool(
        name="get_table_schema",
        description="Get detailed schema information for a specific table including columns, indexes, and row count.",
        tags={"database", "schema"},
        meta={"version": "1.0", "author": "engineering-team"},
    )
    async def get_table_schema(table_name: str, ctx: Context) -> dict[str, Any]:
        """
        Get detailed schema information for a specific table.

        Returns column information, indexes, and row count.

        Args:
            table_name: Name of the table to inspect

        Returns:
            Table schema details including columns, indexes, and row count

        Example:
            {
                "success": True,
                "table_name": "users",
                "columns": [
                    {
                        "Field": "id",
                        "Type": "int",
                        "Null": "NO",
                        "Key": "PRI",
                        "Default": None,
                        "Extra": "auto_increment"
                    },
                    ...
                ],
                "indexes": [...],
                "row_count": 1000
            }
        """
        db_ctx: DatabaseContext = ctx.request_context.lifespan_context
        connection = db_ctx.pool.get_connection()

        try:
            logger.info(f"Getting schema for table: {table_name}")
            cursor = connection.cursor(dictionary=True)

            # Get table structure
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()

            # Get table indexes
            cursor.execute(f"SHOW INDEX FROM {table_name}")
            indexes = cursor.fetchall()

            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()["count"]

            cursor.close()

            await ctx.info(f"✓ Retrieved schema for table: {table_name}")
            logger.info(f"Table {table_name}: {len(columns)} columns, {row_count} rows")

            return {
                "success": True,
                "table_name": table_name,
                "columns": columns,
                "indexes": indexes,
                "row_count": row_count,
            }
        except Error as e:
            await ctx.error(f"✗ Failed to get table schema: {e}")
            logger.error(
                f"Failed to get schema for table {table_name}: {e}", exc_info=True
            )
            return {"success": False, "error": str(e)}
        finally:
            connection.close()
