from __future__ import annotations

import json
import os
from datetime import datetime, timezone

ANALYSIS_QUEUE_URL_ENV_VAR = "ANALYSIS_QUEUE_URL"


class QueueServiceError(RuntimeError):
    """Raised when an SQS queue operation cannot be completed."""


class QueueConfigurationError(QueueServiceError):
    """Raised when queue configuration is incomplete."""


def _current_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _get_queue_url() -> str:
    queue_url = os.getenv(ANALYSIS_QUEUE_URL_ENV_VAR, "").strip()
    if not queue_url:
        raise QueueConfigurationError(
            f"{ANALYSIS_QUEUE_URL_ENV_VAR} environment variable is not set"
        )

    return queue_url


def _get_client():
    try:
        import boto3
    except ImportError as error:
        raise QueueConfigurationError("boto3 is required to use the queue service") from error

    return boto3.client("sqs")


def send_analysis_job(
    alert_id: str,
    analysis_type: str = "INITIAL_ANALYSIS",
) -> dict:
    requested_at = _current_timestamp()
    message_body = json.dumps(
        {
            "alertId": alert_id,
            "analysisType": analysis_type,
            "requestedAt": requested_at,
        }
    )

    client = _get_client()
    queue_url = _get_queue_url()
    try:
        response = client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
        )
    except Exception as error:
        raise QueueServiceError("Failed to send analysis job to SQS") from error

    return {
        "messageId": response.get("MessageId"),
        "queueUrl": queue_url,
        "requestedAt": requested_at,
    }
