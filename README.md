# AI-Powered Fraud Alert Triage Platform

## Executive Summary

This project is an AWS serverless backend prototype that ingests fraud alerts, stores them in DynamoDB, scores them with deterministic rules, and generates investigator-facing summaries through an asynchronous SQS worker.

It is designed to demonstrate practical backend engineering skills rather than generic AI experimentation: API design, service layering, queue-based workflows, secrets handling, infrastructure as code, and testable business logic.

## Why This Project Exists

Many fraud workflows need clearer tooling after an alert has already been generated. This project focuses on the post-alert triage workflow:

- receive a fraud alert through an API
- persist it in DynamoDB
- score it with explainable deterministic logic
- enrich it with a cautious AI-generated investigation summary
- keep the API responsive by moving longer-running analysis into SQS and Lambda

The design keeps deterministic scoring as the source of `riskScore` and `riskLevel`. AI is used only for summaries and recommended next steps, not for final fraud decisions.

## Architecture Overview

The system follows a simple layered architecture:

- API Gateway exposes REST endpoints for creating and retrieving alerts.
- Thin Lambda handlers translate API Gateway events into service calls.
- `alert_service` coordinates workflow and status transitions.
- `alert_repository` owns DynamoDB access.
- `queue_service` owns SQS messaging.
- `analysis_worker` consumes SQS messages and runs background analysis.
- `risk_scoring_service` produces deterministic risk signals.
- `ai_summary_service` produces cautious investigation summaries.
- `secrets_service` retrieves the OpenAI API key from AWS Secrets Manager.

Detailed documentation:

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Data Model](docs/data-model.md)
- [Deployment Guide](docs/deployment.md)
- [Security Notes](docs/security.md)
- [Interview Notes](docs/interview-notes.md)
- [Interview Demo: AI Insurance Claims Review Copilot](docs/interview-demo-dltx.md)
- [Future Improvements](docs/future-improvements.md)

## Interview Demo: AI Insurance Claims Review Copilot

For interviews with 第一ライフテクノクロス株式会社, this project can be presented as an insurance operations demo called `AI Insurance Claims Review Copilot`. Phase A adds fictional insurance claim cases and internal guidance samples to prepare a future story around AI-OCR output, RAG-style knowledge support, and claim review assistance. The current demo uses fake data only, does not implement real OCR, and does not automate claim payment decisions; the intended value is reviewer productivity, consistency, and safer human-in-the-loop AI support.

See [docs/interview-demo-dltx.md](docs/interview-demo-dltx.md) for the full demo story.

### `POST /rag/query`

The interview demo includes a simple local-guidance RAG MVP for insurance claim review questions. It retrieves relevant fake internal guidance from `src/data/insurance_claim_guidance.json`, generates an answer, and returns the sources used.

Sample request:

```bash
curl -X POST "${API_ENDPOINT}rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "入院給付金の審査では、どの書類や日付を確認すべきですか？"
  }'
```

Sample response:

```json
{
  "answer": "参照したデモ社内ガイダンスに基づくと、請求書、入院証明書、診断書に記載された入院開始日と退院日を照合してください。日付差異や判読困難な記載がある場合は、人間の審査担当者が原本を確認してください。\n\nAIは最終的な請求承認、否認、支払い可否を判断しません。",
  "sources": [
    {
      "id": "GUIDE-DEMO-001",
      "title": "入院給付金審査ガイド",
      "section": "入院期間確認"
    }
  ]
}
```

This endpoint is intentionally simple: it uses keyword-overlap retrieval against local fake guidance documents. It is designed to demonstrate the RAG support pattern, not production-grade retrieval. AI supports human reviewers and does not make final claim payment decisions.

### `POST /claims/analyze`

The interview demo also includes a deterministic claim document analysis endpoint. It accepts OCR-output-like text, extracts basic claim review fields where possible, generates a concise summary, and returns a checklist for human reviewers.

Sample request:

```bash
curl -X POST "${API_ENDPOINT}claims/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "claimText": "請求人: 架空 花子\n請求種別: 入院給付金\n診断名: 急性虫垂炎\n入院期間: 2026年4月3日から2026年4月9日まで\n提出書類: 給付金請求書、入院証明書、診断書、本人確認書類"
  }'
```

Sample response:

```json
{
  "claimType": "入院給付金",
  "extractedFields": {
    "claimantName": "架空 花子",
    "claimType": "入院給付金",
    "hospitalizationPeriod": "2026年4月3日から2026年4月9日まで",
    "treatmentDate": null,
    "eventDateOrPeriod": "2026年4月3日から2026年4月9日まで",
    "diagnosis": "急性虫垂炎",
    "submittedDocuments": [
      "給付金請求書",
      "入院証明書",
      "診断書",
      "本人確認書類"
    ]
  },
  "summary": "入院給付金のOCR出力テキストを確認しました。診断・傷病情報は「急性虫垂炎」、期間または処置日は「2026年4月3日から2026年4月9日まで」として抽出されています。抽出結果は原本書類と照合して確認してください。",
  "reviewChecklist": [
    "OCR抽出結果を原本書類と照合する",
    "請求人、被保険者、受取人、契約者の関係を確認する",
    "契約内容と給付対象条件を確認する",
    "AI出力を参考情報として扱い、最終判断は人間の審査担当者が行う"
  ],
  "governanceNotice": "AIの出力は審査担当者の確認を支援するものであり、支払い可否の最終判断は人間が行います。原本書類、契約内容、社内ルールを必ず確認したうえで判断してください。"
}
```

This endpoint simulates processing text that could have been extracted by OCR. Real OCR, file upload, and document image processing are not implemented in this phase. AI and deterministic extraction support human reviewers and do not make final claim payment decisions.

## Tech Stack

- Python 3.12
- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB
- Amazon SQS with dead-letter queue
- AWS Secrets Manager
- AWS SAM
- GitHub Actions
- OpenAI API via `urllib.request`
- `pytest` with mocked AWS and OpenAI boundaries

## Core Features

- Create alerts through a REST API
- Retrieve a single alert or list recent alerts
- Queue analysis asynchronously through SQS
- Run deterministic fraud scoring in a background worker
- Generate AI-assisted investigation summaries with deterministic fallback behavior
- Store OpenAI credentials in AWS Secrets Manager instead of Lambda environment variables
- Validate infrastructure with SAM and application behavior with unit tests in CI

## End-to-End Flow

1. A client sends `POST /alerts` with alert details.
2. The create handler validates the API request and calls `alert_service.create_alert`.
3. The service creates the alert with status `PENDING_ANALYSIS`, stores it in DynamoDB, and queues an SQS message.
4. `AnalysisWorkerFunction` consumes the message and calls `alert_service.analyze_alert`.
5. `risk_scoring_service` calculates deterministic signals, `riskScore`, and `riskLevel`.
6. `ai_summary_service` retrieves the OpenAI key through `secrets_service`, calls OpenAI if available, and falls back to a deterministic summary if not.
7. The repository stores `analysisResult` and updates the alert to `ANALYSIS_COMPLETED`.

Re-analysis uses the same async pattern through `POST /alerts/{alertId}/analyze`.

## Security Design

- The OpenAI API key is stored in AWS Secrets Manager.
- Lambda environment variables contain only `OPENAI_SECRET_NAME`, not the secret value itself.
- Only `AnalysisWorkerFunction` has `secretsmanager:GetSecretValue`.
- API handler Lambdas do not have permission to read the OpenAI secret.
- GitHub Actions uses placeholder environment variables only and does not use real AWS credentials or real OpenAI keys.
- AI output is intentionally limited to summaries and recommended actions.
- Final fraud decisions remain a human responsibility supported by deterministic signals.

See [docs/security.md](docs/security.md) for the full security notes.

## Testing And CI

The project includes unit tests for repository, service, handler, queue, secrets, worker, and AI summary behavior.

- `pytest` is used for unit testing.
- AWS clients are mocked in tests.
- Secrets Manager access is mocked in tests.
- OpenAI HTTP calls are mocked in tests.
- GitHub Actions runs:
  - `python -m pytest`
  - `sam validate`
  - `sam build`

Real deployment still happens manually with AWS SAM. The OpenAI secret remains in AWS Secrets Manager and is not stored in GitHub Actions.

The CI workflow is defined in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Deployment Overview

The application is deployed with AWS SAM.

Typical workflow:

```bash
python3 -m pytest -q
sam validate
sam build
sam deploy --guided
```

Recommended deployment values:

- Stack name: `ai-fraud-triage-dev`
- Region: `ap-northeast-1`

Full deployment instructions are in [docs/deployment.md](docs/deployment.md).

## Example API Usage

Set the API base URL from the CloudFormation `ApiEndpoint` output:

```bash
API_ENDPOINT="https://your-api-id.execute-api.ap-northeast-1.amazonaws.com/Prod/"
```

Create an alert:

```bash
curl -X POST "${API_ENDPOINT}alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "cust-001",
    "accountId": "acct-001",
    "alertType": "SUSPICIOUS_TRANSFER",
    "amount": 125000,
    "country": "JP",
    "historicalAverageAmount": 25000,
    "isNewBeneficiary": true,
    "transactionCountLastHour": 4
  }'
```

List alerts:

```bash
curl "${API_ENDPOINT}alerts"
```

Get one alert:

```bash
curl "${API_ENDPOINT}alerts/<alertId>"
```

Requeue analysis:

```bash
curl -X POST "${API_ENDPOINT}alerts/<alertId>/analyze"
```

Detailed request and response examples are in [docs/api.md](docs/api.md).

## Limitations

- The data model is intentionally simple and optimized for MVP clarity rather than broad query flexibility.
- `list_alerts` currently uses a DynamoDB `Scan`, which is acceptable for a small prototype but not ideal at larger scale.
- The worker currently relies on SQS retries, DLQ behavior, and logs for failure visibility instead of persisting an `ANALYSIS_FAILED` status update.
- Authentication and authorization are not implemented yet.
- There is no frontend dashboard in this repository.
- AI output quality depends on external model behavior and is intentionally constrained to a non-decision-support role.
- This repository is a focused backend prototype, not a replacement for a full enterprise fraud operations platform.

## Future Improvements

- Add Cognito or another authorizer for API protection
- Add GSIs for operational query patterns such as `customerId`, `status`, `riskLevel`, and `createdAt`
- Persist explicit failure states for worker analysis failures
- Add CloudWatch custom metrics, alarms, and X-Ray tracing
- Add multi-environment deployment strategy
- Add a frontend investigator dashboard
- Evaluate Bedrock for AWS-native model integration

See [docs/future-improvements.md](docs/future-improvements.md) for a more detailed roadmap.
