import { AlertCircle, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { analyzeClaim, isMockMode, queryRag } from "./api";
import { ClaimAnalysisPanel } from "./components/ClaimAnalysisPanel";
import { ClaimDocumentInput } from "./components/ClaimDocumentInput";
import { GovernanceNotice } from "./components/GovernanceNotice";
import { RagCopilotPanel } from "./components/RagCopilotPanel";
import { ReviewChecklistPanel } from "./components/ReviewChecklistPanel";
import type { ClaimAnalysisResponse, RagQueryResponse } from "./types";

const sampleClaimText =
  "申請者: 山田太郎。請求種別: 入院給付金。入院期間: 2026年5月1日から2026年5月10日。診断名: 肺炎。提出書類: 診断書、入院証明書、請求書。";

const sampleQuestion = "入院給付金の審査で確認すべき項目は何ですか？";

const workflowSteps = [
  "OCR-like claim text",
  "Deterministic extraction",
  "RAG guidance search",
  "Human reviewer decision",
];

export function App() {
  const [claimText, setClaimText] = useState(sampleClaimText);
  const [question, setQuestion] = useState(sampleQuestion);
  const [analysis, setAnalysis] = useState<ClaimAnalysisResponse | null>(null);
  const [ragResponse, setRagResponse] = useState<RagQueryResponse | null>(null);
  const [claimError, setClaimError] = useState<string | null>(null);
  const [ragError, setRagError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isAsking, setIsAsking] = useState(false);

  async function handleAnalyzeClaim() {
    setIsAnalyzing(true);
    setClaimError(null);

    try {
      setAnalysis(await analyzeClaim(claimText));
    } catch (error) {
      setClaimError(error instanceof Error ? error.message : "Claim analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleAskCopilot() {
    setIsAsking(true);
    setRagError(null);

    try {
      setRagResponse(await queryRag(question));
    } catch (error) {
      setRagError(error instanceof Error ? error.message : "RAG query failed.");
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main>
      <header className="app-header">
        <div>
          <p className="eyebrow">Interview demo</p>
          <h1>AI Insurance Claims Review Copilot</h1>
          <p className="subtitle">
            A demo for insurance claim document analysis, RAG knowledge search,
            and human-in-the-loop review.
          </p>
        </div>
        <div className={`mode-pill ${isMockMode ? "mock" : "connected"}`}>
          {isMockMode ? (
            <AlertCircle size={16} aria-hidden="true" />
          ) : (
            <CheckCircle2 size={16} aria-hidden="true" />
          )}
          {isMockMode ? "Demo mode: using mock data" : "Connected mode: using backend API"}
        </div>
      </header>

      <ol className="workflow-strip" aria-label="Demo workflow">
        {workflowSteps.map((step, index) => (
          <li key={step}>
            <span>{index + 1}</span>
            {step}
          </li>
        ))}
      </ol>

      <GovernanceNotice notice={analysis?.governanceNotice} />

      <div className="dashboard-grid">
        <ClaimDocumentInput
          claimText={claimText}
          sampleClaimText={sampleClaimText}
          isLoading={isAnalyzing}
          onChange={setClaimText}
          onAnalyze={handleAnalyzeClaim}
          onUseSample={() => setClaimText(sampleClaimText)}
        />

        <div className="analysis-column">
          {claimError && <p className="error-banner">{claimError}</p>}
          <ClaimAnalysisPanel analysis={analysis} isLoading={isAnalyzing} />
          <ReviewChecklistPanel items={analysis?.reviewChecklist || []} />
        </div>
      </div>

      {ragError && <p className="error-banner">{ragError}</p>}
      <RagCopilotPanel
        question={question}
        sampleQuestion={sampleQuestion}
        response={ragResponse}
        isLoading={isAsking}
        onChange={setQuestion}
        onAsk={handleAskCopilot}
        onUseSample={() => setQuestion(sampleQuestion)}
      />
    </main>
  );
}
