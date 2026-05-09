from __future__ import annotations

from typing import Any


def _require_non_empty_string(input_data: dict[str, Any], field_name: str) -> str:
    value = input_data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required and must be a non-empty string")

    return value.strip()


def _optional_string(
    input_data: dict[str, Any],
    field_name: str,
    default: str | None = None,
) -> str | None:
    value = input_data.get(field_name, default)
    if value is None:
        return None

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string when provided")

    return value.strip()


def _non_negative_float(
    input_data: dict[str, Any],
    field_name: str,
    default: float | None = None,
) -> float:
    if field_name in input_data:
        value = input_data[field_name]
    else:
        value = default

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")

    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")

    return float(value)


def _non_negative_int(
    input_data: dict[str, Any],
    field_name: str,
    default: int = 0,
) -> int:
    value = input_data.get(field_name, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")

    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")

    return value


def _optional_bool(
    input_data: dict[str, Any],
    field_name: str,
    default: bool = False,
) -> bool:
    value = input_data.get(field_name, default)
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")

    return value


def validate_alert_input(input_data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(input_data, dict):
        raise ValueError("Alert input must be a JSON object")

    return {
        "customerId": _require_non_empty_string(input_data, "customerId"),
        "accountId": _require_non_empty_string(input_data, "accountId"),
        "alertType": _require_non_empty_string(input_data, "alertType"),
        "amount": _non_negative_float(input_data, "amount"),
        "currency": _optional_string(input_data, "currency", default="JPY"),
        "country": _require_non_empty_string(input_data, "country"),
        "description": _optional_string(input_data, "description", default=None),
        "historicalAverageAmount": _non_negative_float(
            input_data,
            "historicalAverageAmount",
            default=0,
        ),
        "isNewBeneficiary": _optional_bool(
            input_data,
            "isNewBeneficiary",
            default=False,
        ),
        "transactionCountLastHour": _non_negative_int(
            input_data,
            "transactionCountLastHour",
            default=0,
        ),
    }
