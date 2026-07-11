import { CheckCircle2 } from "lucide-react";

type ReviewChecklistPanelProps = {
  items: string[];
};

export function ReviewChecklistPanel({ items }: ReviewChecklistPanelProps) {
  return (
    <section className="panel checklist-panel">
      <p className="eyebrow">人による確認（Human-in-the-loop）</p>
      <h2>確認チェックリスト</h2>
      {items.length === 0 ? (
        <p className="muted">請求内容を分析すると、審査担当者向けの確認項目が表示されます。</p>
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
