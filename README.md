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
- Unit tests for risk scoring

### Next Steps

- Add DynamoDB repository layer
- Add Lambda API handlers
- Add SQS analysis worker
- Add AWS SAM template
- Deploy to AWS
