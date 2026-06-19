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
        <p className="eyebrow">Document analysis</p>
        <h2>Extracted Fields</h2>
        <div className="skeleton-stack" aria-label="Loading claim analysis">
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
        <p className="eyebrow">Document analysis</p>
        <h2>Extracted Fields</h2>
        <p>Run analysis to review extracted claim information.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <p className="eyebrow">Document analysis</p>
      <h2>Extracted Fields</h2>
      <dl className="field-grid">
        {(Object.keys(fieldLabels) as Array<keyof ExtractedFields>).map((fieldName) => (
          <div key={fieldName}>
            <dt>{fieldLabels[fieldName]}</dt>
            <dd>{formatValue(analysis.extractedFields[fieldName])}</dd>
          </div>
        ))}
      </dl>
      <div className="summary-box">
        <p className="eyebrow">Summary</p>
        <p>{analysis.summary}</p>
      </div>
    </section>
  );
}
