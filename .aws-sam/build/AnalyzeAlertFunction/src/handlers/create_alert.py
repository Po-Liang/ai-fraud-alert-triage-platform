import json
from json import JSONDecodeError

from pydantic import ValidationError

from src.services import alert_service
from src.utils.response import error_response, success_response


def lambda_handler(event, context):
    del context

    body = event.get("body")
    if body is None:
        return error_response("Request body is required", status_code=400)

    try:
        input_data = json.loads(body)
    except (TypeError, JSONDecodeError):
        return error_response("Request body must be valid JSON", status_code=400)

    if not isinstance(input_data, dict):
        return error_response("Request body must be a JSON object", status_code=400)

    try:
        created_alert = alert_service.create_alert(input_data)
    except (ValidationError, ValueError) as error:
        return error_response(str(error), status_code=400)

    return success_response(created_alert, status_code=201)
