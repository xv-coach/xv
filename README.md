# xv

ラグビー向けの CMS です。

現在のコードは、Django 管理画面（admin）をベースにしたレガシーなプロトタイプです（チーム・メンバー・試合などのマスタ／記録を管理画面で扱う）。今後の方向性（ラグビー特化のヘッドレス CMS 基盤としての xv）は [Issue #3](https://github.com/xv-coach/xv/issues/3) で検討中で、決定は ADR で記録していく予定です。

## 技術スタック

| 項目 | バージョン |
|---|---|
| Python | 3.14 |
| Django | 6.1 |
| PostgreSQL | 18（Docker / CI） |
| パッケージ管理 | [uv](https://docs.astral.sh/uv/) |
| アプリケーションサーバー | gunicorn 26 |
| 静的ファイル配信 | WhiteNoise 6 |
| Lint / Format | ruff |
| CI | GitHub Actions |

## ディレクトリ構成

```
.
├── src/                      # Django プロジェクト（uv のプロジェクトルート）
│   ├── manage.py
│   ├── pyproject.toml / uv.lock
│   ├── xv_rugby/             # 設定パッケージ（settings.py, urls.py, wsgi.py）
│   ├── common/               # 共通の抽象モデル（BaseModel: 論理削除・作成/更新日時）
│   ├── master/               # マスタ（ポジション、役職、得点方法、反則など）
│   ├── member/               # チーム・メンバー
│   └── match/                # 試合・イベント記録
├── containers/django/        # Django（gunicorn）の Dockerfile
├── docker-compose.yml
├── .env.example              # 環境変数のテンプレート
└── .github/workflows/ci.yml  # CI
```

## セットアップ

### ローカル（uv）

前提: [uv](https://docs.astral.sh/uv/getting-started/installation/) と PostgreSQL が使えること。

```bash
cd src
uv sync

# 環境変数（例）。値は各自の環境に合わせてください
export DJANGO_DEBUG=1
export POSTGRES_DB=xv_rugby
export POSTGRES_USER=xv_rugby
export POSTGRES_PASSWORD=<ローカルDBのパスワード>
export DB_HOST=localhost

uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

http://127.0.0.1:8000/admin/ で管理画面にログインできます。

本番相当（gunicorn + WhiteNoise）で動かす場合:

```bash
export DJANGO_DEBUG=0 DJANGO_SECRET_KEY=<生成したキー> DJANGO_ALLOWED_HOSTS=localhost
uv run python manage.py collectstatic --noinput   # リポジトリ直下の static/ に出力
uv run gunicorn xv_rugby.wsgi:application --bind 127.0.0.1:8000
```

HTTP で確認するときは `DJANGO_SECURE_COOKIES=0` も設定してください（DEBUG オフ時は Cookie が Secure になるため、HTTP ではログインできません）。

`DJANGO_DEBUG=1` かつ `DJANGO_SECRET_KEY` 未設定の場合は、起動ごとに使い捨てのキーが生成されます（再起動するとログインセッションは切れます）。

### Docker Compose

> ⚠️ Docker Compose での起動は、まだローカルで動作確認できていません。

```bash
cp .env.example .env

# 新しい SECRET_KEY を生成して .env の DJANGO_SECRET_KEY に設定
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# .env の POSTGRES_PASSWORD も任意の値に変更

docker compose up -d --build
docker compose exec django python manage.py migrate
docker compose exec django python manage.py createsuperuser
```

django コンテナは起動時に `collectstatic` を実行してから gunicorn を起動します。http://localhost:8000/admin/ にアクセスします（ポートは `DJANGO_HOST_PORT`）。静的ファイルは WhiteNoise が配信します。`.env.example` では `GUNICORN_CMD_ARGS=--reload` によりコード変更時に自動で再起動します。PostgreSQL のポートはデフォルトではホストに公開していません。

本番では TLS を終端するリバースプロキシ／ロードバランサーを gunicorn の前段に置く想定です。

## 環境変数

Django が読む環境変数（`src/xv_rugby/settings.py`）:

| 名前 | 必須 | 説明 | デフォルト |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | `DJANGO_DEBUG` オフ時は必須 | Django の SECRET_KEY | なし（DEBUG 時のみ起動ごとに自動生成） |
| `DJANGO_DEBUG` | - | `1` / `true` / `yes` / `on` で DEBUG 有効 | オフ |
| `DJANGO_ALLOWED_HOSTS` | 本番では必須 | カンマ区切りのホスト名 | DEBUG 時 `localhost,127.0.0.1`、それ以外は空 |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | - | カンマ区切りのオリジン（`https://example.com` など） | 空 |
| `DJANGO_STATIC_ROOT` | - | `collectstatic` の出力先 | リポジトリ直下の `static/`（Docker では `/static`） |
| `DJANGO_SECURE_COOKIES` | - | DEBUG オフ時に Cookie を Secure にするか | `1` |
| `DJANGO_SECURE_SSL_REDIRECT` | - | DEBUG オフ時に HTTPS へリダイレクトするか | `0` |
| `DJANGO_SECURE_HSTS_SECONDS` | - | DEBUG オフ時の HSTS 秒数 | `0` |
| `POSTGRES_DB` | - | データベース名（postgres コンテナと共用） | `xv_rugby` |
| `POSTGRES_USER` | - | DB ユーザー（postgres コンテナと共用） | `xv_rugby` |
| `POSTGRES_PASSWORD` | 必須 | DB パスワード（postgres コンテナと共用） | 空 |
| `DB_HOST` | - | DB ホスト（docker compose では `postgres` に上書き） | `localhost` |
| `DB_PORT` | - | DB ポート | `5432` |
| `DB_CONN_MAX_AGE` | - | DB 接続の再利用秒数 | `60` |

docker compose／gunicorn 用の変数（`DJANGO_HOST_PORT`、`DJANGO_SOURCE`、`GUNICORN_CMD_ARGS` など）は `.env.example` を参照してください。`GUNICORN_CMD_ARGS` は gunicorn 標準の環境変数で、`--workers 4` などのオプションを渡せます。

## テスト・Lint

```bash
cd src
uv run python manage.py test                 # PostgreSQL への接続が必要
uv run python manage.py makemigrations --check --dry-run
uv run ruff check .
uv run ruff format --check .                 # 整形するときは uv run ruff format .
```

## CI

GitHub Actions（`.github/workflows/ci.yml`）で、`master` への push と Pull Request ごとに以下を実行します。

- PostgreSQL 18 のサービスコンテナを起動
- `uv sync --locked`
- `manage.py check` / `makemigrations --check --dry-run` / `migrate` / `test`
- `ruff check` / `ruff format --check`

Action は commit SHA で固定しており、更新は Dependabot（`.github/dependabot.yml`）に任せています。

## セキュリティ

- **以前 `settings.py` にハードコードされていた `SECRET_KEY` は git 履歴に残っており、公開リポジトリで漏洩済みです。どの環境でも絶対に再利用しないでください。** 環境ごとに新しいキーを生成し、`.env`（gitignore 済み）や環境変数で渡してください。
- `.env` や実際のパスワード・キーはコミットしないでください。

## コントリビュート

- Pull Request のタイトル・本文は日本語で書きます（[Issue #4](https://github.com/xv-coach/xv/issues/4)）。PR テンプレートの項目（概要・変更内容・関連 Issue・検証・影響・互換性）に沿って記載してください。
- AI エージェント向けのガイド（`AGENTS.md`）と PR テンプレートは [PR #6](https://github.com/xv-coach/xv/pull/6) で追加予定です。

## ライセンス

MIT（`pyproject.toml` 記載）。LICENSE ファイルは未作成です。
