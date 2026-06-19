import { Search } from "lucide-react";
import type { RagQueryResponse } from "../types";
import { SourceList } from "./SourceList";

type RagCopilotPanelProps = {
  question: string;
  sampleQuestion: string;
  response: RagQueryResponse | null;
  isLoading: boolean;
  onChange: (value: string) => void;
  onAsk: () => void;
  onUseSample: () => void;
};

export function RagCopilotPanel({
  question,
  sampleQuestion,
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
          <p className="eyebrow">RAG knowledge search</p>
          <h2>Claims Review Copilot</h2>
        </div>
        <button className="ghost-button" type="button" onClick={onUseSample}>
          Sample
        </button>
      </div>

      <div className="rag-input-row">
        <input
          aria-label="RAG question"
          value={question}
          placeholder={sampleQuestion}
          onChange={(event) => onChange(event.target.value)}
        />
        <button
          className="primary-button"
          type="button"
          onClick={onAsk}
          disabled={isLoading || !question.trim()}
        >
          <Search size={17} aria-hidden="true" />
          {isLoading ? "Searching..." : "Ask Copilot"}
        </button>
      </div>

      <div className="rag-results">
        <div>
          <p className="eyebrow">Answer</p>
          <p className="answer-text">
            {response?.answer || "Ask a question to retrieve fake internal guidance."}
          </p>
        </div>
        <div>
          <p className="eyebrow">Sources</p>
          <SourceList sources={response?.sources || []} />
        </div>
      </div>
    </section>
  );
}
