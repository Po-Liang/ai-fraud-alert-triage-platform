import json

from src.handlers import analyze_claim


def test_analyze_claim_returns_analysis_result(monkeypatch):
    monkeypatch.setattr(
        analyze_claim.claim_review_service,
        "analyze_claim_text",
        lambda claim_text: {
            "claimType": "入院給付金",
            "extractedFields": {
                "claimantName": "架空 花子",
                "claimType": "入院給付金",
                "hospitalizationPeriod": "2026年4月3日から2026年4月9日まで",
                "treatmentDate": None,
                "diagnosis": "急性虫垂炎",
                "submittedDocuments": ["診断書"],
            },
            "summary": f"summary: {claim_text}",
            "reviewChecklist": ["原本書類を確認する"],
            "governanceNotice": "AIの出力は審査担当者の確認を支援するものであり、支払い可否の最終判断は人間が行います。",
        },
    )

    response = analyze_claim.lambda_handler(
        {"body": json.dumps({"claimText": "入院給付金の請求"})},
        None,
    )

    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["claimType"] == "入院給付金"
    assert body["extractedFields"]["claimantName"] == "架空 花子"
    assert "支払い可否の最終判断は人間が行います" in body["governanceNotice"]


def test_analyze_claim_returns_400_when_body_is_missing():
    response = analyze_claim.lambda_handler({}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"message": "Request body is required"}


def test_analyze_claim_returns_400_for_invalid_json():
    response = analyze_claim.lambda_handler({"body": "{not-json}"}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "Request body must be valid JSON"
    }


def test_analyze_claim_returns_400_for_non_object_json():
    response = analyze_claim.lambda_handler({"body": json.dumps(["claimText"])}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "Request body must be a JSON object"
    }


def test_analyze_claim_returns_400_when_claim_text_is_missing():
    response = analyze_claim.lambda_handler({"body": json.dumps({})}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"message": "claimText is required"}


def test_analyze_claim_returns_400_when_claim_text_is_empty():
    response = analyze_claim.lambda_handler({"body": json.dumps({"claimText": "   "})}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"message": "claimText is required"}
