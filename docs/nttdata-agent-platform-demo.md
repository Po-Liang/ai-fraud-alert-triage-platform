# NTT DATA 面接デモ：金融不正アラート調査 AI Agent Platform Prototype

## 目的

このデモでは、既存の不正アラート分析基盤を、エージェント指向の調査ワークフローとして拡張する。

トリアージ、判断根拠の取得、調査タスクプラン作成、人による最終確認という処理を、論理的なステージに分けて表示する。完全自律型のマルチエージェントではなく、既存のバックエンド、非同期処理、ローカル文書検索、Human-in-the-loopを再利用した、軽量なAIエージェントプラットフォームのPoCである。

利用する顧客、口座、取引、ガイドラインはすべて架空のデモデータであり、実在する金融機関の業務ルールを示すものではない。

## 実装済みアーキテクチャ

```text
React / TypeScript interview UI
  ├─ POST /alerts
  │    └─ Lambda → DynamoDB → SQS
  │                           └─ analysis worker
  │                                ├─ deterministic risk scoring
  │                                ├─ OpenAI summary or deterministic fallback
  │                                └─ DynamoDB status/result update
  ├─ GET /alerts/{alertId}  （非同期ステータスのポーリング）
  ├─ POST /rag/query        （ローカル文書検索＋OpenAIまたは決定的フォールバック）
  └─ POST /alerts/{alertId}/review
       └─ DynamoDB reviewHistory へ担当者判断を追記

SQS repeated failures → Dead-letter queue
OpenAI credential → AWS Secrets Manager
```

AWS上の実装は API Gateway、Lambda、DynamoDB、SQS、DLQ、Secrets Manager、SAMを再利用している。新しいエージェントフレームワーク、ベクトルデータベース、ワークフローサービスは追加していない。

## エージェント指向ワークフロー

| Stage ID | 表示名 | 論理的な役割 | 実際の処理 |
|---|---|---|---|
| `triage` | トリアージ・リスク分析 | Risk Analysis Role | 既存アラートAPI、SQS worker、決定的ルールスコア、AI要約 |
| `evidence` | 判断根拠・ガイドライン検索 | Evidence Retrieval Role | ローカルJSON文書のキーワード検索、任意のOpenAI回答、決定的フォールバック |
| `planning` | 調査タスクプラン作成 | Investigation Planning Role | 分析結果と取得済み根拠から決定的な構造化タスクを作成 |
| `human_review` | 人による確認・最終判断 | Human Analyst | 承認、再分析依頼、エスカレーション、クローズを人が選択 |

ステージの状態は `pending`、`running`、`completed`、`failed`、`waiting_for_human` で表現する。実行開始・終了時刻と画面から観測した処理時間を表示する。SQSリトライ回数はアプリケーションで追跡していないため表示しない。

## 構造化タスクプラン

```text
taskId
taskType
description
status
assignedAgent
evidence[]
requiresHumanApproval
```

タスクはLLMの自由文から生成せず、既存のアラート、ルール分析、取得済み参照情報から決定的に作成する。構造と状態値をフロントエンドで検証する。

- 顧客プロファイルを確認する
- 直近の取引履歴を確認する
- 関連口座や資金移動を確認する
- 関連する社内ガイドラインを取得する
- 不足情報を特定する
- 定義済み条件に該当する場合はエスカレーションする

文書検索が完了したタスクだけを `completed` とし、実際に確認していない顧客・口座・取引タスクは `planned` のまま表示する。エスカレーションは `waiting_for_human` とし、最終判断を自動化しない。

## 判断根拠とGrounding

現在の検索は高度なベクトルRAGではない。ローカルJSON文書に対する単語・日本語n-gramの重複検索であり、最大3件を取得する。

金融不正用の文書は `src/data/fraud_alert_guidance.json` に保存し、UIでは `デモ用社内ガイドライン` と明示する。APIは文書に実在するID、タイトル、セクション、本文抜粋だけを返す。

| 状態 | 表示 |
|---|---|
| 文書を取得 | `参照情報に基づく` |
| 該当文書なし | `参照情報なし` |
| 文書ロードまたは検索失敗 | `取得失敗` / `参照情報を取得できませんでした` |

OpenAIが利用できる場合も、取得した文書だけをコンテキストとして回答するよう指示する。APIキーがない、通信に失敗した、JSON出力が不正な場合は、取得済み文書本文から決定的な回答を作る。文書がない場合は回答を推測しない。

既存のAI推奨アクションはRAGより前に非同期workerで生成される。そのため「RAGでgroundedされた推奨」とは主張せず、UIで推奨と参照情報を分け、担当者が照合する。

## Human-in-the-loop と監査情報

AIは調査担当者の判断を支援するものであり、最終判断は人間が行う。

担当者は次のいずれかを選ぶ。

- 承認
- 再分析を依頼
- エスカレーション
- クローズ

再分析とエスカレーションでは理由を必須にする。接続モードでは、既存のDynamoDBアラート項目に `reviewHistory` を追記する。

```json
{
  "reviewEventId": "server-generated UUID",
  "action": "ESCALATE",
  "reviewedAt": "server-generated UTC timestamp",
  "workflowRunId": "browser-generated workflow run ID",
  "workflowVersion": "nttdata-fraud-investigation-v1",
  "comment": "担当者が入力した理由"
}
```

これはPoCの追跡履歴であり、改ざん防止された規制対応監査ログではない。

## 軽量AgentOps / LLMOps

実行ステータス、処理時間、エラー状態、ワークフローバージョン、担当者フィードバックを記録し、継続的な改善につなげる設計を意識している。

表示する情報は実際に取得・生成したものだけである。

- workflow run ID
- workflow version
- alert ID
- stage status
- ブラウザから観測した開始・終了時刻と処理時間
- mock / AWS connected mode
- RAG generation mode
- RAGで実際に利用したモデル名（OpenAI呼び出しが成功した場合のみ）
- analyst action and feedback

現在取得していないトークン数、コスト、SQSリトライ回数、品質スコア、confidenceは表示しない。既存の `riskScore` はルールスコアであり、モデルの確信度ではない。

## セキュリティと信頼性

実装済み：

- OpenAI APIキーはAWS Secrets Managerから取得し、フロントエンドに置かない。
- Lambda IAMはDynamoDB、SQS、Secrets Managerの必要な操作とリソースに限定する。
- RAG質問は1,000文字まで、レビューコメントは1,000文字までに制限する。
- RAGのknowledge baseは許可リストで検証する。
- LLMの構造化JSON出力を検証し、失敗時は決定的フォールバックを使う。
- analysis worker timeoutを30秒、SQS visibility timeoutを180秒に設定する。
- SQS partial batch failureと3回受信後のDLQ移動を維持する。
- ローカル文書をロードできない場合は、根拠を捏造せず取得失敗を返す。
- 入力質問と取得文書を信頼できないデータとして扱うようLLMへ指示する。
- フロントエンドはステージ単位の失敗と部分継続を表示する。

本番で必要だが未実装：認証・認可、制限CORS、WAF、レート制限、個人情報マスキング、暗号鍵設計、改ざん防止監査ログ、prompt injection専用対策、文書承認パイプライン、アラームとDLQ運用、冪等性、モデル評価・承認ワークフロー。

## 現在のLLM providerと将来設計

現在はOpenAI APIを利用している。Amazon Bedrock、Azure AI Foundry、Vertex AIは実装・テストしておらず、現在サポートしているとは主張しない。

LLM呼び出しは現在 `ai_summary_service` と `rag_service` に直接実装されている。面接前の差分と回帰リスクを抑えるためprovider抽象化は行わない。将来は次の境界を導入し、秘密情報、タイムアウト、構造化出力検証を共通化する。

```text
LLMProvider
  generateStructuredOutput(...)
  getModelMetadata(...)

OpenAIProvider (current behavior)
Future: BedrockProvider / AzureAIProvider / VertexAIProvider
```

## 実装範囲と意図的な簡略化

実装した範囲：既存非同期分析の可視化、構造化タスク、金融不正デモ文書検索、担当者判断の記録、実行メタデータ、決定的モック・フォールバック。

簡略化した範囲：自律エージェント間通信、動的ツール選択、ベクトル検索、実顧客データ、認証、業務システム連携、モデル評価基盤、エンタープライズデータ基盤、規制準拠。

## 5分デモ手順

1. `npm run dev:nttdata` で `http://localhost:5176/nttdata-agent-demo` を開き、業務課題を説明する。
2. 架空の120万円・新規受取人・短時間5件のアラートを確認する。
3. `調査ワークフローを開始` を押す。
4. API → DynamoDB → SQS → workerの非同期処理とルールスコアを説明する。
5. 4つの論理ステージと各ステータス・画面計測時間を確認する。
6. 6件の構造化タスクを確認し、未実施タスクを完了扱いしていない点を説明する。
7. デモ用ガイドラインのID、タイトル、抜粋、grounding状態を確認する。
8. AI推奨と人の判断が分離されている点を説明する。
9. 判断理由を入力して `エスカレーション` を押す。
10. run ID、version、担当者判断、フィードバックを確認し、セキュリティとprovider roadmapで締める。

## 面接用説明

> このデモでは、既存の不正アラート分析基盤を、エージェント指向の調査ワークフローとして拡張しました。トリアージ、判断根拠の取得、調査タスクプラン作成、人による最終確認という処理を、論理的なステージに分けて表示しています。完全自律型のマルチエージェントではなく、既存のバックエンド、非同期処理、RAG、Human-in-the-loopを再利用した、軽量なAIエージェントプラットフォームのPoCです。

## 想定質問と回答

**Q. これはマルチエージェントですか。**

A. いいえ。現在は既存サービスを論理的な役割とステージとして整理したワークフローPoCです。自律的なエージェント間通信や動的なツール選択は実装していません。

**Q. RAGはベクトル検索ですか。**

A. いいえ。ローカルの架空ガイドラインに対するキーワード・日本語n-gram検索です。取得元と本文抜粋を確認でき、文書がない場合は回答を捏造しません。

**Q. LLMが停止した場合はどうなりますか。**

A. ルールスコアとローカル文書検索は継続し、取得済み文書から決定的な回答を返します。外部LLMを5分デモの必須条件にしていません。

**Q. なぜBedrockへ移行しなかったのですか。**

A. 面接前は既存挙動とテストを守ることを優先しました。provider境界の将来設計を示しつつ、未実装のBedrock対応を主張しない判断です。

**Q. 継続的改善には何を使いますか。**

A. ステージ状態、実行時間、エラー、参照文書、担当者アクションとコメントを評価データ候補として蓄積します。本番では匿名化、評価基準、モデル・prompt version、監視を追加します。

**Q. 本番化で最初に追加するものは何ですか。**

A. 認証・認可、データ分類とマスキング、監査ログ、冪等性とDLQ運用、承認済み文書の取り込み、監視・評価を優先します。
