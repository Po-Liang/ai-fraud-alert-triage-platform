import json
import logging
from json import JSONDecodeError

from src.services import rag_service
from src.utils.response import error_response, success_response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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

    try:
        result = rag_service.answer_question(question)
    except Exception:
        logger.exception("rag_query_failed")
        return error_response(
            "ガイドライン検索を完了できませんでした。しばらくしてから再度お試しください。",
            status_code=500,
        )

    return success_response(result)
