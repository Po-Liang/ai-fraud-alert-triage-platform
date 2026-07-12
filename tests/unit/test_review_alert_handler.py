import json

from src.handlers import review_alert
from src.services import alert_service


def test_review_alert_returns_created_event(monkeypatch):
    monkeypatch.setattr(
        review_alert.alert_service,
        "record_review",
        lambda alert_id, input_data: {
            "alertId": alert_id,
            "reviewStatus": input_data["action"],
            "reviewEvent": {"workflowRunId": input_data["workflowRunId"]},
        },
    )

    response = review_alert.lambda_handler(
        {
            "pathParameters": {"alertId": "alert-1"},
            "body": json.dumps(
                {"action": "ESCALATE", "workflowRunId": "run-1"}
            ),
        },
        None,
    )

    assert response["statusCode"] == 201
    assert json.loads(response["body"])["reviewStatus"] == "ESCALATE"


def test_review_alert_rejects_invalid_action(monkeypatch):
    def reject(alert_id, input_data):
        raise ValueError("action is not supported")

    monkeypatch.setattr(review_alert.alert_service, "record_review", reject)

    response = review_alert.lambda_handler(
        {
            "pathParameters": {"alertId": "alert-1"},
            "body": json.dumps({"action": "AUTO_BLOCK", "workflowRunId": "run-1"}),
        },
        None,
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"message": "action is not supported"}


def test_review_alert_returns_not_found(monkeypatch):
    def reject(alert_id, input_data):
        raise alert_service.AlertNotFoundError("missing")

    monkeypatch.setattr(review_alert.alert_service, "record_review", reject)

    response = review_alert.lambda_handler(
        {
            "pathParameters": {"alertId": "missing"},
            "body": json.dumps({"action": "CLOSE", "workflowRunId": "run-1"}),
        },
        None,
    )

    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {"message": "Alert not found"}


def test_review_alert_requires_path_and_body():
    missing_path = review_alert.lambda_handler({"body": "{}"}, None)
    missing_body = review_alert.lambda_handler(
        {"pathParameters": {"alertId": "alert-1"}},
        None,
    )

    assert missing_path["statusCode"] == 400
    assert missing_body["statusCode"] == 400


def test_review_alert_returns_safe_cors_error_for_service_failure(monkeypatch):
    def reject(alert_id, input_data):
        raise alert_service.AlertServiceError("Failed to record review")

    monkeypatch.setattr(review_alert.alert_service, "record_review", reject)

    response = review_alert.lambda_handler(
        {
            "pathParameters": {"alertId": "alert-1"},
            "body": json.dumps({"action": "APPROVE", "workflowRunId": "run-1"}),
        },
        None,
    )

    assert response["statusCode"] == 500
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert json.loads(response["body"]) == {"message": "Failed to record review"}
