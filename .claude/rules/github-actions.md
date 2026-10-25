---
paths:
  - ".github/workflows/**"
  - ".github/actions/**"
---

# GitHub Actions

GitHub 公式（`actions/*`）以外の action は、commit SHA で固定し、行末にバージョンをコメントで残す。タグは提供元が侵害されると差し替えられるため。

```yaml
uses: astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0   # OK
uses: astral-sh/setup-uv@v6                                                  # NG
```

- `@main` / `@vX` / `@vX.Y.Z` のようなタグ・ブランチ参照はすべて SHA に置き換える。移動するメジャータグ（`@v1`）を固定するときは、その時点の最新パッチの SHA を選び、コメントにもパッチまで書く
- `actions/*`、および同じリポジトリ内の reusable workflow（`./.github/workflows/foo.yml`）はタグ参照のままでよい
- 更新は Dependabot の `github-actions` ecosystem に任せる（SHA とコメントを両方更新する PR が来る）。`.github/dependabot.yml` が未設定なら `package-ecosystem: "github-actions"` を追加する
- 既存の workflow にタグ参照が残っていたら、その workflow を触る PR で SHA 固定に直す（別 PR に分けてもよい）

SHA の取り方（annotated tag は 2 段階で commit を解決する）:

```bash
gh api repos/<owner>/<repo>/git/refs/tags/<tag> --jq '.object'   # type が commit ならこの sha
gh api repos/<owner>/<repo>/git/tags/<sha> --jq '.object.sha'     # type が tag のとき
```
