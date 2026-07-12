# Security Notes

## Secrets Manager For The OpenAI API Key

The OpenAI API key is stored in AWS Secrets Manager instead of being hardcoded in the repository or injected directly as a raw Lambda environment variable.

Benefits:

- reduces accidental secret exposure
- centralizes secret management
- supports future rotation
- provides better operational auditability

## Lambda Environment Variables Store Only The Secret Name

The worker Lambda receives:

- `OPENAI_SECRET_NAME`
- `OPENAI_MODEL`

It does not receive the raw OpenAI API key value in its environment variables.

At runtime:

1. `AnalysisWorkerFunction` calls `ai_summary_service`
2. `ai_summary_service` calls `secrets_service`
3. `secrets_service` retrieves the secret value from AWS Secrets Manager
4. the secret is cached in memory for warm invocations

## Least-Privilege IAM

The infrastructure follows a least-privilege mindset:

- API handler Lambdas receive only the DynamoDB and SQS permissions they need
- `AnalysisWorkerFunction` receives DynamoDB update permissions and permission to read the OpenAI secret
- only the functions that call OpenAI (`AnalysisWorkerFunction` and `RagQueryFunction`) have `secretsmanager:GetSecretValue`

This means alert CRUD, claim analysis, and human-review Lambdas do not have access to the OpenAI secret.

## NTT DATA Demo Reliability Boundaries

- The analysis worker timeout is 30 seconds and the SQS visibility timeout is 180 seconds.
- Failed SQS records use partial batch failure reporting and move to the DLQ after three receives.
- Fraud guidance uses local fictional demo documents and returns an explicit unavailable state when documents cannot be loaded.
- Human review actions are allow-listed and comments are length-limited.
- The prototype still uses open CORS and has no authentication. Restricting origins and adding identity and authorization are required before production use.

## No Real Secrets In GitHub Or GitHub Actions

The repository does not store a real OpenAI key.

GitHub Actions CI:

- uses placeholder environment variables only
- does not configure AWS credentials
- does not deploy infrastructure
- runs mocked tests and local SAM validation/build checks only

## AI Does Not Make Final Fraud Decisions

This is an important design choice.

Deterministic scoring remains the source of:

- `riskScore`
- `riskLevel`
- rule-based suspicious signals

AI is used only for:

- `aiSummary`
- `recommendedActions`

The model is instructed to use cautious language such as:

- may indicate
- should be reviewed
- requires verification

## Human-In-The-Loop Design

The system is built to support investigators, not replace them.

Human reviewers remain responsible for:

- interpreting the alert context
- validating evidence
- deciding whether activity is actually fraudulent
- choosing the final operational action

This boundary keeps the prototype grounded in a realistic investigator-support role and aligned with responsible AI usage.
