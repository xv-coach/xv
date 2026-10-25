# Issue / PR の表記

文章中の Issue と PR は、取り違えないよう絵文字と書式の両方で区別する。

| 対象 | 書式 |
|---|---|
| Issue | 📋 + inline code: 📋 `owner/repo#NNN` |
| PR | 🔀 + Markdown リンク: 🔀 [owner/repo#NNN](https://github.com/owner/repo/pull/NNN) |

- Issue の URL が必要なら inline code の後に別途書く
- リポジトリ内の文章は `owner/repo#NNN` 形式にする。ユーザーへの応答などリポジトリ外では `owner/repo` を省略してよい
- 応答・作業報告・調査レポート・計画メモ・docs に適用する
- コミットメッセージ、ブランチ / worktree 名、PR 本文の `Closes` 等のキーワード、コード・設定の識別子、CLI 引数は対象外
