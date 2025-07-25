#!/usr/bin/env bash
set -e

################################################################################
# Helper: ensure .venv uses Python 3.13
################################################################################
poetry env use "$(command -v python3.13)"

################################################################################
# Helper: fetch OPENAI_API_KEY from 1Password if not already set
################################################################################
load_openai_key() {
  if [[ -z "$OPENAI_API_KEY" ]]; then
    # Sign in if the session isn't active
    if ! op whoami &>/dev/null; then
      echo "🔑  1Password session not found – signing in…"
      eval "$(op signin --account https://my.1password.com)" \
        || { echo "❌  1Password sign-in failed"; exit 1; }
    fi

    echo "🔐  Fetching OPENAI_API_KEY from 1Password item udacity--openai…"
    export OPENAI_API_KEY="$(op item get "udacity--openai" --field "password" --format json --reveal | jq -r ".value")"
  fi
}


################################################################################
# Main dispatcher
################################################################################
cmd="$1"; shift || true
case "$cmd" in
  jn|notebook) load_openai_key; poetry run jupyter notebook "$@";;
  shell)       load_openai_key; poetry run python "$@";;
  test)        load_openai_key; poetry run pytest "$@";;
  "")          load_openai_key; poetry run python - <<'PY'
import os, textwrap, sys
print(textwrap.dedent(f"""
    Usage:
      ./run.sh <command> [args…]

    Common shortcuts
      jn           Launch Jupyter Notebook
      shell        Python REPL in project venv
      test         Run pytest

    Environment
      Python:      {sys.executable}
      OPENAI key:  {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}
"""))
PY
  ;;
  *)            load_openai_key; poetry run "$cmd" "$@";;
esac