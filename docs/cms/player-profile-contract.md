# 選手紹介の編集・公開契約（P0）

> **位置付け:** 📋 `xv-coach/xv#3` の「最初の小さな PR」で定める、選手紹介 1 フローの**言語・HTTP 方式に依存しない**最小契約。
> URL、HTTP メソッド、GraphQL SDL、特定言語の型、DB のテーブル形式は決めない（→ [ADR 0001](../adr/0001-backend-and-api-evaluation.md)、Status: Proposed）。
> 具体例は [`fixtures/player-profile-scenarios.json`](fixtures/player-profile-scenarios.json)、受入仕様は [`player-profile-acceptance.md`](player-profile-acceptance.md)。

この文書で「〜する」と書いたものは P0 の契約。「未決」と書いたものは G1（slice 合意）で 📋 `xv-coach/xv#3` に集約して決める。

## 1. 利用シーン

架空クラブの editor が選手紹介の下書きを作り、publisher がプレビューして公開する。認証不要のクラブ公開サイトは、公開済みの紹介だけを読む。管理側と公開側は別の利用者・別のキャッシュ方針として扱う。

## 2. データ契約

フィールドの型は「文字列」「日付」「日時」「ID」などの意味だけを示す。長さ・文字種・ID 形式は実装時に決める。

### 2.1 Club（テナント）

| フィールド | 意味 |
|---|---|
| `id` | テナント ID。すべてのクラブ所有データはこの ID に属する |
| `name` | クラブ名（公開 DTO には含めない。公開サイト側の設定で扱う） |

- クラブをまたぐ参照は作らない。初期はクラブ間で個人 ID（Player）を共通化しない

### 2.2 Team

| フィールド | 意味 |
|---|---|
| `id` | チーム ID |
| `club_id` | 所属クラブ。Team は 1 つの Club にだけ属する |
| `name` | 表示名 |

### 2.3 Season

| フィールド | 意味 |
|---|---|
| `id` | シーズン ID |
| `club_id` | 所属クラブ（P0 ではクラブごとに持つ。共通カレンダーにするかは未決） |
| `label` | 表示ラベル（例: `2026`） |
| `starts_on` / `ends_on` | 期間（日付）。`starts_on <= ends_on` |

### 2.4 Player

| フィールド | 意味 | 公開 |
|---|---|---|
| `id` | クラブ内で安定した内部 ID | 出さない |
| `club_id` | 所属クラブ | 出さない |
| `public_id` | 公開用の安定 ID。クラブ内で一意 | 出す |
| `is_adult` | 成人か。P0 は成人のみを対象にする | 出さない |
| `private.birthday` | 誕生日 | 出さない |
| `private.contact_email` | 連絡先 | 出さない |
| `private.internal_note` | 内部メモ | 出さない |
| `private.consent_evidence_ref` | 掲載許可の証跡への参照 | 出さない |

- 非公開フィールドは ProfileRevision に入れない。紹介の編集操作でも受け付けない（`unknown_field`）
- 未成年（`is_adult = false`）の選手紹介は P0 の対象外。掲載許可・閲覧権限・停止運用は P5 で設計する

### 2.5 RosterMembership（所属）

| フィールド | 意味 |
|---|---|
| `id` | 所属 ID |
| `club_id` | 所属クラブ |
| `player_id` / `team_id` / `season_id` | すべて `club_id` と同じクラブに属すること |
| `starts_on` | 開始日 |
| `ends_on` | 終了日。`null` は継続中。値があれば `starts_on <= ends_on` |

- 他クラブの Team / Season / Player を指す入力は `INVALID_INPUT`（`reference_not_found`）。存在しない ID と区別しない
- 所属の重複・期間の重なりの扱いは未決（P0 の fixture では 1 選手 1 所属）

### 2.6 ProfileRevision（紹介の版）

| フィールド | 意味 |
|---|---|
| `id` | revision ID。作成後に変わらない |
| `club_id` / `player_id` | 対象の選手とそのクラブ |
| `number` | 選手ごとの連番（1, 2, …） |
| `based_on_revision_id` | 直前の head revision。最初の版は `null` |
| `created_by` / `created_at` | 作成者と作成日時 |
| `fields.display_name` | 表示名（必須、空文字不可） |
| `fields.roster_membership_id` | 表示するチーム・シーズンの元になる所属（同じ選手・同じクラブのもの） |
| `fields.position_ids` | ポジション語彙の ID（1 件以上） |
| `fields.bio` | 紹介文 |

- **revision は変更不能（immutable）**。保存済み revision の `fields` は書き換えない。下書きの「更新」は、新しい revision を作って選手の head を進める操作とする
- 選手ごとに **head revision**（最新の revision）を 1 つ持つ
- revision の削除は P0 の操作に含めない。論理削除（`deleted_at`）を revision や公開停止の代わりに使わない

### 2.7 Publication（公開状態）

選手 1 名につき 1 件。revision とは別に持ち、下書きの作成・更新では変わらない。

| フィールド | 意味 |
|---|---|
| `club_id` / `player_id` | 対象 |
| `status` | `none` / `published` / `unpublish_pending` / `unpublished` |
| `current_revision_id` | 公開中の revision。`published` のときだけ値を持つ |
| `last_published_revision_id` | 公開停止前に公開していた revision（停止後の参照用） |
| `published_at` / `unpublished_at` | 最後に公開した日時 / 公開停止が完了した日時 |

状態遷移:

```text
none ──publish──▶ published ──publish(次の head)──▶ published
                     │
                     └─unpublish──▶ unpublish_pending ──配信キャッシュ失効の確認──▶ unpublished
                                     （失効の確認までは完了扱いにしない）

unpublished ──publish──▶ published   （P0 の fixture には含めない。可否は未決）
```

- 公開読取（origin）は `status = published` のときだけ `current_revision_id` の内容を返す。`unpublish_pending` は origin では即座に非公開として扱う
- `unpublish_pending` 中の `publish` を許すかは未決（P0 の fixture には含めない）

### 2.8 公開 DTO（許可リスト）

公開読取とプレビューは同じ形の DTO を返す。**許可リストにないフィールドは出さない**（拒否リスト方式にしない）。

| 許可するフィールド | 元データ |
|---|---|
| `public_id` | Player.public_id |
| `display_name` | revision.fields.display_name |
| `team` | revision.fields.roster_membership_id → Team の表示名 |
| `season` | 同 → Season の表示ラベル |
| `positions` | revision.fields.position_ids → 語彙の表示名 |
| `bio` | revision.fields.bio（一覧では省略する） |
| `revision_id` | 表示している revision |

明示的に出さないフィールド（fixture の `public_dto.forbidden_fields`）: 内部 ID（`id`）、`club_id`、`birthday`、`contact_email`、`internal_note`、`consent_evidence_ref`、ロール・権限・操作者などの認証情報（`roles`、`actor_id`）、`height`、`weight`、`photo`。

- 身長・体重・写真は最初の slice では出さない。追加するときに公開範囲を判断し、この許可リストを更新する
- 許可リストの変更は公開契約の変更として扱う（→ [ADR 0001](../adr/0001-backend-and-api-evaluation.md) の契約バージョニング）

### 2.9 監査記録（AuditRecord）

成功した状態変更（下書き作成・更新、公開、公開停止）ごとに 1 件。

| フィールド | 意味 |
|---|---|
| `actor_id` | 誰が |
| `club_id` | どのクラブで |
| `operation` | 何を（`draft.create` など） |
| `player_id` / `revision_id` | どの選手・どの revision に |
| `previous_revision_id` | 公開で置き換えた revision（公開のみ） |
| `invalidation` | 配信キャッシュ失効の結果（公開停止のみ: `confirmed` / `failed`） |
| `at` | いつ |

## 3. ロールと club 文脈

| ロール | できること |
|---|---|
| `editor` | 自クラブの下書き作成・更新、所属の登録、プレビュー |
| `publisher` | 自クラブのプレビュー、公開、公開停止 |
| `anonymous` | 公開版の一覧・詳細の読取だけ |

- P0 では 1 アクターが 1 クラブに属する。複数クラブ所属・ロールの兼任は未決
- **管理操作の club 文脈は、認証主体と所属権限から決める。** リクエストに含まれる club ID は信用せず、認可にもデータの絞り込みにも使わない（fixture `rej-04-b-editor-update-a-draft` の `club_id` は無視される）
- 対象（選手・revision）は、認証主体のクラブの中だけで解決する。他クラブの対象は「存在しない」と同じ結果になる
- **公開読取の club 文脈は、公開サイトの設定（ドメインなど）から決める。** 公開読取は club ID と公開状態（`published`）の両方で絞る

## 4. 操作

すべての操作は、成功すると「出力」を、失敗すると §5 のエラーを 1 つ返す。失敗した操作は状態を変えず、監査記録も作らない。

| 操作 | 実行できるロール | 必須入力 | 成功時の出力 | 状態の変化 |
|---|---|---|---|---|
| `draft.create` | editor | `player_id`、`fields` | 作成した revision（`number = 1`） | head を作る。Publication は変えない |
| `draft.update` | editor | `player_id`、`expected_head_revision_id`、`fields` | 作成した revision（`based_on_revision_id` = 元の head） | head を進める。既存 revision と Publication は変えない |
| `roster_membership.create` | editor | `player_id`、`team_id`、`season_id`、`starts_on`、`ends_on` | 作成した所属 | 所属を追加 |
| `preview` | editor、publisher | `revision_id` | 公開 DTO と同じ形の出力。非公開キャッシュ | なし |
| `publish` | publisher | `revision_id`、`expected_current_revision_id` | 更新後の Publication | `published` にし `current_revision_id` を置き換える |
| `unpublish` | publisher | `player_id`、`expected_current_revision_id` | 更新後の Publication と失効結果 | `unpublish_pending` → 失効確認後 `unpublished` |
| `public.list` | anonymous（誰でも） | なし（club は公開サイト設定から） | 公開中の選手の公開 DTO の一覧（`bio` を除く） | なし |
| `public.detail` | anonymous（誰でも） | `public_id` | 公開 DTO 1 件 | なし |

fixture では一覧と詳細の確認をまとめて `public.list_and_detail` と書く。

- `draft.create` は、head がすでにある選手には `REVISION_CONFLICT`
- `publish` は **head revision だけ**を公開できる。head でない revision（古い revision）の公開は `REVISION_CONFLICT`。過去版への巻き戻しは P0 の対象外
- 一覧の並び順・ページネーションは未決（G3 で API 方式と併せて決める）

### 4.1 競合検査（expected revision）

- `draft.update` は `expected_head_revision_id` が現在の head と一致するときだけ成功する
- `publish` / `unpublish` は `expected_current_revision_id` が現在の `current_revision_id`（未公開なら `null`）と一致するときだけ成功する
- 不一致は `REVISION_CONFLICT`。エラーに現在値（`current_head_revision_id` / `current_revision_id`）を含め、呼び出し側が再読込できるようにする

### 4.2 整合性境界

- `publish` / `unpublish` は「競合検査 → Publication の更新 → 監査記録の追加」を **1 つの整合性境界**（一括で成功するか、何も残らないか）で行う。監査記録だけ・公開参照だけが残る状態を作らない
- `draft.create` / `draft.update` も「head 検査 → revision 追加 → head 更新 → 監査記録」を同じ境界で行う
- 実現手段（DB トランザクション、条件付き更新など）は未決（G2 の比較項目）

## 5. エラーの意味

| エラー | 意味 | 例（fixture） |
|---|---|---|
| `UNAUTHENTICATED` | 認証が必要な操作を未認証で呼んだ | `rej-01-anonymous-draft-create`、`rej-02-anonymous-preview` |
| `FORBIDDEN` | 認証済みだが、その操作のロールを持たない | `rej-05-b-editor-publish-a`、`rej-07-a-editor-publish`、`rej-08-a-editor-unpublish` |
| `NOT_FOUND` | 操作の対象が自クラブの中に見つからない。**他クラブの対象（内部理由 `CROSS_CLUB`）も外部には同じ結果を返す** | `rej-03-b-editor-preview-a`、`rej-04-b-editor-update-a-draft`、`rej-06-b-publisher-publish-a`、`rej-12-draft-nonexistent-player` |
| `INVALID_INPUT` | 入力の形・値・参照が不正。フィールドごとの理由（`required`、`unknown_field`、`reference_not_found`、`before_starts_on`）を返す | `rej-09-membership-other-club-team`、`rej-10-membership-reversed-period`、`rej-11-draft-nonexistent-refs`、`rej-13-draft-private-and-invalid-fields` |
| `REVISION_CONFLICT` | expected revision の不一致、または head でない revision の公開 | `rej-14-draft-update-stale-head`、`rej-15-publish-stale-expected`、`rej-16-publish-non-head` |

判定の順序: `UNAUTHENTICATED` → `FORBIDDEN`（ロール） → `NOT_FOUND`（対象の解決） → `INVALID_INPUT` → `REVISION_CONFLICT`。ロールを先に見るので、権限のない利用者には対象の有無が分からない。

- 他クラブ参照は内部ではログ・監視用に `CROSS_CLUB` として区別してよいが、応答で区別しない（存在の有無を漏らさない）
- 拒否した要求を監査記録とは別のセキュリティログに残すかは未決

`invalidation_pending` はエラーではなく、`unpublish` の「未完了」結果（§6.3）。

## 6. キャッシュと配信

### 6.1 プレビュー

- 認証必須（未認証は `UNAUTHENTICATED`）。対象は自クラブの revision だけ
- 応答は**非公開キャッシュ**（共有キャッシュ・CDN に保存しない。fixture の `cache.scope = private`、`store = false`）
- プレビューの内容・URL・識別子を公開読取のキャッシュキーや公開一覧に混ぜない

### 6.2 公開キャッシュの識別

- 公開キャッシュの識別には**クラブと revision を含める**（fixture の `cache.key_components`）。キー文字列の形式は決めない
- revision に結び付いた内容（`club + public_id + revision_id`）は revision が immutable なので変わらない
- 「いま公開中の版」を返す入口（`club + public_id` の詳細、`club` の一覧）は公開状態に依存する。公開・再公開・公開停止のたびに、その入口を失効させる（fixture の `invalidate`）

### 6.3 公開停止と失効

公開停止の完了条件は、origin の読取だけでなく**配信済みキャッシュ（CDN・共有キャッシュ）を含めて**公開版が返らなくなったことを確認できること。

1. 整合性境界の中で Publication を `unpublish_pending` にし、監査記録を残す。この時点で origin の公開読取は `NOT_FOUND` を返す
2. 対象の入口（`club + public_id`、`club` の一覧）と、公開していた revision の内容を配信キャッシュから失効させる
3. 失効を確認できたら `unpublished` にし、`unpublish` は `ok` を返す（`op-10-unpublish-a1`）
4. 失効に失敗・タイムアウトしたら `unpublish_pending` のままにし、`invalidation_pending` を返す。**「公開停止完了」と扱わない。** 失効は再試行が必要な状態として残し、監査記録に `invalidation: failed` を残す（`op-11-unpublish-a1-invalidation-fails`）

- 再試行の方式（キュー、定期処理、手動操作）、失効の上限時間、利用者への通知方法は未決
- 公開・再公開の失効失敗は、古い公開版がしばらく見える問題であり、非公開情報の漏えいとは重さが違う。P0 では公開停止の失効だけを完了条件に含める

## 7. P0 の対象外

ニュース、試合イベント・集計、課金、ドメイン設定、テーマ、画像アップロード・写真、実データ移行、未成年プロフィールの本番対応、過去版への巻き戻し、revision の削除、複数クラブ所属のアクター、一覧のページネーション。

## 8. 未決事項（G1 で確認）

1. Season をクラブごとに持つか、共通カレンダーにするか（P0 はクラブごと）
2. ポジション語彙をクラブ共通にするか、クラブごとに持つか（P0 は共通の参照語彙）
3. 他クラブ参照を外部に `NOT_FOUND` として返す方針でよいか
4. 拒否した要求をセキュリティログに残すか、その保存期間
5. `unpublished` からの再公開、`unpublish_pending` 中の公開の可否
6. 公開停止の失効の再試行方式と上限時間
7. 所属の重複・期間の重なりの扱い
8. 下書きの保存ごとに revision を作る方式で、revision 数が増えすぎないか（自動保存の扱い）
