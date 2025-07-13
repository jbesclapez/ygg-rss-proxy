import enum
import logging
import os
from pydantic import ValidationError, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """Settings for the application"""

    # ygg.re
    ygg_user: str = "user"
    ygg_pass: str = "pass"
    ygg_url: str = "https://www.ygg.re"

    # RSS PROXY
    rss_host: str = "localhost"
    rss_port: int = 8080
    rss_shema: str = "http"

    # FLARESOLVERR
    flaresolverr_host: str = "localhost"
    flaresolverr_shema: str = "http"
    flaresolverr_port: int = 8191

    # GUNICORN
    gunicorn_workers: int = 4
    gunicorn_port: int = 8080
    gunicorn_binder: str = "0.0.0.0"
    gunicorn_timeout: int = 180

    # LOGGING
    log_level: LogLevel = LogLevel.INFO
    log_path: str = "/app/config/logs/rss-proxy.log"
    log_redacted: bool = True

    # FLASK SESSIONS - REQUIRED SECURITY
    secret_key: str = Field(
        ...,  # Required field, no default
        description="Secret key for Flask session encryption. Must be set via SECRET_KEY environment variable.",
        min_length=32
    )

    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validate SECRET_KEY meets security requirements"""
        if not v:
            logging.error("🚨 SECURITY ERROR: SECRET_KEY environment variable is required!")
            logging.error("Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\"")
            raise ValueError("SECRET_KEY environment variable is required")
        
        if len(v) < 32:
            logging.error(f"🚨 SECURITY ERROR: SECRET_KEY must be at least 32 characters (current: {len(v)})")
            raise ValueError("SECRET_KEY must be at least 32 characters for security")
        
        # Check for known weak/default values
        weak_keys = [
            "superkey_that_can_be_changed",
            "your_secure_random_secret_key_here", 
            "secret",
            "key",
            "password",
            "changeme"
        ]
        
        if v.lower() in [key.lower() for key in weak_keys]:
            logging.error(f"🚨 SECURITY ERROR: SECRET_KEY cannot use default/weak value: {v}")
            logging.error("Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\"")
            raise ValueError(f"SECRET_KEY cannot use weak/default value")
        
        logging.info("✅ SECRET_KEY validation passed")
        return v

    # SQLITE
    db_path: str = "/app/config/rss-proxy.db"
    db_timeout: int = 15

    # User-Agent
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # DEVELOPMENT
    debug: bool = True
    dev_host: str = "0.0.0.0"
    dev_port: int = 8080

    # Version
    version_path: str = "/app/pyproject.toml"

    model_config = SettingsConfigDict(
        env_file=".env", secrets_dir="/run/secrets", env_file_encoding="utf-8"
    )


def _check_secret_key_env():
    """Check if SECRET_KEY is properly set in environment"""
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        logging.error("")
        logging.error("🚨" + "="*50 + "🚨")
        logging.error("🚨 CRITICAL SECURITY ERROR: SECRET_KEY NOT SET 🚨")
        logging.error("🚨" + "="*50 + "🚨")
        logging.error("")
        logging.error("The SECRET_KEY environment variable is required for secure operation.")
        logging.error("This key protects your YGG authentication cookies and session data.")
        logging.error("")
        logging.error("TO FIX:")
        logging.error("1. Generate a secure key:")
        logging.error("   python -c \"import secrets; print('SECRET_KEY=' + secrets.token_hex(32))\"")
        logging.error("")
        logging.error("2. Add the key to your .env file:")
        logging.error("   SECRET_KEY=your_generated_key_here")
        logging.error("")
        logging.error("3. Restart the application")
        logging.error("")
        logging.error("🚨 APPLICATION STARTUP BLOCKED FOR SECURITY 🚨")
        logging.error("")
        return False
    return True

try:
    # Check SECRET_KEY before attempting to create settings
    if not _check_secret_key_env():
        raise RuntimeError("SECRET_KEY environment variable is required")
    
    settings = Settings()
    logging.info(f"✅ Configuration loaded successfully with secure SECRET_KEY ({len(settings.secret_key)} chars)")
    
except ValidationError as e:
    logging.error(f"🚨 Configuration validation failed: {e}")
    raise RuntimeError(f"Configuration validation error: {e}")
except Exception as e:
    logging.error(f"🚨 Failed to initialize settings: {e}")
    raise
