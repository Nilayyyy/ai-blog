#!/usr/bin/env bash
# Commit the generated draft to a new branch and open a pull request.
# Every network step retries with a growing wait, because GitHub occasionally answers
# a push or an API call with a 500 and succeeds a minute later.
#
# Needs: DRAFT_TITLE, DRAFT_PATH, PR_BODY_FILE, GH_TOKEN (GitHub CLI), and a checkout with push rights.
# Optional: RETRY_ATTEMPTS (default 5), RETRY_SLEEP seconds (default 20), BASE_BRANCH (default main).
set -euo pipefail

: "${DRAFT_TITLE:?DRAFT_TITLE is required}"
: "${DRAFT_PATH:?DRAFT_PATH is required}"
: "${PR_BODY_FILE:?PR_BODY_FILE is required}"

BRANCH="draft/${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
ATTEMPTS="${RETRY_ATTEMPTS:-5}"
BASE_SLEEP="${RETRY_SLEEP:-20}"
BASE_BRANCH="${BASE_BRANCH:-main}"

# retry <description> <command...>
retry() {
  local what="$1"; shift
  local n=1
  until "$@"; do
    if (( n >= ATTEMPTS )); then
      echo "::error::${what} failed after ${n} attempts"
      return 1
    fi
    local wait=$(( BASE_SLEEP * n ))
    echo "::warning::${what} failed (attempt ${n}/${ATTEMPTS}); retrying in ${wait}s"
    sleep "${wait}"
    n=$(( n + 1 ))
  done
}

create_pr() {
  # If an earlier attempt already created the PR, we're done.
  local existing
  existing="$(gh pr list --head "${BRANCH}" --state open --json url --jq '.[0].url // empty' 2>/dev/null || true)"
  if [[ -n "${existing}" ]]; then
    echo "Pull request already exists: ${existing}"
    return 0
  fi
  gh pr create --base "${BASE_BRANCH}" --head "${BRANCH}" \
    --title "Draft: ${DRAFT_TITLE}" --body-file "${PR_BODY_FILE}"
}

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git checkout -B "${BRANCH}"
git add -- "${DRAFT_PATH}"
git commit -m "Add draft: ${DRAFT_TITLE}"

# The branch name is unique to this run, so --force only ever replaces our own earlier attempt.
retry "git push" git push --force origin "${BRANCH}"
retry "open pull request" create_pr
echo "Done: ${BRANCH}"
