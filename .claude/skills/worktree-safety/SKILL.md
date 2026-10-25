---
description: git worktree を作成・削除・整理する際、または "ENOENT: no such file or directory" / posix_spawn エラーで CWD が壊れた状態の復旧時に参照する。worktree の健全性チェック・削除順序・マージ/クリーンアップ手順・CWD 復旧の SSoT。
allowed-tools: Read, Bash, Agent
---

# Git Worktree 安全運用ルール

本スキルは worktree 運用手順の **Single Source of Truth**。worktree を使う作業の健全性チェック・マージ・クリーンアップ・CWD 復旧はここを参照する。

## なぜ順序が重要か

worktree ディレクトリ内で `git worktree remove` や `git branch -D` を実行すると、シェルの CWD が無効になり Claude Code が続行不能になる（`ENOENT: no such file or directory, posix_spawn '/bin/sh'` エラー）。**worktree を削除・prune する前に必ず CWD をメインリポジトリに移動すること。`git -C` での代用は禁止**（CWD 自体を移すこと）。

## セッション開始時の健全性チェック

worktree を使う前に孤立参照を点検する:

```bash
git worktree list           # 存在しないパスが出ていないか
git worktree prune          # 孤立参照を削除
git branch --list 'worktree-*'   # 対応 worktree の無いブランチを確認
ls .claude/worktrees/ 2>/dev/null  # 登録外の孤立ディレクトリを確認
```

異常時の復旧:
1. `git worktree prune` で孤立参照削除
2. `.claude/worktrees/` 内の孤立ディレクトリを削除（登録済みなら `git worktree remove --force <パス>`、登録外の残存ディレクトリは `rm -r <パス>`）。**`rm -rf` は安全 hook (validate-bash.sh) と deny 設定がブロックするため使わない**
3. 対応 worktree の無い `worktree-*` ブランチを `git branch -D`
4. `git worktree list` が main のみになることを確認

## worktree マージ・クリーンアップ手順（必須順序）

```bash
# Step 1: CWD をメインリポジトリへ（必ず最初／単独の Bash 呼び出し）
#   ⚠️ git -C で代用しない。CWD 自体を移動する。
cd /path/to/main-repo

# Step 2: マージで入ってくるファイルと同じパスの未追跡ファイルが main にあれば、中身を確かめて退避・削除する
#   ⚠️ rm -rf は安全 hook (validate-bash.sh) がブロックする。-f を付けず rm -r を使う。
git status --short

# Step 3: マージ（CWD 変更後の別コマンドとして実行）
git merge <ブランチ名> --no-ff -m "Merge branch '<ブランチ名>'"

# Step 4: クリーンアップ（CWD がメインリポジトリであることを確認のうえ）
git worktree remove .claude/worktrees/<名前>   # または git worktree prune
git branch -d <ブランチ名>                       # 未 push は -D
```

### クリーンアップ完了の検証（1つでも残れば未完了）

```bash
git worktree list            # → main のみ
git branch --list 'worktree-*'   # → 空
ls .claude/worktrees/ 2>/dev/null  # → 空またはディレクトリ不在
```

## セッション終了前チェック

自動クリーンアップに**頼らない**。マージ・クリーンアップはセッション中に手動で完了させ、終了時点で CWD がメインリポジトリを指していることを保証する（さもないと再起動が必要な posix_spawn エラーになる）。

```bash
pwd                          # → プロジェクトルート（worktree パスなら即 cd で移動）
git worktree list            # → main のみ
git branch --list 'worktree-*'   # → 空
```

- **CWD が worktree 内**: まず `cd /path/to/main-repo`（最優先）→ 未マージならマージ手順 → 削除 → 全クリーンアップ完了後に終了。
- **未コミット変更を残して中断する場合**: worktree 内で WIP コミット → CWD をメインへ移動 → worktree は**削除しない** → worktree とブランチ名をユーザーに伝え次回継続を案内。

## Agent tool の `isolation: "worktree"` 使用時

エージェント完了後のクリーンアップ時も本ルールが適用される。worktree 内に CWD がある状態で削除コマンドを実行しないこと。

## 避けること

- worktree ディレクトリ内での `git worktree remove` / `git branch -d|-D` 実行
- メインリポジトリに `cd` せずに worktree を削除すること

## CWD が既に壊れている場合

シェルの CWD が削除済みディレクトリを指し通常の Bash コマンドが一切実行できない場合は、**Agent tool（subagent_type=general-purpose）** を使って別プロセスからクリーンアップを実行する。
