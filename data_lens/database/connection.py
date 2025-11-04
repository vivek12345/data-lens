"""
Database connection management with SSH tunnel support.

This module demonstrates:
- SSH tunnel setup for secure remote database connections
- Connection pooling for efficient resource management
- Lifespan management with FastMCP
- Proper cleanup on shutdown
"""

import os
from dataclasses import dataclass
from typing import Optional

import mysql.connector
from mysql.connector import Error, pooling
from sshtunnel import SSHTunnelForwarder

from data_lens.config import db_config, settings, ssh_config
from data_lens.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseContext:
    """
    Database connection pool context for FastMCP lifespan management.

    This context is shared across all requests during the server's lifetime.
    """

    pool: pooling.MySQLConnectionPool


class DatabaseState:
    """
    Manages database connections with optional SSH tunnel.

    Features:
    - Automatic SSH tunnel setup and teardown
    - Connection pooling for performance
    - Graceful error handling
    - Support for both SSH key and password authentication
    """

    def __init__(self):
        self.pool: Optional[pooling.MySQLConnectionPool] = None
        self.tunnel: Optional[SSHTunnelForwarder] = None

    async def initialize(self):
        """
        Initialize SSH tunnel (if needed) and database connection pool.

        This is called during the FastMCP lifespan startup phase.
        """
        try:
            # Validate required configuration
            if not db_config.DB_NAME or not db_config.DB_USER:
                raise ValueError(
                    "Missing required configuration. "
                    "Please set DB_NAME and DB_USER environment variables."
                )

            # Start SSH tunnel if configured
            if settings.USE_SSH_TUNNEL and self.tunnel is None:
                await self._start_ssh_tunnel()

            # Determine connection configuration
            if settings.USE_SSH_TUNNEL:
                # Connect through SSH tunnel
                connection_config = {
                    "host": "127.0.0.1",
                    "port": settings.LOCAL_BIND_PORT,
                    "user": db_config.DB_USER,
                    "password": db_config.DB_PASSWORD,
                    "database": db_config.DB_NAME,
                }
                logger.info(
                    f"✓ Connecting through SSH tunnel: localhost:{settings.LOCAL_BIND_PORT}"
                )
            else:
                # Direct connection
                connection_config = {
                    "host": db_config.DB_HOST,
                    "port": db_config.DB_PORT,
                    "user": db_config.DB_USER,
                    "password": db_config.DB_PASSWORD,
                    "database": db_config.DB_NAME,
                }
                logger.info(f"✓ Direct connection to {db_config.DB_HOST}")

            # Create connection pool
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="mcp_pool",
                pool_size=5,
                pool_reset_session=True,
                **connection_config,
            )
            logger.info(f"✓ Connected to MySQL database: {db_config.DB_NAME}")
        except Error as e:
            logger.error(f"✗ Failed to connect to MySQL: {e}")
            raise

    async def _start_ssh_tunnel(self):
        """
        Start SSH tunnel for MySQL connection.

        Supports both SSH key and password authentication.
        """
        try:
            # Configure SSH authentication
            ssh_auth = {}

            if ssh_config.SSH_KEY_PATH and os.path.exists(ssh_config.SSH_KEY_PATH):
                ssh_auth["ssh_pkey"] = ssh_config.SSH_KEY_PATH
                logger.info(f"✓ Using SSH key: {ssh_config.SSH_KEY_PATH}")
            elif ssh_config.SSH_PASSWORD:
                ssh_auth["ssh_password"] = ssh_config.SSH_PASSWORD
                logger.info("✓ Using SSH password authentication")
            else:
                raise ValueError(
                    f"SSH authentication failed: "
                    f"SSH key not found at {ssh_config.SSH_KEY_PATH if ssh_config.SSH_KEY_PATH else 'None'} "
                    "and no SSH_PASSWORD environment variable provided"
                )

            # Create and start SSH tunnel
            self.tunnel = SSHTunnelForwarder(
                (ssh_config.SSH_HOST, ssh_config.SSH_PORT),
                ssh_username=ssh_config.SSH_USER,
                **ssh_auth,
                remote_bind_address=(db_config.DB_HOST, db_config.DB_PORT),
                local_bind_address=("127.0.0.1", settings.LOCAL_BIND_PORT),
            )

            self.tunnel.start()
            logger.info(
                f"✓ SSH Tunnel established: "
                f"{ssh_config.SSH_USER}@{ssh_config.SSH_HOST}:{ssh_config.SSH_PORT} -> "
                f"localhost:{settings.LOCAL_BIND_PORT} -> {db_config.DB_HOST}:{db_config.DB_PORT}"
            )
        except Exception as e:
            logger.error(f"✗ Failed to start SSH tunnel: {e}")
            raise

    async def cleanup(self):
        """
        Cleanup database connections and SSH tunnel.

        This is called during the FastMCP lifespan shutdown phase.
        """
        if self.pool:
            # Connection pools are automatically managed by mysql-connector
            logger.info("✓ Database connections cleaned up")

        if self.tunnel:
            self.tunnel.stop()
            self.tunnel = None
            logger.info("✓ SSH tunnel closed")

    async def get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return self.pool.get_connection()
