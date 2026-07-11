import type { ClaimAnalysisResponse, ExtractedFields } from "../types";

type ClaimAnalysisPanelProps = {
  analysis: ClaimAnalysisResponse | null;
  isLoading: boolean;
};

const fieldLabels: Record<keyof ExtractedFields, string> = {
  claimantName: "申請者 / 請求人",
  claimType: "請求種別",
  hospitalizationPeriod: "入院期間",
  treatmentDate: "治療日 / 手術日",
  eventDateOrPeriod: "対象日・期間",
  diagnosis: "診断名",
  submittedDocuments: "提出書類",
};

function formatValue(value: string | string[] | null) {
  if (Array.isArray(value)) {
    return value.length > 0 ? value.join("、") : "未抽出";
  }

  return value || "未抽出";
}

export function ClaimAnalysisPanel({ analysis, isLoading }: ClaimAnalysisPanelProps) {
  if (isLoading) {
    return (
      <section className="panel">
        <p className="eyebrow">請求書類の分析</p>
        <h2>抽出項目</h2>
        <div className="skeleton-stack" aria-label="請求内容を分析中">
          <span />
          <span />
          <span />
          <span />
        </div>
      </section>
    );
  }

  if (!analysis) {
    return (
      <section className="panel empty-panel">
        <p className="eyebrow">請求書類の分析</p>
        <h2>抽出項目</h2>
        <p>「請求内容を分析」を押すと、抽出された請求情報を確認できます。</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <p className="eyebrow">請求書類の分析</p>
      <h2>抽出項目</h2>
      <dl className="field-grid">
        {(Object.keys(fieldLabels) as Array<keyof ExtractedFields>).map((fieldName) => (
          <div key={fieldName}>
            <dt>{fieldLabels[fieldName]}</dt>
            <dd>{formatValue(analysis.extractedFields[fieldName])}</dd>
          </div>
        ))}
      </dl>
      <div className="summary-box">
        <p className="eyebrow">要約</p>
        <p>{analysis.summary}</p>
      </div>
    </section>
  );
}
