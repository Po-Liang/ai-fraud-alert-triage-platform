from src.services import alert_service
from src.utils.response import error_response, success_response


def lambda_handler(event, context):
    del context

    path_parameters = event.get("pathParameters") or {}
    alert_id = str(path_parameters.get("alertId") or "").strip()

    if not alert_id:
        return error_response("alertId path parameter is required", status_code=400)

    try:
        queued_result = alert_service.request_analysis(alert_id)
    except alert_service.AlertNotFoundError:
        return error_response("Alert not found", status_code=404)
    except alert_service.AnalysisRequestError as error:
        return error_response(str(error), status_code=500)

    return success_response(queued_result, status_code=202)
