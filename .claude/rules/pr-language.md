# Pull Request の言語と本文

📋 `xv-coach/xv#4` の方針。PR の目的と検証結果を読みやすくするため、PR の言語と本文の構成をそろえる。

## 言語

- 人が作成する PR、および人の依頼で AI が作成する PR は、タイトル・本文を日本語で書く
- コードの識別子、ファイルパス、コマンド、ログ、エラーメッセージ、ライブラリ名などの固有名詞は原文のまま書く（翻訳しない）
- Dependabot / Renovate などの機械生成 PR は例外。人が説明を書き足す場合は日本語を基本にする
- コミットメッセージとブランチ名の言語はこの規約の対象外（→ `git-conventions.md`）

## 本文の節

`.github/pull_request_template.md` の節を使う。該当しない節も削らず「なし」「該当なし」と書く。

| 節 | 書くこと |
|---|---|
| 概要 | 目的・背景 |
| 変更内容 | 主な変更と範囲 |
| 関連 Issue | `Closes #N` / `Refs #N`。無ければ「なし」 |
| 検証 | 実行したコマンドと結果。未実施なら理由と未確認の範囲 |
| 影響・互換性 | 破壊的変更、移行・設定変更（`.env` の追加項目など）の要否 |
| UI のスクリーンショット | UI 変更がある場合のみ、画像と確認内容。機密情報・個人情報（実在選手の情報を含む）を写さない |

## 記入例

タイトル: `選手プロフィールの公開状態を revision 単位で管理する`

```markdown
## 概要
選手紹介の下書き更新が公開中の内容を書き換えないよう、公開状態を revision 単位で持つ。

## 変更内容
- `member` に `ProfileRevision` と `Publication` を追加
- 管理画面で公開対象の revision を選べるようにした

## 関連 Issue
Refs #3

## 検証
- `uv run python manage.py test member`: 12 件成功
- `uv run python manage.py makemigrations --check --dry-run`: `No changes detected`
- 未実施: Docker 上での E2E（公開サイトが未実装のため）

## 影響・互換性
- マイグレーションの追加あり（`member/migrations/0003_...`）。既存データの移行は不要

## UIのスクリーンショット
該当なし
```
