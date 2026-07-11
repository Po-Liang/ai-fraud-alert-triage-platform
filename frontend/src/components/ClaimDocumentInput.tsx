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
          <p className="eyebrow">AI-OCR出力テキスト</p>
          <h2>請求書類テキスト入力</h2>
        </div>
        <button className="ghost-button" type="button" onClick={onUseSample}>
          <Clipboard size={16} aria-hidden="true" />
          サンプルを入力
        </button>
      </div>

      <label className="input-label" htmlFor="claim-document-text">
        サンプル請求書類テキスト
      </label>
      <textarea
        id="claim-document-text"
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
          {isLoading ? "分析中..." : "請求内容を分析"}
        </button>
        <button
          className="secondary-button"
          type="button"
          onClick={() => onChange("")}
          disabled={isLoading || !claimText}
        >
          <RotateCcw size={16} aria-hidden="true" />
          クリア
        </button>
      </div>
    </section>
  );
}
