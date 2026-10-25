# Git 規約

## ブランチ運用

- コード変更は `master` から作成した作業ブランチで行う（例: `feature/player-profile`、`fix/match-score`、`docs/adr-backend`、`chore/update-deps`）。命名と作成手順は `git-workflow` skill
- `master` へは PR 経由でマージする。PR のタイトル・本文は日本語（→ `pr-language.md`）
- 他の人・agent が進めている PR のブランチには、依頼がない限りコミット・push しない

## コミット

- 1 コミット = 1 論理変更。実装コード + 対応テスト + マイグレーション + 影響ドキュメントは同一コミット可
- 依存の更新（`pyproject.toml` / `uv.lock`）、既存コードへの一括整形は、機能変更と別のコミットにする
- メッセージは 1 行目で変更の要点が分かるように書く。言語・プレフィックスは現時点で指定しない（📋 `xv-coach/xv#4` の対象外）
- ステージはファイルを個別に指定する（`git add .` / `-A` は `.env` やビルド成果物を巻き込むため、hook がブロックする）
