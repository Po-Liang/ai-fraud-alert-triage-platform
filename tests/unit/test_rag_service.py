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
        assert timeout == rag_service.OPENAI_REQUEST_TIMEOUT_SECONDS
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


def test_answer_question_falls_back_when_secret_lookup_fails(monkeypatch):
    def raise_error():
        raise RuntimeError("secret lookup failed")

    monkeypatch.setattr(
        rag_service.secrets_service,
        "get_openai_api_key",
        raise_error,
    )

    result = rag_service.answer_question(
        "入院給付金の審査で確認すべき項目は何ですか？"
    )

    assert "参照したデモ社内ガイダンス" in result["answer"]
    assert result["sources"]


def test_packaged_guidance_path_is_module_relative():
    expected_path = (
        rag_service.Path(rag_service.__file__).resolve().parents[1]
        / "data"
        / "insurance_claim_guidance.json"
    )

    assert rag_service.KNOWLEDGE_BASE_PATH == expected_path
    assert rag_service.KNOWLEDGE_BASE_PATH.is_file()


def test_answer_question_rejects_empty_question():
    try:
        rag_service.answer_question(" ")
    except ValueError as error:
        assert str(error) == "question is required"
    else:
        raise AssertionError("Expected ValueError")


def test_fraud_retrieval_returns_real_demo_evidence():
    documents = rag_service.retrieve_relevant_documents(
        "新規受取人への高額送金では何を確認しますか？",
        knowledge_base="fraud_alerts",
    )

    assert documents
    assert documents[0]["id"].startswith("FRAUD-GUIDE-DEMO-")
    assert "面接デモ用" in documents[0]["content"]


def test_fraud_answer_exposes_grounding_metadata_and_exact_excerpt(monkeypatch):
    monkeypatch.setattr(
        rag_service.secrets_service,
        "get_openai_api_key",
        lambda: None,
    )

    result = rag_service.answer_question(
        "短時間の連続取引で確認すべき項目は？",
        knowledge_base="fraud_alerts",
    )

    assert result["metadata"] == {
        "knowledgeBase": "fraud_alerts",
        "retrievalStatus": "COMPLETED",
        "groundingStatus": "GROUNDED",
        "generationMode": "DETERMINISTIC_FALLBACK",
    }
    assert result["sources"]
    source = result["sources"][0]
    matching_document = next(
        document
        for document in rag_service._load_guidance_documents("fraud_alerts")
        if document["id"] == source["id"]
    )
    assert source["excerpt"] == matching_document["content"]
    assert source["sourceType"] == "demo_internal_guideline"
    assert "最終判断は人間が行います" in result["answer"]
    assert "取引記録、顧客情報" in result["answer"]
    assert "原本書類、契約情報" not in result["answer"]


def test_fraud_answer_reports_no_evidence_without_inventing_sources(monkeypatch):
    monkeypatch.setattr(
        rag_service.secrets_service,
        "get_openai_api_key",
        lambda: "must-not-be-used",
    )

    result = rag_service.answer_question(
        "今日の天気を教えてください",
        knowledge_base="fraud_alerts",
    )

    assert result["sources"] == []
    assert result["metadata"]["retrievalStatus"] == "NO_EVIDENCE"
    assert result["metadata"]["groundingStatus"] == "NOT_GROUNDED"
    assert "関連するデモ用社内ガイドラインを特定できませんでした" in result["answer"]


def test_fraud_answer_reports_guidance_load_failure(monkeypatch):
    def raise_missing_file(question, knowledge_base):
        del question, knowledge_base
        raise FileNotFoundError("demo guidance missing")

    monkeypatch.setattr(rag_service, "retrieve_relevant_documents", raise_missing_file)

    result = rag_service.answer_question(
        "新規受取人を確認したい",
        knowledge_base="fraud_alerts",
    )

    assert result["sources"] == []
    assert result["metadata"]["retrievalStatus"] == "FAILED"
    assert "参照情報を取得できませんでした" in result["answer"]


def test_answer_question_rejects_unknown_knowledge_base():
    try:
        rag_service.answer_question("確認項目は？", knowledge_base="unknown")
    except ValueError as error:
        assert str(error) == "knowledgeBase is not supported"
    else:
        raise AssertionError("Expected unsupported knowledge base error")
