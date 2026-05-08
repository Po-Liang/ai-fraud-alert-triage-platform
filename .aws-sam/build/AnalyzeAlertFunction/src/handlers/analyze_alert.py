from src.services import alert_service
from src.utils.response import error_response, success_response


def lambda_handler(event, context):
    del context

    path_parameters = event.get("pathParameters") or {}
    alert_id = str(path_parameters.get("alertId") or "").strip()

    if not alert_id:
        return error_response("alertId path parameter is required", status_code=400)

    try:
        analysis_result = alert_service.analyze_alert(alert_id)
    except alert_service.AlertNotFoundError:
        return error_response("Alert not found", status_code=404)

    return success_response(analysis_result)
