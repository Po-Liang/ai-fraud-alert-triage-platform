from typing import Any, Dict, List


def generate_investigation_summary(
    alert: Dict[str, Any],
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate an investigation summary.

    MVP version:
    This is a deterministic stub.

    Future version:
    Replace this with OpenAI API or Amazon Bedrock.
    """

    risk_level = risk_result.get("riskLevel", "UNKNOWN")
    signals: List[str] = risk_result.get("signals", [])

    if signals:
        signal_text = "; ".join(signals)
    else:
        signal_text = "No major suspicious signals were detected."

    summary = (
        f"This alert is classified as {risk_level} risk based on the current "
        f"rule-based scoring logic. Key signals: {signal_text}. "
        "This summary is intended to support human investigation and does not "
        "make a final fraud determination."
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
