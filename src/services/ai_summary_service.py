from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List

from src.services import secrets_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_investigation_summary(
    alert: Dict[str, Any],
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    alert_id = alert.get("alertId")
    logger.info("ai_summary_service_called alertId=%s", alert_id)
    logger.info("openai_secret_lookup_started alertId=%s", alert_id)
    api_key = secrets_service.get_openai_api_key()
    if not api_key:
        logger.info("ai_summary_fallback_used alertId=%s reason=missing_openai_api_key", alert_id)
        result = _generate_fallback_summary(risk_result)
        logger.info("ai_summary_result_returned alertId=%s mode=fallback", alert_id)
        return result

    logger.info("openai_secret_lookup_succeeded alertId=%s", alert_id)

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        result = _generate_openai_summary(
            alert=alert,
            risk_result=risk_result,
            api_key=api_key,
            model=model,
        )
        logger.info("ai_summary_result_returned alertId=%s mode=openai", alert_id)
        return result
    except Exception:
        logger.warning("openai_api_call_failed alertId=%s", alert_id)
        logger.info("ai_summary_fallback_used alertId=%s reason=openai_call_failed", alert_id)
        result = _generate_fallback_summary(risk_result)
        logger.info("ai_summary_result_returned alertId=%s mode=fallback", alert_id)
        return result


def _generate_openai_summary(
    alert: Dict[str, Any],
    risk_result: Dict[str, Any],
    api_key: str,
    model: str,
) -> Dict[str, Any]:
    alert_id = alert.get("alertId")
    logger.info("openai_api_call_attempted alertId=%s model=%s", alert_id, model)
    prompt = _build_prompt(alert, risk_result)
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You support fraud investigators. Respond in Japanese. You must not make a final "
                        "fraud determination. Use cautious language such as 'may "
                        "indicate', 'should be reviewed', and 'requires verification'. "
                        "Return only valid JSON with keys aiSummary and "
                        "recommendedActions. recommendedActions must be an array of "
                        "short strings."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url="https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        status_code = getattr(response, "status", None)
        if status_code is None and hasattr(response, "getcode"):
            status_code = response.getcode()
        logger.info(
            "openai_api_call_succeeded alertId=%s model=%s statusCode=%s",
            alert_id,
            model,
            status_code,
        )
        response_body = response.read().decode("utf-8")

    parsed_response = json.loads(response_body)
    content = (
        parsed_response.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not isinstance(content, str):
        raise ValueError("OpenAI response content is missing")

    parsed_content = json.loads(content)
    validated_output = _validate_ai_output(parsed_content)
    logger.info("ai_summary_parsing_succeeded alertId=%s", alert_id)
    return validated_output


def _build_prompt(alert: Dict[str, Any], risk_result: Dict[str, Any]) -> str:
    return json.dumps(
        {
            "alert": {
                "alertId": alert.get("alertId"),
                "alertType": alert.get("alertType"),
                "amount": alert.get("amount"),
                "country": alert.get("country"),
                "description": alert.get("description"),
                "historicalAverageAmount": alert.get("historicalAverageAmount"),
                "isNewBeneficiary": alert.get("isNewBeneficiary"),
                "transactionCountLastHour": alert.get("transactionCountLastHour"),
            },
            "riskResult": risk_result,
            "instructions": {
                "summaryStyle": (
                    "Write a brief investigation summary that mentions suspicious "
                    "signals cautiously and explicitly states the case requires "
                    "human verification."
                ),
                "outputFormat": {
                    "aiSummary": "string",
                    "recommendedActions": ["string"],
                },
            },
        }
    )


def _validate_ai_output(parsed_content: Any) -> Dict[str, Any]:
    if not isinstance(parsed_content, dict):
        raise ValueError("AI output must be a JSON object")

    ai_summary = parsed_content.get("aiSummary")
    recommended_actions = parsed_content.get("recommendedActions")

    if not isinstance(ai_summary, str) or not ai_summary.strip():
        raise ValueError("AI output aiSummary is invalid")

    if not isinstance(recommended_actions, list) or not recommended_actions:
        raise ValueError("AI output recommendedActions is invalid")

    if not all(isinstance(item, str) and item.strip() for item in recommended_actions):
        raise ValueError("AI output recommendedActions entries are invalid")

    return {
        "aiSummary": ai_summary.strip(),
        "recommendedActions": [item.strip() for item in recommended_actions],
    }


def _generate_fallback_summary(risk_result: Dict[str, Any]) -> Dict[str, Any]:
    risk_level = risk_result.get("riskLevel", "UNKNOWN")
    signals: List[str] = risk_result.get("signals", [])

    if signals:
        signal_text = "; ".join(signals)
    else:
        signal_text = "No major suspicious signals were detected."

    summary = (
        f"This alert is currently assessed as {risk_level} risk based on the "
        f"deterministic scoring logic. Key signals may indicate suspicious "
        f"activity and should be reviewed: {signal_text}. This case requires "
        "verification by a human investigator and does not make a final fraud "
        "determination."
    )

    recommended_actions = generate_recommended_actions(risk_level)

    return {
        "aiSummary": summary,
        "recommendedActions": recommended_actions,
    }


def generate_recommended_actions(risk_level: str) -> List[str]:
    if risk_level == "HIGH":
        return [
            "Verify the beneficiary relationship",
            "Review recent login and device activity",
            "Check for similar alerts on the same customer",
            "Escalate for manual investigation",
        ]

    if risk_level == "MEDIUM":
        return [
            "Review customer transaction history",
            "Check whether the transaction pattern is unusual",
            "Monitor for additional suspicious activity",
        ]

    return [
        "Record the alert result",
        "No immediate escalation required based on current signals",
    ]
