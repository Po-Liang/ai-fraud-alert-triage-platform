import json

from src.handlers import analyze_alert, create_alert, get_alert, list_alerts


def test_create_alert_returns_201_with_created_alert(monkeypatch):
    monkeypatch.setattr(
        create_alert.alert_service,
        "create_alert",
        lambda input_data: {"alertId": "alert-123", **input_data},
    )

    response = create_alert.lambda_handler(
        {
            "body": json.dumps(
                {
                    "customerId": "cust-1",
                    "accountId": "acct-1",
                    "alertType": "SUSPICIOUS_TRANSFER",
                    "amount": 1000,
                    "country": "JP",
                }
            )
        },
        None,
    )

    assert response["statusCode"] == 201
    assert response["headers"]["Content-Type"] == "application/json"
    assert json.loads(response["body"])["alertId"] == "alert-123"


def test_create_alert_returns_400_when_body_is_missing():
    response = create_alert.lambda_handler({}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"message": "Request body is required"}


def test_create_alert_returns_400_for_invalid_json():
    response = create_alert.lambda_handler({"body": "{not-json}"}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "Request body must be valid JSON"
    }
    assert response["headers"]["Content-Type"] == "application/json"


def test_create_alert_returns_400_for_non_object_json():
    response = create_alert.lambda_handler({"body": json.dumps(["not", "an", "object"])}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "Request body must be a JSON object"
    }


def test_get_alert_returns_400_when_alert_id_is_missing():
    response = get_alert.lambda_handler({"pathParameters": {}}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "alertId path parameter is required"
    }


def test_get_alert_returns_404_when_alert_is_not_found(monkeypatch):
    monkeypatch.setattr(get_alert.alert_service, "get_alert", lambda alert_id: None)

    response = get_alert.lambda_handler(
        {"pathParameters": {"alertId": "missing-alert"}},
        None,
    )

    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {"message": "Alert not found"}


def test_get_alert_returns_200_when_alert_exists(monkeypatch):
    monkeypatch.setattr(
        get_alert.alert_service,
        "get_alert",
        lambda alert_id: {"alertId": alert_id, "status": "PENDING_ANALYSIS"},
    )

    response = get_alert.lambda_handler(
        {"pathParameters": {"alertId": "alert-123"}},
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "alertId": "alert-123",
        "status": "PENDING_ANALYSIS",
    }


def test_list_alerts_uses_default_limit(monkeypatch):
    captured = {}

    def fake_list_alerts(limit=20):
        captured["limit"] = limit
        return [{"alertId": "alert-1"}]

    monkeypatch.setattr(list_alerts.alert_service, "list_alerts", fake_list_alerts)

    response = list_alerts.lambda_handler({}, None)

    assert captured["limit"] == 20
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"items": [{"alertId": "alert-1"}]}


def test_list_alerts_accepts_limit_query_parameter(monkeypatch):
    monkeypatch.setattr(
        list_alerts.alert_service,
        "list_alerts",
        lambda limit=20: [{"alertId": "alert-1"}] * limit,
    )

    response = list_alerts.lambda_handler(
        {"queryStringParameters": {"limit": "2"}},
        None,
    )

    assert response["statusCode"] == 200
    assert len(json.loads(response["body"])["items"]) == 2


def test_list_alerts_returns_400_for_invalid_limit():
    response = list_alerts.lambda_handler(
        {"queryStringParameters": {"limit": "abc"}},
        None,
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"message": "limit must be an integer"}


def test_list_alerts_returns_400_when_service_rejects_limit(monkeypatch):
    def raise_invalid_limit(limit=20):
        raise ValueError("limit must be greater than 0")

    monkeypatch.setattr(list_alerts.alert_service, "list_alerts", raise_invalid_limit)

    response = list_alerts.lambda_handler(
        {"queryStringParameters": {"limit": "-1"}},
        None,
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "limit must be greater than 0"
    }


def test_analyze_alert_returns_400_when_alert_id_is_missing():
    response = analyze_alert.lambda_handler({"pathParameters": {}}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "message": "alertId path parameter is required"
    }


def test_analyze_alert_returns_404_when_alert_is_not_found(monkeypatch):
    def raise_not_found(alert_id):
        raise analyze_alert.alert_service.AlertNotFoundError("missing")

    monkeypatch.setattr(
        analyze_alert.alert_service,
        "analyze_alert",
        raise_not_found,
    )

    response = analyze_alert.lambda_handler(
        {"pathParameters": {"alertId": "missing-alert"}},
        None,
    )

    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {"message": "Alert not found"}


def test_analyze_alert_returns_200_with_analysis_result(monkeypatch):
    monkeypatch.setattr(
        analyze_alert.alert_service,
        "analyze_alert",
        lambda alert_id: {
            "riskScore": 75,
            "riskLevel": "HIGH",
            "signals": ["Beneficiary is new"],
            "aiSummary": "Escalate for manual review.",
            "recommendedActions": ["Verify the beneficiary relationship"],
        },
    )

    response = analyze_alert.lambda_handler(
        {"pathParameters": {"alertId": "alert-123"}},
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"])["riskLevel"] == "HIGH"
