# 選手紹介の編集・公開 受入仕様（P0）

> **これは仕様であり、実行済みのテストではない。** P0 の時点でこのシナリオを実行する実装・テストは存在しない。
> P1 で選んだバックエンドの統合テスト、P2 で E2E として実装し、そのときにこの文書の ID と対応付ける。

- 契約: [`player-profile-contract.md`](player-profile-contract.md)
- 架空 fixture: [`fixtures/player-profile-scenarios.json`](fixtures/player-profile-scenarios.json)（`schema_version: 0.1.0`、`synthetic: true`）
- 方針の集約先: 📋 `xv-coach/xv#3`

## 読み方

- `inline code` の ID はすべて fixture の ID。シナリオの入力・期待結果の具体値は fixture 側を正とする
- 各シナリオの **Given** は fixture の `after`（直前の状態）に対応する。`seed` は主フロー開始前の状態
- 「状態を変えない」は、revision・head・Publication・所属・監査記録のいずれも増減・変更しないこと
- 拒否系の各シナリオは、指定した `after` の状態から独立に実行する（拒否は状態を変えないので、順番に依存しない）

## 登場するデータ

| 種類 | ID |
|---|---|
| クラブ | `club-a`（主フロー）、`club-b`（境界確認用） |
| チーム | `team-a1`（`club-a`）、`team-b1`（`club-b`） |
| シーズン | `season-a-2026`、`season-b-2026` |
| 選手 | `player-a1`（公開 ID `pub-a-001`）、`player-b1`（公開 ID `pub-b-001`）。どちらも架空の成人 |
| 所属 | `rm-a1`、`rm-b1` |
| ポジション語彙 | `pos-flanker`、`pos-lock` |
| アクター | `actor-a-editor`、`actor-a-publisher`、`actor-b-editor`、`actor-b-publisher`、`actor-anonymous` |
| revision | `rev-a1-r1`、`rev-a1-r2`（主フローで作成）、`rev-b1-r1`（`seed` で公開済み） |
| 存在しない ID | `player-does-not-exist`、`rm-does-not-exist`、`pos-does-not-exist` |

## A. 主フロー（Club A）

### AC-01 下書き r1 を作成する（`op-01-create-draft-a1-r1`）

- **Given** `seed`（`player-a1` には revision も公開もない。Publication は `none`）
- **When** `actor-a-editor` が `player-a1` に `draft.create` を実行する（所属 `rm-a1`、ポジション `pos-flanker`）
- **Then** `rev-a1-r1`（`number = 1`、`based_on_revision_id = null`）ができ、head は `rev-a1-r1` になる
- **And** Publication は `none` のまま
- **And** 監査記録 `audit-01` が 1 件残る

### AC-02 r1 をプレビューする（`op-02-preview-a1-r1`）

- **Given** `op-01-create-draft-a1-r1` の後
- **When** `actor-a-publisher` が `rev-a1-r1` を `preview` する
- **Then** 出力は `exp-preview-a1-r1` と一致する
- **And** キャッシュは非公開（共有キャッシュ・CDN に保存しない）

### AC-03 公開前は公開読取に出ない（`op-03-public-read-before-publish`）

- **Given** `op-02-preview-a1-r1` の後（プレビュー済みだが未公開）
- **When** `actor-anonymous` が `club-a` の公開サイトで一覧と `pub-a-001` の詳細を読む
- **Then** 一覧は `exp-public-list-a-empty`、詳細は `exp-public-detail-not-found`
- **And** プレビューの内容は公開キャッシュに入っていない

### AC-04 r1 を公開する（`op-04-publish-a1-r1`）

- **Given** `op-03-public-read-before-publish` の後
- **When** `actor-a-publisher` が `rev-a1-r1` を `expected_current_revision_id = null` で `publish` する
- **Then** Publication は `published`、`current_revision_id = rev-a1-r1`
- **And** `club-a` + `pub-a-001` の詳細と `club-a` の一覧の入口が失効対象になる
- **And** 監査記録 `audit-02`（`previous_revision_id = null`）が Publication の更新と同じ整合性境界で残る

### AC-05 anonymous に r1 が見える（`op-05-public-read-r1`）

- **Given** `op-04-publish-a1-r1` の後
- **When** `actor-anonymous` が `club-a` の公開サイトで一覧と `pub-a-001` の詳細を読む
- **Then** 一覧は `exp-public-list-a-r1`、詳細は `exp-public-detail-a1-r1`
- **And** 公開キャッシュの識別に `club-a` と `rev-a1-r1` が含まれる

### AC-06 次版 r2 を編集する（`op-06-update-draft-a1-r2`）

- **Given** `op-05-public-read-r1` の後
- **When** `actor-a-editor` が `expected_head_revision_id = rev-a1-r1` で `draft.update` を実行する（ポジションに `pos-lock` を追加）
- **Then** `rev-a1-r2`（`number = 2`、`based_on_revision_id = rev-a1-r1`）ができ、head は `rev-a1-r2` になる
- **And** `rev-a1-r1` の内容は変わらない
- **And** Publication は `published`、`current_revision_id = rev-a1-r1` のまま
- **And** 監査記録 `audit-03` が残る

### AC-07 r2 編集中も anonymous には r1 だけが見える（`op-07-public-read-during-r2`）

- **Given** `op-06-update-draft-a1-r2` の後
- **When** `actor-anonymous` が `club-a` の公開サイトで一覧と `pub-a-001` の詳細を読む
- **Then** 一覧は `exp-public-list-a-r1`、詳細は `exp-public-detail-a1-r1`
- **And** `rev-a1-r2` の内容（`pos-lock`、r2 の紹介文）はどこにも含まれない

### AC-08 r2 をプレビューする（`op-08-preview-a1-r2`）

- **Given** `op-07-public-read-during-r2` の後
- **When** `actor-a-publisher` が `rev-a1-r2` を `preview` する
- **Then** 出力は `exp-preview-a1-r2` と一致し、非公開キャッシュになる
- **And** 公開読取は引き続き `exp-public-detail-a1-r1` を返す

### AC-09 r2 を再公開する（`op-09-republish-a1-r2`）

- **Given** `op-08-preview-a1-r2` の後
- **When** `actor-a-publisher` が `rev-a1-r2` を `expected_current_revision_id = rev-a1-r1` で `publish` する
- **Then** Publication は `published`、`current_revision_id = rev-a1-r2`
- **And** 公開読取は一覧 `exp-public-list-a-r2`、詳細 `exp-public-detail-a1-r2` を返す
- **And** `club-a` + `pub-a-001` の詳細と `club-a` の一覧の入口が失効対象になる
- **And** 監査記録 `audit-04`（`previous_revision_id = rev-a1-r1`）が残る

### AC-10 公開停止する（失効成功）（`op-10-unpublish-a1`）

- **Given** `op-09-republish-a1-r2` の後、配信キャッシュの失効が成功する環境
- **When** `actor-a-publisher` が `player-a1` を `expected_current_revision_id = rev-a1-r2` で `unpublish` する
- **Then** origin の公開読取は直ちに一覧 `exp-public-list-a-empty`、詳細 `exp-public-detail-not-found` を返す
- **And** 配信キャッシュ（CDN・共有キャッシュ）の失効を確認した後に、Publication は `unpublished`（`last_published_revision_id = rev-a1-r2`）になり、結果は `ok`
- **And** `rev-a1-r1` と `rev-a1-r2` は削除・変更されない
- **And** 監査記録 `audit-05`（`invalidation = confirmed`）が残る

### AC-11 公開停止する（失効失敗）（`op-11-unpublish-a1-invalidation-fails`）

AC-10 の代わりに、`op-09-republish-a1-r2` の後から分岐するシナリオ。

- **Given** `op-09-republish-a1-r2` の後、配信キャッシュの失効が失敗する環境
- **When** `actor-a-publisher` が `player-a1` を `expected_current_revision_id = rev-a1-r2` で `unpublish` する
- **Then** origin の公開読取は一覧 `exp-public-list-a-empty`、詳細 `exp-public-detail-not-found` を返す
- **And** 結果は `invalidation_pending` で、Publication は `unpublish_pending` のまま。**公開停止完了として扱わない**（`unpublished_at` は入らない）
- **And** 失効は再試行が必要な状態として残る
- **And** 監査記録 `audit-06`（`invalidation = failed`）が残る

## B. 拒否系

すべて、期待するエラーを返し、状態を変えない（`no_state_change`）。

### 未認証

- **AC-20**（`rej-01-anonymous-draft-create`）
  **Given** `seed` **When** `actor-anonymous` が `player-a1` に `draft.create` を実行する **Then** `UNAUTHENTICATED`
- **AC-21**（`rej-02-anonymous-preview`）
  **Given** `op-01-create-draft-a1-r1` の後 **When** `actor-anonymous` が `rev-a1-r1` を `preview` する **Then** `UNAUTHENTICATED`。下書きの内容は返らない

### 他クラブ（Club B から Club A の ID）

- **AC-22**（`rej-03-b-editor-preview-a`）
  **Given** `op-01-create-draft-a1-r1` の後 **When** `actor-b-editor` が `rev-a1-r1` を `preview` する **Then** `NOT_FOUND`（内部理由 `CROSS_CLUB`）。存在しない ID と区別できない
- **AC-23**（`rej-04-b-editor-update-a-draft`）
  **Given** `op-01-create-draft-a1-r1` の後 **When** `actor-b-editor` が入力に `club_id = club-a` を含めて `player-a1` に `draft.update` を実行する **Then** `NOT_FOUND`（内部理由 `CROSS_CLUB`）。入力の `club_id` は club 文脈に使われない（認証主体のクラブ `club-b` で解決する）
- **AC-24**（`rej-05-b-editor-publish-a`）
  **Given** `op-01-create-draft-a1-r1` の後 **When** `actor-b-editor` が `rev-a1-r1` を `publish` する **Then** `FORBIDDEN`（ロールの判定が先なので、対象の有無は分からない）
- **AC-25**（`rej-06-b-publisher-publish-a`）
  **Given** `op-01-create-draft-a1-r1` の後 **When** `actor-b-publisher` が `rev-a1-r1` を `publish` する **Then** `NOT_FOUND`（内部理由 `CROSS_CLUB`）
- **AC-26**（`rej-09-membership-other-club-team`）
  **Given** `seed` **When** `actor-a-editor` が `player-a1` の所属を `team-b1`（他クラブの Team）と `season-a-2026` で `roster_membership.create` する **Then** `INVALID_INPUT`（`team_id: reference_not_found`）
- **AC-27**（`rej-17-public-read-cross-club`）
  **Given** `seed`（`player-b1` は `rev-b1-r1` で公開済み） **When** `actor-anonymous` が `club-a` の公開サイトで一覧と `pub-b-001` の詳細を読む **Then** 一覧は `exp-public-list-a-empty`、詳細は `exp-public-detail-not-found`
  **And** `club-b` の公開サイトの一覧は `exp-public-list-b-r1` のまま

### ロール不足（editor による公開・停止）

- **AC-28**（`rej-07-a-editor-publish`）
  **Given** `op-02-preview-a1-r1` の後 **When** `actor-a-editor` が `rev-a1-r1` を `publish` する **Then** `FORBIDDEN`
- **AC-29**（`rej-08-a-editor-unpublish`）
  **Given** `op-05-public-read-r1` の後 **When** `actor-a-editor` が `player-a1` を `unpublish` する **Then** `FORBIDDEN`。公開中の `rev-a1-r1` は見え続ける

### 参照不正・入力不正

- **AC-30**（`rej-10-membership-reversed-period`）
  **Given** `seed` **When** `actor-a-editor` が `starts_on = 2026-09-01`、`ends_on = 2026-04-01` の所属を登録する **Then** `INVALID_INPUT`（`ends_on: before_starts_on`）
- **AC-31**（`rej-11-draft-nonexistent-refs`）
  **Given** `op-01-create-draft-a1-r1` の後 **When** `actor-a-editor` が所属 `rm-does-not-exist`、ポジション `pos-does-not-exist` で `draft.update` を実行する **Then** `INVALID_INPUT`（両フィールドとも `reference_not_found`）
- **AC-32**（`rej-12-draft-nonexistent-player`）
  **Given** `seed` **When** `actor-a-editor` が `player-does-not-exist` に `draft.create` を実行する **Then** `NOT_FOUND`
- **AC-33**（`rej-13-draft-private-and-invalid-fields`）
  **Given** `seed` **When** `actor-a-editor` が空の `display_name` と、紹介フィールドにない `birthday`・`contact_email` を含めて `draft.create` を実行する **Then** `INVALID_INPUT`（`display_name: required`、`birthday`・`contact_email: unknown_field`）。非公開フィールドは revision に入らない

### revision 競合

- **AC-34**（`rej-14-draft-update-stale-head`）
  **Given** `op-06-update-draft-a1-r2` の後（head は `rev-a1-r2`） **When** `actor-a-editor` が `expected_head_revision_id = rev-a1-r1` で `draft.update` を実行する **Then** `REVISION_CONFLICT`（現在の head `rev-a1-r2` を返す）
- **AC-35**（`rej-15-publish-stale-expected`）
  **Given** `op-06-update-draft-a1-r2` の後（公開中は `rev-a1-r1`） **When** `actor-a-publisher` が `rev-a1-r2` を `expected_current_revision_id = null` で `publish` する **Then** `REVISION_CONFLICT`（現在の公開 `rev-a1-r1` を返す）。公開中の版は `rev-a1-r1` のまま
- **AC-36**（`rej-16-publish-non-head`）
  **Given** `op-06-update-draft-a1-r2` の後 **When** `actor-a-publisher` が head でない `rev-a1-r1` を `publish` する **Then** `REVISION_CONFLICT`（現在の head `rev-a1-r2` を返す）

## C. 横断条件（すべてのシナリオで成り立つこと）

- **AC-40 公開 DTO の許可リスト:** すべての公開読取とプレビューの出力（`exp-` で始まる fixture）に、`public_dto.forbidden_fields` のフィールド（内部 ID、`club_id`、`birthday`、`contact_email`、`internal_note`、`consent_evidence_ref`、`roles`、`actor_id`、`height`、`weight`、`photo`）が**どの階層にも含まれない**。含まれるのは `public_dto.allowed_fields` だけ
- **AC-41 下書き・プレビューは公開読取に出ない:** `published` の `current_revision_id` 以外の revision（AC-03 の `rev-a1-r1`、AC-07 の `rev-a1-r2`）の内容は、公開一覧・公開詳細・公開キャッシュのどこにも出ない
- **AC-42 プレビューは非公開キャッシュ:** `exp-preview-a1-r1`・`exp-preview-a1-r2` は共有キャッシュ・CDN に保存されない
- **AC-43 公開キャッシュの識別:** 公開読取の出力のキャッシュ識別にはクラブと（公開中の版がある場合は）revision が含まれる（fixture の `cache.key_components`）。`club-a` と `club-b` のキャッシュは混ざらない
- **AC-44 監査と公開参照の一体性:** `audit-02`・`audit-04`・`audit-05`・`audit-06` は、対応する Publication の更新と同じ整合性境界で作られる。どちらか一方だけが残る状態はない。拒否系では監査記録は増えない
- **AC-45 論理削除は代替にならない:** 公開停止は revision や選手の論理削除（`deleted_at`）で表さない。AC-10 / AC-11 の後も `rev-a1-r1`・`rev-a1-r2` は読める（管理側から）

## D. 未カバー（P0 では扱わない）

画像・写真、未成年の選手、`unpublished` からの再公開、`unpublish_pending` 中の公開、失効の再試行そのものの手順、一覧のページネーション、同時に 2 人が編集する場合の UI 上の扱い。いずれも [`player-profile-contract.md`](player-profile-contract.md) §8 の未決事項として 📋 `xv-coach/xv#3` に集約する。
