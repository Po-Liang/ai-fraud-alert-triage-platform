# Deployment Guide

## Prerequisites

- Python 3.12
- AWS CLI
- AWS SAM CLI
- An AWS account with permission to deploy:
  - Lambda
  - API Gateway
  - DynamoDB
  - SQS
  - IAM
  - CloudFormation
  - Secrets Manager

## Check Local Tooling

Check AWS CLI:

```bash
aws --version
```

Check SAM CLI:

```bash
sam --version
```

Confirm the AWS identity that will deploy the stack:

```bash
aws sts get-caller-identity
```

## Validate The Project Locally

Run tests:

```bash
python3 -m pytest -q
```

Validate the SAM template:

```bash
sam validate
```

Build the application:

```bash
sam build
```

## Create The OpenAI Secret In AWS Secrets Manager

The worker Lambda expects an OpenAI secret name, not a raw API key in environment variables.

Example using placeholder structure:

```bash
aws secretsmanager create-secret \
  --name ai-fraud-triage/openai-api-key \
  --secret-string '{"OPENAI_API_KEY":"REPLACE_WITH_REAL_KEY"}' \
  --region ap-northeast-1
```

You can also update an existing secret:

```bash
aws secretsmanager put-secret-value \
  --secret-id ai-fraud-triage/openai-api-key \
  --secret-string '{"OPENAI_API_KEY":"REPLACE_WITH_REAL_KEY"}' \
  --region ap-northeast-1
```

Do not commit real secret values to the repository.

## Deploy With AWS SAM

Use guided deployment:

```bash
sam deploy --guided
```

Recommended values:

- Stack name: `ai-fraud-triage-dev`
- AWS Region: `ap-northeast-1`
- Confirm changes before deploy: your preference
- Save arguments to `samconfig.toml`: yes

When prompted for parameter overrides, use values such as:

- `OpenAISecretName=ai-fraud-triage/openai-api-key`
- `OpenAIModel=gpt-4o-mini`

## Find The API Endpoint

After deployment, check the CloudFormation output named `ApiEndpoint`.

Example:

```bash
aws cloudformation describe-stacks \
  --stack-name ai-fraud-triage-dev \
  --region ap-northeast-1
```

Set it locally:

```bash
API_ENDPOINT="https://your-api-id.execute-api.ap-northeast-1.amazonaws.com/Prod/"
```

## Test The API With `curl`

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
    "description": "Large outbound transfer to a new beneficiary",
    "historicalAverageAmount": 25000,
    "isNewBeneficiary": true,
    "transactionCountLastHour": 4
  }'
```

List alerts:

```bash
curl "${API_ENDPOINT}alerts"
```

Get an alert:

```bash
curl "${API_ENDPOINT}alerts/<alertId>"
```

Requeue analysis:

```bash
curl -X POST "${API_ENDPOINT}alerts/<alertId>/analyze"
```

## Check CloudWatch Logs

Useful log groups:

- `/aws/lambda/CreateAlertFunction`
- `/aws/lambda/ListAlertsFunction`
- `/aws/lambda/GetAlertFunction`
- `/aws/lambda/AnalyzeAlertFunction`
- `/aws/lambda/AnalysisWorkerFunction`

Example:

```bash
aws logs tail /aws/lambda/AnalysisWorkerFunction --follow --region ap-northeast-1
```

Helpful worker log markers:

- `analysis_worker_started`
- `analysis_started_for_alert`
- `risk_scoring_completed`
- `ai_summary_service_called`
- `openai_api_call_attempted`
- `ai_summary_fallback_used`
- `analysis_completed_for_alert`

## Verify AWS Resources

Check DynamoDB:

- confirm the alert exists in `FraudAlertsTable`
- confirm `PK = ALERT#{alertId}`
- confirm `SK = METADATA`

Check SQS:

- `FraudAnalysisQueue` should receive analysis jobs
- failed messages should eventually move to `FraudAnalysisDeadLetterQueue`

Check Lambda:

- API Lambdas should return quickly
- `AnalysisWorkerFunction` should handle background analysis

## Delete The Stack

When finished:

```bash
sam delete --stack-name ai-fraud-triage-dev --region ap-northeast-1
```

If you no longer need the secret, delete it separately. This is most appropriate for short-lived demo environments:

```bash
aws secretsmanager delete-secret \
  --secret-id ai-fraud-triage/openai-api-key \
  --force-delete-without-recovery \
  --region ap-northeast-1
```

Use that last command carefully in any environment where secret recovery matters.
