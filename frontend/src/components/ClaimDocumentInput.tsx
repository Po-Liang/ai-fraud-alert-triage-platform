import { Clipboard, FileText, RotateCcw } from "lucide-react";

type ClaimDocumentInputProps = {
  claimText: string;
  sampleClaimText: string;
  isLoading: boolean;
  onChange: (value: string) => void;
  onAnalyze: () => void;
  onUseSample: () => void;
};

export function ClaimDocumentInput({
  claimText,
  sampleClaimText,
  isLoading,
  onChange,
  onAnalyze,
  onUseSample,
}: ClaimDocumentInputProps) {
  return (
    <section className="panel input-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">OCR-output text</p>
          <h2>Claim Document Input</h2>
        </div>
        <button className="ghost-button" type="button" onClick={onUseSample}>
          <Clipboard size={16} aria-hidden="true" />
          Sample
        </button>
      </div>

      <textarea
        aria-label="Claim OCR text"
        value={claimText}
        placeholder={sampleClaimText}
        onChange={(event) => onChange(event.target.value)}
      />
      <p className="input-note">
        架空のデモ文書のみを入力してください。実在顧客・証券情報は入力しないでください。
      </p>

      <div className="button-row">
        <button
          className="primary-button"
          type="button"
          onClick={onAnalyze}
          disabled={isLoading || !claimText.trim()}
        >
          <FileText size={17} aria-hidden="true" />
          {isLoading ? "Analyzing..." : "Analyze Claim"}
        </button>
        <button
          className="secondary-button"
          type="button"
          onClick={() => onChange("")}
          disabled={isLoading || !claimText}
        >
          <RotateCcw size={16} aria-hidden="true" />
          Clear
        </button>
      </div>
    </section>
  );
}
