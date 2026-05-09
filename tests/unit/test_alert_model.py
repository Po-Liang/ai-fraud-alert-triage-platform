from src.models.alert import validate_alert_input


def test_validate_alert_input_applies_defaults():
    result = validate_alert_input(
        {
            "customerId": "cust-1",
            "accountId": "acct-1",
            "alertType": "SUSPICIOUS_TRANSFER",
            "amount": 1000,
            "country": "JP",
        }
    )

    assert result == {
        "customerId": "cust-1",
        "accountId": "acct-1",
        "alertType": "SUSPICIOUS_TRANSFER",
        "amount": 1000.0,
        "currency": "JPY",
        "country": "JP",
        "description": None,
        "historicalAverageAmount": 0.0,
        "isNewBeneficiary": False,
        "transactionCountLastHour": 0,
    }


def test_validate_alert_input_rejects_missing_required_string():
    try:
        validate_alert_input(
            {
                "accountId": "acct-1",
                "alertType": "SUSPICIOUS_TRANSFER",
                "amount": 1000,
                "country": "JP",
            }
        )
    except ValueError as error:
        assert str(error) == "customerId is required and must be a non-empty string"
    else:
        raise AssertionError("Expected validate_alert_input to reject missing customerId")


def test_validate_alert_input_rejects_negative_amount():
    try:
        validate_alert_input(
            {
                "customerId": "cust-1",
                "accountId": "acct-1",
                "alertType": "SUSPICIOUS_TRANSFER",
                "amount": -1,
                "country": "JP",
            }
        )
    except ValueError as error:
        assert str(error) == "amount must be greater than or equal to 0"
    else:
        raise AssertionError("Expected validate_alert_input to reject negative amount")


def test_validate_alert_input_rejects_non_integer_transaction_count():
    try:
        validate_alert_input(
            {
                "customerId": "cust-1",
                "accountId": "acct-1",
                "alertType": "SUSPICIOUS_TRANSFER",
                "amount": 1000,
                "country": "JP",
                "transactionCountLastHour": 1.5,
            }
        )
    except ValueError as error:
        assert str(error) == "transactionCountLastHour must be an integer"
    else:
        raise AssertionError(
            "Expected validate_alert_input to reject non-integer transaction count"
        )
