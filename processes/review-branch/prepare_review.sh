#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  prepare_review.sh <pr_url>
  prepare_review.sh <remote_url> <branch>
Options:
  --base <branch>       (default: master, fallback to main)
  --paths p1,p2,...     (optional; prints priority paths)
  --merge-base          (opt in to local merge of upstream base)
  --no-merge-base       (skip local merge; the default)
Notes:
  - Requires local git remote named 'upstream'.
  - Supports HTTPS, SSH (including host:path), and existing local directories.
  - Relative local directory paths are resolved from the repository root.
  - Git URL rewrites must also use those transports; redirects default to disabled.
  - Does not run tests; CI is authoritative by default.
USAGE
}

BASE_BRANCH="master"
PATHS=""
NO_MERGE_BASE="1"

ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)
      if [[ $# -lt 2 ]]; then echo "ERROR: --base requires a branch."; exit 1; fi
      BASE_BRANCH="$2"
      shift 2
      ;;
    --paths)
      if [[ $# -lt 2 ]]; then echo "ERROR: --paths requires a value."; exit 1; fi
      PATHS="$2"
      shift 2
      ;;
    --no-merge-base)
      NO_MERGE_BASE="1"
      shift
      ;;
    --merge-base)
      NO_MERGE_BASE="0"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "ERROR: Unsupported option."
      exit 1
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#ARGS[@]} -lt 1 || ${#ARGS[@]} -gt 2 ]]; then
  usage
  exit 1
fi

INPUT1="${ARGS[0]}"
INPUT2="${ARGS[1]:-}"

is_pr_url() {
  [[ "$1" =~ ^https://github\.com/[^/]+/[^/]+/pull/[0-9]+/?$ ]]
}

if [[ "$INPUT1" == *"/pull/"* ]] && ! is_pr_url "$INPUT1"; then
  echo "ERROR: Expected an HTTPS github.com PR URL."
  exit 1
fi

# Restrict the actual transport, including URL rewrites, submodule fetches and
# helpers. Do not let ambient GIT_ALLOW_PROTOCOL or protocol.*.allow widen it.
# libcurl redirects are separate from Git's protocol selection: disable them.
export GIT_ALLOW_PROTOCOL=https:ssh:file
git() {
  command git -c protocol.allow=never -c protocol.https.allow=always \
    -c protocol.ssh.allow=always -c protocol.file.allow=always \
    -c http.followRedirects=false "$@"
}

validate_remote_url() {
  local url="$1"
  # Git accepts helper::address and option-like operands. Neither is a URL in
  # this interface. Keep local paths explicit by requiring an existing directory.
  if [[ -z "$url" || "$url" == -* || "$url" == *$'\n'* || "$url" == *$'\r'* ]]; then
    echo "ERROR: Unsupported Git remote; use HTTPS, SSH, or an existing local directory."
    exit 1
  fi
  if [[ "$url" != *:* && -d "$url" ]]; then
    return
  fi
  if [[ "$url" =~ [[:space:]] ]]; then
    echo "ERROR: Unsupported Git remote; use HTTPS, SSH, or an existing local directory."
    exit 1
  fi
  if [[ "$url" =~ ^https://[^/[:space:]]+/[^[:space:]]+$ || \
        "$url" =~ ^ssh://[^/[:space:]]+/[^[:space:]]+$ ]]; then
    return
  fi
  # SCP-style SSH requires a nonempty path that does not start with ':', so
  # http::http://... (Git's remote-helper notation) cannot pass as host:path.
  if [[ "$url" =~ ^([^@/:[:space:]]+@)?[a-zA-Z0-9._-]+:[^:[:space:]][^[:space:]]*$ && \
        "$url" != *://* ]]; then
    return
  fi
  echo "ERROR: Unsupported Git remote; use HTTPS, SSH, or an existing local directory."
  exit 1
}

validate_transport() {
  validate_remote_url "$1"
  # --get-url expands url.*.insteadOf without contacting a server or changing
  # repository state. Check that effective URL before any fetch or remote add.
  validate_remote_url "$(git ls-remote --get-url "$1")"
}

require_upstream() {
  if ! git remote get-url upstream >/dev/null 2>&1; then
    echo "ERROR: upstream remote not found. Please add it first:"
    echo "  git remote add upstream <url>"
    exit 1
  fi
  local url
  while IFS= read -r url; do
    validate_transport "$url"
  done < <(git remote get-url --all upstream)
}

# Match Git fetch's root-relative local paths even when invoked in a subdirectory.
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if ! is_pr_url "$INPUT1"; then
  validate_transport "$INPUT1"
elif [[ ${#ARGS[@]} -ne 1 ]]; then
  usage
  exit 1
fi

require_upstream

REVIEW_REMOTE_URL=""
REVIEW_BRANCH=""
PR_BASE_REF=""

if is_pr_url "$INPUT1"; then
  PR_URL="$INPUT1"

  if command -v gh >/dev/null 2>&1; then
    JSON="$(gh pr view "$PR_URL" --json headRefName,headRepository,baseRefName)"
    REVIEW_BRANCH="$(printf '%s' "$JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["headRefName"])')"
    REVIEW_REMOTE_URL="$(printf '%s' "$JSON" | python3 -c 'import json,sys; repo=json.load(sys.stdin).get("headRepository") or {}; print(repo.get("sshUrl") or repo.get("url") or "")')"
    PR_BASE_REF="$(printf '%s' "$JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("baseRefName", ""))')"
  else
    if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
      OWNER="${BASH_REMATCH[1]}"
      REPO="${BASH_REMATCH[2]}"
      NUM="${BASH_REMATCH[3]}"
    else
      echo "ERROR: Unsupported PR URL format (expected github.com/OWNER/REPO/pull/NUM)"
      exit 1
    fi

    API="https://api.github.com/repos/${OWNER}/${REPO}/pulls/${NUM}"
    AUTH_HEADER=()
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
      AUTH_HEADER=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
    fi

    JSON="$(curl -sSL --proto '=https' --proto-redir '=https' "${AUTH_HEADER[@]}" -H "Accept: application/vnd.github+json" "$API")"
    REVIEW_BRANCH="$(printf '%s' "$JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["head"]["ref"])')"
    REVIEW_REMOTE_URL="$(printf '%s' "$JSON" | python3 -c 'import json,sys; repo=json.load(sys.stdin)["head"]["repo"]; print(repo.get("ssh_url") or repo.get("clone_url") or "")')"
    PR_BASE_REF="$(printf '%s' "$JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["base"]["ref"])')"
  fi

  if [[ -z "$REVIEW_REMOTE_URL" || -z "$REVIEW_BRANCH" ]]; then
    echo "ERROR: Failed to resolve PR into remote URL and branch."
    echo "For private PRs, run 'gh auth login' or export GITHUB_TOKEN."
    exit 1
  fi

  if [[ -n "$PR_BASE_REF" && "$PR_BASE_REF" != "$BASE_BRANCH" ]]; then
    echo "NOTE: PR base is '$PR_BASE_REF' while current --base is '$BASE_BRANCH'."
  fi
else
  if [[ -z "$INPUT2" ]]; then
    usage
    exit 1
  fi
  REVIEW_REMOTE_URL="$INPUT1"
  REVIEW_BRANCH="$INPUT2"
fi

if [[ "$BASE_BRANCH" == -* || "$REVIEW_BRANCH" == -* ]] || \
   ! git check-ref-format "refs/heads/$BASE_BRANCH" || \
   ! git check-ref-format "refs/heads/$REVIEW_BRANCH"; then
  echo "ERROR: Invalid base or review branch name."
  exit 1
fi

validate_transport "$REVIEW_REMOTE_URL"

REVIEW_REMOTE_NAME="codex_review_remote"
if git remote get-url "$REVIEW_REMOTE_NAME" >/dev/null 2>&1; then
  while IFS= read -r url; do
    validate_transport "$url"
  done < <(git remote get-url --all "$REVIEW_REMOTE_NAME")
  EXISTING_URL="$(git remote get-url "$REVIEW_REMOTE_NAME")"
  if [[ "$EXISTING_URL" != "$REVIEW_REMOTE_URL" ]]; then
    echo "ERROR: remote '$REVIEW_REMOTE_NAME' exists but URL differs."
    echo "Existing: $EXISTING_URL"
    echo "Wanted:   $REVIEW_REMOTE_URL"
    exit 1
  fi
fi

echo "== Fetching latest upstream/${BASE_BRANCH} =="
if ! git fetch --prune upstream "$BASE_BRANCH"; then
  if [[ "$BASE_BRANCH" == "master" ]]; then
    echo "master not found, trying main..."
    BASE_BRANCH="main"
    git fetch --prune upstream "$BASE_BRANCH"
  else
    echo "ERROR: failed to fetch upstream/${BASE_BRANCH}"
    exit 1
  fi
fi
BASE_REF="upstream/${BASE_BRANCH}"

if ! git remote get-url "$REVIEW_REMOTE_NAME" >/dev/null 2>&1; then
  git remote add "$REVIEW_REMOTE_NAME" "$REVIEW_REMOTE_URL"
fi

echo "== Fetching review branch =="
git fetch --prune "$REVIEW_REMOTE_NAME" "$REVIEW_BRANCH"

SAFE_BRANCH="${REVIEW_BRANCH//\//_}"
SAFE_BRANCH="$(printf '%s' "$SAFE_BRANCH" | tr -cd '[:alnum:]_.-')"
RAW_BRANCH="codex/review/${SAFE_BRANCH}"

WORKTREE_DIR="${REPO_ROOT}/.codex/worktrees/review-${SAFE_BRANCH}"
if [[ -e "$WORKTREE_DIR" || -L "$WORKTREE_DIR" ]] || \
   git show-ref --verify --quiet "refs/heads/$RAW_BRANCH"; then
  echo "ERROR: Review worktree or branch already exists; preserve it and choose a fresh review."
  exit 1
fi

git worktree add -b "$RAW_BRANCH" "$WORKTREE_DIR" "$REVIEW_REMOTE_NAME/$REVIEW_BRANCH"
if [[ "$NO_MERGE_BASE" != "1" ]]; then
  echo "== Merging ${BASE_REF} into ${RAW_BRANCH} (local-only) =="
  (
    cd "$WORKTREE_DIR"
    git merge --no-edit "$BASE_REF" || {
      echo "ERROR: Merge conflict while merging ${BASE_REF} into ${RAW_BRANCH}."
      echo "Resolve conflicts manually in ${WORKTREE_DIR}."
      exit 2
    }
  )
else
  echo "== Skipping local base merge (--no-merge-base) =="
fi

echo
echo "Prepared for review."
echo "BASE: ${BASE_REF}"
echo "HEAD: ${RAW_BRANCH}"
if [[ -n "$PATHS" ]]; then
  echo "PRIORITY PATHS: $PATHS"
fi
echo
echo "Suggested next commands:"
echo "  git diff --stat ${BASE_REF}...${RAW_BRANCH}"
echo "  git log --oneline --no-merges ${BASE_REF}..${RAW_BRANCH}"
