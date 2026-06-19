from src.services import claim_review_service


def test_analyze_claim_text_returns_extracted_fields_summary_checklist_and_governance_notice():
    claim_text = """
    請求人: 架空 花子
    請求種別: 入院給付金
    診断名: 急性虫垂炎
    入院期間: 2026年4月3日から2026年4月9日まで
    提出書類: 給付金請求書、入院証明書、診断書、本人確認書類
    """

    result = claim_review_service.analyze_claim_text(claim_text)

    assert result["claimType"] == "入院給付金"
    assert result["extractedFields"] == {
        "claimantName": "架空 花子",
        "claimType": "入院給付金",
        "hospitalizationPeriod": "2026年4月3日から2026年4月9日まで",
        "treatmentDate": None,
        "diagnosis": "急性虫垂炎",
        "submittedDocuments": [
            "給付金請求書",
            "入院証明書",
            "診断書",
            "本人確認書類",
        ],
    }
    assert "入院給付金" in result["summary"]
    assert "急性虫垂炎" in result["summary"]
    assert result["reviewChecklist"]
    assert "does not make final payment decisions" in result["governanceNotice"]


def test_analyze_claim_text_extracts_treatment_date_for_surgery_claim():
    claim_text = (
        "請求人: 架空 健一\n"
        "手術給付金の請求。診断名: 胆石症\n"
        "手術日: 2026年4月18日\n"
        "提出書類: 給付金請求書、手術証明書、診療明細書"
    )

    result = claim_review_service.analyze_claim_text(claim_text)

    assert result["claimType"] == "手術給付金"
    assert result["extractedFields"]["treatmentDate"] == "2026年4月18日"
    assert result["extractedFields"]["hospitalizationPeriod"] is None


def test_analyze_claim_text_parses_submitted_documents_when_present():
    claim_text = "提出書類: 給付金請求書、診断書、本人確認書類"

    result = claim_review_service.analyze_claim_text(claim_text)

    assert result["extractedFields"]["submittedDocuments"] == [
        "給付金請求書",
        "診断書",
        "本人確認書類",
    ]


def test_analyze_claim_text_detects_submitted_documents_from_free_text():
    claim_text = "診断書と入院証明書は提出済み。"

    result = claim_review_service.analyze_claim_text(claim_text)

    assert "診断書" in result["extractedFields"]["submittedDocuments"]
    assert "入院証明書" in result["extractedFields"]["submittedDocuments"]


def test_analyze_claim_text_does_not_treat_missing_documents_as_submitted():
    claim_text = "診断書は提出済み。本人確認書類は未提出。"

    result = claim_review_service.analyze_claim_text(claim_text)

    assert "診断書" in result["extractedFields"]["submittedDocuments"]
    assert "本人確認書類" not in result["extractedFields"]["submittedDocuments"]
    assert "本人確認書類または受取人本人確認書類の提出状況を確認する" in result["reviewChecklist"]


def test_analyze_claim_text_allows_missing_fields_as_none():
    result = claim_review_service.analyze_claim_text("OCR結果の一部のみ判読可能")

    assert result["claimType"] is None
    assert result["extractedFields"]["claimantName"] is None
    assert result["extractedFields"]["diagnosis"] is None
    assert result["governanceNotice"] == claim_review_service.GOVERNANCE_NOTICE


def test_analyze_claim_text_rejects_empty_text():
    try:
        claim_review_service.analyze_claim_text(" ")
    except ValueError as error:
        assert str(error) == "claimText is required"
    else:
        raise AssertionError("Expected ValueError")
