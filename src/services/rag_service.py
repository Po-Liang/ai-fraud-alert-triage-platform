from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.services import secrets_service

KNOWLEDGE_BASE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "insurance_claim_guidance.json"
)
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
OPENAI_REQUEST_TIMEOUT_SECONDS = 5
MAX_RETRIEVED_DOCUMENTS = 3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def answer_question(question: str) -> dict[str, Any]:
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("question is required")

    logger.info("rag_question_received questionLength=%s", len(normalized_question))
    retrieved_documents = retrieve_relevant_documents(normalized_question)
    sources = [_source_from_document(document) for document in retrieved_documents]

    try:
        api_key = secrets_service.get_openai_api_key()
    except Exception:
        logger.warning("rag_secret_lookup_failed", exc_info=True)
        api_key = None

    if not api_key:
        logger.info("rag_fallback_used reason=missing_openai_api_key")
        return {
            "answer": _build_fallback_answer(normalized_question, retrieved_documents),
            "sources": sources,
        }

    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    try:
        answer = _generate_openai_answer(
            question=normalized_question,
            documents=retrieved_documents,
            api_key=api_key,
            model=model,
        )
    except Exception:
        logger.warning("rag_fallback_used reason=openai_call_failed", exc_info=True)
        answer = _build_fallback_answer(normalized_question, retrieved_documents)

    return {
        "answer": answer,
        "sources": sources,
    }


def retrieve_relevant_documents(question: str) -> list[dict[str, str]]:
    question_tokens = _tokenize(question)
    scored_documents = []

    for index, document in enumerate(_load_guidance_documents()):
        document_text = " ".join(
            [
                document.get("title", ""),
                document.get("section", ""),
                document.get("content", ""),
            ]
        )
        document_tokens = _tokenize(document_text)
        overlap_score = len(question_tokens & document_tokens)
        title_score = len(question_tokens & _tokenize(document.get("title", ""))) * 2
        section_score = len(question_tokens & _tokenize(document.get("section", "")))
        scored_documents.append(
            (
                overlap_score + title_score + section_score,
                -index,
                document,
            )
        )

    scored_documents.sort(reverse=True)

    return [
        document
        for score, _index, document in scored_documents[:MAX_RETRIEVED_DOCUMENTS]
        if score > 0
    ]


@lru_cache(maxsize=1)
def _load_guidance_documents() -> tuple[dict[str, str], ...]:
    logger.info("rag_guidance_load_started path=%s", KNOWLEDGE_BASE_PATH)
    with KNOWLEDGE_BASE_PATH.open(encoding="utf-8") as guidance_file:
        documents = json.load(guidance_file)

    if not isinstance(documents, list):
        raise ValueError("insurance claim guidance must be a list")

    validated_documents = tuple(_validate_document(document) for document in documents)
    logger.info("rag_guidance_load_completed documentCount=%s", len(validated_documents))
    return validated_documents


def _validate_document(document: Any) -> dict[str, str]:
    if not isinstance(document, dict):
        raise ValueError("insurance claim guidance document must be an object")

    validated = {}
    for field_name in ("id", "title", "section", "content"):
        field_value = document.get(field_name)
        if not isinstance(field_value, str) or not field_value.strip():
            raise ValueError(f"insurance claim guidance document must include {field_name}")
        validated[field_name] = field_value.strip()

    return validated


def _tokenize(text: str) -> set[str]:
    normalized = text.lower()
    tokens = set(re.findall(r"[a-z0-9_]{2,}", normalized))

    for segment in re.findall(r"[\u3040-\u30ff\u3400-\u9fff]+", normalized):
        if len(segment) == 1:
            tokens.add(segment)
            continue

        tokens.add(segment)
        for size in (2, 3):
            if len(segment) >= size:
                tokens.update(
                    segment[index : index + size]
                    for index in range(0, len(segment) - size + 1)
                )

    return tokens


def _source_from_document(document: dict[str, str]) -> dict[str, str]:
    return {
        "id": document["id"],
        "title": document["title"],
        "section": document["section"],
    }


def _build_prompt(question: str, documents: list[dict[str, str]]) -> str:
    context = [
        {
            "id": document["id"],
            "title": document["title"],
            "section": document["section"],
            "content": document["content"],
        }
        for document in documents
    ]

    return json.dumps(
        {
            "question": question,
            "retrievedContext": context,
            "instructions": {
                "language": "Japanese",
                "grounding": "Use only the retrievedContext. If the context is insufficient, say what should be checked by a human reviewer.",
                "decisionBoundary": "Do not approve, reject, or make a final insurance claim payment decision.",
                "outputFormat": {"answer": "string"},
            },
        },
        ensure_ascii=False,
    )


def _generate_openai_answer(
    question: str,
    documents: list[dict[str, str]],
    api_key: str,
    model: str,
) -> str:
    logger.info("rag_openai_call_attempted model=%s sourceCount=%s", model, len(documents))
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You support Japanese insurance claim reviewers. Answer only "
                        "from the provided internal demo guidance. Do not make final "
                        "claim approval, denial, or payment decisions. Return only "
                        "valid JSON with one key: answer."
                    ),
                },
                {"role": "user", "content": _build_prompt(question, documents)},
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        url=OPENAI_CHAT_COMPLETIONS_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=OPENAI_REQUEST_TIMEOUT_SECONDS,
    ) as response:
        status_code = getattr(response, "status", None)
        if status_code is None and hasattr(response, "getcode"):
            status_code = response.getcode()
        logger.info("rag_openai_call_succeeded model=%s statusCode=%s", model, status_code)
        response_body = response.read().decode("utf-8")

    parsed_response = json.loads(response_body)
    content = (
        parsed_response.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not isinstance(content, str):
        raise ValueError("OpenAI response content is missing")

    parsed_content = json.loads(content)
    answer = parsed_content.get("answer") if isinstance(parsed_content, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("OpenAI answer is invalid")

    return _append_human_review_boundary(answer.strip())


def _build_fallback_answer(question: str, documents: list[dict[str, str]]) -> str:
    if not documents:
        return (
            "関連するデモ社内ガイダンスを特定できませんでした。原本書類と契約情報を担当者が確認し、"
            "必要に応じて追加確認してください。AIは最終的な支払い可否を判断しません。"
        )

    guidance_lines = [
        f"- {document['title']}（{document['section']}）: {document['content']}"
        for document in documents
    ]
    answer = (
        "参照したデモ社内ガイダンスに基づくと、次の観点を確認してください。\n"
        + "\n".join(guidance_lines)
        + "\n\nこの回答は社内ナレッジ確認の補助です。原本書類、契約情報、最新の業務ルールを人間の審査担当者が確認してください。"
    )

    return _append_human_review_boundary(answer)


def _append_human_review_boundary(answer: str) -> str:
    decision_boundary = "AIは最終的な請求承認、否認、支払い可否を判断しません。"
    if decision_boundary in answer:
        return answer

    return f"{answer}\n\n{decision_boundary}"
