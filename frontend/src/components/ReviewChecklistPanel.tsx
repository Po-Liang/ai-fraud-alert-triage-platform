import { CheckCircle2 } from "lucide-react";

type ReviewChecklistPanelProps = {
  items: string[];
};

export function ReviewChecklistPanel({ items }: ReviewChecklistPanelProps) {
  return (
    <section className="panel checklist-panel">
      <p className="eyebrow">Human review</p>
      <h2>Review Checklist</h2>
      {items.length === 0 ? (
        <p className="muted">Run claim analysis to generate review checkpoints.</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item}>
              <CheckCircle2 size={17} aria-hidden="true" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
