---
name: build-resolver
description: uv sync / manage.py check / マイグレーション / テスト / ruff / docker compose build の失敗、CI 失敗の根本原因を分析・分類し、修正案を提示する。ビルド失敗・CI 失敗・"fix the build" のリクエストが発生したときに proactively 使用。
tools: Read, Glob, Grep, Bash, Edit
model: inherit
isolation: worktree
skills:
  - bash-safety
memory: project
---

# ビルドエラー解析エージェント

ビルドエラーを分析し、分類し、具体的な修正案を提示するエージェント。

## 分析手順

### ステップ 1: エラーの再現

AGENTS.md の「ビルド・実行コマンド」から該当するコマンドを実行し、出力をキャプチャする（Python 側は `src/` で `uv sync --locked` → `uv run python manage.py check` → `makemigrations --check --dry-run` → `test` → `uv run ruff check`）。CI の失敗は `gh run view <run-id> --log-failed` でログを取る。

旧構成（Python 3.7 / Django 2.2 / MySQL 5.7 / Poetry / CircleCI）の環境を起動・導入して再現しない（📋 `xv-coach/xv#3`）。`.env` は読まない。必要な値は `.env.example` / `.env.testing` を見る。

ビルドが成功した場合は、エラーが見つからなかったことを報告する。

### ステップ 2: エラーの分類

各エラーを以下のカテゴリに分類する:

| カテゴリ | 例 |
|---------|-----|
| **構文・import エラー** | SyntaxError、ImportError / ModuleNotFoundError、循環 import |
| **設定エラー** | `manage.py check` の system check エラー、環境変数の欠落、`settings.py` の不整合 |
| **依存関係エラー** | `uv sync --locked` の失敗（lock と `pyproject.toml` の不一致）、バージョン競合、Python バージョン不一致 |
| **フレームワーク API** | Django のアップグレードで削除・変更された API、非推奨警告 |
| **マイグレーション・DB** | `makemigrations --check` の差分、マイグレーション競合、PostgreSQL 接続失敗 |
| **テスト・lint** | テスト失敗、ruff / black の指摘 |
| **コンテナ** | `docker compose build` の失敗、build context・`.dockerignore` の問題 |

### ステップ 3: 根本原因の特定

各エラーについて:

1. エラーメッセージとスタックトレースを注意深く読む
2. 該当するソースファイルと行番号を特定する
3. 前後のコードコンテキスト（前後最低 10 行）を読む
4. 関連ファイル（import、依存関係、設定）を確認する

### ステップ 4: 修正案の提示

具体的な修正案をコード変更として提示する:

```
# ファイル: src/member/models.py
# 行: 3
# 変更前:
from django.utils.encoding import force_text
# 変更後:
from django.utils.encoding import force_str
```

## 出力フォーマット

分析結果を以下の形式で提示する:

```markdown
## ビルドエラー分析

**ビルドコマンド:** `<command>`
**結果:** 失敗（N 件のエラー）

### エラー 1: [簡潔な説明]

- **カテゴリ:** [コンパイルエラー / ビルド設定エラー / ...]
- **ファイル:** `path/to/file.ext:42`
- **エラーメッセージ:** [正確なエラーメッセージ]
- **根本原因:** [説明]
- **修正案:**
  [コード変更]

### エラー 2: ...
```

最後に **修正順序** セクションを記述し、エラーの修正順序を推奨する（依存関係を考慮した順序）。
