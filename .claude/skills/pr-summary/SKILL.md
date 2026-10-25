---
description: 現在のブランチまたは指定 PR の差分を要約する。「PR を要約して」「差分を要約」リクエストに proactively 使用。Explore エージェントで fork 実行し、本会話のコンテキストを汚さない。
context: fork
agent: Explore
allowed-tools: Bash(gh *), Bash(git diff*), Bash(git log*)
---

# PR Summary スキル

## 動的コンテキスト

- 現在のブランチ: !`git branch --show-current 2>/dev/null`
- 直近 5 コミット: !`git log --oneline -5 2>/dev/null`
- 起点ブランチ（`origin/HEAD`）との差分ファイル: !`git diff origin/HEAD...HEAD --name-only 2>/dev/null | head -20`
- 差分サイズ: !`git diff origin/HEAD...HEAD --stat 2>/dev/null | tail -1`
- PR 番号 (gh CLI 利用可能時): !`gh pr view --json number -q .number 2>/dev/null || echo "(no PR yet)"`

## タスク

上記の差分情報をもとに、以下を含む簡潔な要約を作成する:

1. **変更の目的** (PR タイトル / 直近コミットメッセージから推定)
2. **主要な変更点** (bullet。数は差分の規模に合わせる)
3. **影響範囲** (touched modules / files の傾向)
4. **テスト状況** (テストファイルが含まれているか、既存テストが影響を受ける可能性)
5. **レビューで注意すべき点** (大きい diff / セキュリティ関連 / マイグレーション / breaking change の可能性)

## 出力ガイドライン

- PR レビュー前の "tl;dr" として、レビュアーが一読で全体を掴める長さにする
- 推測した内容は明示する（「〜と思われる」「〜の可能性」）
- 数値データ（変更行数 / ファイル数）は冒頭に置く
