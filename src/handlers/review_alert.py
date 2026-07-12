import json
import logging
from json import JSONDecodeError

from src.services import alert_service
from src.utils.response import error_response, success_response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    del context

    path_parameters = event.get("pathParameters") or {}
    alert_id = str(path_parameters.get("alertId") or "").strip()
    if not alert_id:
        return error_response("alertId path parameter is required", status_code=400)

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
        result = alert_service.record_review(alert_id, input_data)
    except ValueError as error:
        return error_response(str(error), status_code=400)
    except alert_service.AlertNotFoundError:
        return error_response("Alert not found", status_code=404)
    except alert_service.AlertServiceError as error:
        logger.exception("review_alert_failed alertId=%s", alert_id)
        return error_response(str(error), status_code=500)

    return success_response(result, status_code=201)
