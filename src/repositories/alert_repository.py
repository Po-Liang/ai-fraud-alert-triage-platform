from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

ALERTS_TABLE_NAME_ENV_VAR = "ALERTS_TABLE_NAME"
ALERT_PRIMARY_KEY_PREFIX = "ALERT#"
ALERT_METADATA_SORT_KEY = "METADATA"


class RepositoryConfigurationError(RuntimeError):
    """Raised when repository configuration is incomplete."""


class AlertRepositoryError(RuntimeError):
    """Raised when a DynamoDB repository operation fails."""


class AlertAlreadyExistsError(AlertRepositoryError):
    """Raised when attempting to create an alert that already exists."""


class AlertNotFoundError(AlertRepositoryError):
    """Raised when an alert cannot be found for an update operation."""


def _get_table_name() -> str:
    table_name = os.getenv(ALERTS_TABLE_NAME_ENV_VAR, "").strip()

    if not table_name:
        raise RepositoryConfigurationError(
            f"{ALERTS_TABLE_NAME_ENV_VAR} environment variable is not set"
        )

    return table_name


def _get_table():
    try:
        import boto3
    except ImportError as error:
        raise RepositoryConfigurationError(
            "boto3 is required to use the alert repository"
        ) from error

    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(_get_table_name())


def _build_key(alert_id: str) -> dict[str, str]:
    return {
        "PK": f"{ALERT_PRIMARY_KEY_PREFIX}{alert_id}",
        "SK": ALERT_METADATA_SORT_KEY,
    }


def _current_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _serialize_for_dynamodb(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _serialize_for_dynamodb(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_serialize_for_dynamodb(item) for item in value]

    if isinstance(value, float):
        return Decimal(str(value))

    return value


def _deserialize_from_dynamodb(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _deserialize_from_dynamodb(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_deserialize_from_dynamodb(item) for item in value]

    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)

        return float(value)

    return value


def _get_aws_error_code(error: Exception) -> str | None:
    response = getattr(error, "response", None)
    if not isinstance(response, dict):
        return None

    error_payload = response.get("Error")
    if not isinstance(error_payload, dict):
        return None

    code = error_payload.get("Code")
    if isinstance(code, str):
        return code

    return None


def _raise_repository_error(error: Exception, operation: str) -> None:
    error_code = _get_aws_error_code(error)

    if error_code == "ConditionalCheckFailedException":
        if operation == "create":
            raise AlertAlreadyExistsError("Alert already exists") from error

        if operation in {
            "update_status",
            "update_analysis_result",
            "append_review_event",
        }:
            raise AlertNotFoundError("Alert was not found") from error

    if error_code is not None:
        raise AlertRepositoryError(
            f"DynamoDB operation failed during {operation}: {error_code}"
        ) from error

    raise error


def _require_alert_id(alert: dict[str, Any]) -> str:
    alert_id = str(alert.get("alertId", "")).strip()
    if not alert_id:
        raise ValueError("alert must include a non-empty alertId")

    return alert_id


def create_alert(alert: dict) -> dict:
    alert_id = _require_alert_id(alert)
    timestamp = _current_timestamp()
    item = {
        **alert,
        "alertId": alert_id,
        **_build_key(alert_id),
        "createdAt": alert.get("createdAt", timestamp),
        "updatedAt": timestamp,
    }

    table = _get_table()
    try:
        table.put_item(
            Item=_serialize_for_dynamodb(item),
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )
    except Exception as error:
        _raise_repository_error(error, operation="create")

    return item


def get_alert(alert_id: str) -> dict | None:
    table = _get_table()
    try:
        response = table.get_item(Key=_build_key(alert_id))
    except Exception as error:
        _raise_repository_error(error, operation="get_alert")

    item = response.get("Item")

    if not item:
        return None

    return _deserialize_from_dynamodb(item)


def list_alerts(limit: int = 20) -> list[dict]:
    if limit < 1:
        raise ValueError("limit must be greater than 0")

    table = _get_table()
    items: list[dict] = []
    scan_kwargs: dict[str, Any] = {
        "FilterExpression": "#sk = :sk",
        "ExpressionAttributeNames": {"#sk": "SK"},
        "ExpressionAttributeValues": {":sk": ALERT_METADATA_SORT_KEY},
        "Limit": limit,
    }

    while len(items) < limit:
        try:
            response = table.scan(**scan_kwargs)
        except Exception as error:
            _raise_repository_error(error, operation="list_alerts")

        page_items = response.get("Items", [])

        for item in page_items:
            items.append(_deserialize_from_dynamodb(item))
            if len(items) == limit:
                break

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key or len(items) == limit:
            break

        scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

    return items


def update_status(alert_id: str, status: str) -> dict:
    table = _get_table()
    timestamp = _current_timestamp()
    try:
        response = table.update_item(
            Key=_build_key(alert_id),
            UpdateExpression="SET #status = :status, updatedAt = :updatedAt",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues=_serialize_for_dynamodb(
                {
                    ":status": status,
                    ":updatedAt": timestamp,
                }
            ),
            ReturnValues="ALL_NEW",
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except Exception as error:
        _raise_repository_error(error, operation="update_status")

    return _deserialize_from_dynamodb(response.get("Attributes", {}))


def update_analysis_result(alert_id: str, analysis_result: dict) -> dict:
    table = _get_table()
    timestamp = _current_timestamp()
    try:
        response = table.update_item(
            Key=_build_key(alert_id),
            UpdateExpression=(
                "SET analysisResult = :analysisResult, updatedAt = :updatedAt"
            ),
            ExpressionAttributeValues=_serialize_for_dynamodb(
                {
                    ":analysisResult": analysis_result,
                    ":updatedAt": timestamp,
                }
            ),
            ReturnValues="ALL_NEW",
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except Exception as error:
        _raise_repository_error(error, operation="update_analysis_result")

    return _deserialize_from_dynamodb(response.get("Attributes", {}))


def append_review_event(alert_id: str, review_event: dict[str, Any]) -> dict:
    table = _get_table()
    timestamp = _current_timestamp()
    review_status = str(review_event.get("action", "")).strip()
    if not review_status:
        raise ValueError("review_event must include an action")

    try:
        response = table.update_item(
            Key=_build_key(alert_id),
            UpdateExpression=(
                "SET reviewHistory = list_append(if_not_exists(reviewHistory, :empty), :event), "
                "reviewStatus = :reviewStatus, updatedAt = :updatedAt"
            ),
            ExpressionAttributeValues=_serialize_for_dynamodb(
                {
                    ":empty": [],
                    ":event": [review_event],
                    ":reviewStatus": review_status,
                    ":updatedAt": timestamp,
                }
            ),
            ReturnValues="ALL_NEW",
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
        )
    except Exception as error:
        _raise_repository_error(error, operation="append_review_event")

    return _deserialize_from_dynamodb(response.get("Attributes", {}))
