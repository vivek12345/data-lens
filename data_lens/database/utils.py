"""
Database utility functions.
"""

import re


def is_read_only_query(query: str) -> bool:
    """
    Check if a SQL query is read-only.

    Only SELECT, SHOW, DESCRIBE, and EXPLAIN queries are considered read-only.
    This is a security measure to prevent data modification.

    Args:
        query: SQL query to check

    Returns:
        True if query is read-only, False otherwise
    """
    query = query.strip().upper()
    read_only_keywords = ["SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN"]

    # Remove comments
    query = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
    query = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)

    # Get the first keyword
    first_keyword = query.split()[0] if query.split() else ""

    return first_keyword in read_only_keywords
