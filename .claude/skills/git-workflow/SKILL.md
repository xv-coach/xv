---
description: Git ワークフロー（DoD 付き Issue の作成と更新 / ブランチ作成 / コミット / 日本語 PR の作成 / 状態確認）を自動化するスキル。「Issue 作って」「DoD を書いて」「DoD を更新して」「コミットして」「ブランチ切って」「PR 作って」のリクエストに proactively 使用。`git-conventions.md`（ブランチ・コミット）と `pr-language.md`（PR は日本語）に準拠。
allowed-tools: Bash, Read, Glob, Grep
---

# Git ワークフロー

`git-conventions.md`・`pr-language.md`・`definition-of-done.md` に準拠した Issue の作成、ブランチ作成、コミット、PR 作成を支援するスキル。

## 現在の状態（自動取得）

- ブランチ: !`git branch --show-current 2>/dev/null`
- 状態: !`git status --short 2>/dev/null | head -10`
- 直近 3 コミット: !`git log --oneline -3 2>/dev/null`
- リモート差分: !`git status -sb 2>/dev/null | head -1`

## 使い方

- `/git-workflow issue <タイトル>` — DoD 付きの Issue を作成する
- `/git-workflow issue check <番号>` — 満たした DoD の項目を `[x]` に更新する
- `/git-workflow branch <名前>` — 命名規則に従うブランチを作成
- `/git-workflow commit` — 変更内容を分析し、コミットメッセージを生成・実行
- `/git-workflow commit -m "メッセージ"` — メッセージを指定してコミット
- `/git-workflow pr` — `gh pr create` で日本語のプルリクエストを作成
- `/git-workflow status` — ブランチ状態 + コミット規約リマインダーを表示

引数なしの `/git-workflow` は `status` として動作する。

---

## モード: issue

### 目的

作業の完了条件（DoD）を Issue の本文に置く（→ `definition-of-done.md`）。DoD は会話ではなく Issue に残すので、`/clear` の後や別の agent に引き継いだ後も同じ完了条件で進められる。

### Issue 本文のフォーマット

```markdown
## 背景
- なぜこの作業が要るか

## 方針
- 採るアプローチ。解釈の幅があれば仮定とトレードオフ

## DoD
- [ ] <確かめられる完了条件>（検証: `<コマンド>`）
- [ ] テスト: <追加・更新するテスト>
- [ ] ドキュメント: <更新するファイル>（無ければ「影響なし」と書く）

## 対象外
- やらないこと
```

DoD の各項目は、テストやコマンドの結果で満たしたか判定できる形にする（→ `testing.md`）。

### 手順

1. 既存の Issue があるか確認する: `gh issue list --search "<キーワード>"`
2. 無ければ上のフォーマットで本文を作り、ユーザーに DoD の承認を得る
3. 作成する:

```bash
gh issue create --title "<タイトル>" --body-file <本文のファイル>
```

4. 既存の Issue に DoD が無ければ、本文に `## DoD` 節を追記して承認を得る（手順は次の check と同じ）

### check: DoD の更新

満たした項目を `[x]` にする。範囲が増えたら項目を追記する。本文は丸ごと置き換わるので、取得 → 編集 → 書き戻しの順に行う。

```bash
f=$(mktemp)
gh issue view <番号> --json body -q .body > "$f"
# "$f" の該当行を `- [x]` に編集する
gh issue edit <番号> --body-file "$f"
rm -f "$f"
```

- 満たしたか確かめていない項目は `[x]` にしない
- 未完了の項目を残して作業を止めるときは、何が残っているかを Issue にコメントする

---

## モード: branch

### 目的

命名規則に従ったブランチを作成する。

### ブランチ命名規則

| プレフィックス | 用途 | 例 |
|--------------|------|-----|
| `feature/` | 新機能追加 | `feature/player-profile` |
| `fix/` | バグ修正 | `fix/match-score-total` |
| `refactor/` | リファクタリング | `refactor/common-base-model` |
| `docs/` | ドキュメント・ADR | `docs/adr-backend-language` |
| `test/` | テスト追加・修正 | `test/edge-cases` |
| `chore/` | 設定・依存関係等 | `chore/update-dependencies` |

### 手順

1. 引数からブランチ名を取得する
2. プレフィックスが含まれていない場合、ユーザーに確認する
3. 現在のブランチ状態を確認する:

```bash
git status
git branch --show-current
```

4. 未コミットの変更がある場合はユーザーに警告する
5. 最新の `master` からブランチを作成・チェックアウトする:

```bash
git fetch origin master
git checkout -b <ブランチ名> origin/master
```

---

## モード: commit

### 目的

変更内容を分析し、`git-conventions.md` に沿った 1 論理変更のコミットを作る。差分が大きい・複数の関心事が混ざっているときは、先に `commit-advisor` エージェントで分け方を決める。

### 手順

#### 1. 変更内容の確認

```bash
git status
git diff
git diff --cached
```

#### 2. ステージング

個別ファイル指定で `git add` する（`git add .` / `-A` は秘密情報やビルド成果物を巻き込むため、validate-bash hook もブロックする）。

変更ファイルを分析し、以下を除外する:
- `.env` / `credentials.json` 等の秘密情報ファイル
- `.venv/` / `__pycache__/` / `*.pyc` / `static/` / `log/` 内のログ / `node_modules/` 等の生成物

```bash
git add src/member/models.py src/member/migrations/0003_xxx.py src/member/tests.py
```

#### 3. コミットメッセージ生成

`-m` オプションでメッセージが指定されている場合はそのまま使う。

指定されていない場合:
- 差分内容を分析し、1 行目で変更の要点が分かるメッセージを生成する。言語・プレフィックスの指定はない（📋 `xv-coach/xv#4` の対象外）ので、直近の `git log --oneline` の書き方に合わせる
- 理由や補足が要るときは 2 行目を空けて本文に書く

#### 4. コミット実行

```bash
git commit -m "$(cat <<'EOF'
選手プロフィールの公開状態を追加

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

帰属行は、ハーネスが提示するもの（モデル名入り）があればそれを使う。

#### 5. push に関するルール

`git push` はユーザーの明示的な指示があるときだけ実行する（push は外部に公開される操作で取り消しにくいため）。

コミット完了後、push が必要かどうかをユーザーに確認するメッセージを表示する。

---

## モード: pr

### 目的

`gh` CLI を使用してプルリクエストを作成する。

### 手順

#### 1. 現在の状態確認

```bash
git branch --show-current
git fetch origin master
git log --oneline origin/master..HEAD
git diff origin/master...HEAD --stat
```

#### 2. Issue の DoD の確認

対応する Issue の DoD が全項目 `[x]` か確認する（`gh issue view <番号>`）。未完了の項目があれば、PR を作る前にユーザーに伝える。

#### 3. PR タイトルの生成

- タイトルは**日本語**で書く（→ `pr-language.md`）。識別子・コマンド・ライブラリ名は原文のまま
- コミット履歴を分析し、変更の主目的を 1 文（目安 50 文字以内）で表す

#### 4. PR 本文の生成

`.github/pull_request_template.md` の節を日本語で埋める。該当しない節も削らず「なし」「該当なし」と書く:

```markdown
## 概要
- 目的・背景（1〜3 行）

## 変更内容
- 主な変更と範囲

## 関連 Issue
Closes #<Issue 番号>（関連のみなら Refs #<番号>。無ければ「なし」）

## 検証
- `uv run python manage.py test`: <結果>
- `uv run ruff check .` / `uv run ruff format --check .`: <結果>
- 未実施: <理由と未確認の範囲>

## 影響・互換性
- 破壊的変更、マイグレーション、`.env` の追加項目などの有無

## UIのスクリーンショット
該当なし

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

- 検証欄には実際に実行したコマンドと結果だけを書く。実行していないものを成功と書かない
- スクリーンショット・ログに秘密情報や実在個人の情報を含めない

#### 5. リモートへの push

PR 作成前にリモートへ push する（ユーザーに確認後）:

```bash
git push -u origin <ブランチ名>
```

#### 6. PR 作成

```bash
gh pr create --base master --title "タイトル" --body "$(cat <<'EOF'
本文
EOF
)"
```

作成された PR の URL を表示する。

---

## モード: status

### 目的

現在のブランチ状態とコミット規約のリマインダーを表示する。

### 手順

#### 1. 状態表示

以下のコマンドを実行し、結果を整形して表示する:

```bash
git branch --show-current
git status --short
git log --oneline -5
git stash list
```

#### 2. レポート

```
## Git 状態

**ブランチ**: feature/player-profile
**未コミット変更**: 3ファイル
**最新コミット**: 選手プロフィールの公開状態を追加 (2分前)

### 最近のコミット
1. 選手プロフィールの公開状態を追加
2. 得点集計の誤りを修正

### 未コミット変更
- M  src/member/models.py
- ?? src/member/migrations/0003_xxx.py

### リマインダー
- 1 コミット = 1 論理変更、`git add` はファイルを個別指定
- モデル変更にはマイグレーションを同じコミットで
- PR のタイトル・本文は日本語（`pr-language.md`）
```
