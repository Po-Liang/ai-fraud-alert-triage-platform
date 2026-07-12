import {
  AlertCircle,
  CheckCircle2,
  Database,
  Play,
  ShieldCheck,
} from "lucide-react";
import { useRef, useState } from "react";
import {
  createFraudAlert,
  getFraudAlert,
  isMockMode,
  queryKnowledgeBase,
  requestFraudAnalysis,
  submitAlertReview,
} from "../api";
import {
  buildInvestigationTasks,
  createInitialStages,
  createWorkflowRunId,
  isValidTaskPlan,
  localizeRecommendation,
  localizeRiskSignal,
  workflowVersion,
} from "../fraudWorkflow";
import type {
  AlertInput,
  FraudAlert,
  InvestigationTask,
  RagQueryResponse,
  ReviewAction,
  ReviewEvent,
  WorkflowStage,
} from "../types";

const sampleAlert: AlertInput = {
  customerId: "DEMO-CUST-001",
  accountId: "DEMO-ACCT-001",
  alertType: "SUSPICIOUS_TRANSFER",
  amount: 1_200_000,
  currency: "JPY",
  country: "JP",
  description: "面接デモ用：新規受取人への高額送金と短時間の連続取引を検知",
  historicalAverageAmount: 80_000,
  isNewBeneficiary: true,
  transactionCountLastHour: 5,
};

const stageStatusLabels: Record<WorkflowStage["status"], string> = {
  pending: "未実行",
  running: "実行中",
  completed: "完了",
  failed: "失敗",
  waiting_for_human: "人の確認待ち",
};

const taskStatusLabels: Record<InvestigationTask["status"], string> = {
  planned: "計画済み",
  running: "実行中",
  completed: "完了",
  failed: "失敗",
  waiting_for_human: "人の承認待ち",
};

const reviewActionLabels: Record<ReviewAction, string> = {
  APPROVE: "承認",
  REQUEST_REANALYSIS: "再分析を依頼",
  ESCALATE: "エスカレーション",
  CLOSE: "クローズ",
};

export function FraudInvestigationDemo() {
  const [stages, setStages] = useState(createInitialStages);
  const [alert, setAlert] = useState<FraudAlert | null>(null);
  const [evidence, setEvidence] = useState<RagQueryResponse | null>(null);
  const [tasks, setTasks] = useState<InvestigationTask[]>([]);
  const [workflowRunId, setWorkflowRunId] = useState<string | null>(null);
  const [workflowStartedAt, setWorkflowStartedAt] = useState<string | null>(null);
  const [workflowCompletedAt, setWorkflowCompletedAt] = useState<string | null>(null);
  const [totalDurationMs, setTotalDurationMs] = useState<number | null>(null);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewEvent, setReviewEvent] = useState<ReviewEvent | null>(null);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const runStartRef = useRef<number | null>(null);
  const humanReviewStartRef = useRef<number | null>(null);

  function updateStage(stageId: WorkflowStage["stageId"], patch: Partial<WorkflowStage>) {
    setStages((current) =>
      current.map((stage) => (stage.stageId === stageId ? { ...stage, ...patch } : stage)),
    );
  }

  function startStage(
    stageId: WorkflowStage["stageId"],
    inputSummary: string,
  ): number {
    const started = Date.now();
    updateStage(stageId, {
      status: "running",
      inputSummary,
      outputSummary: "処理中",
      startedAt: new Date(started).toISOString(),
      completedAt: undefined,
      durationMs: undefined,
      error: undefined,
    });
    return started;
  }

  function finishStage(
    stageId: WorkflowStage["stageId"],
    started: number,
    outputSummary: string,
  ) {
    const completed = Date.now();
    updateStage(stageId, {
      status: "completed",
      outputSummary,
      completedAt: new Date(completed).toISOString(),
      durationMs: completed - started,
    });
  }

  function failStage(
    stageId: WorkflowStage["stageId"],
    started: number,
    message: string,
  ) {
    const completed = Date.now();
    updateStage(stageId, {
      status: "failed",
      outputSummary: "処理を完了できませんでした",
      completedAt: new Date(completed).toISOString(),
      durationMs: completed - started,
      error: message,
    });
  }

  async function handleStartWorkflow() {
    const runId = createWorkflowRunId();
    const runStarted = Date.now();
    runStartRef.current = runStarted;
    setWorkflowRunId(runId);
    setWorkflowStartedAt(new Date(runStarted).toISOString());
    setWorkflowCompletedAt(null);
    setTotalDurationMs(null);
    setStages(createInitialStages());
    setAlert(null);
    setEvidence(null);
    setTasks([]);
    setReviewEvent(null);
    setReviewComment("");
    setWorkflowError(null);
    setReviewError(null);
    setIsRunning(true);
    humanReviewStartRef.current = null;

    const triageStarted = startStage(
      "triage",
      `${sampleAlert.alertType} / ${formatCurrency(sampleAlert.amount)}`,
    );

    let analyzedAlert: FraudAlert;
    try {
      const createdAlert = await createFraudAlert(sampleAlert);
      setAlert(createdAlert);
      analyzedAlert = await waitForCompletedAnalysis(createdAlert);
      setAlert(analyzedAlert);
      const analysis = analyzedAlert.analysisResult;
      if (!analysis) {
        throw new Error("分析結果が返されませんでした。");
      }
      finishStage(
        "triage",
        triageStarted,
        `ルールスコア ${analysis.riskScore} / リスク ${analysis.riskLevel}`,
      );
    } catch (error) {
      const message = errorMessage(error, "トリアージ処理に失敗しました。");
      failStage("triage", triageStarted, message);
      setWorkflowError(message);
      setIsRunning(false);
      return;
    }

    const evidenceStarted = startStage(
      "evidence",
      "ルールシグナルとアラート概要",
    );
    let retrievedEvidence: RagQueryResponse | null = null;
    try {
      retrievedEvidence = await queryKnowledgeBase(
        "新規受取人への高額送金と短時間の連続取引では、何を確認し、いつエスカレーションしますか？",
        "fraud_alerts",
      );
      setEvidence(retrievedEvidence);
      const retrievalStatus = retrievedEvidence.metadata?.retrievalStatus;
      if (retrievalStatus === "FAILED") {
        throw new Error("参照情報を取得できませんでした");
      }
      finishStage(
        "evidence",
        evidenceStarted,
        retrievedEvidence.sources.length > 0
          ? `${retrievedEvidence.sources.length}件のデモ用ガイドラインを取得`
          : "該当する参照情報なし",
      );
    } catch (error) {
      const message = errorMessage(error, "参照情報を取得できませんでした");
      retrievedEvidence = {
        answer: "参照情報を取得できませんでした。担当者が社内ルールを直接確認してください。",
        sources: [],
        metadata: {
          knowledgeBase: "fraud_alerts",
          retrievalStatus: "FAILED",
          groundingStatus: "NOT_GROUNDED",
          generationMode: "NOT_RUN",
        },
      };
      setEvidence(retrievedEvidence);
      failStage("evidence", evidenceStarted, message);
      setWorkflowError(`一部失敗: ${message}。タスクプラン作成は継続しました。`);
    }

    const planningStarted = startStage(
      "planning",
      retrievedEvidence?.metadata?.groundingStatus === "GROUNDED"
        ? "リスク分析結果と取得済み参照情報"
        : "リスク分析結果（参照情報なし）",
    );
    try {
      const taskPlan = buildInvestigationTasks(analyzedAlert, retrievedEvidence);
      if (!isValidTaskPlan(taskPlan)) {
        throw new Error("タスクプランの構造が不正です。");
      }
      setTasks(taskPlan);
      finishStage("planning", planningStarted, `${taskPlan.length}件の構造化タスクを作成`);
    } catch (error) {
      const message = errorMessage(error, "タスクプラン作成に失敗しました。");
      failStage("planning", planningStarted, message);
      setWorkflowError(message);
      setIsRunning(false);
      return;
    }

    const humanReviewStarted = Date.now();
    humanReviewStartRef.current = humanReviewStarted;
    updateStage("human_review", {
      status: "waiting_for_human",
      inputSummary: "分析結果、参照情報、タスクプラン",
      outputSummary: "調査担当者の最終判断待ち",
      startedAt: new Date(humanReviewStarted).toISOString(),
    });
    setIsRunning(false);
  }

  async function handleReview(action: ReviewAction) {
    if (!alert || !workflowRunId) {
      return;
    }
    if (["REQUEST_REANALYSIS", "ESCALATE"].includes(action) && !reviewComment.trim()) {
      setReviewError("再分析またはエスカレーションでは、判断理由を入力してください。");
      return;
    }

    setIsReviewing(true);
    setReviewError(null);
    const reviewStageStarted = humanReviewStartRef.current ?? Date.now();
    try {
      if (action === "REQUEST_REANALYSIS") {
        await requestFraudAnalysis(alert.alertId);
      }
      const result = await submitAlertReview(
        alert.alertId,
        action,
        workflowRunId,
        reviewComment,
      );
      setReviewEvent(result.reviewEvent);
      finishStage(
        "human_review",
        reviewStageStarted,
        `${reviewActionLabels[action]}を担当者判断として記録`,
      );
      const completed = Date.now();
      setWorkflowCompletedAt(new Date(completed).toISOString());
      if (runStartRef.current !== null) {
        setTotalDurationMs(completed - runStartRef.current);
      }
    } catch (error) {
      const message = errorMessage(error, "担当者判断を記録できませんでした。");
      failStage("human_review", reviewStageStarted, message);
      setReviewError(message);
    } finally {
      setIsReviewing(false);
    }
  }

  const analysis = alert?.analysisResult;
  const groundingLabel = evidence?.metadata
    ? evidence.metadata.retrievalStatus === "FAILED"
      ? "取得失敗"
      : evidence.metadata.groundingStatus === "GROUNDED"
        ? "参照情報に基づく"
        : "参照情報なし"
    : "未実行";

  return (
    <>
      <header className="app-header fraud-header">
        <div>
          <p className="eyebrow">NTT DATA 面接用PoC</p>
          <h1>AI Agent Platform Prototype</h1>
          <p className="subtitle">金融不正アラート調査のエージェント指向ワークフロー</p>
          <p className="context-note">
            完全自律型のマルチエージェントではなく、既存のAPI、SQS非同期処理、
            ローカル文書検索、Human-in-the-loopを再利用した軽量プロトタイプです。
          </p>
        </div>
        <div className={`mode-pill ${isMockMode ? "mock" : "connected"}`}>
          {isMockMode ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
          {isMockMode ? "デモモード：決定的モック" : "接続モード：AWSバックエンド"}
        </div>
      </header>

      <section className="business-problem panel">
        <div>
          <p className="section-number">1</p>
          <p className="eyebrow">業務課題</p>
          <h2>不正アラート調査の初動を標準化</h2>
          <p>
            不正アラートの件数が多く、調査担当者が優先順位付け、根拠確認、
            調査計画作成を手作業で行う負担が大きい。
          </p>
        </div>
        <div className="sample-alert-card">
          <span>架空のデモアラート</span>
          <strong>{formatCurrency(sampleAlert.amount)}</strong>
          <small>新規受取人・直近1時間に5件の取引</small>
          <button
            className="primary-button"
            type="button"
            onClick={handleStartWorkflow}
            disabled={isRunning || isReviewing}
          >
            <Play size={17} />
            {isRunning ? "ワークフロー実行中..." : "調査ワークフローを開始"}
          </button>
        </div>
      </section>

      {workflowError && <p className="error-banner workflow-error">{workflowError}</p>}

      <section className="panel workflow-panel">
        <SectionTitle number="2" eyebrow="AIエージェント実行状況" title="論理ワークフローステージ" />
        <div className="stage-list">
          {stages.map((stage, index) => (
            <article className={`stage-item status-${stage.status}`} key={stage.stageId}>
              <div className="stage-index">{index + 1}</div>
              <div className="stage-content">
                <div className="stage-heading">
                  <div>
                    <h3>{stage.stageName}</h3>
                    <small>論理エージェント役割：{stage.logicalAgentRole}</small>
                  </div>
                  <StatusBadge status={stage.status} label={stageStatusLabels[stage.status]} />
                </div>
                <dl className="stage-details">
                  <div><dt>入力</dt><dd>{stage.inputSummary}</dd></div>
                  <div><dt>出力</dt><dd>{stage.outputSummary}</dd></div>
                  <div><dt>開始</dt><dd>{formatTimestamp(stage.startedAt)}</dd></div>
                  <div>
                    <dt>終了 / 画面計測</dt>
                    <dd>
                      {stage.completedAt ? formatTimestamp(stage.completedAt) : "未記録"}
                      {stage.durationMs === undefined ? "" : ` / ${stage.durationMs} ms`}
                    </dd>
                  </div>
                </dl>
                {stage.error && <p className="stage-error">{stage.error}</p>}
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="fraud-grid">
        <section className="panel task-panel">
          <SectionTitle number="3" eyebrow="タスクプラン" title="構造化された調査タスク" />
          {tasks.length === 0 ? (
            <p className="muted">ワークフロー実行後に、未実施・完了・人の承認待ちを区別して表示します。</p>
          ) : (
            <div className="task-list">
              {tasks.map((task) => (
                <article key={task.taskId}>
                  <div className="task-heading">
                    <span>{task.taskId}</span>
                    <StatusBadge status={task.status} label={taskStatusLabels[task.status]} />
                  </div>
                  <strong>{task.description}</strong>
                  <small>{task.assignedAgent}</small>
                  <p>
                    根拠：{task.evidence.length > 0 ? task.evidence.join(" / ") : "未取得・未確認"}
                  </p>
                  {task.requiresHumanApproval && <em>人の承認が必要</em>}
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="panel evidence-panel">
          <SectionTitle number="4" eyebrow="判断根拠・参照情報" title="デモ用社内ガイドライン" />
          <div className="grounding-row">
            <Database size={18} />
            <strong>{groundingLabel}</strong>
          </div>
          {!evidence ? (
            <p className="muted">参照情報はまだ取得されていません。</p>
          ) : evidence.sources.length === 0 ? (
            <p className="evidence-unavailable">
              {evidence.metadata?.retrievalStatus === "NO_EVIDENCE"
                ? "該当する参照情報はありませんでした"
                : "参照情報を取得できませんでした"}
            </p>
          ) : (
            <div className="evidence-list">
              {evidence.sources.map((source) => (
                <article key={source.id}>
                  <span>{source.id}</span>
                  <strong>{source.title}</strong>
                  <small>{source.section}</small>
                  <p>{source.excerpt || "該当箇所はAPIから返されていません。"}</p>
                </article>
              ))}
            </div>
          )}
          {evidence && <p className="grounded-answer">{evidence.answer}</p>}
        </section>
      </div>

      <div className="fraud-grid lower-grid">
        <section className="panel recommendation-panel">
          <SectionTitle number="5" eyebrow="推奨アクション" title="AIによる調査支援" />
          {!analysis ? (
            <p className="muted">トリアージ完了後に表示します。</p>
          ) : (
            <>
              <div className={`risk-score risk-${analysis.riskLevel.toLowerCase()}`}>
                <span>ルールスコア</span>
                <strong>{analysis.riskScore}</strong>
                <small>{analysis.riskLevel}</small>
              </div>
              <ul>
                {analysis.signals.map((signal) => (
                  <li key={signal}>{localizeRiskSignal(signal)}</li>
                ))}
              </ul>
              <h3>推奨する確認</h3>
              <ul>
                {analysis.recommendedActions.map((action) => (
                  <li key={action}>{localizeRecommendation(action)}</li>
                ))}
              </ul>
              <p className="boundary-note">
                既存のAI推奨とルール分析を表示しています。RAG参照情報は別に示し、担当者が照合します。
              </p>
            </>
          )}
        </section>

        <section className="panel human-review-panel">
          <SectionTitle number="6" eyebrow="人による最終判断" title="担当者アクション" />
          <div className="human-boundary">
            <ShieldCheck size={20} />
            <p>AIは調査担当者の判断を支援するものであり、最終判断は人間が行います。</p>
          </div>
          <label htmlFor="review-comment">判断理由・コメント</label>
          <textarea
            id="review-comment"
            value={reviewComment}
            maxLength={1000}
            onChange={(event) => setReviewComment(event.target.value)}
            placeholder="確認した内容や追加調査の理由を入力"
            disabled={!alert || isReviewing || Boolean(reviewEvent)}
          />
          <div className="review-actions">
            {(Object.keys(reviewActionLabels) as ReviewAction[]).map((action) => (
              <button
                type="button"
                key={action}
                className={action === "ESCALATE" ? "primary-button" : "secondary-button"}
                disabled={!alert || isRunning || isReviewing || Boolean(reviewEvent)}
                onClick={() => handleReview(action)}
              >
                {reviewActionLabels[action]}
              </button>
            ))}
          </div>
          {reviewError && <p className="stage-error">{reviewError}</p>}
          {reviewEvent && (
            <div className="review-recorded">
              <CheckCircle2 size={18} />
              <span>
                {reviewActionLabels[reviewEvent.action]}を {formatTimestamp(reviewEvent.reviewedAt)} に記録しました。
              </span>
            </div>
          )}
        </section>
      </div>

      <section className="panel execution-panel">
        <SectionTitle number="7" eyebrow="実行・評価情報" title="軽量AgentOps / LLMOpsメタデータ" />
        <dl className="metadata-grid">
          <Metadata label="ワークフローRun ID" value={workflowRunId || "未実行"} />
          <Metadata label="ワークフローバージョン" value={workflowVersion} />
          <Metadata label="アラートID" value={alert?.alertId || "未作成"} />
          <Metadata label="開始時刻" value={formatTimestamp(workflowStartedAt)} />
          <Metadata label="完了時刻" value={formatTimestamp(workflowCompletedAt)} />
          <Metadata
            label="ワークフロー経過時間（人の判断待ちを含む・画面計測）"
            value={
              totalDurationMs === null
                ? workflowRunId
                  ? "人の判断待ち"
                  : "未実行"
                : `${totalDurationMs} ms`
            }
          />
          <Metadata label="実行モード" value={isMockMode ? "決定的モック" : "AWS接続"} />
          <Metadata
            label="RAG生成モード"
            value={evidence?.metadata?.generationMode || "未実行"}
          />
          {evidence?.metadata?.model && (
            <Metadata label="RAGモデル" value={evidence.metadata.model} />
          )}
          <Metadata
            label="担当者アクション"
            value={reviewEvent ? reviewActionLabels[reviewEvent.action] : "未記録"}
          />
          <Metadata label="担当者フィードバック" value={reviewEvent?.comment || "未記録"} />
        </dl>
        <p className="metadata-note">
          トークン数、コスト、リトライ回数、品質スコアは現在取得していないため表示していません。
        </p>
      </section>
    </>
  );
}

function SectionTitle({ number, eyebrow, title }: { number: string; eyebrow: string; title: string }) {
  return (
    <div className="numbered-heading">
      <p className="section-number">{number}</p>
      <div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div>
    </div>
  );
}

function StatusBadge({ status, label }: { status: string; label: string }) {
  return <span className={`status-badge status-${status}`}>{label}</span>;
}

function Metadata({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}

async function waitForCompletedAnalysis(createdAlert: FraudAlert): Promise<FraudAlert> {
  let currentAlert = createdAlert;
  for (let attempt = 0; attempt < 30; attempt += 1) {
    if (currentAlert.status === "ANALYSIS_COMPLETED") {
      return currentAlert;
    }
    await sleep(isMockMode ? 300 : 1000);
    currentAlert = await getFraudAlert(createdAlert.alertId);
  }
  throw new Error("非同期分析が制限時間内に完了しませんでした。");
}

function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("ja-JP", { style: "currency", currency: "JPY" }).format(amount);
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "未記録";
  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}
