import json
from json import JSONDecodeError

from src.services import rag_service
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

    question = str(input_data.get("question") or "").strip()
    if not question:
        return error_response("question is required", status_code=400)

    result = rag_service.answer_question(question)

    return success_response(result)
