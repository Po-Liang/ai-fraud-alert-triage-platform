import json
from typing import Any

DEFAULT_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def _json_response(payload: Any, status_code: int) -> dict:
    return {
        "statusCode": status_code,
        "headers": DEFAULT_HEADERS.copy(),
        "body": json.dumps(payload, ensure_ascii=False),
    }


def success_response(data: dict, status_code: int = 200) -> dict:
    return _json_response(data, status_code=status_code)


def error_response(message: str, status_code: int = 400) -> dict:
    return _json_response({"message": message}, status_code=status_code)
