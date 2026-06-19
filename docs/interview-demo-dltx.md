# AI Insurance Claims Review Copilot

## Target Interview Context

This interview demo is prepared for 第一ライフテクノクロス株式会社 and an AI Engineer role focused on company-wide AI strategy, use case planning, PoC delivery, production implementation, LLM applications, data pipeline integration, MLOps design, AI governance, and security.

The existing backend project is an AI fraud investigation copilot. For the interview story, it is adapted into an insurance operations demo called `AI Insurance Claims Review Copilot`.

## Demo Data Safety Statement

All insurance claim cases and guidance documents added in Phase A are fictional demo fixtures.

- claimant names use clearly artificial `架空` names
- claim IDs and policy IDs use `DEMO` identifiers
- no real customer information is included
- no real policy numbers are included
- no confidential insurance documents are included
- no real company claim payment rules are included

## Business Problem

Insurance claim review teams often need to compare claim forms, medical certificates, identity documents, contract information, and internal guidance before deciding the next review action.

Common operational pain points include:

- identifying missing documents
- comparing dates and names across multiple documents
- summarizing long claim text for reviewers
- finding relevant internal guidance quickly
- keeping human reviewers in control of final payment decisions

This demo frames those needs as an AI-assisted claims review workflow.

## Business Value For The Interview Demo

The business value is not automatic claim approval. The value is reviewer productivity and consistency.

The demo is intended to show how AI could help:

- reduce time spent reading long claim text
- surface missing-document candidates earlier
- highlight inconsistencies across OCR-output-like text
- connect reviewers to relevant internal guidance
- standardize escalation reasoning across teams
- keep final decisions with trained human reviewers

This maps well to an AI Engineer role that spans use case planning, PoC design, secure implementation, governance, and production-readiness thinking.

## Why This Demo Was Adapted For Insurance Operations

The existing system already demonstrates patterns that are useful for insurance operations:

- API-based intake
- asynchronous background analysis
- deterministic scoring before AI summarization
- secure secret retrieval through AWS Secrets Manager
- unit-tested service boundaries
- infrastructure defined with AWS SAM

For the interview version, the domain story changes from suspicious transaction investigation to insurance claim review. The runtime backend is not changed in Phase A. This phase only adds fake sample claim cases, fake internal guidance documents, and demo documentation.

## Mapping To Target Use Cases

### 1. 生成AI × AI-OCR／書類処理システム

The sample claim cases include `claimText` fields that are written like OCR-output-like text from claim documents.

In this phase:

- real OCR is not implemented
- document images are not processed
- the demo assumes OCR-output-like text is already available

Future phases could connect an AI-OCR or document processing pipeline before the LLM summarization step.

### 2. 社内ナレッジ検索／RAG型業務支援システム

The fake guidance file, `src/data/insurance_claim_guidance.json`, represents internal knowledge that could later be indexed for RAG.

Example guidance topics include:

- 入院給付金審査ガイド
- 診断書確認ガイド
- 書類不備対応ガイド
- 本人確認・契約確認ガイド
- 支払い審査エスカレーション基準
- AI利用ガバナンスポリシー
- 個人情報取り扱い注意事項

In this phase, those documents are static demo data only. There is no vector database, embedding pipeline, retrieval service, or RAG runtime yet.

### 3. 保険金・給付金支払い／審査支援AI

The sample claim cases are designed around common review-support scenarios:

- hospitalization benefit review
- surgery benefit review
- death benefit review
- missing document follow-up
- date mismatch review
- identity and contract confirmation

The intended AI role is to help reviewers understand what to check next. The AI does not approve claims, reject claims, or make final payment decisions.

## Human-In-The-Loop Design

This demo keeps the human reviewer responsible for final decisions.

AI can assist with:

- summarizing claim text
- identifying possible missing documents
- highlighting inconsistencies
- suggesting review questions
- surfacing relevant guidance

Human reviewers remain responsible for:

- checking original documents
- interpreting contract terms
- deciding whether escalation is needed
- making final payment or non-payment decisions
- communicating with customers

## AI Governance And Security Considerations

The demo story is designed around responsible AI use:

- no real customer data is used
- no real insurance policy documents are included
- the OpenAI API key remains in AWS Secrets Manager
- Lambda environment variables contain only secret names, not secret values
- AI output is treated as reviewer support, not an automated decision
- final decisions remain human-in-the-loop
- future RAG sources should be versioned, permissioned, and auditable

In a production setting, additional controls would be needed for data minimization, access control, prompt logging policy, model output review, retention rules, and monitoring.

## What Is Implemented Now

Phase A adds:

- fake insurance claim cases in `src/data/sample_claim_cases.json`
- fake internal guidance documents in `src/data/insurance_claim_guidance.json`
- this interview demo brief
- a README link to the insurance demo story

These additions are documentation and sample data only.

## What Is Intentionally Simulated

The following are intentionally simulated or deferred:

- real OCR
- claim document image processing
- policy administration system integration
- claims payment system integration
- RAG retrieval
- vector search
- automated claim approval
- automated claim denial
- production insurance business rules

The sample files are fictional and should be treated as demo fixtures.

## Future Production Improvements

Possible future improvements for a production-grade version:

- connect AI-OCR output from document intake systems
- add a RAG pipeline for internal guidance search
- add access controls for role-based claim review
- add audit logs for AI input, retrieved context, and reviewer actions
- add human feedback capture for quality improvement
- add MLOps and LLMOps monitoring for latency, cost, failures, and output quality
- add PII redaction and data minimization before model calls
- add a frontend reviewer dashboard
- integrate with claim workflow and policy administration systems through controlled APIs
