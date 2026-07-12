import { AlertCircle, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { analyzeClaim, isMockMode, queryRag } from "../api";
import type { ClaimAnalysisResponse, RagQueryResponse } from "../types";
import { ClaimAnalysisPanel } from "./ClaimAnalysisPanel";
import { ClaimDocumentInput } from "./ClaimDocumentInput";
import { GovernanceNotice } from "./GovernanceNotice";
import { RagCopilotPanel } from "./RagCopilotPanel";
import { ReviewChecklistPanel } from "./ReviewChecklistPanel";

const sampleClaimText =
  "申請者: 山田太郎。請求種別: 入院給付金。入院期間: 2026年5月1日から2026年5月10日。診断名: 肺炎。提出書類: 診断書、入院証明書、請求書。";

const sampleQuestion = "入院給付金の審査で確認すべき項目は何ですか？";

const workflowSteps = [
  "AI-OCRで抽出したテキスト",
  "ルールベースの項目抽出",
  "RAGガイドライン検索",
  "審査担当者による最終判断",
];

export function InsuranceClaimsDemo() {
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
      setClaimError(error instanceof Error ? error.message : "請求内容の分析に失敗しました。");
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
      setRagError(error instanceof Error ? error.message : "ガイドライン検索に失敗しました。");
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <>
      <header className="app-header">
        <div>
          <p className="eyebrow">面接用PoCデモ</p>
          <h1>AI Insurance Claims Review Copilot</h1>
          <p className="subtitle">
            保険金・給付金の審査業務を想定したPoCデモです。請求書類テキストの整理、
            確認チェックリストの作成、社内ガイドラインの検索を支援します。
          </p>
          <p className="context-note">
            このデモは、AI-OCRで読み取った後のテキストを入力として扱います。
            OCR機能自体は実装しておらず、抽出済みテキストを審査業務でどう活用するかに焦点を当てています。
          </p>
        </div>
        <div className={`mode-pill ${isMockMode ? "mock" : "connected"}`}>
          {isMockMode ? (
            <AlertCircle size={16} aria-hidden="true" />
          ) : (
            <CheckCircle2 size={16} aria-hidden="true" />
          )}
          {isMockMode
            ? "デモモード：モックデータを使用中"
            : "接続モード：バックエンドAPIを使用中"}
        </div>
      </header>

      <ol className="workflow-strip" aria-label="デモの処理フロー">
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
        response={ragResponse}
        isLoading={isAsking}
        onChange={setQuestion}
        onAsk={handleAskCopilot}
        onUseSample={() => setQuestion(sampleQuestion)}
      />
    </>
  );
}
