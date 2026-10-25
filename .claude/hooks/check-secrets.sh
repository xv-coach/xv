#!/usr/bin/env bash
# PreToolUse Edit/Write hook — シークレットらしき文字列のコミット混入を防ぐ
# 検出されたら deny、`# claude-allow-secret` がコンテンツに含まれていれば許可

set -euo pipefail

input=$(cat)

# Shared JSON reader (jq -> python3 -> plutil). A guard that cannot read its input blocks (exit 2).
HOOK_JSON_LIB="$(dirname "$0")/lib/json.sh"
[ -r "$HOOK_JSON_LIB" ] || { echo "BLOCKED by check-secrets: $HOOK_JSON_LIB is missing; restore .claude/hooks/lib/json.sh from the repository" >&2; exit 2; }
# shellcheck source=lib/json.sh
. "$HOOK_JSON_LIB"
hook_json_require check-secrets

# 検査対象は Edit の new_string、Write の content
content=$(hook_json_get "$input" tool_input.new_string tool_input.content || true)

if [ -z "$content" ]; then
  exit 0
fi

# deny の JSON は理由文をエスケープして組み立てる（引用符が入っても壊れないように。jq 不要）
deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' \
    "$(hook_json_string "$1")"
  exit 0
}

# 明示的なオプトアウト（コンテンツに `claude-allow-secret` が含まれていれば検査スキップ）
if grep -q "claude-allow-secret" <<<"$content"; then
  exit 0
fi

# 高信頼パターン（誤検知が少ないもの）
patterns=(
  'AKIA[0-9A-Z]{16}'                                        # AWS Access Key ID
  'ghp_[A-Za-z0-9]{36}'                                     # GitHub PAT (classic)
  'github_pat_[A-Za-z0-9_]{82}'                             # GitHub fine-grained PAT
  '(^|[^A-Za-z0-9])sk-(ant-[a-z0-9]+-)?[A-Za-z0-9_-]{32,}'  # OpenAI / Anthropic keys（task- 等の語中の sk- は除外）
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'                      # PEM private keys
)

for pattern in "${patterns[@]}"; do
  # 数字か大文字を含む一致だけを拾う。実キーはランダム文字列なので必ず含み、
  # sk-learn-model-... のようなケバブケースの語は含まないので除外できる。
  # 入力は here-string で渡す（`printf | grep -q` は SIGPIPE + pipefail で大きな内容を見逃す）
  matched=$(grep -oE -- "$pattern" <<<"$content" | grep -E '[A-Z0-9]' | sed -n 1p || true)
  if [ -n "$matched" ]; then
    [[ $pattern == '(^|'* && $matched =~ ^[^A-Za-z0-9] ]] && matched=${matched:1}  # 境界として拾った先頭の 1 文字を落とす
    deny "シークレットらしき文字列が検出されました（パターン: $pattern, 一致: ${matched:0:8}...）。本当に書き込む場合は、編集対象のコンテンツに「# claude-allow-secret」コメントを含めてください。"
  fi
done

# 汎用パターン（key/secret/token = "..." または ": ..." 形式の長い値）
generic_pattern='\b(api[_-]?key|secret|password|token)[^=:]{0,8}[=:][^=:]{0,4}["'\''`][A-Za-z0-9_/+=.-]{16,}["'\''`]'
if grep -qiE -- "$generic_pattern" <<<"$content"; then
  deny '汎用シークレットパターン (api_key/secret/password/token = "...") が検出されました。コンテンツに「# claude-allow-secret」コメントを含めてオプトアウトできます。'
fi

exit 0
