# assert の具体例

`SKILL.md` の「assert の要点」の詳細。例は Vitest の matcher で書く（`toBeTypeOf` は Vitest 固有。Jest では `typeof` の比較で代える）。他のフレームワークでも同じ考え方で対応する matcher を選ぶ。

## 値全体を assert する

```typescript
// NG: 断片的。書き忘れたフィールドが誤っていても通る
expect(result.name).toBe('My Name')
expect(result.status).toBe('ACTIVE')

// OK: 1 つの assert で全体が見え、どのズレでも落ちる
expect(result).toEqual({
  id: expect.stringMatching(/^user-/),
  name: 'My Name',
  status: 'ACTIVE',
  createdAt: '2025-01-02T03:04:05.000Z',
})
```

## 配列

| 状況 | 使うもの |
|---|---|
| 順序が決定的 | `toEqual([...])` |
| 順序が非決定的 | `toHaveLength(n)` + `toEqual(expect.arrayContaining([...]))` |
| 要素の一部フィールドだけ見る | `toEqual([expect.objectContaining({...}), ...])` |
| 空 | `toEqual([])` |

```typescript
// NG: 無関係な行が返っても通る
expect(users.length).toBeGreaterThan(0)
users.forEach((u) => expect(u.email).toContain('alice'))

// NG: filter で絞ると、無関係なエラーが素通りする
expect(body.errors.filter((e) => e.code === 'NOT_FOUND')).toEqual([])

// OK: 期待する内容そのものを固定する
expect(users).toEqual([expect.objectContaining({ email: 'alice@example.com' })])
expect(body.errors).toEqual([
  expect.objectContaining({ code: 'UNAUTHORIZED', message: 'Authentication required' }),
])
```

否定形（`not.toEqual(expect.arrayContaining([...]))`）は、周囲が本当に非決定的で「これが現れない」だけが安定したシグナルのときに使う。否定形は空配列でも形違いでも通るので、先にセットアップを決定的にして全体を assert できないか検討する。

## 文字列と型

文字列は `toBe` で全文を比較し、予測不能な部分だけ `expect.stringMatching(/.../)` か `expect.any(String)` にする。`toContain` の部分一致は前後の誤りを通す。

型の確認は `toBeTypeOf('boolean')` / `toBeInstanceOf(Array)` のような専用 matcher を使うと失敗メッセージが読みやすい。

## 部分一致: `objectContaining` と `toMatchObject`

`expect.objectContaining` は浅く、ネストした階層は再度包まないと完全一致になる。`toMatchObject` は深く部分一致する。どちらでもよく、短さか明示性で選ぶ。

```typescript
expect(result).toMatchObject({ name: 'foo', meta: { code: 'NOT_FOUND' } })
expect(result).toEqual(expect.objectContaining({
  name: 'foo',
  meta: expect.objectContaining({ code: 'NOT_FOUND' }),
}))
```

## クラスインスタンスと `toEqual`

`toEqual` は own かつ列挙可能なプロパティを比較し、prototype は見ない。データを `#private` フィールドや getter で持つクラスは、どの 2 インスタンスも `{}` 同士として等しく見え、誤った値でも通る。その場合はアクセサを assert する（`expect(d.totalMs()).toBe(500)`）か、型だけが問題なら `expect.any(TheClass)` を使う。

## エラー

### HTTP エラー

status だけでなく、Content-Type と body 全体を固定する。status だけだと、同じ status に変換される別のエラーでも通る。エラー形式はプロジェクトの規約（RFC 9457 Problem Details など）に合わせる。

```typescript
const res = await app.request('/api/users/does-not-exist')

expect(res.status).toBe(404)
expect(res.headers.get('content-type')).toContain('application/problem+json')
expect(await res.json()).toEqual({
  type: 'about:blank',
  title: 'Not Found',
  status: 404,
  detail: 'User not found',
  instance: '/api/users/does-not-exist',
  code: 'NotFoundError', // 機械可読なコードを固定する
})
```

body の一部が安定しないときは `toMatchObject` で契約にあたるメンバー（status・コード・detail）を固定する。

### throw されるエラー

```typescript
await expect(loadConfig(path)).rejects.toThrow('Invalid config: port must be a number')
```

エラークラスが export されておらずフィールドを見たいときは、捕捉して構造で比較する。throw されなかった経路は明示的に失敗させる。`try` の中で失敗させると、その失敗自体が `catch` に捕まって的外れな比較になるため、成功側と失敗側を分けて受ける。

```typescript
const caught: unknown = await loadConfig(path).then(
  () => { throw new Error('should have rejected') }, // 成功したらここでテストを落とす
  (e: unknown) => e,                                  // 失敗したらエラーを比較に回す
)
expect(caught).toEqual(expect.objectContaining({
  name: 'ConfigError',
  message: 'Invalid config: port must be a number',
  field: 'port',
}))
```

期待するエラーの形は `expect.objectContaining` で包む。`objectContaining` / `toMatchObject` は prototype の getter と列挙不可の `message` も比較するが、素の `toEqual({...})` は own かつ列挙可能なキーしか見ないため getter を取りこぼす。

Python では `pytest.raises` の `match` が正規表現の部分一致なので、全文を固定するなら捕捉後に比較する。

```python
with pytest.raises(ConfigError) as exc_info:
    load_config(path)
assert str(exc_info.value) == "Invalid config: port must be a number"
assert exc_info.value.field == "port"
```

## ログ

多くのログは実装の詳細なので assert しない。assert するのは、ログ自体が仕様であるとき（秘密や PII が出ないこと、監査イベントが残ること）か、振る舞いの唯一の観測可能な痕跡であるとき。戻り値やエラーで既に証明済みの振る舞いをログでも assert すると、文言変更で落ちるだけになる。

logger は mock せず、本物の logger の出力先を差し替えて実際に書かれた内容を捕捉する。redact やシリアライザは本物の logger の中でしか動かないため、mock では「トークンが出ない」ことを証明したつもりで実際には出ている状態を見逃す。

```typescript
const lines: string[] = []
const logger = createLogger({ level: 'info', destination: { write: (s: string) => lines.push(s) } })

await sendEmail({ to: ['u@example.com'], subject: 'Hi', body: secret }, { logger })

expect(lines.map((l) => JSON.parse(l))).toEqual(expect.arrayContaining([
  expect.objectContaining({ msg: 'Sending email', recipientCount: 1, subject: 'Hi' }),
]))
```

構造化ログは parse してから比較する。安全なフィールドを肯定形で列挙すると、秘密が含まれないことの証明を兼ね、新しいフィールドが漏れ始めれば落ちる。`not.toContain(secret)` のような否定形スキャンを使うときは、空のログで空虚に通らないよう肯定形の assert と組み合わせる。

Python では pytest の `caplog` が標準 logging の実レコードを捕捉する（`caplog.records` の属性を比較する）。

## 時刻を固定する

`Date.now()` を使った動的な比較ではなく、フェイクタイマーで時刻を固定してリテラルと比較する。複数ステップでは「進める」ではなく時刻を明示的に設定すると、期待値がリテラルのまま保てる。

```typescript
beforeEach(() => vi.useFakeTimers({ toFake: ['Date'] }))
afterEach(() => vi.useRealTimers())

vi.setSystemTime(new Date('2025-01-01T00:00:00.000Z'))
const created = await createUser(input)
vi.setSystemTime(new Date('2025-01-01T00:01:00.000Z'))
const updated = await updateUser(created.id, patch)

expect(updated).toMatchObject({
  createdAt: '2025-01-01T00:00:00.000Z',
  updatedAt: '2025-01-01T00:01:00.000Z',
})
```

`Date` 型のフィールドは `toEqual(new Date('...'))` で比較できる（時刻値で比較される）。Python では `freezegun` や `time-machine` で同じことをする。

### フェイクタイマーと I/O

タイマー全体を偽装すると、誰も進めないタイマーを待つ promise が永遠に解決しない。さらに `setTimeout` / `setImmediate` を偽装した状態でマイクロタスクだけを回し続けると、イベントループが I/O フェーズに入らず、DB ドライバのソケット読み取りが止まることがある。選択肢を安い順に並べる。

1. 時刻の固定だけが目的なら `Date` だけを偽装する（上の例）。タイマーは本物なので I/O は止まらない
2. 対象コードが自前のタイマーで待つ（リトライ・バックオフ）なら、全タイマーを偽装したまま「次のタイマーまで進める」非同期 API で進める。1 ステップごとにマクロタスクを経由するので I/O も進み、時刻は決定的なまま
3. 複数の呼び出しを織り交ぜるなら本物のタイマーに戻し、ポーリングではなく完了通知（`Promise.withResolvers()` など）で同期する。タイムスタンプは `expect.any(String)` にする

## 期待値に計算を入れない

期待値の中で関数を呼ぶと、テストが「何を期待するか」ではなく「どう再導出するか」の記述になり、実装と同じ誤りを共有する。

```typescript
// NG
expect(sortedIds).toEqual(getSortedIds(items))
expect(formatted).toBe(formatDate(now))

// OK
expect(sortedIds).toEqual(['id1', 'id2', 'id3'])
expect(formatted).toBe('2025-01-01')
```

採番される ID は作成結果から取る。

```typescript
const created = await createTask(input)
expect(await getTask(created.id)).toEqual({ id: created.id, title: 'Buy milk' })
```

## union 型のリテラルにキャストしない

```typescript
role: 'admin' as UserRole // NG: variant を rename してもキャストが型エラーを黙らせ続ける
role: 'admin'             // OK: union に対して型検査される
```

キャスト無しで通らないなら union 側が変わっているので、値を直す。
