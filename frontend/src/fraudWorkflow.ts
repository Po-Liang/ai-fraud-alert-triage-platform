import type {
  FraudAlert,
  InvestigationTask,
  InvestigationTaskStatus,
  RagQueryResponse,
  WorkflowStage,
  WorkflowStageStatus,
} from "./types";

export const workflowVersion = "nttdata-fraud-investigation-v1";

export const workflowStageStatuses: WorkflowStageStatus[] = [
  "pending",
  "running",
  "completed",
  "failed",
  "waiting_for_human",
];

export const investigationTaskStatuses: InvestigationTaskStatus[] = [
  "planned",
  "running",
  "completed",
  "failed",
  "waiting_for_human",
];

const signalLabels: Record<string, string> = {
  "Beneficiary is new": "新規受取人への取引",
  "High transaction velocity in the last hour": "直近1時間の取引頻度が高い",
  "Moderate transaction velocity in the last hour": "直近1時間の取引頻度がやや高い",
  "Transaction involves a high-risk country": "高リスク国に関連する取引",
  "Transaction amount exceeds 1,000,000 JPY": "取引金額が100万円を超過",
};

const recommendationLabels: Record<string, string> = {
  "Verify the beneficiary relationship": "受取人と顧客の関係を確認する",
  "Review recent login and device activity": "直近のログインと端末情報を確認する",
  "Check for similar alerts on the same customer": "同一顧客の類似アラートを確認する",
  "Escalate for manual investigation": "人による追加調査へエスカレーションする",
  "Review customer transaction history": "顧客の取引履歴を確認する",
  "Check whether the transaction pattern is unusual": "通常と異なる取引パターンか確認する",
  "Monitor for additional suspicious activity": "追加の不審な取引をモニタリングする",
  "Record the alert result": "アラート結果を記録する",
  "No immediate escalation required based on current signals":
    "現在のルールシグナルでは即時エスカレーション不要として記録する",
};

export function createInitialStages(): WorkflowStage[] {
  return [
    {
      stageId: "triage",
      stageName: "トリアージ・リスク分析",
      logicalAgentRole: "Risk Analysis Role",
      status: "pending",
      inputSummary: "不正アラートの入力待ち",
      outputSummary: "未実行",
    },
    {
      stageId: "evidence",
      stageName: "判断根拠・ガイドライン検索",
      logicalAgentRole: "Evidence Retrieval Role",
      status: "pending",
      inputSummary: "リスク分析結果の待機中",
      outputSummary: "未実行",
    },
    {
      stageId: "planning",
      stageName: "調査タスクプラン作成",
      logicalAgentRole: "Investigation Planning Role",
      status: "pending",
      inputSummary: "分析結果と参照情報の待機中",
      outputSummary: "未実行",
    },
    {
      stageId: "human_review",
      stageName: "人による確認・最終判断",
      logicalAgentRole: "Human Analyst",
      status: "pending",
      inputSummary: "調査結果の待機中",
      outputSummary: "未実行",
    },
  ];
}

export function buildInvestigationTasks(
  alert: FraudAlert,
  evidenceResponse: RagQueryResponse | null,
): InvestigationTask[] {
  const sources = evidenceResponse?.sources || [];
  const retrievalStatus = evidenceResponse?.metadata?.retrievalStatus;
  const evidenceIds = sources.map((source) => `${source.id}: ${source.title}`);
  const riskEvidence = alert.analysisResult
    ? [
        `ルールスコア: ${alert.analysisResult.riskScore}`,
        ...alert.analysisResult.signals.map(localizeRiskSignal),
      ]
    : [];

  return [
    {
      taskId: "TASK-01",
      taskType: "confirm_customer_profile",
      description: "顧客プロファイルを確認する",
      status: "planned",
      assignedAgent: "Customer Context Role",
      evidence: [],
      requiresHumanApproval: false,
    },
    {
      taskId: "TASK-02",
      taskType: "review_recent_transactions",
      description: "直近の取引履歴を確認する",
      status: "planned",
      assignedAgent: "Transaction Review Role",
      evidence: riskEvidence,
      requiresHumanApproval: false,
    },
    {
      taskId: "TASK-03",
      taskType: "inspect_related_accounts",
      description: "関連口座や資金移動を確認する",
      status: "planned",
      assignedAgent: "Relationship Analysis Role",
      evidence: [],
      requiresHumanApproval: false,
    },
    {
      taskId: "TASK-04",
      taskType: "retrieve_guidelines",
      description: "関連する社内ガイドラインを取得する",
      status:
        retrievalStatus === "FAILED"
          ? "failed"
          : retrievalStatus === "COMPLETED" || retrievalStatus === "NO_EVIDENCE"
            ? "completed"
            : "planned",
      assignedAgent: "Evidence Retrieval Role",
      evidence: evidenceIds,
      requiresHumanApproval: false,
    },
    {
      taskId: "TASK-05",
      taskType: "identify_missing_information",
      description: "不足情報を特定する",
      status: "planned",
      assignedAgent: "Investigation Planning Role",
      evidence: [],
      requiresHumanApproval: false,
    },
    {
      taskId: "TASK-06",
      taskType: "escalation_review",
      description: "定義済み条件に該当する場合はエスカレーションする",
      status: "waiting_for_human",
      assignedAgent: "Human Analyst",
      evidence: riskEvidence,
      requiresHumanApproval: true,
    },
  ];
}

export function isValidTaskPlan(tasks: InvestigationTask[]): boolean {
  const taskIds = new Set<string>();

  return tasks.every((task) => {
    if (taskIds.has(task.taskId)) {
      return false;
    }
    taskIds.add(task.taskId);

    return (
      Boolean(task.taskId && task.taskType && task.description && task.assignedAgent) &&
      investigationTaskStatuses.includes(task.status) &&
      Array.isArray(task.evidence) &&
      task.evidence.every((item) => typeof item === "string" && item.length > 0) &&
      typeof task.requiresHumanApproval === "boolean"
    );
  });
}

export function createWorkflowRunId(): string {
  return `workflow-${crypto.randomUUID()}`;
}

export function localizeRiskSignal(signal: string): string {
  if (signalLabels[signal]) {
    return signalLabels[signal];
  }

  const ratioMatch = signal.match(
    /Transaction amount is ([0-9.]+)x higher than historical average/,
  );
  if (ratioMatch) {
    return `取引金額が過去平均の${ratioMatch[1]}倍`;
  }

  return signal;
}

export function localizeRecommendation(recommendation: string): string {
  return recommendationLabels[recommendation] || recommendation;
}
