"""
MCP tools for data visualization.

This module demonstrates:
- Returning images from tools
- Integration with pandas and matplotlib
- Complex parameter handling
"""

import io

import matplotlib
import pandas as pd

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from fastmcp import Context, FastMCP
from fastmcp.utilities.types import Image
from mysql.connector import Error

from data_lens.database import DatabaseContext, is_read_only_query


def register_visualization_tools(mcp: FastMCP):
    """Register data visualization tools with the MCP instance."""

    @mcp.tool(
        name="plot_graph",
        description="Execute a SQL query and create a graph visualization (bar, line, pie, or scatter chart).",
        tags={"database", "visualization"},
        meta={"version": "1.0", "author": "engineering-team"},
    )
    async def plot_graph(
        query: str,
        chart_type: str,
        x_column: str,
        y_column: str,
        title: str = "",
        ctx: Context = None,
    ):
        """
        Execute a query and create a graph visualization.

        Returns a PNG image of the chart.

        Args:
            query: SQL SELECT query to execute
            chart_type: Type of chart - "bar", "line", "pie", or "scatter"
            x_column: Column name for x-axis (or labels for pie chart)
            y_column: Column name for y-axis (or values for pie chart)
            title: Optional chart title

        Returns:
            Image object containing the generated chart

        Example Usage:
            query = "SELECT category, SUM(sales) as total FROM products GROUP BY category"
            chart_type = "bar"
            x_column = "category"
            y_column = "total"
            title = "Sales by Category"
        """
        if not is_read_only_query(query):
            return {
                "success": False,
                "error": "Only read-only queries (SELECT) are allowed.",
            }

        db_ctx: DatabaseContext = ctx.request_context.lifespan_context
        connection = db_ctx.pool.get_connection()

        try:
            # Execute query and get results as DataFrame
            df = pd.read_sql(query, connection)

            if df.empty:
                return {"success": False, "error": "Query returned no results."}

            if x_column not in df.columns or y_column not in df.columns:
                return {
                    "success": False,
                    "error": (
                        f"Columns '{x_column}' or '{y_column}' not found in query results. "
                        f"Available columns: {', '.join(df.columns)}"
                    ),
                }

            # Create plot
            plt.figure(figsize=(10, 6))

            if chart_type == "bar":
                plt.bar(df[x_column], df[y_column])
                plt.xlabel(x_column)
                plt.ylabel(y_column)
                plt.xticks(rotation=45, ha="right")
            elif chart_type == "line":
                plt.plot(df[x_column], df[y_column], marker="o")
                plt.xlabel(x_column)
                plt.ylabel(y_column)
                plt.xticks(rotation=45, ha="right")
            elif chart_type == "pie":
                plt.pie(df[y_column], labels=df[x_column], autopct="%1.1f%%")
            elif chart_type == "scatter":
                plt.scatter(df[x_column], df[y_column])
                plt.xlabel(x_column)
                plt.ylabel(y_column)
            else:
                return {
                    "success": False,
                    "error": (
                        f"Unsupported chart type: {chart_type}. "
                        "Supported types: bar, line, pie, scatter"
                    ),
                }

            if title:
                plt.title(title)

            plt.tight_layout()

            # Save plot to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.getvalue()
            plt.close()

            await ctx.info(f"✓ Generated {chart_type} chart with {len(df)} data points")

            # Return Image object
            return Image(data=image_bytes, format="png")

        except Error as e:
            await ctx.error(f"✗ Failed to create plot: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        except Exception as e:
            await ctx.error(f"✗ Failed to create plot: {e}")
            return {"success": False, "error": f"Error creating plot: {str(e)}"}
        finally:
            connection.close()
