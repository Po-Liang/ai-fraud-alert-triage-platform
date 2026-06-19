import json

from src.services import rag_service


class MockResponse:
    def __init__(self, payload: str):
        self._payload = payload

    def read(self):
        return self._payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_answer_question_returns_fallback_answer_and_sources_when_secret_is_missing(monkeypatch):
    monkeypatch.setattr(
        rag_service.secrets_service,
        "get_openai_api_key",
        lambda: None,
    )

    result = rag_service.answer_question("診断書で確認する項目は何ですか？")

    assert "AIは最終的な請求承認、否認、支払い可否を判断しません" in result["answer"]
    assert result["sources"]
    assert all({"id", "title", "section"} <= set(source) for source in result["sources"])


def test_retrieval_returns_relevant_insurance_guidance():
    documents = rag_service.retrieve_relevant_documents(
        "入院給付金の審査では入院期間をどう確認しますか？"
    )

    assert documents[0]["id"] == "GUIDE-DEMO-001"
    assert documents[0]["title"] == "入院給付金審査ガイド"


def test_retrieval_returns_no_sources_for_unrelated_question():
    documents = rag_service.retrieve_relevant_documents("今日の天気を教えてください")

    assert documents == []


def test_answer_question_returns_no_sources_when_guidance_is_not_relevant(monkeypatch):
    monkeypatch.setattr(
        rag_service.secrets_service,
        "get_openai_api_key",
        lambda: None,
    )

    result = rag_service.answer_question("今日の天気を教えてください")

    assert result["sources"] == []
    assert "関連するデモ社内ガイダンスを特定できませんでした" in result["answer"]


def test_answer_question_uses_openai_when_available(monkeypatch):
    monkeypatch.setattr(
        rag_service.secrets_service,
        "get_openai_api_key",
        lambda: "sk-test",
    )
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    def mock_urlopen(request, timeout):
        assert request.full_url == rag_service.OPENAI_CHAT_COMPLETIONS_URL
        assert timeout == 15
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["model"] == "test-model"
        assert "Authorization" in request.headers
        return MockResponse(
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "answer": (
                                            "診断書、請求書、入院証明書の日付差異を確認し、"
                                            "必要に応じて担当者が原本確認してください。"
                                        )
                                    }
                                )
                            }
                        }
                    ]
                }
            )
        )

    monkeypatch.setattr(rag_service.urllib.request, "urlopen", mock_urlopen)

    result = rag_service.answer_question("入院期間の確認観点を教えてください")

    assert "診断書、請求書、入院証明書" in result["answer"]
    assert "AIは最終的な請求承認、否認、支払い可否を判断しません" in result["answer"]
    assert result["sources"]


def test_answer_question_falls_back_when_openai_call_fails(monkeypatch):
    monkeypatch.setattr(
        rag_service.secrets_service,
        "get_openai_api_key",
        lambda: "sk-test",
    )

    def raise_error(request, timeout):
        raise RuntimeError("api failed")

    monkeypatch.setattr(rag_service.urllib.request, "urlopen", raise_error)

    result = rag_service.answer_question("書類不備の場合の確認観点は？")

    assert "参照したデモ社内ガイダンス" in result["answer"]
    assert "AIは最終的な請求承認、否認、支払い可否を判断しません" in result["answer"]
    assert result["sources"]


def test_answer_question_rejects_empty_question():
    try:
        rag_service.answer_question(" ")
    except ValueError as error:
        assert str(error) == "question is required"
    else:
        raise AssertionError("Expected ValueError")
