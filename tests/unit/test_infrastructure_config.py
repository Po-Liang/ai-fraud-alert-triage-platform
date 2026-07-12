from pathlib import Path


TEMPLATE = (Path(__file__).resolve().parents[2] / "template.yaml").read_text()


def test_analysis_queue_has_explicit_visibility_timeout_and_dlq():
    assert "VisibilityTimeout: 180" in TEMPLATE
    assert "deadLetterTargetArn: !GetAtt FraudAnalysisDeadLetterQueue.Arn" in TEMPLATE
    assert "maxReceiveCount: 3" in TEMPLATE


def test_analysis_worker_timeout_is_shorter_than_queue_visibility():
    worker_section = TEMPLATE.split("AnalysisWorkerFunction:", 1)[1].split(
        "ReviewAlertFunction:", 1
    )[0]

    assert "Timeout: 30" in worker_section
    assert "FunctionResponseTypes:" in worker_section
    assert "ReportBatchItemFailures" in worker_section
