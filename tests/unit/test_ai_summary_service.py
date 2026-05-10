import json

from src.services import ai_summary_service


class MockResponse:
    def __init__(self, payload: str):
        self._payload = payload

    def read(self):
        return self._payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_generate_investigation_summary_uses_openai_when_available(monkeypatch):
    monkeypatch.setattr(
        ai_summary_service.secrets_service,
        "get_openai_api_key",
        lambda: "sk-test",
    )
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    def mock_urlopen(request, timeout):
        assert request.full_url == "https://api.openai.com/v1/chat/completions"
        assert timeout == 15
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["model"] == "gpt-4o-mini"
        return MockResponse(
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "aiSummary": (
                                            "The activity may indicate elevated risk and "
                                            "should be reviewed. The transaction requires "
                                            "verification by an investigator."
                                        ),
                                        "recommendedActions": [
                                            "Review the transaction context",
                                            "Verify the beneficiary relationship",
                                        ],
                                    }
                                )
                            }
                        }
                    ]
                }
            )
        )

    monkeypatch.setattr(ai_summary_service.urllib.request, "urlopen", mock_urlopen)

    result = ai_summary_service.generate_investigation_summary(
        {"alertId": "alert-123"},
        {"riskLevel": "HIGH", "signals": ["Beneficiary is new"]},
    )

    assert result == {
        "aiSummary": (
            "The activity may indicate elevated risk and should be reviewed. "
            "The transaction requires verification by an investigator."
        ),
        "recommendedActions": [
            "Review the transaction context",
            "Verify the beneficiary relationship",
        ],
    }


def test_generate_investigation_summary_falls_back_when_secret_is_missing(monkeypatch):
    monkeypatch.setattr(
        ai_summary_service.secrets_service,
        "get_openai_api_key",
        lambda: None,
    )

    result = ai_summary_service.generate_investigation_summary(
        {"alertId": "alert-123"},
        {"riskLevel": "MEDIUM", "signals": ["Moderate transaction velocity in the last hour"]},
    )

    assert "requires verification by a human investigator" in result["aiSummary"]
    assert result["recommendedActions"] == [
        "Review customer transaction history",
        "Check whether the transaction pattern is unusual",
        "Monitor for additional suspicious activity",
    ]


def test_generate_investigation_summary_falls_back_when_api_call_fails(monkeypatch):
    monkeypatch.setattr(
        ai_summary_service.secrets_service,
        "get_openai_api_key",
        lambda: "sk-test",
    )

    def raise_error(request, timeout):
        raise RuntimeError("api failed")

    monkeypatch.setattr(ai_summary_service.urllib.request, "urlopen", raise_error)

    result = ai_summary_service.generate_investigation_summary(
        {"alertId": "alert-123"},
        {"riskLevel": "LOW", "signals": []},
    )

    assert "requires verification by a human investigator" in result["aiSummary"]
    assert result["recommendedActions"] == [
        "Record the alert result",
        "No immediate escalation required based on current signals",
    ]


def test_generate_investigation_summary_fallback_is_deterministic(monkeypatch):
    monkeypatch.setattr(
        ai_summary_service.secrets_service,
        "get_openai_api_key",
        lambda: None,
    )

    result = ai_summary_service.generate_investigation_summary(
        {"alertId": "alert-xyz"},
        {"riskLevel": "HIGH", "signals": ["Beneficiary is new"]},
    )

    assert "deterministic scoring logic" in result["aiSummary"]
    assert result["recommendedActions"] == [
        "Verify the beneficiary relationship",
        "Review recent login and device activity",
        "Check for similar alerts on the same customer",
        "Escalate for manual investigation",
    ]
