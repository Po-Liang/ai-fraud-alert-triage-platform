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
- Lambda handlers for REST API layer
- AWS SAM infrastructure template
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

## Phase 4: Lambda Handler Layer

Phase 4 adds thin Lambda handlers as the REST API entry points for the platform.

These handlers parse API Gateway proxy-style events, validate incoming request data, and return HTTP-style JSON responses. Business logic remains in the alert service layer, and DynamoDB access remains in the repository layer.

Current handlers include:

- Create alert
- Get alert
- List alerts
- Analyze alert

The handler layer is implemented locally in Python for now. Actual API Gateway and AWS SAM deployment wiring will be added in the next phase.

## Phase 5: AWS SAM Infrastructure

Phase 5 adds an AWS SAM template that defines the core infrastructure for the current backend.

The `template.yaml` file defines the serverless infrastructure for the project. API Gateway routes are mapped to the existing Lambda handlers, the DynamoDB table stores fraud alerts using the `PK` and `SK` key structure, and the SQS queue plus dead-letter queue are prepared for future asynchronous analysis workflows.

This infrastructure layer is intentionally simple for the MVP. Deployment will be handled in a later phase, and the current template does not yet include Cognito authentication or real AI model integration such as OpenAI or Bedrock.

### Next Steps

- Add SQS analysis worker
- Deploy to AWS
