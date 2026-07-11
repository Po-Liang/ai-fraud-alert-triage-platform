import type { ClaimAnalysisResponse, RagQueryResponse } from "./types";

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
  if (isMockMode) {
    return delay(mockRagResponse);
  }

  return postJson<RagQueryResponse>("/rag/query", { question });
}
