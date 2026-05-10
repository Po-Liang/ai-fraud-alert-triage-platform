from src.handlers import analysis_worker


def test_analysis_worker_processes_valid_records(monkeypatch):
    processed = []

    monkeypatch.setattr(
        analysis_worker.alert_service,
        "analyze_alert",
        lambda alert_id: processed.append(alert_id),
    )

    result = analysis_worker.lambda_handler(
        {
            "Records": [
                {
                    "messageId": "msg-1",
                    "body": '{"alertId": "alert-123", "analysisType": "INITIAL_ANALYSIS"}',
                }
            ]
        },
        None,
    )

    assert processed == ["alert-123"]
    assert result == {"batchItemFailures": []}


def test_analysis_worker_calls_alert_service_analyze_alert(monkeypatch):
    called = {"alertId": None}

    def fake_analyze_alert(alert_id):
        called["alertId"] = alert_id

    monkeypatch.setattr(
        analysis_worker.alert_service,
        "analyze_alert",
        fake_analyze_alert,
    )

    analysis_worker.lambda_handler(
        {
            "Records": [
                {
                    "messageId": "msg-call-check",
                    "body": '{"alertId": "alert-call-check"}',
                }
            ]
        },
        None,
    )

    assert called["alertId"] == "alert-call-check"


def test_analysis_worker_marks_invalid_json_as_failed(monkeypatch):
    monkeypatch.setattr(
        analysis_worker.alert_service,
        "analyze_alert",
        lambda alert_id: None,
    )

    result = analysis_worker.lambda_handler(
        {
            "Records": [
                {
                    "messageId": "msg-1",
                    "body": "{not-json}",
                }
            ]
        },
        None,
    )

    assert result == {"batchItemFailures": [{"itemIdentifier": "msg-1"}]}


def test_analysis_worker_marks_missing_alert_id_as_failed(monkeypatch):
    monkeypatch.setattr(
        analysis_worker.alert_service,
        "analyze_alert",
        lambda alert_id: None,
    )

    result = analysis_worker.lambda_handler(
        {
            "Records": [
                {
                    "messageId": "msg-2",
                    "body": '{"analysisType": "INITIAL_ANALYSIS"}',
                }
            ]
        },
        None,
    )

    assert result == {"batchItemFailures": [{"itemIdentifier": "msg-2"}]}


def test_analysis_worker_marks_service_failure_as_failed(monkeypatch):
    def raise_error(alert_id):
        raise RuntimeError("analysis failed")

    monkeypatch.setattr(
        analysis_worker.alert_service,
        "analyze_alert",
        raise_error,
    )

    result = analysis_worker.lambda_handler(
        {
            "Records": [
                {
                    "messageId": "msg-3",
                    "body": '{"alertId": "alert-999"}',
                }
            ]
        },
        None,
    )

    assert result == {"batchItemFailures": [{"itemIdentifier": "msg-3"}]}
