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
