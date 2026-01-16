"""Config module."""

from enum import Enum
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Environment enum."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """LogLevel enum."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BaseConfig(BaseSettings):
    """Base config class."""

    model_config = SettingsConfigDict(extra="ignore", frozen=True)


class APPConfig(BaseConfig):
    """APP config class."""

    host: str = "0.0.0.0"  # noqa: S104 # nosec
    port: int = Field(default=5000, ge=1, le=65535)
    environment: Environment = Environment.PRODUCTION
    log_level: LogLevel = LogLevel.INFO
    organization_name: str = "OrgName"

    @property
    def is_production(self) -> bool:
        """Check if the environment is production."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if the environment is development."""
        return self.environment == Environment.DEVELOPMENT


class JWTConfig(BaseConfig):
    """JWT config class."""

    secret: str = Field(min_length=32)
    issuer: str = "StatusPage"
    expires_in: int = 3600
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        extra="ignore",
        frozen=True,
    )


class CookieConfig(BaseConfig):
    """JWT config class."""

    key: str = "token"
    secure: bool = False
    httponly: bool = True

    model_config = SettingsConfigDict(
        env_prefix="COOKIE_",
        extra="ignore",
        frozen=True,
    )


class AdminConfig(BaseConfig):
    """Admin config class."""

    path: str = Field(default="/admin")
    username: str = Field(default="admin")
    password: str

    model_config = SettingsConfigDict(
        env_prefix="ADMIN_",
        extra="ignore",
        frozen=True,
    )

    @property
    def safe_path(self) -> str:
        """Safe admin path."""
        return self.path.strip("/")


class DBConfig(BaseConfig):
    """DB config class."""

    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    user: str
    password: str
    db: str

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        extra="ignore",
        frozen=True,
    )

    @property
    def url(self) -> str:
        """DB URL."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class Config:
    """Global application config."""

    app: ClassVar[APPConfig] = APPConfig()  # type: ignore[call-arg]
    jwt: ClassVar[JWTConfig] = JWTConfig()  # type: ignore[call-arg]
    cookie: ClassVar[CookieConfig] = CookieConfig()  # type: ignore[call-arg]
    admin: ClassVar[AdminConfig] = AdminConfig()  # type: ignore[call-arg]
    db: ClassVar[DBConfig] = DBConfig()  # type: ignore[call-arg]


config = Config()
