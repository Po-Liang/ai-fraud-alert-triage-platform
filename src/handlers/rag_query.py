import json
import logging
from json import JSONDecodeError

from src.services import rag_service
from src.utils.response import error_response, success_response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_QUESTION_LENGTH = 1000
ALLOWED_KNOWLEDGE_BASES = {"insurance_claims", "fraud_alerts"}


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
    if len(question) > MAX_QUESTION_LENGTH:
        return error_response(
            f"question must be {MAX_QUESTION_LENGTH} characters or fewer",
            status_code=400,
        )

    raw_knowledge_base = input_data.get("knowledgeBase")
    if raw_knowledge_base is None:
        knowledge_base = None
    elif not isinstance(raw_knowledge_base, str):
        return error_response("knowledgeBase must be a string", status_code=400)
    else:
        knowledge_base = raw_knowledge_base.strip()
        if knowledge_base not in ALLOWED_KNOWLEDGE_BASES:
            return error_response("knowledgeBase is not supported", status_code=400)

    try:
        if knowledge_base is None:
            result = rag_service.answer_question(question)
        else:
            result = rag_service.answer_question(
                question,
                knowledge_base=knowledge_base,
            )
    except Exception:
        logger.exception("rag_query_failed")
        return error_response(
            "ガイドライン検索を完了できませんでした。しばらくしてから再度お試しください。",
            status_code=500,
        )

    return success_response(result)
