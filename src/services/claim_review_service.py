from __future__ import annotations

import logging
import re
from typing import Any

GOVERNANCE_NOTICE = (
    "AI supports human reviewers and does not make final payment decisions. "
    "A human claim reviewer must verify original documents, contract terms, "
    "and applicable business rules before deciding claim payment handling."
)

KNOWN_CLAIM_TYPES = (
    "入院給付金",
    "手術給付金",
    "死亡保険金",
    "書類不備対応",
)

KNOWN_DOCUMENT_TYPES = (
    "給付金請求書",
    "保険金請求書",
    "入院証明書",
    "手術証明書",
    "診断書",
    "診療明細書",
    "領収書",
    "本人確認書類",
    "受取人本人確認書類",
    "戸籍関係書類",
    "契約内容確認書",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def analyze_claim_text(claim_text: str) -> dict[str, Any]:
    normalized_text = claim_text.strip()
    if not normalized_text:
        raise ValueError("claimText is required")

    logger.info("claim_review_analysis_started textLength=%s", len(normalized_text))
    extracted_fields = _extract_fields(normalized_text)
    summary = _build_summary(extracted_fields)

    return {
        "claimType": extracted_fields["claimType"],
        "extractedFields": extracted_fields,
        "summary": summary,
        "reviewChecklist": _build_review_checklist(extracted_fields),
        "governanceNotice": GOVERNANCE_NOTICE,
    }


def _extract_fields(claim_text: str) -> dict[str, Any]:
    return {
        "claimantName": _extract_claimant_name(claim_text),
        "claimType": _extract_claim_type(claim_text),
        "hospitalizationPeriod": _extract_hospitalization_period(claim_text),
        "treatmentDate": _extract_treatment_date(claim_text),
        "diagnosis": _extract_diagnosis(claim_text),
        "submittedDocuments": _extract_submitted_documents(claim_text),
    }


def _extract_claimant_name(claim_text: str) -> str | None:
    return _extract_labeled_value(
        claim_text,
        labels=("請求人", " claimantName", "氏名", "契約者", "受取人"),
    )


def _extract_claim_type(claim_text: str) -> str | None:
    labeled_claim_type = _extract_labeled_value(
        claim_text,
        labels=("請求種別", "請求区分", "claimType"),
    )
    if labeled_claim_type:
        for claim_type in KNOWN_CLAIM_TYPES:
            if claim_type in labeled_claim_type:
                return claim_type

    for claim_type in KNOWN_CLAIM_TYPES:
        if claim_type in claim_text:
            return claim_type

    return None


def _extract_hospitalization_period(claim_text: str) -> str | None:
    labeled_period = _extract_labeled_value(
        claim_text,
        labels=("入院期間", "hospitalizationPeriod"),
    )
    if labeled_period:
        return labeled_period

    match = re.search(
        r"(\d{4}年\d{1,2}月\d{1,2}日)\s*(?:から|〜|～|-|－)\s*(\d{4}年\d{1,2}月\d{1,2}日)",
        claim_text,
    )
    if match:
        return f"{match.group(1)}から{match.group(2)}まで"

    return None


def _extract_treatment_date(claim_text: str) -> str | None:
    labeled_date = _extract_labeled_value(
        claim_text,
        labels=("手術日", "治療日", "診療日", "treatmentDate"),
    )
    if labeled_date:
        return labeled_date

    match = re.search(
        r"(?:手術日|治療日|診療日)[は：:\s]*(\d{4}年\d{1,2}月\d{1,2}日)",
        claim_text,
    )
    if match:
        return match.group(1)

    return None


def _extract_diagnosis(claim_text: str) -> str | None:
    labeled_diagnosis = _extract_labeled_value(
        claim_text,
        labels=("診断名", "病名", "diagnosis"),
    )
    if labeled_diagnosis:
        return labeled_diagnosis

    match = re.search(r"([^\n。．、,]{2,30})(?:による|のための|に対する).{0,20}(?:請求|入院|手術)", claim_text)
    if match:
        return match.group(1).strip()

    return None


def _extract_submitted_documents(claim_text: str) -> list[str]:
    labeled_documents = _extract_labeled_value(
        claim_text,
        labels=("提出書類", "添付書類", "submittedDocuments"),
    )
    if labeled_documents:
        parsed_documents = [
            document.strip()
            for document in re.split(r"[、,，/／\n]+", labeled_documents)
            if document.strip()
        ]
        if parsed_documents:
            return _deduplicate_documents(parsed_documents)

    detected_documents = [
        document_type
        for document_type in KNOWN_DOCUMENT_TYPES
        if document_type in claim_text
        and not _document_is_marked_missing(claim_text, document_type)
    ]

    return _deduplicate_documents(detected_documents)


def _extract_labeled_value(claim_text: str, labels: tuple[str, ...]) -> str | None:
    normalized_labels = [label.strip() for label in labels]
    label_pattern = "|".join(re.escape(label) for label in normalized_labels)
    match = re.search(
        rf"(?:{label_pattern})\s*[：:]\s*([^\n。;；]+)",
        claim_text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).strip(" 　,，、")

    return None


def _deduplicate_documents(documents: list[str]) -> list[str]:
    unique_documents = []
    seen = set()

    for document in documents:
        normalized_document = document.strip()
        if normalized_document and normalized_document not in seen:
            unique_documents.append(normalized_document)
            seen.add(normalized_document)

    return unique_documents


def _document_is_marked_missing(claim_text: str, document_type: str) -> bool:
    missing_markers = ("未提出", "未添付", "不足", "なし", "未受領")

    for match in re.finditer(re.escape(document_type), claim_text):
        context = claim_text[max(match.start() - 8, 0) : match.end() + 12]
        if any(marker in context for marker in missing_markers):
            return True

    return False


def _build_summary(extracted_fields: dict[str, Any]) -> str:
    claim_type = extracted_fields.get("claimType") or "不明な請求種別"
    diagnosis = extracted_fields.get("diagnosis") or "診断名未抽出"
    period_or_date = (
        extracted_fields.get("hospitalizationPeriod")
        or extracted_fields.get("treatmentDate")
        or "日付情報未抽出"
    )

    return (
        f"{claim_type}のOCR出力テキストを確認しました。"
        f"診断・傷病情報は「{diagnosis}」、期間または処置日は「{period_or_date}」として抽出されています。"
        "抽出結果は原本書類と照合して確認してください。"
    )


def _build_review_checklist(extracted_fields: dict[str, Any]) -> list[str]:
    checklist = [
        "OCR抽出結果を原本書類と照合する",
        "請求人、被保険者、受取人、契約者の関係を確認する",
        "契約内容と給付対象条件を確認する",
    ]

    if not extracted_fields.get("claimantName"):
        checklist.append("請求人名が読み取れないため本人確認書類で確認する")

    if not extracted_fields.get("claimType"):
        checklist.append("請求種別が読み取れないため請求書の種別欄を確認する")

    if not extracted_fields.get("hospitalizationPeriod") and not extracted_fields.get("treatmentDate"):
        checklist.append("入院期間または治療日・手術日の記載を確認する")

    if not extracted_fields.get("diagnosis"):
        checklist.append("診断名または傷病名を診断書で確認する")

    submitted_documents = extracted_fields.get("submittedDocuments", [])
    if not submitted_documents:
        checklist.append("提出書類一覧が読み取れないため受付記録を確認する")
    elif "本人確認書類" not in submitted_documents and "受取人本人確認書類" not in submitted_documents:
        checklist.append("本人確認書類または受取人本人確認書類の提出状況を確認する")

    checklist.append("AI出力を参考情報として扱い、最終判断は人間の審査担当者が行う")

    return checklist
