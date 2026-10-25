---
description: 直近のコード変更が**プロジェクト規約に準拠しているか**を `code-reviewer` エージェントに委譲して検証する。コミット前 / PR 作成前に `/review` で明示起動。バグ検出そのものが目的なら公式の `/code-review` を使う。Writer/Reviewer 分離で本会話のコンテキストを汚さない。
allowed-tools: Read, Glob, Grep, Bash, Agent
disable-model-invocation: true
---

# Review スキル

直近のコード変更に対して**プロジェクト規約準拠**のレビューを実行します。

## 公式 `/code-review` との住み分け

| | 公式 `/code-review` | 本スキル `/review` |
|---|---|---|
| 見るもの | correctness バグ、簡素化・再利用の余地 | このリポジトリの規約への準拠（コメント規約 / テスト存在 / 自動生成ファイル保護 / デッドコード等 8 観点） |
| 知識源 | 汎用。差分だけを見る | `code-reviewer` エージェント（`memory: project` でリポジトリ固有の知見を蓄積） |
| 付随機能 | `--fix` で自動修正、`ultra` でクラウド多エージェント | ビルド・テスト存在・コミットメッセージの追加チェックを統合レポート化 |

見る範囲が重ならないので、コミット前は両方を流す（`/code-review` → `/review` の順）。バグは公式 `/code-review` の方が強く、規約準拠は本スキルにしか判定できない。

## 使い方

- `/review` — 未コミットの変更をレビュー
- `/review HEAD~3..HEAD` — 指定範囲のコミットをレビュー
- `/review src/path/to/File.ext` — 特定ファイルをレビュー

## 手順

### 1. レビュー対象の特定

引数に応じてレビュー対象を決定する:

- **引数なし**: `git diff --name-only` + `git diff --cached --name-only` で変更ファイルを取得
- **コミット範囲** (例: `HEAD~3..HEAD`): `git diff --name-only <範囲>` で変更ファイルを取得
- **ファイルパス**: 指定されたファイルをそのまま対象とする

設定ファイルやドキュメントは除外し、ソースコードファイルのみを対象とする。

### 2. code-reviewer エージェントの起動

Agent ツールで `.claude/agents/code-reviewer.md` のサブエージェントを起動する:

```
Agent(subagent_type="code-reviewer", prompt="Review the following files for project convention compliance: <ファイルリスト>")
```

結果を手順 4 の統合レポートに使うので、`run_in_background` は付けずに完了を待つ。

### 3. セルフレビューの実行

code-reviewer エージェントの結果に加え、以下の追加チェックを自分で実行する:

- **変更の意図**: `git log --oneline` で直近のコミットメッセージを確認し、変更が意図通りか検証
- **ビルド確認**: AGENTS.md に記載のビルドコマンドでコンパイルが通ることを確認
- **テスト確認**: 変更ファイルに対応するテストファイルが存在するか Glob で確認

### 4. レビュー結果の報告

以下の形式で統合レポートを出力する:

```
## Code Review Report

### Automated Checks (code-reviewer agent)
<エージェントの出力テーブル>

### Additional Checks
| Check | Status | Details |
|-------|--------|---------|
| Build | PASS/FAIL | ... |
| Tests exist | PASS/WARN | ... |
| Commit messages | PASS/WARN | ... |

### Recommendations
- <優先度順の改善提案>
```
