"""
Configuration settings for Data Lens MCP Server.

Environment Variables:
- USE_SSH_TUNNEL: Enable SSH tunnel (default: true)
- SSH_HOST: SSH server hostname
- SSH_PORT: SSH server port (default: 22)
- SSH_USER: SSH username
- SSH_KEY_PATH: Path to SSH private key (default: ~/.ssh/id_rsa)
- SSH_PASSWORD: SSH password (alternative to SSH key)
- DB_HOST: MySQL host (default: localhost)
- DB_PORT: MySQL port (default: 3306)
- DB_USER: MySQL username
- DB_PASSWORD: MySQL password
- DB_NAME: MySQL database name
- LOCAL_BIND_PORT: Local port for SSH tunnel (default: 3306)
"""

import os
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SSHConfig(BaseSettings):
    """SSH tunnel configuration."""

    SSH_HOST: Optional[str] = Field(None, alias="SSH_HOST")
    SSH_PORT: int = Field(22, alias="SSH_PORT")
    SSH_USER: Optional[str] = Field(None, alias="SSH_USER")
    SSH_KEY_PATH: str = Field("~/.ssh/id_rsa", alias="SSH_KEY_PATH")
    SSH_PASSWORD: Optional[str] = Field(None, alias="SSH_PASSWORD")

    @field_validator("SSH_KEY_PATH")
    @classmethod
    def expand_key_path(cls, v: str) -> str:
        """Expand the SSH key path to absolute path."""
        return os.path.expanduser(v)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class DatabaseConfig(BaseSettings):
    """MySQL database configuration."""

    DB_HOST: str = Field("localhost", alias="DB_HOST")
    DB_PORT: int = Field(3306, alias="DB_PORT")
    DB_USER: str = Field("root", alias="DB_USER")
    DB_PASSWORD: str = Field("", alias="DB_PASSWORD")
    DB_NAME: str = Field("", alias="DB_NAME")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class Settings(BaseSettings):
    """Main application settings."""

    PROJECT_NAME: str = "mcp-server"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.0.1"

    DEBUG: bool = False

    # MCP SERVER
    TRANSPORT_MODE: Literal["stdio", "http"] = Field("stdio", alias="TRANSPORT_MODE")

    # SSH Configuration
    USE_SSH_TUNNEL: bool = Field(True, alias="USE_SSH_TUNNEL")
    LOCAL_BIND_PORT: int = Field(3306, alias="LOCAL_BIND_PORT")

    # Server Configuration
    SERVER_HOST: str = Field("0.0.0.0", alias="SERVER_HOST")
    SERVER_PORT: int = Field(8000, alias="SERVER_PORT")

    # Authentication (for future implementation)
    AUTH_ENABLED: bool = Field(False, alias="AUTH_ENABLED")
    GOOGLE_CLIENT_ID: str = Field("enter your google client id here", alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field("enter your google client secret here", alias="GOOGLE_CLIENT_SECRET")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )


# Create settings instances
settings = Settings()
ssh_config = SSHConfig()
db_config = DatabaseConfig()
