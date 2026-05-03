from src.services.risk_scoring_service import calculate_risk_score


def test_low_risk_alert():
    alert = {
        "amount": 10000,
        "historicalAverageAmount": 9000,
        "isNewBeneficiary": False,
        "transactionCountLastHour": 1,
        "country": "JP",
    }

    result = calculate_risk_score(alert)

    assert result["riskLevel"] == "LOW"
    assert result["riskScore"] < 40
    assert isinstance(result["signals"], list)


def test_high_risk_alert_with_large_amount_new_beneficiary_and_velocity():
    alert = {
        "amount": 950000,
        "historicalAverageAmount": 50000,
        "isNewBeneficiary": True,
        "transactionCountLastHour": 8,
        "country": "JP",
    }

    result = calculate_risk_score(alert)

    assert result["riskLevel"] == "HIGH"
    assert result["riskScore"] >= 70
    assert "Beneficiary is new" in result["signals"]
    assert "High transaction velocity in the last hour" in result["signals"]


def test_medium_risk_alert():
    alert = {
        "amount": 2500000,
        "historicalAverageAmount": 50000,
        "isNewBeneficiary": False,
        "transactionCountLastHour": 3,
        "country": "JP",
    }

    result = calculate_risk_score(alert)

    assert result["riskLevel"] == "MEDIUM"
    assert 40 <= result["riskScore"] < 70


def test_high_risk_country_adds_signal():
    alert = {
        "amount": 10000,
        "historicalAverageAmount": 10000,
        "isNewBeneficiary": False,
        "transactionCountLastHour": 1,
        "country": "IR",
    }

    result = calculate_risk_score(alert)

    assert "Transaction involves a high-risk country" in result["signals"]


def test_zero_historical_average_does_not_crash():
    alert = {
        "amount": 100000,
        "historicalAverageAmount": 0,
        "isNewBeneficiary": False,
        "transactionCountLastHour": 1,
        "country": "JP",
    }

    result = calculate_risk_score(alert)

    assert result["riskScore"] >= 0
    assert result["riskLevel"] in ["LOW", "MEDIUM", "HIGH"]
