---
description: Red Team（攻撃者視点）と Blue Team（防御者視点）の対立する分析を統合してセキュリティ監査を行う。`/redblue-audit` で起動。「攻撃者視点で見て」「セキュリティ監査して」「Red Team レビューして」リクエスト時、または認証 / 認可 / 暗号 / 入力検証など security 関連モジュールの設計を見直すときに本スキルを案内する。差分の脆弱性検査だけが目的なら公式の `/security-review` を使う。
allowed-tools: Read, Glob, Grep, Bash, Agent
disable-model-invocation: true
effort: xhigh
---

# Red/Blue セキュリティ監査スキル

Red Team（攻撃者視点）と Blue Team（防御者視点）の2つのエージェントを並列実行し、対立する分析を統合したレポートを生成します。

## 公式 `/security-review` との住み分け

| | 公式 `/security-review` | 本スキル `/redblue-audit` |
|---|---|---|
| 対象 | 現在のブランチの差分 | 差分 / コミット範囲 / 任意のファイル |
| 手法 | 単一視点での脆弱性検出 | 攻撃者と防御者の対立分析を統合 |
| 向く場面 | コミット前の定型チェック | 設計の妥当性を問い直したいとき、深掘りしたいとき |
| コスト | 低 | 高（`effort: xhigh` で 2 エージェント並列） |

日常のコミット前チェックは公式 `/security-review` で足りる。本スキルは、認証・認可の設計変更のように「そもそもこの守り方で良いのか」を問いたい場面で使う。

## 使い方

- `/redblue-audit` — 未コミットの変更を監査
- `/redblue-audit HEAD~3..HEAD` — 指定範囲のコミットを監査
- `/redblue-audit src/path/to/File.ext` — 特定ファイルを監査

## 手順

### 1. レビュー対象の特定

引数に応じてレビュー対象を決定する:

- **引数なし**: `git diff --name-only` + `git diff --cached --name-only` で変更ファイルを取得
- **コミット範囲** (例: `HEAD~3..HEAD`): `git diff --name-only <範囲>` で変更ファイルを取得
- **ファイルパス**: 指定されたファイルをそのまま対象とする

設定ファイルやドキュメントも含める（設定ファイルのセキュリティも重要なため）。ただし `.md` ファイルは除外する。

対象ファイルが0件の場合は「レビュー対象のファイルがありません」と報告して終了する。

### 2. 攻撃者視点 / 防御者視点の並列起動

`security-reviewer` エージェントを、異なる役割プロンプトで2つ同時に起動する。片方に攻撃者（Red Team）視点、もう片方に防御者（Blue Team）視点を担わせ、対立する2つの分析を得る:

```
Agent(subagent_type="security-reviewer", prompt="【Red Team = 攻撃者視点】以下のファイルに対して脅威分析を行ってください。悪用可能な脆弱性・攻撃経路を、深刻度付きで洗い出すことに集中してください: <ファイルリスト>")
Agent(subagent_type="security-reviewer", prompt="【Blue Team = 防御者視点】以下のファイルに対して防御評価を行ってください。既存の防御・入力検証・認可制御が十分かを、不足箇所とともに評価することに集中してください: <ファイルリスト>")
```

2 つの分析は互いに独立しているので、同じメッセージ内で並列に呼び出す。どちらも実在の `security-reviewer` エージェントを使い、役割はプロンプトで切り替える。

### 3. Confrontation Matrix の生成

Red Team と Blue Team の結果を突き合わせ、以下の統合分析を行う:

- Red Team が発見した各脅威に対して、Blue Team の防御評価を照合する
- 防御が存在しない脅威（ギャップ）を特定する
- 各ギャップに対する推奨対策と優先度を決定する

### 4. 統合レポートの出力

以下の形式で統合レポートを出力する:

```markdown
## Security Review Report

### レビュー対象
- ファイル一覧

### Threat Analysis (Red Team)

<Red Team エージェントの出力をそのまま掲載>

### Defense Assessment (Blue Team)

<Blue Team エージェントの出力をそのまま掲載>

### Confrontation Matrix

Red Team の脅威と Blue Team の防御を突き合わせた統合分析:

| # | 脅威 (Red Team) | 深刻度 | 現在の防御 (Blue Team) | ギャップ | 推奨対策 | 対応優先度 |
|---|----------------|--------|----------------------|---------|---------|-----------|
| 1 | SQLi の可能性 | High | パラメータ化クエリ使用 | なし | - | - |
| 2 | Zip Slip | High | パス検証なし | あり | Path.GetFullPath で正規化 | Critical |

### Action Items

ギャップが存在する項目を優先度順にリストアップする:

1. **[Critical]** 項目名 — 対象ファイル:行番号 — 推奨対策
2. **[High]** 項目名 — 対象ファイル:行番号 — 推奨対策
3. **[Medium]** ...
4. **[Low]** ...

### Summary

- 分析した脅威の総数
- 防御が確認された脅威の数
- ギャップ（防御なし）の数
- Critical / High / Medium / Low の内訳
```

## 注意事項

- `run_in_background` は使用しない（結果を待って統合レポートを生成する）
- レビュー結果はあくまで静的分析に基づく指摘であり、すべてが実際に悪用可能とは限らない
- False positive の可能性がある場合は、その旨を明記する
