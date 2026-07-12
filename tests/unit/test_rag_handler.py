import json

from src.handlers import rag_query


def test_rag_query_returns_answer_and_sources(monkeypatch):
    monkeypatch.setattr(
        rag_query.rag_service,
        "answer_question",
        lambda question: {
            "answer": f"回答: {question}",
            "sources": [
                {
                    "id": "GUIDE-DEMO-003",
                    "title": "書類不備対応ガイド",
                    "section": "不足書類の特定",
                }
            ],
        },
    )

    response = rag_query.lambda_handler(
        {"body": json.dumps({"question": "不足書類は何を確認しますか？"})},
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "answer": "回答: 不足書類は何を確認しますか？",
        "sources": [
            {
                "id": "GUIDE-DEMO-003",
                "title": "書類不備対応ガイド",
                "section": "不足書類の特定",
            }
        ],
    }


def test_rag_query_returns_japanese_fallback_with_sources(monkeypatch):
    monkeypatch.setattr(
        rag_query.rag_service.secrets_service,
        "get_openai_api_key",
        lambda: None,
    )

    response = rag_query.lambda_handler(
        {
            "body": json.dumps(
                {"question": "入院給付金の審査で確認すべき項目は何ですか？"},
                ensure_ascii=False,
            )
        },
        None,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert "入院給付金" in body["answer"]
    assert body["sources"]
    assert "入院給付金" in response["body"]
    assert "\\u5165\\u9662" not in response["body"]


def test_rag_query_returns_safe_cors_error_when_service_fails(monkeypatch):
    def raise_error(question):
        raise RuntimeError("internal detail")

    monkeypatch.setattr(rag_query.rag_service, "answer_question", raise_error)

    response = rag_query.lambda_handler(
        {"body": json.dumps({"question": "審査項目は何ですか？"})},
        None,
    )

    assert response["statusCode"] == 500
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert "internal detail" not in response["body"]


def test_rag_query_returns_400_when_body_is_missing():
    response = rag_query.lambda_handler({}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"message": "Request body is required"}


def test_rag_query_returns_400_for_invalid_json():
    response = rag_query.lambda_handler({"body": "{not-json}"}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "Request body must be valid JSON"
    }


def test_rag_query_returns_400_for_non_object_json():
    response = rag_query.lambda_handler({"body": json.dumps(["question"])}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "Request body must be a JSON object"
    }


def test_rag_query_returns_400_when_question_is_missing():
    response = rag_query.lambda_handler({"body": json.dumps({})}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"message": "question is required"}


def test_rag_query_returns_400_when_question_is_empty():
    response = rag_query.lambda_handler({"body": json.dumps({"question": "   "})}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"message": "question is required"}


def test_rag_query_forwards_fraud_knowledge_base(monkeypatch):
    calls = {}

    def answer_question(question, knowledge_base):
        calls.update(question=question, knowledge_base=knowledge_base)
        return {"answer": "回答", "sources": [], "metadata": {}}

    monkeypatch.setattr(rag_query.rag_service, "answer_question", answer_question)

    response = rag_query.lambda_handler(
        {
            "body": json.dumps(
                {
                    "question": "新規受取人を確認したい",
                    "knowledgeBase": "fraud_alerts",
                }
            )
        },
        None,
    )

    assert response["statusCode"] == 200
    assert calls == {
        "question": "新規受取人を確認したい",
        "knowledge_base": "fraud_alerts",
    }


def test_rag_query_rejects_unknown_knowledge_base():
    response = rag_query.lambda_handler(
        {
            "body": json.dumps(
                {"question": "確認項目は？", "knowledgeBase": "unknown"}
            )
        },
        None,
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "knowledgeBase is not supported"
    }


def test_rag_query_rejects_overly_long_question():
    response = rag_query.lambda_handler(
        {"body": json.dumps({"question": "あ" * 1001})},
        None,
    )

    assert response["statusCode"] == 400
    assert "1000 characters or fewer" in json.loads(response["body"])["message"]
