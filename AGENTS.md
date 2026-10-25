# AGENTS.md

AI エージェント（Claude Code / Codex / Cursor など）と人間の開発者が共通で読む、xv の作業規約の入口。規約本文は `.claude/rules/*.md` に置き、本ファイルには概要・コマンド・索引だけを置く。

## 最上位原則: Verification-first

コード変更には、エージェント自身が実行できる検証手段（テスト / `manage.py check` / ruff / ビルド）を併設する。曖昧な指示は着手前に検証可能なゴールへ変換する（→ `.claude/rules/testing.md`）。Claude Code では、コード変更後に検証を実行していないターンを Stop hook が止める。

## プロジェクト概要

xv は、複数のラグビークラブが選手・ニュース・試合結果などを管理できる、**ラグビー特化の CMS** を目指すプロジェクト。

- 現状: `src/` 以下に 2019 年頃のレガシー Django 実装がある。登録ルートは `admin/` のみで、公開 API / 公開サイトは未実装
  - Django アプリ: `common`（タイムスタンプ・論理削除の基底）、`master`（ポジション・得点方式・反則などの語彙）、`member`（チーム・選手）、`match`（試合・登録選手・得点 / 反則 / 交替イベント）
  - 設定パッケージ: `src/xv_rugby/`（`settings.py` / `urls.py` / `wsgi.py`）
- 実行環境（🔀 [xv-coach/xv#5](https://github.com/xv-coach/xv/pull/5) と 🔀 [xv-coach/xv#7](https://github.com/xv-coach/xv/pull/7) のマージ後）: Python 3.14 / Django 6.1 / PostgreSQL 18 / uv / gunicorn / WhiteNoise / GitHub Actions
  - #5 で Python 3.7 / Django 2.2 / MySQL 5.7 / Poetry / CircleCI から移行し、lint と format を ruff に統一
  - #7 で uWSGI を gunicorn に、nginx を WhiteNoise（静的ファイル配信）に置き換え。pytest + pytest-django、mypy + django-stubs、pre-commit も #7 で導入予定
- 依存の方針: 使われていない・更新が止まっているツールやライブラリは、積極的に後継へ移行する
- 秘密情報: `SECRET_KEY`・DB 認証情報などは環境変数（`.env`）から読む。`.env` はコミットしない。`.env.example` はプレースホルダ、`.env.testing` は CI 用ダミー値のみ
- 旧 `settings.py` にハードコードされていた `SECRET_KEY` は git 履歴に残っており漏洩済み。どの環境でも再利用しない。旧設定の値を Issue・ログ・fixture・PR に転載しない

### 今後の方向性（📋 `xv-coach/xv#3`）

方向性の議論は 📋 `xv-coach/xv#3` に集約する。着手前に最新の内容を確認する。

- 管理画面・コンテンツ管理・API と公開サイトの UI を分離する**ヘッドレス CMS** を軸に検討中。共通の管理基盤を複数クラブで使い、公開側はクラブごとのフロントエンド・テーマ・ドメインを扱う
- フロントエンドは TypeScript より **ReScript を優先**する
- **バックエンド言語・API 方式（REST / GraphQL）は未決定**。Django / Go / Rust / Haskell / ReScript(Node.js) を候補に、小さな検証と ADR（`docs/adr/`）で決める。ADR が Accepted になるまで、特定の言語・フレームワーク・DB 形式・既存 CMS の採用を暗黙に固定しない
- 既存 Django 実装は、語彙・関係・制約の知識を参照する資料として扱う。全面書き換えも、そのままの継承も前提にしない
- 新しい実行環境・依存・秘密管理が決まるまでは、旧コンテナや旧依存（Python 3.7 / Django 2.2 / MySQL 5.7 / Poetry）を起動・導入しない
- テナント（クラブ）分離・公開範囲・未成年の情報の扱いは、認可と公開 DTO の許可リストで守り、テストで確かめる
- fixture・テストデータは架空のものだけを使う。実在選手の情報・写真・旧 DB dump・実在のメールアドレスや認証情報は使わない

## ビルド・実行コマンド

🔀 [xv-coach/xv#5](https://github.com/xv-coach/xv/pull/5) と 🔀 [xv-coach/xv#7](https://github.com/xv-coach/xv/pull/7) のマージ後の構成を前提とする。pytest / mypy / pre-commit の行は #7 で導入された後に使える。`pyproject.toml` / `uv.lock` / `.python-version` は `src/` にある。

```bash
# 初回: 環境変数ファイルを用意し、DJANGO_SECRET_KEY と POSTGRES_PASSWORD を新しく生成した値にする
cp .env.example .env

# 依存関係のインストール（src/ で実行）
cd src
uv sync --locked

# 設定・マイグレーション・テスト（src/ で実行。PostgreSQL が必要）
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate
uv run python manage.py test
uv run pytest            # #7 で pytest + pytest-django を導入後

# lint / format / 型チェック
uv run ruff check .
uv run ruff format --check .
uv run mypy .            # #7 で mypy + django-stubs を導入後
uv run pre-commit run --all-files   # #7 で pre-commit を導入後

# Docker で起動（PostgreSQL 18 + Django(gunicorn) + WhiteNoise。http://localhost:8000）
docker compose up -d --build
```

- 依存の追加・更新は `uv add` / `uv lock` で行い、`uv.lock` を手で編集しない
- Docker を使わずに Django を動かす場合は、ローカルの PostgreSQL を `.env` の `DB_HOST` / `DB_PORT` に合わせる
- 整形・lint は ruff（`ruff check` + `ruff format`）に統一している。既存コードは #5 で `ruff format` 済み。設定の変更による一括整形は別 PR にし、機能変更と混ぜない
- CI は GitHub Actions（`.github/workflows/ci.yml`）で、`master` への push と pull request に対して `uv sync --locked` → `check` → `makemigrations --check` → `migrate` → `test` → `ruff check` / `ruff format --check` を実行する（action は SHA で固定）

## Pull Request

PR のタイトル・本文は**日本語**で書く（📋 `xv-coach/xv#4`）。本文は `.github/pull_request_template.md` の節（概要 / 変更内容 / 関連 Issue / 検証 / 影響・互換性 / UI のスクリーンショット）に沿う。詳細は `.claude/rules/pr-language.md`。

## Required Rules

`.claude/rules/*.md` が規約の単一ソース。本ファイルには索引だけを置き、ルール本文は写さない（`@import` もしない）。Claude Code は `paths:` の無いルールを常時、`paths:` のあるルールを一致するファイルを扱うときにロードする。

`.claude/rules/` を自動でロードしない環境（Codex / Cursor など）では、対象ファイルを調査・編集する前に該当ルールの本文を自分で読む。索引の要約だけでは規約を読んだことにならない。

| ルール | ロード条件 | 内容 |
|---|---|---|
| [`definition-of-done`](.claude/rules/definition-of-done.md) | 常時 | 計画〜マージ後の完了条件。方向性に関わる判断は ADR に残す |
| [`pr-language`](.claude/rules/pr-language.md) | 常時 | PR のタイトル・本文は日本語。識別子・コマンド・ログは原文、Bot の PR は例外 |
| [`git-conventions`](.claude/rules/git-conventions.md) | 常時 | 1 コミット 1 論理変更、`master` から作業ブランチを切る |
| [`testing`](.claude/rules/testing.md) | 常時 | 曖昧な指示を検証可能なゴールに変換、3 回失敗したら相談 |
| [`issue-pr-reference`](.claude/rules/issue-pr-reference.md) | 常時 | 文章中の Issue は 📋 + inline code、PR は 🔀 + リンクで区別 |
| [`test-authoring`](.claude/rules/test-authoring.md) | ソースファイル | コード変更にはテストを作成・更新、配置と命名 |
| [`code-comments`](.claude/rules/code-comments.md) | ソースファイル | 周囲に合わせ、名前から復元できない「なぜ」だけを書く |
| [`minimal-change`](.claude/rules/minimal-change.md) | ソースファイル | 要求を満たす最小の差分、ついで改善を混ぜない |
| [`github-actions`](.claude/rules/github-actions.md) | `.github/workflows/**` ほか | 外部 action は SHA 固定 + バージョンコメント |
| [`docker-build-context`](.claude/rules/docker-build-context.md) | Dockerfile / compose ほか | `.gitignore` と `.dockerignore` を併せて見直す |

「ソースファイル」は各ルールの `paths:` に一致するファイル。正確な条件は各ルールの frontmatter を確認する。

## Claude Code 固有の設定

- `.claude/settings.json`: 権限（`.env` の読み取り拒否など）と安全 hook（`git add .` / `git push --force` / `rm -rf` のブロック、シークレット混入の検知、`uv.lock` の直接編集のブロック）。hook には `jq`（無ければ `python3`）が要る
- `.claude/agents/`: `code-reviewer` / `security-reviewer` / `debugger` / `build-resolver` / `commit-advisor`
- `.claude/skills/`（`.agents/skills` は同じディレクトリへの symlink）: `/review`、`git-workflow`、`pr-summary`、`test-design`、`bash-safety`、`worktree-safety`、`/redblue-audit`
- 必須にしたい指示は hook や個人設定だけに置かず、本ファイルか `.claude/rules/` に書く

## 個人メモ

チームに共有しない指示は `~/.claude/CLAUDE.md` に書く。このディレクトリや上位ディレクトリに `CLAUDE.md` / `.claude/CLAUDE.md` / `CLAUDE.local.md` があると、Claude Code は本ファイルを読まなくなる（Claude Code v2.1.277 以降の挙動）。
