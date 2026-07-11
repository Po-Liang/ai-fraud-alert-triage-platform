import { Search } from "lucide-react";
import type { RagQueryResponse } from "../types";
import { SourceList } from "./SourceList";

type RagCopilotPanelProps = {
  question: string;
  response: RagQueryResponse | null;
  isLoading: boolean;
  onChange: (value: string) => void;
  onAsk: () => void;
  onUseSample: () => void;
};

export function RagCopilotPanel({
  question,
  response,
  isLoading,
  onChange,
  onAsk,
  onUseSample,
}: RagCopilotPanelProps) {
  return (
    <section className="panel rag-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">社内ナレッジ検索</p>
          <h2>RAGガイドライン検索</h2>
        </div>
        <button className="ghost-button" type="button" onClick={onUseSample}>
          サンプルを入力
        </button>
      </div>

      <div className="rag-input-row">
        <input
          aria-label="審査ガイドラインへの質問"
          value={question}
          placeholder="審査ガイドラインについて質問してください"
          onChange={(event) => onChange(event.target.value)}
        />
        <button
          className="primary-button"
          type="button"
          onClick={onAsk}
          disabled={isLoading || !question.trim()}
        >
          <Search size={17} aria-hidden="true" />
          {isLoading ? "検索中..." : "ガイドラインを検索"}
        </button>
      </div>

      <div className="rag-results">
        <div>
          <p className="eyebrow">回答</p>
          <p className="answer-text">
            {response?.answer || "質問を入力すると、架空の社内ガイドラインを検索して回答します。"}
          </p>
        </div>
        <div>
          <p className="eyebrow">参照元</p>
          <SourceList sources={response?.sources || []} />
        </div>
      </div>
    </section>
  );
}
