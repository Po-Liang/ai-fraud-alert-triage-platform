# Frontend Interview Demo

## Purpose

The frontend demo presents the `AI Insurance Claims Review Copilot` workflow in a way that is easy to show during an interview.

It demonstrates:

- OCR-output-like claim text analysis
- extracted claim review fields
- reviewer checklist generation
- RAG-style internal guidance search
- source-backed answers
- human-in-the-loop governance

The frontend is intentionally small and is not a production deployment target.

The two company demos use separate local development servers:

- `npm run dev:nttdata` → `http://localhost:5176/nttdata-agent-demo`
- `npm run dev:insurance` → `http://localhost:5177/insurance-claims-demo`

Each server renders only its intended company demo; there is no cross-company selector. Both reuse the same frontend project, API client, components, and styling. The NTT DATA workflow is documented in `docs/nttdata-agent-platform-demo.md`.

## Install Dependencies

From the repository root:

```bash
cd frontend
npm install
```

## Run Locally

Start the insurance claims demo:

```bash
npm run dev:insurance
```

Open:

```text
http://localhost:5177/insurance-claims-demo
```

The NTT DATA demo can run concurrently in another terminal:

```bash
npm run dev:nttdata
```

## Configure Backend API

Set `VITE_API_BASE_URL` to the deployed API Gateway base URL when you want the frontend to call the backend:

```bash
VITE_API_BASE_URL="https://your-api-id.execute-api.ap-northeast-1.amazonaws.com/Prod" npm run dev:insurance
```

Or create a local file from the example:

```bash
cp .env.local.example .env.local
```

Then edit `.env.local` with your deployed API URL and restart the relevant demo command. Vite reads `VITE_` environment variables when the dev server starts.

The frontend calls:

- `POST /claims/analyze`
- `POST /rag/query`

## Demo Without Backend

If `VITE_API_BASE_URL` is not set, the frontend uses built-in mock responses.

The UI shows:

```text
デモモード：モックデータを使用中
```

This is useful for interview walkthroughs where the deployed backend is unavailable or network access is limited.
The mock responses are intentionally fictional and should be treated as sample UI data only.

## Connected Mode

If `VITE_API_BASE_URL` is set, the UI shows:

```text
接続モード：バックエンドAPIを使用中
```

In this mode, the dashboard calls the deployed SAM backend.

## What Is Intentionally Simplified

- No login
- No Cognito
- No real OCR
- No file upload
- No S3 upload
- No frontend production deployment
- No complex state management
- No real customer data
- No real insurance data

The dashboard is designed for a short interview demo, not for production operations.

## Security Notes

- No OpenAI API key is stored in the frontend.
- No AWS credentials are stored in the frontend.
- The frontend only calls backend API endpoints.
- The OpenAI API key remains in AWS Secrets Manager on the backend side.
- Demo content uses fictional insurance claim text only.
- Do not paste real customer names, policy numbers, claim documents, or confidential insurance data into the local demo.
- AI supports human reviewers and does not make final claim payment decisions.
- Original documents, contract terms, and internal rules must be verified by humans.
