# AI-Powered Fraud Alert Triage Platform

This project is a serverless AWS backend prototype that demonstrates how suspicious activity alerts can be ingested, triaged, scored, and summarized for human investigators.

It is not intended to replace enterprise-grade fraud detection platforms. Instead, it focuses on the post-alert investigation workflow: API ingestion, deterministic risk scoring, asynchronous AI-assisted analysis, and human-in-the-loop review.

## MVP Goal

The MVP will include:

- REST API with API Gateway and Lambda
- DynamoDB alert storage
- SQS-based asynchronous analysis
- Rule-based fraud risk scoring
- AI-generated investigation summary
- CloudWatch logging
- Infrastructure as Code using AWS SAM
- GitHub Actions CI

## Current Status

### Completed

- Project structure
- Local Python environment
- Deterministic risk scoring service
- AI summary service stub
- DynamoDB repository layer
- Alert service layer
- Unit tests for risk scoring

## Phase 2: DynamoDB Repository Layer

Phase 2 adds a dedicated repository layer for alert persistence in DynamoDB. This layer is responsible for creating alerts, fetching a single alert, listing alerts, and updating stored status or analysis results.

Database access is intentionally separated from business logic so the scoring and summary services can stay focused on fraud analysis rather than storage concerns. This keeps the code easier to test, easier to evolve, and clearer for future Lambda handlers that will orchestrate the workflow.

Current DynamoDB item design:

- `PK = ALERT#{alertId}`
- `SK = METADATA`

The repository layer is implemented locally in Python for now. Actual AWS infrastructure and deployment wiring will be added later with AWS SAM.

## Phase 3: Alert Service Layer

Phase 3 adds an alert service layer that coordinates business workflows for creating alerts, retrieving alerts, listing alerts, and running alert analysis.

The service layer is responsible for orchestrating the workflow, while the repository layer remains responsible for DynamoDB access only. Deterministic fraud scoring is handled by the risk scoring service, and investigation narrative output is handled by the AI summary service.

This separation makes the backend easier to test, easier to maintain, and easier to extend as Lambda handlers, queues, and deployment infrastructure are added in later phases.

### Next Steps

- Add Lambda API handlers
- Add SQS analysis worker
- Add AWS SAM template
- Deploy to AWS
