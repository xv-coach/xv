#!/bin/sh
# PreToolUse hook for Edit/Write tools.
# Blocks prohibition language (禁止表現) in .claude/rules/*.md files.
# Enforces positive/affirmative phrasing in project rules.
# Reads JSON from stdin, checks content against prohibition patterns.
# Exit 0 = allow, Exit 2 = block.

# Read stdin
INPUT=$(cat)

# Shared JSON reader (jq -> python3 -> plutil). A guard that cannot read its input blocks (exit 2).
HOOK_JSON_LIB="$(dirname "$0")/lib/json.sh"
[ -r "$HOOK_JSON_LIB" ] || { echo "BLOCKED by check-prohibition-language: $HOOK_JSON_LIB is missing; restore .claude/hooks/lib/json.sh from the repository" >&2; exit 2; }
# shellcheck source=lib/json.sh
. "$HOOK_JSON_LIB"
hook_json_require check-prohibition-language

FILE_PATH=$(hook_json_get "$INPUT" tool_input.file_path)

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Only check .claude/rules/*.md files
case "$FILE_PATH" in
  */.claude/rules/*.md) ;;
  *) exit 0 ;;
esac

# Extract content to check: new_string (Edit) or content (Write)
TOOL_NAME=$(hook_json_get "$INPUT" tool_name)

if [ "$TOOL_NAME" = "Edit" ]; then
  CONTENT=$(hook_json_get "$INPUT" tool_input.new_string)
elif [ "$TOOL_NAME" = "Write" ]; then
  CONTENT=$(hook_json_get "$INPUT" tool_input.content)
else
  exit 0
fi

if [ -z "$CONTENT" ]; then
  exit 0
fi

# Check for prohibition patterns
# The **禁止:** label form is a list-bullet prohibition that the verb patterns miss.
# (:|：) rather than [:：]: under the C locale (Git Bash's default) a bracket matches single
# bytes, so the 3-byte full-width colon would never match.
if printf '%s\n' "$CONTENT" | grep -qE '禁止する|禁止とする|してはならない|してはいけない|することは禁止|\*\*禁止(:|：)\*\*'; then
  cat >&2 <<'MSG'
BLOCKED: 禁止表現が検出されました。肯定的な表現に書き換えてください。

  ✗ "〜は禁止する" → ✓ "〜すること"
  ✗ "〜してはならない" → ✓ "〜しないこと" / "〜ではなく〜を使うこと"
  ✗ "〜してはいけない" → ✓ "〜する代わりに〜すること"

理由: 肯定的な表現は何をすべきかが明確になり、遵守率が向上します。
MSG
  exit 2
fi

exit 0
