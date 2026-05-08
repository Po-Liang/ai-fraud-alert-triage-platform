from unittest.mock import Mock

from src.services import alert_service


def test_create_alert_generates_defaults_and_calls_repository(monkeypatch):
    repository_mock = Mock()
    repository_mock.create_alert.return_value = {"alertId": "alert-123"}
    send_analysis_job_mock = Mock(return_value={"messageId": "msg-123"})
    monkeypatch.setattr(alert_service, "_current_timestamp", lambda: "2026-05-07T10:00:00Z")
    monkeypatch.setattr(alert_service, "_generate_alert_id", lambda: "alert-123")
    monkeypatch.setattr(alert_service.alert_repository, "create_alert", repository_mock.create_alert)
    monkeypatch.setattr(
        alert_service.queue_service,
        "send_analysis_job",
        send_analysis_job_mock,
    )

    result = alert_service.create_alert(
        {
            "customerId": "cust-1",
            "accountId": "acct-1",
            "alertType": "SUSPICIOUS_TRANSFER",
            "amount": 125000,
            "country": "JP",
        }
    )

    assert result == {"alertId": "alert-123"}
    repository_mock.create_alert.assert_called_once_with(
        {
            "customerId": "cust-1",
            "accountId": "acct-1",
            "alertType": "SUSPICIOUS_TRANSFER",
            "amount": 125000.0,
            "currency": "JPY",
            "country": "JP",
            "description": None,
            "historicalAverageAmount": 0.0,
            "isNewBeneficiary": False,
            "transactionCountLastHour": 0,
            "alertId": "alert-123",
            "status": "PENDING_ANALYSIS",
            "createdAt": "2026-05-07T10:00:00Z",
            "updatedAt": "2026-05-07T10:00:00Z",
        }
    )
    send_analysis_job_mock.assert_called_once_with(
        "alert-123",
        analysis_type="INITIAL_ANALYSIS",
    )


def test_create_alert_preserves_existing_identifiers_and_timestamps(monkeypatch):
    repository_mock = Mock()
    repository_mock.create_alert.return_value = {"alertId": "existing-alert"}
    send_analysis_job_mock = Mock(return_value={"messageId": "msg-123"})
    monkeypatch.setattr(alert_service, "_current_timestamp", lambda: "2026-05-07T10:00:00Z")
    monkeypatch.setattr(alert_service.alert_repository, "create_alert", repository_mock.create_alert)
    monkeypatch.setattr(
        alert_service.queue_service,
        "send_analysis_job",
        send_analysis_job_mock,
    )

    result = alert_service.create_alert(
        {
            "alertId": "existing-alert",
            "customerId": "cust-1",
            "accountId": "acct-1",
            "alertType": "SUSPICIOUS_TRANSFER",
            "amount": 125000,
            "country": "JP",
            "createdAt": "2026-05-07T09:00:00Z",
            "updatedAt": "2026-05-07T09:30:00Z",
        }
    )

    assert result == {"alertId": "existing-alert"}
    repository_mock.create_alert.assert_called_once_with(
        {
            "customerId": "cust-1",
            "accountId": "acct-1",
            "alertType": "SUSPICIOUS_TRANSFER",
            "amount": 125000.0,
            "currency": "JPY",
            "country": "JP",
            "description": None,
            "historicalAverageAmount": 0.0,
            "isNewBeneficiary": False,
            "transactionCountLastHour": 0,
            "alertId": "existing-alert",
            "status": "PENDING_ANALYSIS",
            "createdAt": "2026-05-07T09:00:00Z",
            "updatedAt": "2026-05-07T09:00:00Z",
        }
    )
    send_analysis_job_mock.assert_called_once_with(
        "existing-alert",
        analysis_type="INITIAL_ANALYSIS",
    )


def test_create_alert_generates_id_when_input_alert_id_is_blank(monkeypatch):
    repository_mock = Mock()
    repository_mock.create_alert.return_value = {"alertId": "generated-alert"}
    send_analysis_job_mock = Mock(return_value={"messageId": "msg-123"})
    monkeypatch.setattr(alert_service, "_current_timestamp", lambda: "2026-05-07T10:00:00Z")
    monkeypatch.setattr(alert_service, "_generate_alert_id", lambda: "generated-alert")
    monkeypatch.setattr(alert_service.alert_repository, "create_alert", repository_mock.create_alert)
    monkeypatch.setattr(
        alert_service.queue_service,
        "send_analysis_job",
        send_analysis_job_mock,
    )

    alert_service.create_alert(
        {
            "alertId": "   ",
            "customerId": "cust-1",
            "accountId": "acct-1",
            "alertType": "SUSPICIOUS_TRANSFER",
            "amount": 125000,
            "country": "JP",
        }
    )

    repository_mock.create_alert.assert_called_once()
    created_alert = repository_mock.create_alert.call_args.args[0]
    assert created_alert["alertId"] == "generated-alert"
    send_analysis_job_mock.assert_called_once_with(
        "generated-alert",
        analysis_type="INITIAL_ANALYSIS",
    )


def test_get_alert_delegates_to_repository(monkeypatch):
    monkeypatch.setattr(
        alert_service.alert_repository,
        "get_alert",
        lambda alert_id: {"alertId": alert_id},
    )

    result = alert_service.get_alert("alert-123")

    assert result == {"alertId": "alert-123"}


def test_list_alerts_delegates_to_repository(monkeypatch):
    monkeypatch.setattr(
        alert_service.alert_repository,
        "list_alerts",
        lambda limit: [{"alertId": "alert-1"}, {"alertId": "alert-2"}][:limit],
    )

    result = alert_service.list_alerts(limit=2)

    assert result == [{"alertId": "alert-1"}, {"alertId": "alert-2"}]


def test_request_analysis_queues_job_for_existing_alert(monkeypatch):
    get_alert_mock = Mock(return_value={"alertId": "alert-123"})
    update_status_mock = Mock()
    send_analysis_job_mock = Mock(return_value={"messageId": "msg-123"})

    monkeypatch.setattr(alert_service.alert_repository, "get_alert", get_alert_mock)
    monkeypatch.setattr(
        alert_service.alert_repository,
        "update_status",
        update_status_mock,
    )
    monkeypatch.setattr(
        alert_service.queue_service,
        "send_analysis_job",
        send_analysis_job_mock,
    )

    result = alert_service.request_analysis("alert-123")

    assert result == {
        "alertId": "alert-123",
        "status": "PENDING_ANALYSIS",
        "message": "Analysis job queued",
        "messageId": "msg-123",
    }
    get_alert_mock.assert_called_once_with("alert-123")
    update_status_mock.assert_called_once_with("alert-123", "PENDING_ANALYSIS")
    send_analysis_job_mock.assert_called_once_with(
        "alert-123",
        analysis_type="INITIAL_ANALYSIS",
    )


def test_request_analysis_raises_when_alert_does_not_exist(monkeypatch):
    monkeypatch.setattr(alert_service.alert_repository, "get_alert", lambda alert_id: None)

    try:
        alert_service.request_analysis("missing-alert")
    except alert_service.AlertNotFoundError as error:
        assert str(error) == "Alert 'missing-alert' does not exist"
    else:
        raise AssertionError("Expected request_analysis to raise AlertNotFoundError")


def test_create_alert_translates_queue_failure(monkeypatch):
    repository_mock = Mock()
    repository_mock.create_alert.return_value = {"alertId": "alert-123"}
    monkeypatch.setattr(alert_service, "_current_timestamp", lambda: "2026-05-07T10:00:00Z")
    monkeypatch.setattr(alert_service, "_generate_alert_id", lambda: "alert-123")
    monkeypatch.setattr(alert_service.alert_repository, "create_alert", repository_mock.create_alert)
    monkeypatch.setattr(
        alert_service.queue_service,
        "send_analysis_job",
        Mock(side_effect=alert_service.queue_service.QueueServiceError("boom")),
    )

    try:
        alert_service.create_alert(
            {
                "customerId": "cust-1",
                "accountId": "acct-1",
                "alertType": "SUSPICIOUS_TRANSFER",
                "amount": 125000,
                "country": "JP",
            }
        )
    except alert_service.AnalysisRequestError as error:
        assert str(error) == "Failed to queue analysis job"
    else:
        raise AssertionError("Expected create_alert to translate queue failure")


def test_request_analysis_translates_queue_failure(monkeypatch):
    monkeypatch.setattr(
        alert_service.alert_repository,
        "get_alert",
        lambda alert_id: {"alertId": alert_id},
    )
    monkeypatch.setattr(
        alert_service.alert_repository,
        "update_status",
        Mock(),
    )
    monkeypatch.setattr(
        alert_service.queue_service,
        "send_analysis_job",
        Mock(side_effect=alert_service.queue_service.QueueServiceError("boom")),
    )

    try:
        alert_service.request_analysis("alert-123")
    except alert_service.AnalysisRequestError as error:
        assert str(error) == "Failed to queue analysis job"
    else:
        raise AssertionError("Expected request_analysis to translate queue failure")


def test_analyze_alert_raises_clear_error_when_alert_is_missing(monkeypatch):
    monkeypatch.setattr(alert_service.alert_repository, "get_alert", lambda alert_id: None)

    try:
        alert_service.analyze_alert("missing-alert")
    except alert_service.AlertNotFoundError as error:
        assert str(error) == "Alert 'missing-alert' does not exist"
    else:
        raise AssertionError("Expected analyze_alert to raise AlertNotFoundError")


def test_analyze_alert_coordinates_repository_and_analysis_services(monkeypatch):
    alert = {
        "alertId": "alert-123",
        "amount": 950000,
        "historicalAverageAmount": 50000,
        "isNewBeneficiary": True,
        "transactionCountLastHour": 8,
        "country": "JP",
        "status": "PENDING_ANALYSIS",
    }
    risk_result = {
        "riskScore": 75,
        "riskLevel": "HIGH",
        "signals": [
            "Beneficiary is new",
            "High transaction velocity in the last hour",
        ],
    }
    summary_result = {
        "aiSummary": "Escalate for manual review.",
        "recommendedActions": [
            "Verify the beneficiary relationship",
            "Review recent login and device activity",
        ],
    }

    get_alert_mock = Mock(return_value=alert)
    update_status_mock = Mock()
    update_analysis_result_mock = Mock()
    calculate_risk_score_mock = Mock(return_value=risk_result)
    generate_summary_mock = Mock(return_value=summary_result)

    monkeypatch.setattr(alert_service.alert_repository, "get_alert", get_alert_mock)
    monkeypatch.setattr(
        alert_service.alert_repository,
        "update_status",
        update_status_mock,
    )
    monkeypatch.setattr(
        alert_service.alert_repository,
        "update_analysis_result",
        update_analysis_result_mock,
    )
    monkeypatch.setattr(
        alert_service.risk_scoring_service,
        "calculate_risk_score",
        calculate_risk_score_mock,
    )
    monkeypatch.setattr(
        alert_service.ai_summary_service,
        "generate_investigation_summary",
        generate_summary_mock,
    )

    result = alert_service.analyze_alert("alert-123")

    assert result == {
        "riskScore": 75,
        "riskLevel": "HIGH",
        "signals": [
            "Beneficiary is new",
            "High transaction velocity in the last hour",
        ],
        "aiSummary": "Escalate for manual review.",
        "recommendedActions": [
            "Verify the beneficiary relationship",
            "Review recent login and device activity",
        ],
    }
    get_alert_mock.assert_called_once_with("alert-123")
    update_status_mock.assert_any_call("alert-123", "ANALYSIS_IN_PROGRESS")
    update_status_mock.assert_any_call("alert-123", "ANALYSIS_COMPLETED")
    calculate_risk_score_mock.assert_called_once_with(alert)
    generate_summary_mock.assert_called_once_with(alert, risk_result)
    update_analysis_result_mock.assert_called_once_with("alert-123", result)


def test_analyze_alert_translates_repository_not_found_during_status_update(monkeypatch):
    alert = {
        "alertId": "alert-123",
        "amount": 1000,
        "historicalAverageAmount": 100,
        "country": "JP",
    }

    monkeypatch.setattr(
        alert_service.alert_repository,
        "get_alert",
        lambda alert_id: alert,
    )
    monkeypatch.setattr(
        alert_service.alert_repository,
        "update_status",
        Mock(side_effect=alert_service.alert_repository.AlertNotFoundError("missing")),
    )

    try:
        alert_service.analyze_alert("alert-123")
    except alert_service.AlertNotFoundError as error:
        assert str(error) == "Alert 'alert-123' does not exist"
    else:
        raise AssertionError("Expected analyze_alert to translate repository not found")
