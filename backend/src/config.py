import os
from typing import Iterable


class ConfigurationError(RuntimeError):
    """Raised when the application is missing required environment settings."""


AUDIT_REQUIRED_ENV_VARS = (
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_CHAT_DEPLOYMENT",
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_API_KEY",
    "AZURE_SEARCH_INDEX_NAME",
    "AZURE_VI_ACCOUNT_ID",
    "AZURE_VI_LOCATION",
    "AZURE_SUBSCRIPTION_ID",
    "AZURE_RESOURCE_GROUP",
)


def validate_required_env(required_vars: Iterable[str], context: str) -> None:
    missing_vars = [name for name in required_vars if not os.getenv(name)]
    if missing_vars:
        missing_list = ", ".join(missing_vars)
        raise ConfigurationError(
            f"Missing required environment variables for {context}: {missing_list}"
        )


def validate_audit_environment() -> None:
    validate_required_env(AUDIT_REQUIRED_ENV_VARS, "the audit pipeline")
