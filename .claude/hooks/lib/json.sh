# shellcheck shell=sh
# Shared JSON reader for the hooks. Source it, then call hook_json_get.
#
#   hook_json_get "$INPUT" tool_input.file_path [tool_input.path ...]
#     Prints the first dotted path whose value is present and not null / false: strings raw,
#     other values as JSON. Prints nothing when none matches or the JSON is unreadable.
#     Returns 3 when no parser is available.
#   hook_json_require <hook name>
#     For guard hooks. Without a parser the hook cannot see what it is guarding, so it fails
#     closed: prints how to install jq to stderr and exits 2 (Claude Code blocks the tool call).
#     Informational hooks skip this and degrade on their own.
#   hook_json_string "text"
#     Prints "text" as a JSON string literal (for building hook output without jq).
#
# Parser order (HOOK_JSON_BACKEND): jq -> python3 -> plutil (macOS) -> none.
# python3 is used only when it really runs: on macOS without the Command Line Tools,
# /usr/bin/python3 is a stub that opens an install dialog and fails, and on Windows `python3`
# may be the Microsoft Store alias.
# tr -d '\r': Windows-native jq ends every output line with CRLF; a trailing \r breaks comparisons.

HOOK_JSON_BACKEND=none
if command -v jq >/dev/null 2>&1; then
  HOOK_JSON_BACKEND=jq
elif [ "$(python3 -c 'print(1)' 2>/dev/null | tr -d '\r')" = 1 ]; then
  HOOK_JSON_BACKEND=python3
elif command -v plutil >/dev/null 2>&1 \
  && [ "$(printf '{"a":"1"}' | plutil -extract a raw -o - - 2>/dev/null)" = 1 ]; then
  HOOK_JSON_BACKEND=plutil
fi

hook_json_get() {
  _hj_in=$1
  shift
  for _hj_p in "$@"; do
    case $_hj_p in
      '' | .* | *. | *..* | *[!A-Za-z0-9_.]*) echo "hook_json_get: bad path '$_hj_p'" >&2; return 2 ;;
    esac
  done
  case $HOOK_JSON_BACKEND in
    jq)
      _hj_f=
      for _hj_p in "$@"; do _hj_f="$_hj_f.$_hj_p // "; done
      printf '%s' "$_hj_in" | jq -r "${_hj_f}empty" 2>/dev/null | tr -d '\r'
      ;;
    python3)
      printf '%s' "$_hj_in" | python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.buffer.read().decode("utf-8"))
except Exception:
    sys.exit(1)
for p in sys.argv[1:]:
    v = d
    for k in p.split("."):
        v = v.get(k) if isinstance(v, dict) else None
        if v is None:
            break
    if v is None or v is False:
        continue
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    sys.stdout.buffer.write(s.encode("utf-8"))
    break
' "$@" 2>/dev/null | tr -d '\r'
      ;;
    plutil)
      # plutil has no null and "raw" only prints scalars; a missing key is an error.
      for _hj_p in "$@"; do
        if _hj_v=$(printf '%s' "$_hj_in" | plutil -extract "$_hj_p" raw -o - - 2>/dev/null); then
          printf '%s' "$_hj_v"
          return 0
        fi
      done
      ;;
    *) return 3 ;;
  esac
  return 0
}

hook_json_require() {
  [ "$HOOK_JSON_BACKEND" = none ] || return 0
  {
    echo "BLOCKED by ${1:-hook}: no JSON parser (jq / python3 / plutil) was found, so this safety hook cannot read the tool input."
    echo "  Install jq: macOS 'brew install jq' / Debian 'sudo apt-get install jq' / Windows 'winget install jqlang.jq'"
  } >&2
  exit 2
}

hook_json_string() {
  printf '"'
  printf '%s' "$1" | tr -d '\r' | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' \
    | awk 'BEGIN { ORS = "" } NR > 1 { print "\\n" } { print }'
  printf '"'
}
