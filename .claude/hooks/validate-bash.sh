#!/bin/sh
# PreToolUse hook for Bash tool.
# Blocks dangerous commands: git add . / -A / :/, git push --force / -f / +refspec,
# rm -rf (all flag forms), and removing a worktree or deleting a branch while the
# cwd is inside that worktree.
# `git push --force-with-lease` is allowed: the remote rejects it if someone else pushed,
# so it is the safe way to republish a rebased branch.
# Reads JSON from stdin, extracts tool_input.command, and checks against block patterns.
# Exit 0 = allow, Exit 2 = block. Allows unreadable JSON; blocks when no JSON parser
# (jq / python3 / plutil) is available (see lib/json.sh).
#
# Strategy: split the command into segments on shell separators outside quotes, reduce each
# segment to its command word (dropping env assignments, sudo/command/env/xargs, paths), and
# inspect each one. Quoted text stays inside its segment, so `git commit -m "a; rm -rf b"`
# is not a false positive, while `x && rm -rf y`, `x & rm -rf y` and `$(rm -rf y)` are caught.

INPUT=$(cat)

# Shared JSON reader (jq -> python3 -> plutil). A guard that cannot read its input blocks (exit 2).
HOOK_JSON_LIB="$(dirname "$0")/lib/json.sh"
[ -r "$HOOK_JSON_LIB" ] || { echo "BLOCKED by validate-bash: $HOOK_JSON_LIB is missing; restore .claude/hooks/lib/json.sh from the repository" >&2; exit 2; }
# shellcheck source=lib/json.sh
. "$HOOK_JSON_LIB"
hook_json_require validate-bash

COMMAND=$(hook_json_get "$INPUT" tool_input.command)

if [ -z "$COMMAND" ]; then
  exit 0
fi

# One segment per line. Separators: ; & | ( ) ` and newline, outside single/double quotes.
# Heredoc bodies (<<WORD, <<-WORD, <<'WORD') are data, not commands, so they are dropped.
# awk rather than sed so BSD (macOS) and GNU behave the same.
split_segments() {
  printf '%s' "$1" | awk '
    BEGIN { RS = "\001" }
    {
      s = $0; out = ""; q = ""; n = length(s); nh = 0
      for (i = 1; i <= n; i++) {
        c = substr(s, i, 1)
        if (q == "") {
          if (c == "\\") { out = out c substr(s, i + 1, 1); i++; continue }
          if (c == "\"" || c == "\047") { q = c; out = out c; continue }
          # << (not <<<): remember the delimiter; the body starts after the next newline
          if (c == "<" && substr(s, i + 1, 1) == "<" && substr(s, i + 2, 1) != "<") {
            j = i + 2; strip = 0
            if (substr(s, j, 1) == "-") { strip = 1; j++ }
            while (substr(s, j, 1) == " " || substr(s, j, 1) == "\t") j++
            w = ""
            while (j <= n) {
              d = substr(s, j, 1)
              if (d == "\"" || d == "\047" || d == "\\") { j++; continue }
              if (d ~ /[A-Za-z0-9_.-]/) { w = w d; j++ } else break
            }
            if (w != "") { nh++; hd[nh] = w; hs[nh] = strip }
            out = out "<<"; i = j - 1; continue
          }
          if (c == "\n" && nh > 0) {
            out = out "\n"; pos = i + 1
            for (k = 1; k <= nh; k++) {
              while (pos <= n) {
                e = index(substr(s, pos), "\n")
                line = e ? substr(s, pos, e - 1) : substr(s, pos)
                pos = e ? pos + e : n + 1
                if (hs[k]) sub(/^\t+/, "", line)
                if (line == hd[k]) break
              }
            }
            nh = 0; i = pos - 1; continue
          }
          if (c == ";" || c == "&" || c == "|" || c == "(" || c == ")" || c == "`" || c == "\n") { out = out "\n"; continue }
          out = out c
        } else {
          if (q == "\"" && c == "\\") { out = out c substr(s, i + 1, 1); i++; continue }
          if (c == q) q = ""
          if (c == "\n") c = " "
          out = out c
        }
      }
      printf "%s\n", out
    }'
}

# Drop leading env assignments, shell keywords ({ ! if then do ...) and wrappers with their
# options (sudo -u root, xargs -n 1, timeout 5, ...), then reduce the command word to its
# basename (/bin/rm -> rm). For git, drop global options (-C <dir>, -c <k=v>, --no-pager, ...).
# The per-wrapper letter lists are the options that take a separate value argument.
normalize() {
  printf '%s\n' "$1" | sed -E '
:a
s/^[[:space:]]+//
s/^(command|exec|nohup|builtin|if|then|else|elif|do|while|until|!|\{)([[:space:]]+|$)//
s/^sudo([[:space:]]+(-[ugCDhprtU][[:space:]]+[^[:space:]]+|-[^[:space:]]+))*([[:space:]]+|$)//
s/^env([[:space:]]+(-[uCS][[:space:]]+[^[:space:]]+|-[^[:space:]]+))*([[:space:]]+|$)//
s/^time([[:space:]]+(-[fo][[:space:]]+[^[:space:]]+|-[^[:space:]]+))*([[:space:]]+|$)//
s/^nice([[:space:]]+(-n[[:space:]]+[^[:space:]]+|-[^[:space:]]+))*([[:space:]]+|$)//
s/^timeout([[:space:]]+(-[sk][[:space:]]+[^[:space:]]+|-[^[:space:]]+))*[[:space:]]+[^[:space:]]+([[:space:]]+|$)//
s/^xargs([[:space:]]+(-[nILPdEsa][[:space:]]+[^[:space:]]+|-[^[:space:]]+))*([[:space:]]+|$)//
s/^[A-Za-z_][A-Za-z0-9_]*=("[^"]*"|'"'"'[^'"'"']*'"'"'|[^[:space:]]*)([[:space:]]+|$)//
ta
s/^[^[:space:]]*\/([^[:space:]\/]+)/\1/
:g
s/^git[[:space:]]+-[Cc][[:space:]]+("[^"]*"|'"'"'[^'"'"']*'"'"'|[^[:space:]]+)/git/
s/^git[[:space:]]+-[^[:space:]]+/git/
tg
'
}

# Remove quoting characters so "rm", \rm and git add "." are seen as rm and git add .
unquote() { printf '%s\n' "$1" | sed -e 's/[\\"'"'"']//g'; }

# Remove quoted strings entirely, for checks where their content must not count (push -o "a +b").
drop_quoted() { printf '%s\n' "$1" | sed -E -e 's/"[^"]*"//g' -e "s/'[^']*'//g"; }

matches() { printf '%s\n' "$1" | grep -qE "$2"; }

# Resolve a path against $CWD to its physical absolute form (falls back to the input when it
# does not exist).
resolve() {
  case "$1" in
    /*) p=$1 ;;
    \~) p=$HOME ;;
    \~/*) p="$HOME/${1#\~/}" ;;
    # Windows drive paths (C:/x, C:\x): Git Bash's pwd -P reports /c/x.
    [A-Za-z]:[/\\]*) p=$(cygpath -u "$1" 2>/dev/null || printf '%s' "$1") ;;
    *) p="$CWD/$1" ;;
  esac
  (cd "$p" 2>/dev/null && pwd -P) || printf '%s\n' "$p"
}

# True when $1 (a physical path) is $2 or inside it.
inside() { case "$1" in "$2" | "$2"/*) return 0 ;; esac; return 1; }

SEGMENTS=$(split_segments "$COMMAND")
# Tracks `cd` within the command, so `cd <main-repo> && git branch -d x` is judged from there.
CWD=$(pwd -P)

set -f
IFS='
'
for RAW in $SEGMENTS; do
  SEG=$(normalize "$(unquote "$(normalize "$RAW")")")
  [ -n "$SEG" ] || continue

  if matches "$SEG" '^cd([[:space:]]|$)'; then
    DIR=$(printf '%s\n' "$SEG" | awk '{ print ($2 == "" ? "~" : $2) }')
    CWD=$(resolve "$DIR")
    continue
  fi

  if matches "$SEG" '^git[[:space:]]+add([[:space:]]|$)'; then
    # git add . / ./ / :/ (directory- or repository-wide staging), -A / --all in any position
    if matches "$SEG" '[[:space:]](\.|\./|:/|:/\.)([[:space:]]|$)' \
       || matches "$SEG" '([[:space:]]-[A-Za-z]*A|[[:space:]]--all)([[:space:]]|$)'; then
      echo "BLOCKED: 'git add .' / 'git add -A' is not allowed. Stage specific files instead." >&2
      echo "  Why: it sweeps in secrets, build output and nested worktrees under .claude/worktrees/." >&2
      exit 2
    fi
  fi

  if matches "$SEG" '^git[[:space:]]+push([[:space:]]|$)'; then
    # --force, a short-flag cluster containing f (-f, -uf, -fu), or a +refspec.
    # Must NOT match --force-with-lease / --force-if-includes / --follow-tags, nor a branch
    # name that merely contains "-f" (git push origin fix-foo).
    if matches "$SEG" '[[:space:]]--force([[:space:]]|$)' \
       || matches "$SEG" '[[:space:]]-[A-Za-z]*f[A-Za-z]*([[:space:]]|$)' \
       || matches "$(normalize "$(drop_quoted "$RAW")")" '[[:space:]]\+[^[:space:]]'; then
      echo "BLOCKED: 'git push --force' (or -f / +refspec) is not allowed." >&2
      echo "  To republish a rebased branch, use --force-with-lease (rejected if the remote moved)." >&2
      exit 2
    fi
  fi

  # rm with BOTH recursive and force flags, in any flag position (including after operands:
  # `rm dir -rf`) and any combination (`-rf`, `-Rf`, `-r -f`, `--recursive --force`).
  if matches "$SEG" '^rm([[:space:]]|$)' \
     && matches "$SEG" '([[:space:]]-[A-Za-z]*[rR]|[[:space:]]--recursive)' \
     && matches "$SEG" '([[:space:]]-[A-Za-z]*f|[[:space:]]--force)'; then
    echo "BLOCKED: 'rm -rf' (or equivalent) is not allowed. Remove files individually." >&2
    echo "  For directories, use 'rm -r <dir>' after checking the target (see bash-safety skill)." >&2
    exit 2
  fi

  # git worktree remove [-f|--force]... <path>: block when the cwd is that worktree or inside it.
  if matches "$SEG" '^git[[:space:]]+worktree[[:space:]]+remove([[:space:]]|$)'; then
    TARGET=$(printf '%s\n' "$SEG" | awk '{ for (i = 4; i <= NF; i++) if ($i !~ /^-/) { print $i; exit } }' \
      | sed -e "s/^[\"']//" -e "s/[\"']\$//")
    if [ -n "$TARGET" ] && inside "$CWD" "$(resolve "$TARGET")"; then
      echo "BLOCKED: cwd is inside the worktree being removed. Run 'cd <main-repo>' first." >&2
      echo "  'git -C' does not move the shell's cwd; removing it would break every later command." >&2
      exit 2
    fi
  fi

  # git branch -d/-D/--delete: block when the cwd is inside a linked worktree (not the main one).
  if matches "$SEG" '^git[[:space:]]+branch([[:space:]]|$)' \
     && matches "$SEG" '[[:space:]](-[A-Za-z]*[dD][A-Za-z]*|--delete)([[:space:]]|$)'; then
    WORKTREES=$(git worktree list --porcelain 2>/dev/null | sed -n 's/^worktree //p' | sed 1d)
    for W in $WORKTREES; do
      # Git for Windows lists C:/x while pwd -P gives /c/x; convert so the paths compare.
      if command -v cygpath >/dev/null 2>&1; then W=$(cygpath -u "$W"); fi
      if inside "$CWD" "$(resolve "$W")"; then
        MAIN_REPO=$(git worktree list --porcelain 2>/dev/null | sed -n '1s/^worktree //p')
        echo "BLOCKED: cwd is inside a worktree. Run 'cd ${MAIN_REPO}' first." >&2
        exit 2
      fi
    done
  fi
done

exit 0
