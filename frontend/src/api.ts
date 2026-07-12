import type {
  AlertAnalysisResult,
  AlertInput,
  ClaimAnalysisResponse,
  FraudAlert,
  RagQueryResponse,
  ReviewAction,
  ReviewResponse,
} from "./types";

const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const apiBaseUrl = rawApiBaseUrl ? rawApiBaseUrl.replace(/\/+$/, "") : "";

export const isMockMode = !apiBaseUrl;

const governanceNotice =
  "AIの出力は審査担当者の確認を支援するものであり、支払い可否の最終判断は人間が行います。原本書類、契約内容、社内ルールを必ず確認したうえで判断してください。";

const mockClaimAnalysis: ClaimAnalysisResponse = {
  claimType: "入院給付金",
  extractedFields: {
    claimantName: "山田太郎",
    claimType: "入院給付金",
    hospitalizationPeriod: "2026年5月1日から2026年5月10日",
    treatmentDate: null,
    eventDateOrPeriod: "2026年5月1日から2026年5月10日",
    diagnosis: "肺炎",
    submittedDocuments: ["診断書", "入院証明書", "請求書"],
  },
  summary:
    "入院給付金のOCR出力テキストを確認しました。診断・傷病情報は「肺炎」、期間または処置日は「2026年5月1日から2026年5月10日」として抽出されています。抽出結果は原本書類と照合して確認してください。",
  reviewChecklist: [
    "OCR抽出結果を原本書類と照合する",
    "請求人、被保険者、受取人、契約者の関係を確認する",
    "契約内容と給付対象条件を確認する",
    "AI出力を参考情報として扱い、最終判断は人間の審査担当者が行う",
  ],
  governanceNotice,
};

const mockRagResponse: RagQueryResponse = {
  answer:
    "参照したデモ社内ガイダンスに基づくと、入院給付金の審査では請求書、入院証明書、診断書に記載された入院開始日と退院日を照合してください。日付差異や判読困難な記載がある場合は、人間の審査担当者が原本を確認してください。\n\nAIは最終的な請求承認、否認、支払い可否を判断しません。",
  sources: [
    {
      id: "GUIDE-DEMO-001",
      title: "入院給付金審査ガイド",
      section: "入院期間確認",
    },
    {
      id: "GUIDE-DEMO-002",
      title: "診断書確認ガイド",
      section: "診断名・治療内容確認",
    },
  ],
};

const mockFraudRagResponse: RagQueryResponse = {
  answer:
    "参照したデモ用社内ガイドラインに基づき、新規受取人との関係、登録時の端末情報、短時間の連続取引、関連口座を確認してください。複数のルールシグナルが重なる場合は、人による追加調査の候補とします。\n\nAIは調査担当者の判断を支援するものであり、最終判断は人間が行います。",
  sources: [
    {
      id: "FRAUD-GUIDE-DEMO-002",
      title: "新規受取人口座確認ガイド",
      section: "受取人関係と登録経路",
      excerpt:
        "面接デモ用の架空ガイドライン。新規受取人への送金では、受取人と顧客の関係、受取人登録日時、登録時の端末情報、直前の認証変更の有無を確認する。確認結果が得られるまでは最終判断を自動化しない。",
      sourceType: "demo_internal_guideline",
    },
    {
      id: "FRAUD-GUIDE-DEMO-005",
      title: "不正アラート・エスカレーションガイド",
      section: "人による追加調査",
      excerpt:
        "面接デモ用の架空ガイドライン。高額取引、新規受取人、短時間の連続取引など複数のルールシグナルが重なる場合は、上位担当者による追加調査の候補とする。エスカレーションと最終措置は調査担当者が決定する。",
      sourceType: "demo_internal_guideline",
    },
  ],
  metadata: {
    knowledgeBase: "fraud_alerts",
    retrievalStatus: "COMPLETED",
    groundingStatus: "GROUNDED",
    generationMode: "MOCK_DETERMINISTIC",
  },
};

const mockAlerts = new Map<string, FraudAlert>();

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(value), 250);
  });
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  } catch (error) {
    throw new Error(
      error instanceof TypeError
        ? "バックエンドAPIに接続できませんでした。API URL、デプロイ状況、CORS設定を確認してください。"
        : "バックエンドAPIへのリクエストに失敗しました。",
    );
  }

  const responseText = await response.text();
  const payload = responseText ? safeJsonParse(responseText) : {};

  if (!response.ok) {
    throw new Error(getErrorMessage(payload, response.status));
  }

  return payload as T;
}

function safeJsonParse(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return { message: value };
  }
}

function getErrorMessage(payload: unknown, status: number): string {
  if (
    payload &&
    typeof payload === "object" &&
    "message" in payload &&
    typeof payload.message === "string"
  ) {
    return payload.message;
  }

  return `リクエストに失敗しました（HTTP ${status}）。`;
}

export async function analyzeClaim(claimText: string): Promise<ClaimAnalysisResponse> {
  if (isMockMode) {
    return delay(mockClaimAnalysis);
  }

  return postJson<ClaimAnalysisResponse>("/claims/analyze", { claimText });
}

export async function queryRag(question: string): Promise<RagQueryResponse> {
  return queryKnowledgeBase(question, "insurance_claims");
}

export async function queryKnowledgeBase(
  question: string,
  knowledgeBase: "insurance_claims" | "fraud_alerts",
): Promise<RagQueryResponse> {
  if (isMockMode) {
    return delay(knowledgeBase === "fraud_alerts" ? mockFraudRagResponse : mockRagResponse);
  }

  return postJson<RagQueryResponse>("/rag/query", { question, knowledgeBase });
}

export async function createFraudAlert(input: AlertInput): Promise<FraudAlert> {
  if (!isMockMode) {
    return postJson<FraudAlert>("/alerts", input);
  }

  const now = new Date().toISOString();
  const alertId = `demo-${crypto.randomUUID()}`;
  const analysisResult = calculateMockRisk(input);
  const completedAlert: FraudAlert = {
    ...input,
    alertId,
    status: "ANALYSIS_COMPLETED",
    createdAt: now,
    updatedAt: now,
    analysisResult,
  };
  mockAlerts.set(alertId, completedAlert);

  return delay({
    ...completedAlert,
    status: "PENDING_ANALYSIS",
    analysisResult: undefined,
  });
}

export async function getFraudAlert(alertId: string): Promise<FraudAlert> {
  if (!isMockMode) {
    return getJson<FraudAlert>(`/alerts/${encodeURIComponent(alertId)}`);
  }

  const alert = mockAlerts.get(alertId);
  if (!alert) {
    throw new Error("モックアラートが見つかりませんでした。");
  }
  return delay(alert);
}

export async function requestFraudAnalysis(alertId: string): Promise<void> {
  if (isMockMode) {
    await delay(undefined);
    return;
  }

  await postJson(`/alerts/${encodeURIComponent(alertId)}/analyze`, {});
}

export async function submitAlertReview(
  alertId: string,
  action: ReviewAction,
  workflowRunId: string,
  comment: string,
): Promise<ReviewResponse> {
  if (!isMockMode) {
    return postJson<ReviewResponse>(`/alerts/${encodeURIComponent(alertId)}/review`, {
      action,
      workflowRunId,
      comment,
    });
  }

  return delay({
    alertId,
    reviewStatus: action,
    reviewEvent: {
      reviewEventId: `demo-review-${crypto.randomUUID()}`,
      action,
      reviewedAt: new Date().toISOString(),
      workflowRunId,
      workflowVersion: "nttdata-fraud-investigation-v1",
      ...(comment.trim() ? { comment: comment.trim() } : {}),
    },
  });
}

async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`);
  } catch {
    throw new Error("バックエンドAPIに接続できませんでした。");
  }

  const responseText = await response.text();
  const payload = responseText ? safeJsonParse(responseText) : {};
  if (!response.ok) {
    throw new Error(getErrorMessage(payload, response.status));
  }
  return payload as T;
}

function calculateMockRisk(input: AlertInput): AlertAnalysisResult {
  let riskScore = 0;
  const signals: string[] = [];
  if (input.historicalAverageAmount > 0) {
    const ratio = input.amount / input.historicalAverageAmount;
    if (ratio >= 10) {
      riskScore += 30;
      signals.push(`Transaction amount is ${ratio.toFixed(1)}x higher than historical average`);
    } else if (ratio >= 5) {
      riskScore += 20;
      signals.push(`Transaction amount is ${ratio.toFixed(1)}x higher than historical average`);
    } else if (ratio >= 3) {
      riskScore += 10;
      signals.push(`Transaction amount is ${ratio.toFixed(1)}x higher than historical average`);
    }
  }
  if (input.isNewBeneficiary) {
    riskScore += 25;
    signals.push("Beneficiary is new");
  }
  if (input.transactionCountLastHour >= 5) {
    riskScore += 20;
    signals.push("High transaction velocity in the last hour");
  } else if (input.transactionCountLastHour >= 3) {
    riskScore += 10;
    signals.push("Moderate transaction velocity in the last hour");
  }
  if (["IR", "KP", "SY"].includes(input.country.toUpperCase())) {
    riskScore += 15;
    signals.push("Transaction involves a high-risk country");
  }
  if (input.amount >= 1_000_000) {
    riskScore += 10;
    signals.push("Transaction amount exceeds 1,000,000 JPY");
  }
  riskScore = Math.min(riskScore, 100);
  const riskLevel = riskScore >= 70 ? "HIGH" : riskScore >= 40 ? "MEDIUM" : "LOW";

  return {
    riskScore,
    riskLevel,
    signals,
    aiSummary:
      "ルールベースの分析結果を整理しました。複数のシグナルは追加調査の必要性を示す可能性があります。最終判断は人間の調査担当者が行います。",
    recommendedActions: [
      "受取人と顧客の関係を確認する",
      "直近の取引履歴と端末情報を確認する",
      "関連アラートを確認する",
      "必要に応じて人による追加調査へエスカレーションする",
    ],
  };
}
