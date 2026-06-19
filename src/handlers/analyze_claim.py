import json
from json import JSONDecodeError

from src.services import claim_review_service
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

    claim_text = str(input_data.get("claimText") or "").strip()
    if not claim_text:
        return error_response("claimText is required", status_code=400)

    result = claim_review_service.analyze_claim_text(claim_text)

    return success_response(result)
