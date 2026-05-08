import json

from src.services import queue_service


def test_send_analysis_job_sends_expected_message(monkeypatch):
    mock_client = type(
        "MockClient",
        (),
        {
            "send_message": lambda self, **kwargs: {"MessageId": "msg-123", **kwargs},
        },
    )()

    monkeypatch.setattr(queue_service, "_get_client", lambda: mock_client)
    monkeypatch.setattr(queue_service, "_get_queue_url", lambda: "https://example.com/queue")
    monkeypatch.setattr(queue_service, "_current_timestamp", lambda: "2026-05-08T12:00:00Z")

    result = queue_service.send_analysis_job("alert-123")

    assert result == {
        "messageId": "msg-123",
        "queueUrl": "https://example.com/queue",
        "requestedAt": "2026-05-08T12:00:00Z",
    }


def test_send_analysis_job_supports_custom_analysis_type(monkeypatch):
    calls = {}

    class MockClient:
        def send_message(self, **kwargs):
            calls.update(kwargs)
            return {"MessageId": "msg-456"}

    monkeypatch.setattr(queue_service, "_get_client", lambda: MockClient())
    monkeypatch.setattr(queue_service, "_get_queue_url", lambda: "https://example.com/queue")
    monkeypatch.setattr(queue_service, "_current_timestamp", lambda: "2026-05-08T12:00:00Z")

    queue_service.send_analysis_job("alert-456", analysis_type="MANUAL_RETRY")

    assert json.loads(calls["MessageBody"]) == {
        "alertId": "alert-456",
        "analysisType": "MANUAL_RETRY",
        "requestedAt": "2026-05-08T12:00:00Z",
    }
    assert calls["QueueUrl"] == "https://example.com/queue"


def test_send_analysis_job_raises_clear_error_when_client_fails(monkeypatch):
    class MockClient:
        def send_message(self, **kwargs):
            raise RuntimeError("sqs failure")

    monkeypatch.setattr(queue_service, "_get_client", lambda: MockClient())
    monkeypatch.setattr(queue_service, "_get_queue_url", lambda: "https://example.com/queue")
    monkeypatch.setattr(queue_service, "_current_timestamp", lambda: "2026-05-08T12:00:00Z")

    try:
        queue_service.send_analysis_job("alert-789")
    except queue_service.QueueServiceError as error:
        assert str(error) == "Failed to send analysis job to SQS"
    else:
        raise AssertionError("Expected queue service to translate client failures")
