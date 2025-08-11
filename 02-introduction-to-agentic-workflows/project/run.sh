#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

have_cmd() { command -v "$1" >/dev/null 2>&1; }

load_openai_key() {
  if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    if ! have_cmd op; then
      echo "⚠️   1Password CLI 'op' not found. Skipping key load."
      return 0
    fi
    if ! have_cmd jq; then
      echo "⚠️   'jq' not found. Skipping key load."
      return 0
    fi

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

ensure_uv() {
  if ! have_cmd uv; then
    echo "❌  'uv' is required. Please install: https://docs.astral.sh/uv/"
    exit 1
  fi
}

print_usage() {
  python3 - <<'PY'
import os, textwrap, sys
print(textwrap.dedent(f"""
    Usage:
      ./run.sh <command> [args…]

    Commands
      phase1 | p1 [pattern|path ...]
                      Load OPENAI key and run Phase 1 functional scripts.
                      Optionally provide one or more file name patterns or paths
                      to run only matching script(s). Examples:
                        ./run.sh p1 routing
                        ./run.sh p1 phase_1/routing_agent.py
                        ./run.sh p1 knowledge_augmented
      phase1-report | p1-report
                      Run all Phase 1 scripts, capture outputs to files, and
                      generate a Markdown report at reports/phase1/report_phase_1.md
      phase2 | p2    Load OPENAI key (via 1Password if needed) and run Phase 2 tests (or workflow if no tests)
      phase2-report | p2-report
                      Run the Phase 2 workflow, capture outputs to files, and
                      generate a Markdown report at reports/phase2/report_phase_2.md
      package        Generate Phase 1 & Phase 2 reports and zip with reflection.md
                      → submission/submission.zip
      test | tests   Load OPENAI key and run all pytest tests
      help           Show this message
      <anything>     Load OPENAI key and run via 'uv run <anything> [args…]'

    Common shortcuts
      ./run.sh p1
      ./run.sh p2
      ./run.sh test

    Environment
      Python:      {sys.executable}
      OPENAI key:  {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}
  """))
PY
}

run_pytest_patterns() {
  # Run pytest with optional patterns; if none provided, runs full suite
  ensure_uv
  load_openai_key
  echo "🧪 Running pytest ${*:+for patterns: $*}"
  uv run pytest -q "$@"
}

run_phase_tests() {
  # Args: <phase_dir> [fallback_cmd...]
  local phase_dir="$1"; shift || true
  ensure_uv
  load_openai_key
  local pattern="${phase_dir}/*_test.py"
  if [[ "$phase_dir" == "phase_1" ]]; then
    local exec_outdir="executions/phase_1"
    mkdir -p "$exec_outdir"
    if [[ $# -gt 0 ]]; then
      echo "▶️  Running Phase 1 script(s) matching: $*"
      for sel in "$@"; do
        if [[ -f "$sel" ]]; then
          local base_name="$(basename "${sel%.py}")"
          local out_file="$exec_outdir/${base_name}.out"
          echo "Executing: uv run python ./${sel}"
          echo "\$ uv run python ./${sel}" > "$out_file"
          echo "" >> "$out_file"
          uv run python "$sel" >> "$out_file" 2>&1 || { echo "❌ Failed: $sel"; exit 1; }
          echo "Wrote: $out_file"
          continue
        fi
        # Try exact match within phase_dir
        if compgen -G "${phase_dir}/${sel}" > /dev/null; then
          for f in ${phase_dir}/${sel}; do
            local base_name="$(basename "${f%.py}")"
            local out_file="$exec_outdir/${base_name}.out"
            echo "Executing: uv run python ./${f}"
            echo "\$ uv run python ./${f}" > "$out_file"
            echo "" >> "$out_file"
            uv run python "$f" >> "$out_file" 2>&1 || { echo "❌ Failed: $f"; exit 1; }
            echo "Wrote: $out_file"
          done
          continue
        fi
        # Try fuzzy match *sel*.py within phase_dir
        if compgen -G "${phase_dir}/*${sel}*.py" > /dev/null; then
          for f in ${phase_dir}/*${sel}*.py; do
            local base_name="$(basename "${f%.py}")"
            local out_file="$exec_outdir/${base_name}.out"
            echo "Executing: uv run python ./${f}"
            echo "\$ uv run python ./${f}" > "$out_file"
            echo "" >> "$out_file"
            uv run python "$f" >> "$out_file" 2>&1 || { echo "❌ Failed: $f"; exit 1; }
            echo "Wrote: $out_file"
          done
          continue
        fi
        echo "ℹ️  No Phase 1 script matched: $sel"
      done
    else
      # Run functional scripts for Phase 1 in the required order
      echo "▶️  Running Phase 1 functional scripts and saving outputs to $exec_outdir"
      local scripts=(
        direct_prompt_agent.py
        augmented_prompt_agent.py
        knowledge_augmented_prompt_agent.py
        evaluation_agent.py
        routing_agent.py
        action_planning_agent.py
        rag_knowledge_prompt_agent.py
      )
      for s in "${scripts[@]}"; do
        local rel_path="$phase_dir/$s"
        local base_name="${s%.py}"
        local out_file="$exec_outdir/${base_name}.out"
        echo "Executing: uv run python ./${rel_path}"
        echo "\$ uv run python ./${rel_path}" > "$out_file"
        echo "" >> "$out_file"
        uv run python "$rel_path" >> "$out_file" 2>&1 || { echo "❌ Failed: $s"; exit 1; }
        echo "Wrote: $out_file"
      done
    fi
  else
    if compgen -G "$pattern" > /dev/null; then
      run_pytest_patterns "$pattern"
    else
      if [[ $# -gt 0 ]]; then
        echo "ℹ️  No tests found in ${phase_dir}. Running fallback: $*"
        uv run "$@"
      else
        echo "ℹ️  No tests found in ${phase_dir}. Nothing to run."
      fi
    fi
  fi
}

run_phase1_report() {
  ensure_uv
  load_openai_key
  local outdir="reports/phase1"
  mkdir -p "$outdir"
  local report="$outdir/report_phase_1.md"
  echo "📝 Generating $report"
  # Don't abort on a single script failure; continue to next
  set +e

  cat > "$report" <<'MD'
# Phase 1 Functional Test Report

This report contains terminal outputs for all seven Phase 1 scripts. Each section shows the exact command executed, followed by stdout.
MD

  local scripts=(
    direct_prompt_agent.py
    augmented_prompt_agent.py
    knowledge_augmented_prompt_agent.py
    evaluation_agent.py
    routing_agent.py
    action_planning_agent.py
    rag_knowledge_prompt_agent.py
  )

  for s in "${scripts[@]}"; do
    local path="phase_1/$s"
    local title="${s%.py}"
    echo "" >> "$report"
    echo "## ${title}" >> "$report"
    echo "\n$ uv run python ./${path}" >> "$report"
    echo "" >> "$report"
    echo '```text' >> "$report"
    uv run python "$path" >> "$report" 2>&1 || echo "[Command failed]" >> "$report"
    echo '```' >> "$report"
  done

  echo "✅ Report generated: $report"
  # Restore -e
  set -e
}

run_phase2_report() {
  ensure_uv
  load_openai_key
  local outdir="reports/phase2"
  mkdir -p "$outdir"
  local report="$outdir/report_phase_2.md"
  local script="phase_2/agentic_workflow.py"
  echo "📝 Generating $report"
  set +e
  cat > "$report" <<'MD'
# Phase 2 Workflow Report

This report contains the terminal output of the Phase 2 agentic workflow run. The exact command executed is shown followed by stdout.
MD
  echo "" >> "$report"
  echo "$ uv run python ./${script}" >> "$report"
  echo "" >> "$report"
  echo '```text' >> "$report"
  uv run python "$script" >> "$report" 2>&1 || echo "[Command failed]" >> "$report"
  echo '```' >> "$report"
  echo "✅ Report generated: $report"
  set -e
}

package_submission() {
  ensure_uv
  load_openai_key
  run_phase1_report
  run_phase2_report
  local outdir="submission"
  mkdir -p "$outdir"
  local zipfile="$outdir/submission.zip"
  echo "📦 Creating $zipfile"
  rm -f "$zipfile"
  # Include reports and reflection
  zip -r "$zipfile" \
    reports/phase1/report_phase_1.md \
    reports/phase2/report_phase_2.md \
    reflection.md \
    >/dev/null
  echo "✅ Submission bundle ready: $zipfile"
}

run_phase2_execution() {
  ensure_uv
  load_openai_key
  local exec_outdir="executions/phase_2"
  mkdir -p "$exec_outdir"
  local script="phase_2/agentic_workflow.py"
  local out_file="$exec_outdir/agentic_workflow.out"
  echo "Executing: uv run python ./${script}"
  echo "\$ uv run python ./${script}" > "$out_file"
  echo "" >> "$out_file"
  uv run python "$script" >> "$out_file" 2>&1 || { echo "❌ Failed: $script"; exit 1; }
  echo "Wrote: $out_file"
}

cmd="${1:-}"; [[ $# -gt 0 ]] && shift || true

case "${cmd}" in
  p1|phase1)
    run_phase_tests "phase_1" "$@"
    ;;
  p1-report|phase1-report)
    run_phase1_report
    ;;
  p2-report|phase2-report)
    run_phase2_report
    ;;
  p2|phase2)
    run_phase2_execution
    ;;
  package)
    package_submission
    ;;
  test|tests)
    run_pytest_patterns
    ;;
  help|-h|--help|"")
    print_usage
    ;;
  *)
    ensure_uv
    load_openai_key
    echo "▶️  uv run $cmd $*"
    uv run "$cmd" "$@"
    ;;
esac


