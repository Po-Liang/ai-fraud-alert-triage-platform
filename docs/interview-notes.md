# Interview Notes

## 60-Second Project Explanation

This project is a serverless fraud alert triage backend built on AWS. A client sends an alert to an API Gateway endpoint, a Lambda stores it in DynamoDB, and the system queues background analysis through SQS. A worker Lambda then performs deterministic fraud scoring and generates an investigator-facing AI summary using an OpenAI key stored securely in AWS Secrets Manager. The key design point is that deterministic logic owns the risk score and risk level, while AI is limited to summaries and recommended actions. That keeps the system explainable, testable, and easier to operate responsibly.

## 2-Minute Technical Explanation

The architecture is intentionally layered. The Lambda handlers are thin and only deal with API Gateway or SQS event parsing plus response formatting. `alert_service` coordinates business workflows such as creating alerts, requeueing analysis, and running the analysis pipeline. DynamoDB access is isolated in `alert_repository`, SQS messaging is isolated in `queue_service`, and secret retrieval is isolated in `secrets_service`.

On the async path, `POST /alerts` stores the alert and queues an SQS message. `AnalysisWorkerFunction` consumes that message and calls `alert_service.analyze_alert`. That service loads the alert, marks it in progress, runs deterministic scoring, then calls `ai_summary_service`. The AI service retrieves the OpenAI key from Secrets Manager, attempts the model call, and falls back to a deterministic summary if the secret is missing or the call fails. Finally, the service stores the analysis result and marks the alert complete.

I also defined the infrastructure in AWS SAM and added GitHub Actions CI for `pytest`, `sam validate`, and `sam build`. The tests mock AWS clients and OpenAI HTTP calls so CI stays safe and deterministic.

## Architecture Tradeoffs

- I chose clarity over maximum feature depth.
- The DynamoDB model is simple and easy to explain, but not optimized yet for broad search patterns.
- The async worker improves API responsiveness, but the current MVP still relies on logs and DLQ behavior more than rich operational dashboards.
- The AI integration is intentionally constrained so it cannot silently become the fraud decision engine.

## Why Serverless

Serverless fits this use case well because:

- traffic can be bursty
- background analysis is event-driven
- the MVP benefits from low operational overhead
- API, queue, and worker components scale independently

It also keeps the operational model small and well-scoped for an MVP.

## Why SQS

SQS decouples the public API from the slower analysis path.

That gives:

- fast API responses
- retry behavior
- dead-letter handling
- simpler scaling boundaries between ingestion and analysis

## Why DynamoDB

DynamoDB is a good fit for the MVP because:

- the core access pattern is key-based by `alertId`
- it works well with Lambda
- it keeps infrastructure simple
- it demonstrates NoSQL modeling tradeoffs clearly in interviews

## Why Secrets Manager

Secrets Manager keeps the OpenAI key out of source control and out of plain Lambda configuration values. It is also a practical production pattern because it supports auditability, future rotation, and least-privilege IAM.

## Why AI Summary Is Separated From Risk Scoring

I wanted the risk engine to remain deterministic and explainable. If AI owned the score, the system would be harder to test and harder to justify operationally. By separating them, I keep:

- scoring stable and auditable
- AI optional
- fallback behavior safe
- the human investigator in control

## What I Would Improve In Production

- add authentication and authorization
- add DynamoDB GSIs for better operational queries
- persist explicit `ANALYSIS_FAILED` status
- add CloudWatch metrics and alarms
- add tracing and better observability
- add multi-environment deployment strategy
- consider Bedrock if AWS-native model governance becomes important
