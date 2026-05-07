from src.services import alert_service
from src.utils.response import error_response, success_response


def lambda_handler(event, context):
    del context

    query_parameters = event.get("queryStringParameters") or {}
    raw_limit = query_parameters.get("limit")

    if raw_limit in (None, ""):
        limit = 20
    else:
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return error_response("limit must be an integer", status_code=400)

    try:
        alerts = alert_service.list_alerts(limit=limit)
    except ValueError as error:
        return error_response(str(error), status_code=400)

    return success_response({"items": alerts})
