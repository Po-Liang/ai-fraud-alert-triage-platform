from __future__ import annotations

import json
import logging
import os
from typing import Any

OPENAI_SECRET_NAME_ENV_VAR = "OPENAI_SECRET_NAME"

_CACHE_LOADED = False
_CACHED_OPENAI_API_KEY: str | None = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_secret_name() -> str | None:
    secret_name = os.getenv(OPENAI_SECRET_NAME_ENV_VAR, "").strip()
    if not secret_name:
        return None

    return secret_name


def _get_client():
    import boto3

    return boto3.client("secretsmanager")


def _extract_api_key(secret_value: str) -> str | None:
    secret_value = secret_value.strip()
    if not secret_value:
        return None

    try:
        parsed_secret: Any = json.loads(secret_value)
    except json.JSONDecodeError:
        return secret_value

    if isinstance(parsed_secret, dict):
        api_key = parsed_secret.get("OPENAI_API_KEY")
        if isinstance(api_key, str) and api_key.strip():
            return api_key.strip()

    return None


def get_openai_api_key() -> str | None:
    global _CACHE_LOADED, _CACHED_OPENAI_API_KEY

    if _CACHE_LOADED:
        logger.info(
            "openai_secret_cache_used cachedSecretAvailable=%s",
            _CACHED_OPENAI_API_KEY is not None,
        )
        return _CACHED_OPENAI_API_KEY

    secret_name = _get_secret_name()
    logger.info("openai_secret_name_checked configured=%s", secret_name is not None)
    if not secret_name:
        _CACHE_LOADED = True
        _CACHED_OPENAI_API_KEY = None
        return None

    try:
        response = _get_client().get_secret_value(SecretId=secret_name)
    except Exception:
        logger.warning("openai_secret_lookup_failed")
        _CACHE_LOADED = True
        _CACHED_OPENAI_API_KEY = None
        return None

    logger.info("openai_secret_lookup_succeeded")
    secret_string = response.get("SecretString")
    if isinstance(secret_string, str):
        _CACHED_OPENAI_API_KEY = _extract_api_key(secret_string)
        _CACHE_LOADED = True
        return _CACHED_OPENAI_API_KEY

    _CACHE_LOADED = True
    _CACHED_OPENAI_API_KEY = None
    return None
