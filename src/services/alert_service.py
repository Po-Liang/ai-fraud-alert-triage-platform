from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.models.alert import validate_alert_input
from src.repositories import alert_repository
from src.services import ai_summary_service, queue_service, risk_scoring_service

STATUS_PENDING_ANALYSIS = "PENDING_ANALYSIS"
STATUS_ANALYSIS_IN_PROGRESS = "ANALYSIS_IN_PROGRESS"
STATUS_ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
WORKFLOW_VERSION = "nttdata-fraud-investigation-v1"
ALLOWED_REVIEW_ACTIONS = {
    "APPROVE",
    "REQUEST_REANALYSIS",
    "ESCALATE",
    "CLOSE",
}
MAX_REVIEW_COMMENT_LENGTH = 1000
MAX_WORKFLOW_RUN_ID_LENGTH = 100

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AlertServiceError(RuntimeError):
    """Raised when an alert service operation cannot be completed."""


class AlertNotFoundError(AlertServiceError):
    """Raised when the requested alert does not exist."""


class AnalysisRequestError(AlertServiceError):
    """Raised when an analysis job cannot be queued."""


def _current_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _generate_alert_id() -> str:
    return str(uuid4())


def _get_or_generate_alert_id(input_data: dict[str, Any]) -> str:
    alert_id = str(input_data.get("alertId", "")).strip()
    if alert_id:
        return alert_id

    return _generate_alert_id()


def _build_alert_for_create(input_data: dict[str, Any]) -> dict[str, Any]:
    validated_input = validate_alert_input(input_data)
    created_at = input_data.get("createdAt") or _current_timestamp()

    return {
        **validated_input,
        "alertId": _get_or_generate_alert_id(input_data),
        "status": STATUS_PENDING_ANALYSIS,
        "createdAt": created_at,
        "updatedAt": created_at,
    }


def _build_analysis_result(
    risk_result: dict[str, Any],
    summary_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "riskScore": risk_result["riskScore"],
        "riskLevel": risk_result["riskLevel"],
        "signals": risk_result["signals"],
        "aiSummary": summary_result["aiSummary"],
        "recommendedActions": summary_result["recommendedActions"],
    }


def _queue_analysis_job(
    alert_id: str,
    analysis_type: str = "INITIAL_ANALYSIS",
) -> dict[str, Any]:
    try:
        return queue_service.send_analysis_job(
            alert_id,
            analysis_type=analysis_type,
        )
    except queue_service.QueueServiceError as error:
        raise AnalysisRequestError("Failed to queue analysis job") from error


def create_alert(input_data: dict) -> dict:
    created_alert = alert_repository.create_alert(_build_alert_for_create(input_data))
    _queue_analysis_job(created_alert["alertId"])

    return created_alert


def get_alert(alert_id: str) -> dict | None:
    return alert_repository.get_alert(alert_id)


def list_alerts(limit: int = 20) -> list[dict]:
    return alert_repository.list_alerts(limit=limit)


def request_analysis(alert_id: str) -> dict:
    alert = alert_repository.get_alert(alert_id)
    if alert is None:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist")

    try:
        alert_repository.update_status(alert_id, STATUS_PENDING_ANALYSIS)
    except alert_repository.AlertNotFoundError as error:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist") from error

    queue_result = _queue_analysis_job(alert_id)

    return {
        "alertId": alert_id,
        "status": STATUS_PENDING_ANALYSIS,
        "message": "Analysis job queued",
        "messageId": queue_result.get("messageId"),
    }


def analyze_alert(alert_id: str) -> dict:
    logger.info("alert_service_analyze_started alertId=%s", alert_id)
    alert = alert_repository.get_alert(alert_id)
    if alert is None:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist")

    try:
        alert_repository.update_status(alert_id, STATUS_ANALYSIS_IN_PROGRESS)
    except alert_repository.AlertNotFoundError as error:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist") from error

    risk_result = risk_scoring_service.calculate_risk_score(alert)
    logger.info("risk_scoring_completed alertId=%s", alert_id)
    logger.info("ai_summary_generation_started alertId=%s", alert_id)
    summary_result = ai_summary_service.generate_investigation_summary(
        alert,
        risk_result,
    )
    logger.info("ai_summary_generation_completed alertId=%s", alert_id)
    analysis_result = _build_analysis_result(risk_result, summary_result)

    try:
        logger.info("analysis_result_update_started alertId=%s", alert_id)
        alert_repository.update_analysis_result(alert_id, analysis_result)
        alert_repository.update_status(alert_id, STATUS_ANALYSIS_COMPLETED)
        logger.info("analysis_result_update_completed alertId=%s", alert_id)
    except alert_repository.AlertNotFoundError as error:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist") from error

    return analysis_result


def record_review(alert_id: str, input_data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(input_data, dict):
        raise ValueError("Review input must be a JSON object")

    raw_action = input_data.get("action")
    if raw_action is None:
        raise ValueError("action is required")
    if not isinstance(raw_action, str):
        raise ValueError("action must be a string")
    action = raw_action.strip().upper()
    if action not in ALLOWED_REVIEW_ACTIONS:
        raise ValueError("action is not supported")

    raw_workflow_run_id = input_data.get("workflowRunId")
    if raw_workflow_run_id is None:
        raise ValueError("workflowRunId is required")
    if not isinstance(raw_workflow_run_id, str):
        raise ValueError("workflowRunId must be a string")
    workflow_run_id = raw_workflow_run_id.strip()
    if not workflow_run_id:
        raise ValueError("workflowRunId is required")
    if len(workflow_run_id) > MAX_WORKFLOW_RUN_ID_LENGTH:
        raise ValueError(
            f"workflowRunId must be {MAX_WORKFLOW_RUN_ID_LENGTH} characters or fewer"
        )

    raw_comment = input_data.get("comment")
    if raw_comment is None:
        comment = None
    elif not isinstance(raw_comment, str):
        raise ValueError("comment must be a string")
    else:
        comment = raw_comment.strip() or None
        if comment and len(comment) > MAX_REVIEW_COMMENT_LENGTH:
            raise ValueError(
                f"comment must be {MAX_REVIEW_COMMENT_LENGTH} characters or fewer"
            )

    if action in {"REQUEST_REANALYSIS", "ESCALATE"} and not comment:
        raise ValueError("comment is required for re-analysis or escalation")

    if alert_repository.get_alert(alert_id) is None:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist")

    reviewed_at = _current_timestamp()
    review_event = {
        "reviewEventId": str(uuid4()),
        "action": action,
        "reviewedAt": reviewed_at,
        "workflowRunId": workflow_run_id,
        "workflowVersion": WORKFLOW_VERSION,
    }
    if comment:
        review_event["comment"] = comment

    try:
        alert_repository.append_review_event(alert_id, review_event)
    except alert_repository.AlertNotFoundError as error:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist") from error
    except alert_repository.AlertRepositoryError as error:
        raise AlertServiceError("Failed to record review") from error

    return {
        "alertId": alert_id,
        "reviewStatus": action,
        "reviewEvent": review_event,
    }
