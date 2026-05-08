from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.models.alert import AlertInput
from src.repositories import alert_repository
from src.services import ai_summary_service, risk_scoring_service

STATUS_PENDING_ANALYSIS = "PENDING_ANALYSIS"
STATUS_ANALYSIS_IN_PROGRESS = "ANALYSIS_IN_PROGRESS"
STATUS_ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"


class AlertServiceError(RuntimeError):
    """Raised when an alert service operation cannot be completed."""


class AlertNotFoundError(AlertServiceError):
    """Raised when the requested alert does not exist."""


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


def _model_to_dict(model: AlertInput) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


def _build_alert_for_create(input_data: dict[str, Any]) -> dict[str, Any]:
    validated_input = AlertInput(**input_data)
    created_at = input_data.get("createdAt") or _current_timestamp()

    return {
        **_model_to_dict(validated_input),
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


def create_alert(input_data: dict) -> dict:
    return alert_repository.create_alert(_build_alert_for_create(input_data))


def get_alert(alert_id: str) -> dict | None:
    return alert_repository.get_alert(alert_id)


def list_alerts(limit: int = 20) -> list[dict]:
    return alert_repository.list_alerts(limit=limit)


def analyze_alert(alert_id: str) -> dict:
    alert = alert_repository.get_alert(alert_id)
    if alert is None:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist")

    try:
        alert_repository.update_status(alert_id, STATUS_ANALYSIS_IN_PROGRESS)
    except alert_repository.AlertNotFoundError as error:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist") from error

    risk_result = risk_scoring_service.calculate_risk_score(alert)
    summary_result = ai_summary_service.generate_investigation_summary(
        alert,
        risk_result,
    )
    analysis_result = _build_analysis_result(risk_result, summary_result)

    try:
        alert_repository.update_analysis_result(alert_id, analysis_result)
        alert_repository.update_status(alert_id, STATUS_ANALYSIS_COMPLETED)
    except alert_repository.AlertNotFoundError as error:
        raise AlertNotFoundError(f"Alert '{alert_id}' does not exist") from error

    return analysis_result
