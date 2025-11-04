"""
MCP prompts for generating database reports.

This module demonstrates:
- @mcp.prompt decorator usage
- Parameterized prompt templates
- Best practices for AI-assisted data analysis
"""

from fastmcp import FastMCP


def register_report_prompts(mcp: FastMCP):
    """Register report generation prompts with the MCP instance."""

    @mcp.prompt(
        name="generate_report",
        description="Generate a comprehensive data analysis report for a specific table.",
        tags={"database", "reporting"},
        meta={"version": "1.0", "author": "engineering-team"},
    )
    def generate_report(table_name: str, metrics: str = "all") -> str:
        """
        Generate a prompt template for creating a comprehensive data report.

        This prompt guides the AI to create structured reports with:
        - Executive summary
        - Data distribution analysis
        - Key insights and trends
        - Actionable recommendations

        Args:
            table_name: Name of the table to analyze
            metrics: Specific metrics to focus on (default: "all")

        Returns:
            Formatted prompt string for the AI to follow
        """
        return f"""Create a comprehensive report for the '{table_name}' table:

1. Executive Summary:
   - Total rows
   - Key metrics overview
   - Date range (if applicable)

2. Data Distribution:
   - Show numeric column distributions (min, max, avg, median)
   - Show top categories for categorical columns
   - Identify any NULL values or data quality issues

3. Insights:
   - Identify trends if there's a date/timestamp column
   - Highlight any notable patterns or anomalies
   - Compare current period vs historical (if applicable)

4. Recommendations:
   - Data optimization suggestions
   - Potential analysis opportunities
   - Query optimization recommendations

Focus on: {metrics}

Format the report professionally with clear sections and include visualizations where appropriate.
Use the available tools to query the data and generate charts."""

    @mcp.prompt(
        name="query_builder",
        description="Generate optimized SQL queries for common data analysis tasks.",
        tags={"database", "query"},
        meta={"version": "1.0", "author": "engineering-team"},
    )
    def query_builder(
        table_name: str, task: str = "explore", conditions: str = ""
    ) -> str:
        """
        Generate a prompt template for building SQL queries.

        Args:
            table_name: Name of the table to query
            task: Type of task - "explore", "aggregate", "trend", or "compare"
            conditions: Optional WHERE clause conditions

        Returns:
            Formatted prompt string for SQL query generation
        """
        return f"""Generate an optimized SQL query for the '{table_name}' table:

Task Type: {task}

Requirements:
- Use appropriate JOINs if multiple tables are needed
- Include relevant WHERE clauses: {conditions if conditions else 'None specified'}
- Add ORDER BY for meaningful sorting
- Use LIMIT to prevent excessive results (max 1000 rows)
- Include aggregate functions where appropriate (COUNT, SUM, AVG, etc.)

Best Practices:
- Use column aliases for clarity
- Add comments for complex logic
- Optimize for performance (avoid SELECT *)
- Consider using indexes

Example Structure:
SELECT 
    column1 AS alias1,
    COUNT(*) as count,
    AVG(column2) as average
FROM {table_name}
WHERE {conditions if conditions else '1=1'}
GROUP BY column1
ORDER BY count DESC
LIMIT 100;

Generate the appropriate query for the '{task}' task."""
