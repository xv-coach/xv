---
description: Bash で破壊的操作（rm -r / rmdir / git worktree remove 等のディレクトリ削除、docker volume rm 等のデータ削除、リダイレクトでのファイル上書き）を実行する直前に参照する。CWD が削除対象内にないかの確認手順と、hook が自動 block する操作の一覧。
allowed-tools: Read, Bash
---

# Bash 安全規約

## ディレクトリ削除時の CWD チェック

ディレクトリを削除（`rmdir`, `rm -r`, `git worktree remove` 等）する前に、**必ず現在の作業ディレクトリ（CWD）が削除対象のディレクトリ内にないことを確認すること**。

### 手順

1. 削除対象のパスを確認する
2. `pwd` で現在の CWD を確認する
3. CWD が削除対象ディレクトリ内（サブディレクトリ含む）の場合、**先に `cd` で別のディレクトリに移動してから**削除を実行する
4. CWD が削除対象外であることを確認してから削除コマンドを実行する

### 理由

CWD が削除されると Bash ツールのシェルプロセスが復旧不能になり、セッション全体でコマンド実行ができなくなる。`cd` を含む全コマンドが `posix_spawn` レベルで失敗するため、シェル内からの復旧は不可能。

### 重要: `git -C` は CWD 移動の代替にならない

`git -C <path>` は git コマンドの実行ディレクトリを指定するだけで、シェルの CWD は変更しない。そのため、`git -C` で worktree remove や prune を実行しても、CWD が削除対象を指していればシェルは壊れる。**必ず `cd` で CWD 自体を移動すること。**

## データを消す操作

- `docker volume rm` / `docker compose down -v`: ボリューム内のデータ（ローカル DB 等）は復元できない。消してよいかを確認してから実行する。コンテナを止めたいだけなら `-v` を付けない
- リダイレクト（`>`）での上書き: 既存ファイルを上書きする前に中身を確認する。追記なら `>>`

## 自動 block されるもの

`.claude/hooks/validate-bash.sh` が次を止める。引用符の外の `&&` / `||` / `;` / `|` / `&` / `( )` / `$( )` / 改行で区切って 1 つずつ見る。各コマンドは環境変数の代入・`sudo` / `command` / `env` / `xargs`・パス（`/bin/rm`）・git のグローバルオプション（`-C <dir>` 等）を外してから判定するため、それらの後ろに書いても止まる。引用符の中（`git commit -m "a; rm -rf b"`）は区切らない。

| 操作 | 代わりに |
|---|---|
| `git add .` / `git add -A` / `--all` / `git add :/` | ファイルを個別に指定して `git add` |
| `git push --force` / `-f` / `-uf` / `+main`（refspec） | rebase 後の出し直しは `--force-with-lease`（remote が動いていたら拒否されるため許可） |
| `rm -rf`（`-Rf` など、フラグの大小・順序・位置を問わない） | 対象を確かめてから `rm -r` |
| CWD が削除対象の中にある `git worktree remove` | 先にメインリポジトリへ `cd` |
| worktree 内での `git branch -d` / `-D` | 先にメインリポジトリへ `cd` |

## プロジェクト固有の危険操作

xv で取り返しのつかない操作、または方針（📋 `xv-coach/xv#3`）に反する操作と、その代わりにすること。hook では止まらないので、実行前に自分で確かめる。

| 操作 | 何が起きるか | 代わりに |
|---|---|---|
| `docker compose down -v` / `docker volume rm` | PostgreSQL のボリューム（ローカル DB）が消える | 止めるだけなら `docker compose down`（`-v` なし）。消す前にユーザーに確認 |
| `uv run python manage.py flush` / `migrate <app> zero` / `sqlflush` の実行 | DB のデータ・スキーマが消える | 対象 DB が使い捨てのローカル環境か確かめ、ユーザーに確認してから |
| 既存マイグレーションファイルの削除・書き換え | 適用済みの環境とスキーマ履歴が食い違う | 新しいマイグレーションを追加する |
| `src/uv.lock` の手編集 | lock と `pyproject.toml` が食い違い、`uv sync --locked` が失敗する | `uv add` / `uv remove` / `uv lock` |
| 旧構成の起動・導入（Python 3.7 / Django 2.2 / MySQL 5.7 / Poetry、旧コンテナ） | 新環境が決まる前に古い依存を持ち込む | 📋 `xv-coach/xv#3` の ADR で実行環境が決まるのを待つ |
| `.env` の読み取り・表示（`cat .env` など） | 秘密情報がログ・会話に残る | `.env.example` / `.env.testing` を見る |
| `git push --force-with-lease` を他人の PR ブランチへ | 他の人・agent の作業を上書きする | 依頼がない限り他人のブランチに push しない |

## 関連

- `worktree-safety` skill: worktree の削除順序・CWD 復旧手順の SSoT
