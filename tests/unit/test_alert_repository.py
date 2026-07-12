from decimal import Decimal
from unittest.mock import Mock

from src.repositories import alert_repository


class FakeAwsClientError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.response = {"Error": {"Code": code}}


def test_create_alert_writes_item_with_keys_and_timestamps(monkeypatch):
    mock_table = Mock()
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)
    monkeypatch.setattr(
        alert_repository,
        "_current_timestamp",
        lambda: "2026-05-04T12:00:00Z",
    )

    result = alert_repository.create_alert(
        {
            "alertId": "alert-123",
            "customerId": "cust-1",
            "amount": 1250.5,
            "status": "PENDING",
        }
    )

    assert result == {
        "alertId": "alert-123",
        "PK": "ALERT#alert-123",
        "SK": "METADATA",
        "createdAt": "2026-05-04T12:00:00Z",
        "updatedAt": "2026-05-04T12:00:00Z",
        "customerId": "cust-1",
        "amount": 1250.5,
        "status": "PENDING",
    }

    mock_table.put_item.assert_called_once()
    put_item_kwargs = mock_table.put_item.call_args.kwargs

    assert put_item_kwargs["ConditionExpression"] == (
        "attribute_not_exists(PK) AND attribute_not_exists(SK)"
    )
    assert put_item_kwargs["Item"]["amount"] == Decimal("1250.5")


def test_create_alert_requires_alert_id(monkeypatch):
    mock_table = Mock()
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)

    try:
        alert_repository.create_alert({"customerId": "cust-1"})
    except ValueError as error:
        assert str(error) == "alert must include a non-empty alertId"
    else:
        raise AssertionError("Expected create_alert to reject missing alertId")

    mock_table.put_item.assert_not_called()


def test_create_alert_translates_duplicate_item_error(monkeypatch):
    mock_table = Mock()
    mock_table.put_item.side_effect = FakeAwsClientError(
        "ConditionalCheckFailedException"
    )
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)
    monkeypatch.setattr(
        alert_repository,
        "_current_timestamp",
        lambda: "2026-05-04T12:00:00Z",
    )

    try:
        alert_repository.create_alert({"alertId": "alert-123"})
    except alert_repository.AlertAlreadyExistsError as error:
        assert str(error) == "Alert already exists"
    else:
        raise AssertionError("Expected duplicate alert error to be translated")


def test_get_alert_returns_none_when_item_does_not_exist(monkeypatch):
    mock_table = Mock()
    mock_table.get_item.return_value = {}
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)

    result = alert_repository.get_alert("missing-id")

    assert result is None
    mock_table.get_item.assert_called_once_with(
        Key={"PK": "ALERT#missing-id", "SK": "METADATA"}
    )


def test_get_alert_returns_deserialized_item(monkeypatch):
    mock_table = Mock()
    mock_table.get_item.return_value = {
        "Item": {
            "PK": "ALERT#alert-1",
            "SK": "METADATA",
            "alertId": "alert-1",
            "amount": Decimal("5000.25"),
            "transactionCountLastHour": Decimal("3"),
        }
    }
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)

    result = alert_repository.get_alert("alert-1")

    assert result == {
        "PK": "ALERT#alert-1",
        "SK": "METADATA",
        "alertId": "alert-1",
        "amount": 5000.25,
        "transactionCountLastHour": 3,
    }


def test_list_alerts_respects_limit_and_deserializes_items(monkeypatch):
    mock_table = Mock()
    mock_table.scan.side_effect = [
        {
            "Items": [
                {
                    "PK": "ALERT#1",
                    "SK": "METADATA",
                    "alertId": "1",
                    "amount": Decimal("100.5"),
                }
            ],
            "LastEvaluatedKey": {"PK": "ALERT#1", "SK": "METADATA"},
        },
        {
            "Items": [
                {
                    "PK": "ALERT#2",
                    "SK": "METADATA",
                    "alertId": "2",
                    "amount": Decimal("200"),
                }
            ]
        },
    ]
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)

    result = alert_repository.list_alerts(limit=2)

    assert result == [
        {
            "PK": "ALERT#1",
            "SK": "METADATA",
            "alertId": "1",
            "amount": 100.5,
        },
        {
            "PK": "ALERT#2",
            "SK": "METADATA",
            "alertId": "2",
            "amount": 200,
        },
    ]
    assert mock_table.scan.call_count == 2


def test_list_alerts_rejects_invalid_limit():
    try:
        alert_repository.list_alerts(limit=0)
    except ValueError as error:
        assert str(error) == "limit must be greater than 0"
    else:
        raise AssertionError("Expected invalid limit to raise ValueError")


def test_update_status_updates_status_and_timestamp(monkeypatch):
    mock_table = Mock()
    mock_table.update_item.return_value = {
        "Attributes": {
            "PK": "ALERT#alert-1",
            "SK": "METADATA",
            "alertId": "alert-1",
            "status": "PROCESSING",
            "updatedAt": "2026-05-04T12:30:00Z",
        }
    }
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)
    monkeypatch.setattr(
        alert_repository,
        "_current_timestamp",
        lambda: "2026-05-04T12:30:00Z",
    )

    result = alert_repository.update_status("alert-1", "PROCESSING")

    assert result["status"] == "PROCESSING"
    update_kwargs = mock_table.update_item.call_args.kwargs
    assert update_kwargs["Key"] == {"PK": "ALERT#alert-1", "SK": "METADATA"}
    assert update_kwargs["ExpressionAttributeValues"] == {
        ":status": "PROCESSING",
        ":updatedAt": "2026-05-04T12:30:00Z",
    }


def test_update_status_translates_missing_alert_error(monkeypatch):
    mock_table = Mock()
    mock_table.update_item.side_effect = FakeAwsClientError(
        "ConditionalCheckFailedException"
    )
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)
    monkeypatch.setattr(
        alert_repository,
        "_current_timestamp",
        lambda: "2026-05-04T12:30:00Z",
    )

    try:
        alert_repository.update_status("missing-alert", "PROCESSING")
    except alert_repository.AlertNotFoundError as error:
        assert str(error) == "Alert was not found"
    else:
        raise AssertionError("Expected missing alert error to be translated")


def test_update_analysis_result_updates_nested_result(monkeypatch):
    mock_table = Mock()
    mock_table.update_item.return_value = {
        "Attributes": {
            "PK": "ALERT#alert-2",
            "SK": "METADATA",
            "alertId": "alert-2",
            "analysisResult": {
                "riskScore": Decimal("72"),
                "signals": ["High transaction velocity"],
            },
            "updatedAt": "2026-05-04T13:00:00Z",
        }
    }
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)
    monkeypatch.setattr(
        alert_repository,
        "_current_timestamp",
        lambda: "2026-05-04T13:00:00Z",
    )

    result = alert_repository.update_analysis_result(
        "alert-2",
        {
            "riskScore": 72,
            "signals": ["High transaction velocity"],
        },
    )

    assert result == {
        "PK": "ALERT#alert-2",
        "SK": "METADATA",
        "alertId": "alert-2",
        "analysisResult": {
            "riskScore": 72,
            "signals": ["High transaction velocity"],
        },
        "updatedAt": "2026-05-04T13:00:00Z",
    }

    update_kwargs = mock_table.update_item.call_args.kwargs
    assert update_kwargs["ExpressionAttributeValues"] == {
        ":analysisResult": {
            "riskScore": 72,
            "signals": ["High transaction velocity"],
        },
        ":updatedAt": "2026-05-04T13:00:00Z",
    }


def test_get_table_name_requires_environment_variable(monkeypatch):
    monkeypatch.delenv("ALERTS_TABLE_NAME", raising=False)

    try:
        alert_repository._get_table_name()
    except alert_repository.RepositoryConfigurationError as error:
        assert str(error) == "ALERTS_TABLE_NAME environment variable is not set"
    else:
        raise AssertionError("Expected missing table name to raise an error")


def test_get_table_name_strips_whitespace(monkeypatch):
    monkeypatch.setenv("ALERTS_TABLE_NAME", " alerts-table ")

    assert alert_repository._get_table_name() == "alerts-table"


def test_append_review_event_appends_audit_friendly_event(monkeypatch):
    mock_table = Mock()
    review_event = {
        "reviewEventId": "review-1",
        "action": "ESCALATE",
        "reviewedAt": "2026-07-11T10:00:00Z",
        "workflowRunId": "run-1",
        "workflowVersion": "nttdata-fraud-investigation-v1",
    }
    mock_table.update_item.return_value = {
        "Attributes": {
            "PK": "ALERT#alert-1",
            "SK": "METADATA",
            "reviewHistory": [review_event],
            "reviewStatus": "ESCALATE",
        }
    }
    monkeypatch.setattr(alert_repository, "_get_table", lambda: mock_table)
    monkeypatch.setattr(
        alert_repository,
        "_current_timestamp",
        lambda: "2026-07-11T10:00:01Z",
    )

    result = alert_repository.append_review_event("alert-1", review_event)

    assert result["reviewHistory"] == [review_event]
    update_kwargs = mock_table.update_item.call_args.kwargs
    assert "list_append" in update_kwargs["UpdateExpression"]
    assert update_kwargs["ExpressionAttributeValues"][":event"] == [review_event]
    assert update_kwargs["ExpressionAttributeValues"][":reviewStatus"] == "ESCALATE"
