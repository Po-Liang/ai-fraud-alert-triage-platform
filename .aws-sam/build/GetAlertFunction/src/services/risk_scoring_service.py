from typing import Any, Dict, List


def calculate_risk_score(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a deterministic fraud risk score based on alert attributes.

    The AI model should not directly decide fraud.
    This service produces explainable risk signals first.
    """

    risk_score = 0
    signals: List[str] = []

    amount = float(alert.get("amount", 0) or 0)
    historical_average = float(alert.get("historicalAverageAmount", 0) or 0)
    is_new_beneficiary = bool(alert.get("isNewBeneficiary", False))
    transaction_count_last_hour = int(alert.get("transactionCountLastHour", 0) or 0)
    country = str(alert.get("country", "")).upper()

    high_risk_countries = {"IR", "KP", "SY"}

    # Rule 1: Amount anomaly
    if historical_average > 0:
        ratio = amount / historical_average

        if ratio >= 10:
            risk_score += 30
            signals.append(
                f"Transaction amount is {ratio:.1f}x higher than historical average"
            )
        elif ratio >= 5:
            risk_score += 20
            signals.append(
                f"Transaction amount is {ratio:.1f}x higher than historical average"
            )
        elif ratio >= 3:
            risk_score += 10
            signals.append(
                f"Transaction amount is {ratio:.1f}x higher than historical average"
            )

    # Rule 2: New beneficiary
    if is_new_beneficiary:
        risk_score += 25
        signals.append("Beneficiary is new")

    # Rule 3: Transaction velocity
    if transaction_count_last_hour >= 5:
        risk_score += 20
        signals.append("High transaction velocity in the last hour")
    elif transaction_count_last_hour >= 3:
        risk_score += 10
        signals.append("Moderate transaction velocity in the last hour")

    # Rule 4: High-risk country
    if country in high_risk_countries:
        risk_score += 15
        signals.append("Transaction involves a high-risk country")

    # Rule 5: Large absolute amount
    if amount >= 1_000_000:
        risk_score += 10
        signals.append("Transaction amount exceeds 1,000,000 JPY")

    # Cap score at 100
    risk_score = min(risk_score, 100)

    risk_level = classify_risk_level(risk_score)

    return {
        "riskScore": risk_score,
        "riskLevel": risk_level,
        "signals": signals,
    }


def classify_risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"

    if score >= 40:
        return "MEDIUM"

    return "LOW"
