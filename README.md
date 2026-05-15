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
- SQS async analysis worker
- OpenAI secret integration with AWS Secrets Manager
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

## Phase 6: Async Analysis Worker

Phase 6 adds SQS-based asynchronous analysis so API requests do not need to wait for background fraud analysis to finish.

The project now supports asynchronous analysis using SQS. `POST /alerts` creates an alert and immediately queues an analysis job, while `POST /alerts/{alertId}/analyze` requeues analysis for an existing alert.

The `AnalysisWorkerFunction` consumes SQS messages and triggers the actual background analysis flow. Inside the service layer, `alert_service.analyze_alert` performs deterministic risk scoring and AI summary generation before storing the results.

Using SQS decouples API latency from background analysis work, which keeps the REST API responsive and makes the analysis pipeline easier to scale. A dead-letter queue is configured for failed messages so repeated failures can be isolated for investigation.

Real AI model integration will be added in a later phase. The current implementation still uses the deterministic summary flow introduced in earlier phases.

## Phase 7: Deployment

Phase 7 focuses on building, deploying, testing, and cleaning up the serverless stack with AWS SAM.

### Build

Run the SAM build from the project root:

```bash
sam build
```

### Deploy

Deploy the stack with the guided flow:

```bash
sam deploy --guided
```

Recommended values:

- Stack name: `ai-fraud-triage-dev`
- AWS Region: `ap-northeast-1`

After deployment, SAM will print the CloudFormation outputs. You can also find the deployed API URL by checking the `ApiEndpoint` output in the terminal output, in the CloudFormation console, or by running:

```bash
aws cloudformation describe-stacks \
  --stack-name ai-fraud-triage-dev \
  --region ap-northeast-1
```

### API Test Commands

Set the API base URL from the `ApiEndpoint` output:

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

Get one alert by ID:

```bash
curl "${API_ENDPOINT}alerts/<alertId>"
```

Requeue analysis for an alert:

```bash
curl -X POST "${API_ENDPOINT}alerts/<alertId>/analyze"
```

### Verification

After sending requests, verify the system in AWS:

- DynamoDB:
  Check the `FraudAlertsTable` items and confirm the alert record uses `PK = ALERT#{alertId}` and `SK = METADATA`.
- SQS:
  Check `FraudAnalysisQueue` for queued analysis jobs and confirm failed messages would move to `FraudAnalysisDeadLetterQueue`.
- Lambda:
  Review `CreateAlertFunction`, `ListAlertsFunction`, `GetAlertFunction`, `AnalyzeAlertFunction`, and `AnalysisWorkerFunction` in the Lambda console.
- CloudWatch:
  Open the CloudWatch Logs log groups for the API Lambdas and the worker Lambda to confirm successful requests, queued jobs, and background analysis execution.

### Cleanup

When you are finished testing, delete the stack:

```bash
sam delete --stack-name ai-fraud-triage-dev --region ap-northeast-1
```

## Phase 8: OpenAI Secret Integration

Phase 8 adds secure OpenAI API key retrieval through AWS Secrets Manager for the asynchronous analysis worker.

Secrets Manager is used instead of storing the raw API key in Lambda environment variables because it reduces direct secret exposure, supports centralized secret management, and is a safer foundation for future rotation and access auditing. In this design, Lambda receives only the `OPENAI_SECRET_NAME` reference, not the actual API key value.

At runtime, `AnalysisWorkerFunction` reads the `OPENAI_SECRET_NAME` environment variable and uses the dedicated `secrets_service` to load the secret from AWS Secrets Manager. The secret is cached in memory within the Lambda execution environment to reduce repeated Secrets Manager calls during warm invocations.

Safe AWS CLI example with placeholder values only:

```bash
aws secretsmanager create-secret \
  --name ai-fraud-triage/openai-api-key \
  --secret-string '{"OPENAI_API_KEY":"REPLACE_WITH_REAL_KEY"}' \
  --region ap-northeast-1
```

```bash
sam deploy --guided \
  --parameter-overrides \
    OpenAISecretName=ai-fraud-triage/openai-api-key \
    OpenAIModel=gpt-4o-mini
```

Least-privilege IAM is preserved:

- only `AnalysisWorkerFunction` has `secretsmanager:GetSecretValue`
- API handler Lambdas do not have permission to read the OpenAI secret
- API handlers also do not receive the OpenAI secret name in their environment variables

The AI model is used only to generate:

- `aiSummary`
- `recommendedActions`

It does not decide fraud. Deterministic risk scoring remains the source of `riskLevel` and `riskScore`, and the AI output is limited to cautious investigation support language.

Recommended production improvements for a real deployment:

- Enable secret rotation
- Protect the secret with a customer-managed KMS key
- Monitor Secrets Manager access and Lambda errors in CloudWatch
- Add client-side caching to further reduce repeated secret lookups and external API overhead

### CloudWatch Verification For OpenAI Summary Path

After deploying, you can confirm whether the async worker actually attempted the OpenAI path by checking the `AnalysisWorkerFunction` CloudWatch logs.

Expected worker and service log sequence:

- `analysis_worker_started`
- `sqs_record_received`
- `analysis_started_for_alert`
- `alert_service_analyze_started`
- `risk_scoring_completed`
- `ai_summary_generation_started`
- `ai_summary_service_called`
- `openai_secret_lookup_started`

If the OpenAI path is used successfully, you should then see:

- `openai_secret_lookup_succeeded`
- `openai_api_call_attempted`
- `openai_api_call_succeeded`
- `ai_summary_result_returned ... mode=openai`
- `ai_summary_generation_completed`
- `analysis_result_update_completed`
- `analysis_completed_for_alert`

If the deterministic fallback path is used instead, you should see:

- `ai_summary_fallback_used`
- `ai_summary_result_returned ... mode=fallback`

This makes it easier to distinguish:

- secret lookup problems
- OpenAI API call failures
- fallback summary behavior
- successful background analysis completion

## Phase 9: GitHub Actions CI

Phase 9 adds a simple GitHub Actions workflow for continuous integration.

The workflow runs on pushes to `main` and pull requests targeting `main`. It sets up Python 3.12, installs the runtime and development test dependencies, runs `python -m pytest`, runs `sam validate`, and then runs `sam build` as a separate step so test, template, and build failures are easy to identify.

The test suite in CI continues to mock AWS clients, Secrets Manager access, and OpenAI HTTP calls, so GitHub Actions does not need AWS credentials or a real OpenAI API key. Placeholder environment variables such as `OPENAI_SECRET_NAME=test/openai-api-key` and `OPENAI_MODEL=test-model` are used only to support safe test execution.

Deployment is still performed manually with AWS SAM. The real OpenAI API key remains in AWS Secrets Manager in the deployed AWS environment and is not stored in GitHub Actions.

### Next Steps

- Deploy to AWS
