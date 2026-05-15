# Future Improvements

## Security And Access Control

- Add Cognito authentication for API consumers
- Add an API Gateway authorizer
- Refine IAM permissions further as access patterns evolve

## Data Ingestion And Search

- Add S3 CSV upload for batch alert ingestion
- Add OpenSearch for richer alert search and filtering
- Add DynamoDB GSIs for `customerId`, `riskLevel`, `status`, and `createdAt`

## AI And Analysis Evolution

- Evaluate migration from direct OpenAI API usage to Amazon Bedrock
- Add more nuanced summary prompts and response validation
- Persist an explicit `ANALYSIS_FAILED` state for worker failures

## Observability And Operations

- Add CloudWatch custom metrics and alarms
- Add AWS X-Ray tracing
- Add dashboards for queue depth, worker failures, and analysis latency

## Platform And Deployment

- Add multi-environment deployment for dev, staging, and prod
- Add safer release automation after the manual deployment workflow is stable

## Product Surface

- Add a frontend dashboard for investigators
- Add richer analyst workflow features such as case notes and escalation history
