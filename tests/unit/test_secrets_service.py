import sys
from types import SimpleNamespace

from src.services import secrets_service


def _reset_secret_cache():
    secrets_service._CACHE_LOADED = False
    secrets_service._CACHED_OPENAI_API_KEY = None


def test_get_openai_api_key_reads_json_secret(monkeypatch):
    _reset_secret_cache()

    class MockClient:
        def get_secret_value(self, SecretId):
            assert SecretId == "ai-fraud-triage/openai-api-key"
            return {"SecretString": '{"OPENAI_API_KEY": "sk-test-json"}'}

    fake_boto3 = SimpleNamespace(client=lambda service_name: MockClient())
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setenv("OPENAI_SECRET_NAME", "ai-fraud-triage/openai-api-key")

    assert secrets_service.get_openai_api_key() == "sk-test-json"


def test_get_openai_api_key_supports_plain_string_secret(monkeypatch):
    _reset_secret_cache()

    class MockClient:
        def get_secret_value(self, SecretId):
            return {"SecretString": "sk-test-plain"}

    fake_boto3 = SimpleNamespace(client=lambda service_name: MockClient())
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setenv("OPENAI_SECRET_NAME", "ai-fraud-triage/openai-api-key")

    assert secrets_service.get_openai_api_key() == "sk-test-plain"


def test_get_openai_api_key_returns_none_when_env_is_missing(monkeypatch):
    _reset_secret_cache()
    monkeypatch.delenv("OPENAI_SECRET_NAME", raising=False)

    assert secrets_service.get_openai_api_key() is None


def test_get_openai_api_key_uses_cache(monkeypatch):
    _reset_secret_cache()
    call_count = {"count": 0}

    class MockClient:
        def get_secret_value(self, SecretId):
            call_count["count"] += 1
            return {"SecretString": '{"OPENAI_API_KEY": "sk-test-cached"}'}

    fake_boto3 = SimpleNamespace(client=lambda service_name: MockClient())
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setenv("OPENAI_SECRET_NAME", "ai-fraud-triage/openai-api-key")

    assert secrets_service.get_openai_api_key() == "sk-test-cached"
    assert secrets_service.get_openai_api_key() == "sk-test-cached"
    assert call_count["count"] == 1
