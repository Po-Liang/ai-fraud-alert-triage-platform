import type { RagSource } from "../types";

type SourceListProps = {
  sources: RagSource[];
};

export function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) {
    return <p className="muted">No sources returned yet.</p>;
  }

  return (
    <ul className="source-list">
      {sources.map((source) => (
        <li key={source.id}>
          <span>{source.id}</span>
          <strong>{source.title}</strong>
          <small>{source.section}</small>
        </li>
      ))}
    </ul>
  );
}
