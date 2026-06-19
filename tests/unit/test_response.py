import json

from src.utils.response import error_response, success_response


def test_success_response_keeps_japanese_text_readable():
    response = success_response({"answer": "入院給付金を確認してください"})

    assert response["headers"]["Content-Type"] == "application/json; charset=utf-8"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert response["headers"]["Access-Control-Allow-Headers"] == "Content-Type,Authorization"
    assert response["headers"]["Access-Control-Allow-Methods"] == "GET,POST,OPTIONS"
    assert "入院給付金" in response["body"]
    assert "\\u5165\\u9662" not in response["body"]
    assert json.loads(response["body"]) == {"answer": "入院給付金を確認してください"}


def test_error_response_keeps_japanese_text_readable():
    response = error_response("入院給付金の質問が必要です")

    assert response["headers"]["Content-Type"] == "application/json; charset=utf-8"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert response["headers"]["Access-Control-Allow-Headers"] == "Content-Type,Authorization"
    assert response["headers"]["Access-Control-Allow-Methods"] == "GET,POST,OPTIONS"
    assert "入院給付金" in response["body"]
    assert "\\u5165\\u9662" not in response["body"]
    assert json.loads(response["body"]) == {"message": "入院給付金の質問が必要です"}
