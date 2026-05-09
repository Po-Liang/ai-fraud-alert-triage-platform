# Deployment Guide

This document explains how to build, deploy, verify, troubleshoot, and clean up the AWS SAM stack for the AI Fraud Alert Triage Platform.

## Overview

The current stack includes:

- API Gateway REST API
- Lambda handlers for create, list, get, and requeue analysis
- SQS queue and dead-letter queue for asynchronous analysis
- SQS-triggered analysis worker Lambda
- DynamoDB table for fraud alerts

Recommended deployment settings:

- Stack name: `ai-fraud-triage-dev`
- Region: `ap-northeast-1`

## Prerequisites

Before deploying, make sure you have:

- AWS CLI installed and configured
- AWS SAM CLI installed
- Valid AWS credentials for the target account
- Permission to create CloudFormation, Lambda, API Gateway, DynamoDB, SQS, IAM, and CloudWatch resources

Check your current AWS identity:

```bash
aws sts get-caller-identity
```

Check SAM:

```bash
sam --version
```

## Build

From the project root, run:

```bash
sam build
```

Expected result:

- `.aws-sam/build/` is created
- SAM reports `Build Succeeded`

## Deploy

Run the guided deployment:

```bash
sam deploy --guided
```

Recommended values during the guided flow:

- Stack Name: `ai-fraud-triage-dev`
- AWS Region: `ap-northeast-1`
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Disable rollback: `N`
- Save arguments to configuration file: `Y`

After a successful deploy, SAM prints stack outputs including the API endpoint.

## Find the API Endpoint

You can retrieve the API endpoint from the deploy output or with CloudFormation:

```bash
aws cloudformation describe-stacks \
  --stack-name ai-fraud-triage-dev \
  --region ap-northeast-1 \
  --query "Stacks[0].Outputs"
```

Set it locally:

```bash
API_ENDPOINT="https://your-api-id.execute-api.ap-northeast-1.amazonaws.com/Prod/"
```

## Test the API

### Create an alert

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

Expected behavior:

- API returns quickly
- alert is created with `PENDING_ANALYSIS`
- analysis job is sent to SQS

### List alerts

```bash
curl "${API_ENDPOINT}alerts"
```

### Get a single alert

```bash
curl "${API_ENDPOINT}alerts/<alertId>"
```

### Requeue analysis

```bash
curl -X POST "${API_ENDPOINT}alerts/<alertId>/analyze"
```

Expected behavior:

- API returns `202`
- analysis job is queued again

## Verify the Stack in AWS

### DynamoDB

Open `FraudAlertsTable` and confirm:

- records are written successfully
- primary key shape is:
  - `PK = ALERT#{alertId}`
  - `SK = METADATA`
- `status`, `createdAt`, `updatedAt`, and analysis result fields are present as expected

### SQS

Open:

- `FraudAnalysisQueue`
- `FraudAnalysisDeadLetterQueue`

Verify:

- messages appear in the main queue after create or requeue calls
- messages are consumed by `AnalysisWorkerFunction`
- failed messages can move to the DLQ after repeated processing failures

### Lambda

Verify these functions exist and are healthy:

- `CreateAlertFunction`
- `ListAlertsFunction`
- `GetAlertFunction`
- `AnalyzeAlertFunction`
- `AnalysisWorkerFunction`

Review:

- function configuration
- environment variables
- recent invocations

### CloudWatch Logs

Check the log groups for:

- API Lambda functions
- `AnalysisWorkerFunction`

Useful things to confirm:

- request parsing is successful
- queue messages are sent
- worker receives records from SQS
- `alert_service.analyze_alert` completes successfully
- no repeated runtime or IAM errors appear

## Troubleshooting

### Lambda import error

Example:

`Runtime.ImportModuleError: Unable to import module ...`

Likely causes:

- build artifacts are stale
- a runtime dependency is missing
- a compiled dependency was built for the wrong platform

What to do:

1. Rebuild the project:

```bash
sam build
```

2. Redeploy:

```bash
sam deploy
```

3. If the error involves compiled Python packages, remove them from the Lambda runtime path or rebuild them in a Lambda-compatible environment.

For this MVP, the runtime path avoids Pydantic to prevent Linux packaging issues.

### IAM AccessDenied

Examples:

- Lambda cannot write to DynamoDB
- Lambda cannot send to SQS
- worker cannot read from its event source

What to check:

1. Open the failing Lambda in the AWS console.
2. Review its execution role.
3. Confirm the role has the permissions defined in `template.yaml`.
4. Check CloudWatch logs for the specific denied action and resource ARN.

Common examples:

- `dynamodb:PutItem` for create flow
- `dynamodb:GetItem` and `dynamodb:UpdateItem` for analysis flow
- `sqs:SendMessage` for queueing analysis jobs

After changing IAM in the template:

```bash
sam build
sam deploy
```

### SQS worker not processing messages

Symptoms:

- messages remain in `FraudAnalysisQueue`
- worker logs show no invocations

What to check:

1. Confirm `AnalysisWorkerFunction` exists.
2. Confirm the SQS event source mapping was created.
3. Confirm the queue ARN in the template matches the event source.
4. Confirm the worker Lambda has no runtime import or permission error.
5. Check CloudWatch Logs for `AnalysisWorkerFunction`.

If messages move to the DLQ:

1. Inspect the original message body.
2. Check whether `alertId` exists and is valid JSON.
3. Review worker logs for batch item failure details.

### CloudFormation rollback

Symptoms:

- stack status becomes `ROLLBACK_IN_PROGRESS` or `ROLLBACK_COMPLETE`

Common causes:

- IAM role creation blocked
- resource name collision
- insufficient account permissions
- template change causing invalid configuration

What to do:

1. Open the CloudFormation stack events.
2. Find the first failed resource.
3. Read the exact error message.
4. Fix the root cause.
5. Redeploy.

Helpful command:

```bash
aws cloudformation describe-stack-events \
  --stack-name ai-fraud-triage-dev \
  --region ap-northeast-1
```

If a previous failed stack must be removed:

```bash
sam delete --stack-name ai-fraud-triage-dev --region ap-northeast-1
```

## Cleanup

When you are finished testing:

```bash
sam delete --stack-name ai-fraud-triage-dev --region ap-northeast-1
```

This removes the CloudFormation stack and the resources managed by SAM.
