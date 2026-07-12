# Data Model

## DynamoDB Table Design

The MVP uses a single DynamoDB table:

- Table name: `FraudAlertsTable`
- Partition key: `PK` (`String`)
- Sort key: `SK` (`String`)

Alert metadata items use:

- `PK = ALERT#{alertId}`
- `SK = METADATA`

## Why This Works For The MVP

This project currently stores one primary item per alert. That makes the model easy to reason about:

- one canonical record for alert state
- simple point lookups by `alertId`
- straightforward updates for status and analysis results
- clear mapping between the repository layer and the physical table design

For a portfolio project, this tradeoff keeps the implementation readable and easy to explain in interviews.

## Example Item

```json
{
  "PK": "ALERT#1f9aa8d5-66d8-44cf-8f7f-fb1db7b7ec36",
  "SK": "METADATA",
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

## Repository Mapping

The repository layer translates application objects into this table format by:

- enforcing the `ALERT#{alertId}` partition key pattern
- setting `SK` to `METADATA`
- adding `createdAt` and `updatedAt`
- storing analysis output in `analysisResult`

## Current Query Pattern

Current access patterns are intentionally small:

- create an alert
- fetch a single alert by `alertId`
- list recent alerts for MVP exploration
- update status
- update analysis result

The current `list_alerts` implementation uses a `Scan` filtered to metadata items. That is acceptable for a lightweight prototype but should evolve for production scale.

## Future GSI Ideas

Likely secondary indexes for a more production-ready version:

- by `customerId`
  - investigate all alerts for one customer
- by `riskLevel`
  - support analyst queues such as `HIGH` risk cases
- by `status`
  - find alerts waiting for reprocessing or review
- by `createdAt`
  - support time-ordered operational views

Possible future shape:

- `GSI1PK = CUSTOMER#{customerId}`
- `GSI2PK = STATUS#{status}`
- `GSI3PK = RISK#{riskLevel}`
- `GSI4PK = CREATED_AT#{yyyy-mm-dd...}`

Those indexes are intentionally deferred to keep the MVP simple and explainable.

## Human Review History

The NTT DATA demo reuses the existing alert metadata item and appends small review events to `reviewHistory`. It also stores the latest action in `reviewStatus`.

Review events include a generated event ID and timestamp, analyst action, optional comment, workflow run ID, and workflow version. This is sufficient for prototype traceability without introducing a new table or changing the table keys. It is not an immutable or compliance-certified audit log.
