# Definition of Done (完了定義)

作業の完了条件。詳細手順は各参照先を SSoT とする（Issue と PR の `gh` 手順は `git-workflow` skill）。

## Phase 1: 計画（コード着手前）
- 作業ごとに Issue を 1 つ用意し（無ければ作る）、完了条件をテストやコマンドで確かめられる形で書く（→ `testing.md`）。タイポ・1 行の設定変更など軽微な修正は省略してよい
- 要求に解釈の幅がある場合は、仮定とトレードオフを Issue に書いてから着手する
- 方向性（バックエンド言語、API 方式、DB、テナント分離、既存実装の扱いなど）に関わる判断は 📋 `xv-coach/xv#3` を確認し、`docs/adr/NNNN-<slug>.md` の ADR（Status: Proposed → Accepted）に残す。Accepted でない選択肢を実装で既成事実にしない
- 中規模以上の変更は worktree などで隔離する（手順は `worktree-safety` skill）

## Phase 2: 実装（コーディング中）
- 変更コードにコメント規約を適用（→ `code-comments.md`）
- 変更内容に対応するテストを作成・更新（省略時は Issue / PR に理由を書く）（→ `test-authoring.md`）
- モデルを変えたらマイグレーションを同じ作業で作る（`uv run python manage.py makemigrations`）
- 影響するドキュメント（`AGENTS.md` / `docs/` / `.env.example`）を実装と同じ作業内で更新する
- 最小変更原則を守る（→ `minimal-change.md`）

## Phase 3: コミット前（各コミット前）
- `src/` で `uv run python manage.py check`、`makemigrations --check --dry-run`、`test` が通る。新規・変更ファイルは `uv run ruff check` がクリーン（コマンドは `AGENTS.md`）
- 秘密情報（`.env`、鍵、実在の認証情報）や実在個人のデータを含めない
- コミットの粒度は `git-conventions.md`

## Phase 4: マージ前（`master` マージ前）
- PR は日本語のタイトル・本文で、テンプレートの各節を埋める（→ `pr-language.md`）。検証欄に実行コマンドと結果、未実施の範囲を書く
- CI（GitHub Actions）が通っている
- 認証・認可・テナント分離・公開範囲・秘密情報に関わる変更は `security-reviewer` エージェントでレビューする
- マージはユーザー（リポジトリ管理者）の承認を得てから行う

## Phase 5: マージ後（クリーンアップ）
- worktree・マージ済みブランチを片付ける（順序は `worktree-safety` skill）
