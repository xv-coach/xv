---
paths:
  - "**/Dockerfile"
  - "**/*.Dockerfile"
  - "**/.dockerignore"
  - "**/compose.yml"
  - "**/compose.*.yml"
  - "**/docker-compose*.yml"
---

# Docker build context

- `.gitignore` に生成物・ローカル成果物・作業用ディレクトリ（`node_modules/`、`dist/`、`coverage/`、`.claude/worktrees/` など）を足したら、image build に不要かを判断し、不要なら `.dockerignore` にも足す。build context が膨らむとビルドが遅くなり、意図しないファイルが image に入る
- `.env*` や鍵ファイルは build context から除外する（image にシークレットが焼き込まれるのを防ぐ）。compose の `env_file` はクライアント側で読まれるため、`.dockerignore` の影響を受けない。image に本当に必要なファイルだけ `!` で個別に戻す
- Dockerfile の `COPY . .` や build context の範囲を変えたら、`.dockerignore` を見直す
