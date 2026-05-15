# API Reference

Base path after deployment:

```text
https://{api-id}.execute-api.{region}.amazonaws.com/Prod/
```

## Endpoints

### `POST /alerts`

Creates a new alert, stores it in DynamoDB, and queues background analysis.

Example request:

```bash
curl -X POST "${API_ENDPOINT}alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "cust-001",
    "accountId": "acct-001",
    "alertType": "SUSPICIOUS_TRANSFER",
    "amount": 125000,
    "country": "JP",
    "description": "Large outbound transfer to a new beneficiary",
    "historicalAverageAmount": 25000,
    "isNewBeneficiary": true,
    "transactionCountLastHour": 4
  }'
```

Example `201` response:

```json
{
  "alertId": "1f9aa8d5-66d8-44cf-8f7f-fb1db7b7ec36",
  "customerId": "cust-001",
  "accountId": "acct-001",
  "alertType": "SUSPICIOUS_TRANSFER",
  "amount": 125000,
  "country": "JP",
  "description": "Large outbound transfer to a new beneficiary",
  "historicalAverageAmount": 25000,
  "isNewBeneficiary": true,
  "transactionCountLastHour": 4,
  "status": "PENDING_ANALYSIS",
  "createdAt": "2026-05-15T10:00:00Z",
  "updatedAt": "2026-05-15T10:00:00Z"
}
```

Common error responses:

- `400` invalid JSON or invalid request fields
- `500` analysis job could not be queued

### `GET /alerts`

Lists recent alerts. Supports an optional `limit` query parameter.

Example request:

```bash
curl "${API_ENDPOINT}alerts?limit=10"
```

Example `200` response:

```json
{
  "items": [
    {
      "alertId": "1f9aa8d5-66d8-44cf-8f7f-fb1db7b7ec36",
      "customerId": "cust-001",
      "status": "ANALYSIS_COMPLETED",
      "createdAt": "2026-05-15T10:00:00Z",
      "updatedAt": "2026-05-15T10:00:08Z"
    }
  ]
}
```

Common error responses:

- `400` invalid `limit`

### `GET /alerts/{alertId}`

Returns a single alert by ID.

Example request:

```bash
curl "${API_ENDPOINT}alerts/1f9aa8d5-66d8-44cf-8f7f-fb1db7b7ec36"
```

Example `200` response:

```json
{
  "alertId": "1f9aa8d5-66d8-44cf-8f7f-fb1db7b7ec36",
  "customerId": "cust-001",
  "accountId": "acct-001",
  "alertType": "SUSPICIOUS_TRANSFER",
  "amount": 125000,
  "country": "JP",
  "status": "ANALYSIS_COMPLETED",
  "createdAt": "2026-05-15T10:00:00Z",
  "updatedAt": "2026-05-15T10:00:08Z",
  "analysisResult": {
    "riskScore": 35,
    "riskLevel": "LOW",
    "signals": [
      "Transaction amount is 5.0x higher than historical average",
      "Beneficiary is new",
      "Moderate transaction velocity in the last hour"
    ],
    "aiSummary": "This alert may indicate unusual payment behavior and should be reviewed by an investigator.",
    "recommendedActions": [
      "Review customer transaction history",
      "Check whether the transaction pattern is unusual",
      "Monitor for additional suspicious activity"
    ]
  }
}
```

Common error responses:

- `400` missing `alertId`
- `404` alert not found

### `POST /alerts/{alertId}/analyze`

Requeues analysis for an existing alert. This endpoint does not run analysis inline.

Example request:

```bash
curl -X POST "${API_ENDPOINT}alerts/1f9aa8d5-66d8-44cf-8f7f-fb1db7b7ec36/analyze"
```

Example `202` response:

```json
{
  "alertId": "1f9aa8d5-66d8-44cf-8f7f-fb1db7b7ec36",
  "status": "PENDING_ANALYSIS",
  "message": "Analysis job queued",
  "messageId": "0f2c0cfa-7d6e-4e8b-9d2b-0f1f7f6d99f5"
}
```

Common error responses:

- `400` missing `alertId`
- `404` alert not found
- `500` analysis job could not be queued

## Response Format

All handlers return API Gateway proxy-style responses:

- `statusCode`
- `headers`
- `body` as a JSON string

## Status Lifecycle

Current and intended alert statuses:

- `PENDING_ANALYSIS`
  - alert created or requeued
  - waiting for the SQS worker to process it
- `ANALYSIS_IN_PROGRESS`
  - worker has started scoring and summary generation
- `ANALYSIS_COMPLETED`
  - deterministic scoring and summary generation finished successfully
- `ANALYSIS_FAILED`
  - intended failure state for a future enhancement
  - today, repeated failures are primarily surfaced through worker logs, SQS retries, and the dead-letter queue rather than a persisted status update

## Notes

- Deterministic scoring remains the source of `riskScore` and `riskLevel`.
- AI only generates `aiSummary` and `recommendedActions`.
- The API is intentionally small for MVP clarity.
