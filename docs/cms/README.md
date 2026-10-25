# CMS 設計文書（選手紹介の編集・公開スライス）

このディレクトリは、📋 `xv-coach/xv#3`（今後の方向性検討：ラグビー特化ヘッドレス CMS 基盤としての xv）の「実装担当向けの入口（2026-10-04 追記）」にある **P0（最初の小さな PR）** の成果物を置く場所。
議論・判断の集約先は引き続き 📋 `xv-coach/xv#3` とし、この文書群は判断材料として扱う。

> この文書群は**言語・HTTP 方式に依存しない契約と架空データ**だけを定める。バックエンド言語、REST / GraphQL、DB 形式、既存 CMS の採用、全面書き換えのいずれも決めていない（→ [ADR 0001](../adr/0001-backend-and-api-evaluation.md)、Status: Proposed）。

## 読む順番

1. この README（範囲・旧モデルとの対応）
2. [`player-profile-contract.md`](player-profile-contract.md) — 最小データ契約、公開 DTO の許可リスト、ロール、操作、エラー、キャッシュ
3. [`player-profile-acceptance.md`](player-profile-acceptance.md) — fixture ID を参照する Given / When / Then の受入**仕様**（実行済みテストではない）
4. [`fixtures/player-profile-scenarios.json`](fixtures/player-profile-scenarios.json) — 架空の正常系・拒否系入力と期待公開出力（`synthetic: true`）
5. [`../adr/0001-backend-and-api-evaluation.md`](../adr/0001-backend-and-api-evaluation.md) — バックエンド・API 方式の比較方法と判断ゲート（Proposed）

## 固定した確認基準

- **確認基準: `master` の `2078a577cf81b9bcd3caa70643e6577c25cf451d`**（2026-10-25 20:47 JST、🔀 [xv-coach/xv#5](https://github.com/xv-coach/xv/pull/5)・🔀 [xv-coach/xv#7](https://github.com/xv-coach/xv/pull/7)・🔀 [xv-coach/xv#6](https://github.com/xv-coach/xv/pull/6) のマージ後）
- 📋 `xv-coach/xv#3` の追記時点の基準は `8bb7f1cc4b68ef4a3ea1dd4be46a83e0447a45e8`（2019-08-10）。Issue の指示（「着手時に HEAD が変わっていたら、差分を読み直してから更新する」）に従い、差分を読み直して下の対応表を現在の基準で書いた
- 以下のリンクはすべて基準 commit に固定している。HEAD が進んだら、差分を読み直してから基準と対応表を更新する

## 今回の範囲

**利用シーン:** 架空クラブの editor が選手紹介を編集し、publisher がプレビューして公開し、認証不要のクラブ公開サイトが公開済みの紹介だけを読む。

- 範囲: 選手紹介 1 フロー（下書き作成・更新 → プレビュー → 公開 → 次版編集 → 再公開 / 公開停止、公開一覧・詳細）の契約、受入仕様、架空 fixture、バックエンド・API 評価の ADR（Proposed）
- 変更しないもの: 既存ソース（`src/`）、migration、Docker、依存 lock、CI。新しい実行基盤や汎用 CMS 抽象層も作らない
- 対象外: ニュース、試合イベント・集計、課金、ドメイン設定、テーマ市場、実データ移行、画像アップロード、未成年プロフィールの本番対応

### リポジトリの分担（オーナーの方針）

- 将来、**エンドユーザー向けの公開サイト（ReScript を優先）だけを別リポジトリ**に置く。管理画面は本リポジトリに残し、`xv-coach/xv` は**バックエンド**（管理画面・コンテンツ管理・API）を担う
- そのため、この文書群の契約（[`player-profile-contract.md`](player-profile-contract.md)）と公開 DTO の許可リストは、**リポジトリをまたぐ境界**になる。契約のバージョニング、公開サイト側リポジトリでの取り込み・デコード・検証の方法は [ADR 0001](../adr/0001-backend-and-api-evaluation.md) の比較項目に含めた
- fixture の `schema_version` は、両リポジトリが同じ fixture を契約テストに使う場合の版の目印として置いている（取り込み方法は未決）
- 管理画面は、Django を選んだ場合、Django 標準 admin を自前のテンプレート・CSS でデザイン改善して使い、jQuery は使わない。通常のフォームで扱えない画面は ReScript を使うプラグイン（1 プラグイン = 1 Django アプリ）として追加する。Django admin 全体を ReScript で書き直すことは計画しない（→ [ADR 0001](../adr/0001-backend-and-api-evaluation.md) の「管理 UI の方針」。バックエンド言語の採用は未決）

## 旧モデルから新概念への対応

基準: `2078a577cf81b9bcd3caa70643e6577c25cf451d`。**再利用の第一対象は語彙・関係・制約の知識**であり、コードの再利用・移行可否は別途判定する。

| 新しい概念（契約） | 現在の旧モデル | 対応と不足 |
|---|---|---|
| Club（テナント） | なし。[`TeamGroup.is_my_team`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/member/models.py) | `is_my_team` は自チーム識別の真偽値で、認証主体に結び付くテナント認可ではない。クラブ単位のデータ所有・権限は未実装 |
| Team | [`member.Team`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/member/models.py)（`TeamGroup` に属する） | `TeamGroup → Team` の階層は参考になる。クラブ（テナント）への帰属は無い |
| Season | なし | 追加が必要 |
| Player | [`member.Member`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/member/models.py) + [`member.PlayerProfile`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/member/models.py) | 姓名・誕生日・所属 `TeamGroup`（`Member`）、身長・体重・ポジション（`PlayerProfile`）。公開 ID、公開・非公開の区別は無い。`birthday`・`height`・`weight` は P0 の公開 DTO に出さない |
| RosterMembership | `Member.team_group`（1 件の FK、期間なし） | シーズン・期間付きの所属履歴は無い。追加が必要 |
| ProfileRevision | なし（`PlayerProfile` は 1 行を上書き） | 変更不能な版は無い。追加が必要 |
| Publication | なし | 公開状態・公開停止は無い。追加が必要 |
| 監査記録 | なし（`created_at` / `updated_at` のみ） | 誰が・どのクラブで・何をしたかの記録は無い。追加が必要 |
| ポジション語彙 | [`master.PlayerPosition`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/master/models.py)（`number`・`name`・`is_front_row`） | 語彙として参照する。番号・名称の永続的な固定や旧 DB 形式の継承は未決 |
| 役職・試合語彙 | [`master`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/master/models.py) の `StaffPosition`・`ScoringMethod`・`FoulMethod` など | P0 では使わない。P4（試合）で参照する |
| 試合・イベント | [`match`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/match/models.py) の `Match`・`TeamOnMatch`・`PlayerOnMatch`・`Half`・各イベント | P0 では使わない。登録選手と背番号の一意性、イベントの同一試合制約は P4 で再利用候補。`Match.has_been_held()`（開催時刻による判定）は結果確定・公開状態とは分ける |
| 論理削除 | [`common.BaseModel`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/common/models.py) | 版管理・監査・公開停止の代替にしない（契約 §2.6、受入仕様 AC-45） |
| 公開 API / 公開サイト | [`xv_rugby/urls.py`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/xv_rugby/urls.py) は `admin/` のみ | 公開 API・公開サイトは未実装。現ソースを完成済みの実装として扱わない |

### 2019 年の基準からの変化（`8bb7f1cc4b68ef4a3ea1dd4be46a83e0447a45e8` → `2078a577cf81b9bcd3caa70643e6577c25cf451d`）

📋 `xv-coach/xv#3` が「後続で検証する」としていた項目のうち、一部はすでに手が入っている。ただし P0 の契約に必要な境界（テナント、所属履歴、revision、公開状態、監査）はどれもまだ無い。

| 項目 | 2019 年の基準 | 現在の基準 |
|---|---|---|
| 実行環境 | Python 3.7 / Django 2.2 / MySQL 5.7 / Poetry / CircleCI / uWSGI + nginx | Python 3.14 / Django 6.1 / PostgreSQL 18 / uv / GitHub Actions / gunicorn + WhiteNoise（[`pyproject.toml`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/pyproject.toml)、[`containers/django/Dockerfile`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/containers/django/Dockerfile)、[`ci.yml`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/.github/workflows/ci.yml)）。MySQL コンテナは削除済み |
| 秘密情報 | `settings.py` に埋め込み | 環境変数から読む（[`settings.py`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/xv_rugby/settings.py)）。旧キーは漏洩扱いで再利用しない。値はこの文書にも fixture にも転載していない |
| 論理削除 | `QuerySet.delete()` だけが論理削除、インスタンスの `delete()` は物理削除 | インスタンスの `delete()` も論理削除に統一。`hard_delete()`・`is_deleted` を追加（[`common/models.py`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/common/models.py)、[`test_soft_delete.py`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/tests/test_soft_delete.py)）。関連行には連鎖しない。復元操作は無い |
| 一意制約 | `unique_together` | `deleted_at IS NULL` を条件にした部分 `UniqueConstraint`（論理削除した行を除く）。`validate_constraints()` で `deleted_at` を検証から外さない（[`match/models.py`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/match/models.py)、[`test_constraints.py`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/tests/test_constraints.py)） |
| イベントの同一試合制約 | 未検証 | `clean()` で、イベントの選手・ハーフ・関連イベントが同じ試合に属すること、交替の退場・出場選手が別人かつ同じチームであることを検証（[`test_clean.py`](https://github.com/xv-coach/xv/blob/2078a577cf81b9bcd3caa70643e6577c25cf451d/src/tests/test_clean.py)）。DB 制約ではなく `clean()` のため、`clean()` を通らない書き込みには効かない |
| カード | `Enum` から choices を組み立てる独自実装 | `MatchFoulEvent.Card` を `TextChoices` に変更（値 `safe` / `yellow` / `red` は維持） |
| その他 | — | `verbose_name` の整備、pytest + model-bakery のテスト、mypy、ruff、pre-commit、`AGENTS.md` と `.claude/` の作業規約 |

**論理削除は依然として revision・監査・公開停止の代替にならない。** 論理削除は「行を見えなくする」だけで、誰がいつ何を変えたか、どの版を公開していたかを残さず、配信済みキャッシュも失効させない。

### 未検証の範囲

実データの有無・品質、稼働環境、脆弱性の網羅監査は、今回のソース確認では確認していない。この PR ではアプリの起動・テスト実行もしていない（文書のみ）。
