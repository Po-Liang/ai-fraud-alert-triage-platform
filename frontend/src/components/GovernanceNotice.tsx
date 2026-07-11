import { ShieldCheck } from "lucide-react";

type GovernanceNoticeProps = {
  notice?: string;
};

const defaultNotice =
  "AIの出力は審査担当者の確認を支援するものであり、支払い可否の最終判断は人間が行います。原本書類、契約内容、社内ルールを必ず確認したうえで判断してください。";

export function GovernanceNotice({ notice = defaultNotice }: GovernanceNoticeProps) {
  return (
    <section className="governance-strip" aria-label="ガバナンス上の注意点">
      <ShieldCheck size={20} aria-hidden="true" />
      <div>
        <p className="eyebrow">ガバナンス上の注意点</p>
        <p>{notice}</p>
      </div>
    </section>
  );
}
