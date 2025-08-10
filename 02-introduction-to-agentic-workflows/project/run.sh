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
    if [[ $# -gt 0 ]]; then
      echo "▶️  Running Phase 1 script(s) matching: $*"
      for sel in "$@"; do
        if [[ -f "$sel" ]]; then
          echo "----- $sel -----"
          uv run python "$sel" || { echo "❌ Failed: $sel"; exit 1; }
          continue
        fi
        # Try exact match within phase_dir
        if compgen -G "${phase_dir}/${sel}" > /dev/null; then
          for f in ${phase_dir}/${sel}; do
            echo "----- $f -----"
            uv run python "$f" || { echo "❌ Failed: $f"; exit 1; }
          done
          continue
        fi
        # Try fuzzy match *sel*.py within phase_dir
        if compgen -G "${phase_dir}/*${sel}*.py" > /dev/null; then
          for f in ${phase_dir}/*${sel}*.py; do
            echo "----- $f -----"
            uv run python "$f" || { echo "❌ Failed: $f"; exit 1; }
          done
          continue
        fi
        echo "ℹ️  No Phase 1 script matched: $sel"
      done
    else
      # Run functional scripts for Phase 1 in the required order
      echo "▶️  Running Phase 1 functional scripts"
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
        echo "----- $phase_dir/$s -----"
        uv run python "$phase_dir/$s" || { echo "❌ Failed: $s"; exit 1; }
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
  # Don't abort on a single script failure; capture exit codes instead
  set +e
  local scripts=(
    direct_prompt_agent.py
    augmented_prompt_agent.py
    knowledge_augmented_prompt_agent.py
    evaluation_agent.py
    routing_agent.py
    action_planning_agent.py
    rag_knowledge_prompt_agent.py
  )
  echo "▶️  Running Phase 1 scripts and capturing outputs in $outdir"
  for s in "${scripts[@]}"; do
    local path="phase_1/$s"
    echo "----- $path -----"
    # capture stdout and stderr to separate files
    local base="$outdir/${s%.py}"
    uv run python "$path" >"${base}.out.txt" 2>"${base}.err.txt"
    local ec=$?
    echo "$ec" >"${base}.exitcode"
    # mirror output to console for visibility
    cat "${base}.out.txt"
    if [[ -s "${base}.err.txt" ]]; then
      echo "[stderr captured: ${base}.err.txt]" >&2
      cat "${base}.err.txt" >&2
    fi
  done

  local report="$outdir/report_phase_1.md"
  echo "📝 Generating $report"
  cat > "$report" <<'MD'
# Phase 1 Functional Test Report

This report contains terminal outputs for all seven Phase 1 scripts, aligned with the rubric requirements.

MD

  # Append sections per script with prompts context
  {
    echo ""
    echo "## DirectPromptAgent"
    echo "- Prompt used: \"What is the Capital of France?\""
    echo "- Expectation: Explains it used general model knowledge."
    echo ""
    echo "Output:"
    echo ""
    echo '```'
    cat "$outdir/direct_prompt_agent.out.txt"
    echo '```'
    echo "Exit code: $(cat "$outdir/direct_prompt_agent.exitcode")"
    if [[ -s "$outdir/direct_prompt_agent.err.txt" ]]; then
      echo "Stderr:"
      echo '```'
      cat "$outdir/direct_prompt_agent.err.txt"
      echo '```'
    fi

    echo ""
    echo "## AugmentedPromptAgent"
    echo "- Prompt used: \"What is the capital of France?\""
    echo "- Expectation: Notes about persona impact and knowledge source."
    echo ""
    echo "Output:"
    echo ""
    echo '```'
    cat "$outdir/augmented_prompt_agent.out.txt"
    echo '```'
    echo "Exit code: $(cat "$outdir/augmented_prompt_agent.exitcode")"
    if [[ -s "$outdir/augmented_prompt_agent.err.txt" ]]; then
      echo ""
      echo "Stderr:"
      echo '```'
      cat "$outdir/augmented_prompt_agent.err.txt"
      echo '```'
    fi

    echo ""
    echo "## KnowledgeAugmentedPromptAgent"
    echo "- Prompt used: \"What is the capital of France?\""
    echo "- Expectation: Confirms use of provided knowledge (London vs common Paris)."
    echo ""
    echo "Output:"
    echo ""
    echo '```'
    cat "$outdir/knowledge_augmented_prompt_agent.out.txt"
    echo '```'
    echo "Exit code: $(cat "$outdir/knowledge_augmented_prompt_agent.exitcode")"
    if [[ -s "$outdir/knowledge_augmented_prompt_agent.err.txt" ]]; then
      echo ""
      echo "Stderr:"
      echo '```'
      cat "$outdir/knowledge_augmented_prompt_agent.err.txt"
      echo '```'
    fi

    echo ""
    echo "## EvaluationAgent"
    echo "- Prompt used: \"What is the capital of France?\""
    echo "- Expectation: Returns dict with final_response, evaluation, iterations."
    echo ""
    echo "Output:"
    echo '```'
    cat "$outdir/evaluation_agent.out.txt"
    echo '```'
    echo "Exit code: $(cat "$outdir/evaluation_agent.exitcode")"
    if [[ -s "$outdir/evaluation_agent.err.txt" ]]; then
      echo ""
      echo "Stderr:"
      echo '```'
      cat "$outdir/evaluation_agent.err.txt"
      echo '```'
    fi

    echo ""
    echo "## RoutingAgent"
    echo "- Prompts used:"
    echo "  - \"Tell me about the history of Rome, Texas\""
    echo "  - \"Tell me about the history of Rome, Italy\""
    echo "  - \"One story takes 2 days, and there are 20 stories\""
    echo "- Expectation: Routes to Texas, Europe, Math respectively and prints responses."
    echo ""
    echo "Output:"
    echo '```'
    cat "$outdir/routing_agent.out.txt"
    echo '```'
    echo "Exit code: $(cat "$outdir/routing_agent.exitcode")"
    if [[ -s "$outdir/routing_agent.err.txt" ]]; then
      echo ""
      echo "Stderr:"
      echo '```'
      cat "$outdir/routing_agent.err.txt"
      echo '```'
    fi

    echo ""
    echo "## ActionPlanningAgent"
    echo "- Prompt used: \"One morning I wanted to have scrambled eggs\""
    echo "- Expectation: Returns a clean list of steps."
    echo ""
    echo "Output:"
    echo '```'
    cat "$outdir/action_planning_agent.out.txt"
    echo '```'
    echo "Exit code: $(cat "$outdir/action_planning_agent.exitcode")"
    if [[ -s "$outdir/action_planning_agent.err.txt" ]]; then
      echo ""
      echo "Stderr:"
      echo '```'
      cat "$outdir/action_planning_agent.err.txt"
      echo '```'
    fi

    echo ""
    echo "## RAGKnowledgePromptAgent (provided)"
    echo "- Prompt used: \"What is the podcast that Clara hosts about?\""
    echo "- Expectation: Uses retrieved knowledge; shows 'Used RAG knowledge?' check."
    echo ""
    echo "Output:"
    echo '```'
    cat "$outdir/rag_knowledge_prompt_agent.out.txt"
    echo '```'
    echo "Exit code: $(cat "$outdir/rag_knowledge_prompt_agent.exitcode")"
    if [[ -s "$outdir/rag_knowledge_prompt_agent.err.txt" ]]; then
      echo ""
      echo "Stderr:"
      echo '```'
      cat "$outdir/rag_knowledge_prompt_agent.err.txt"
      echo '```'
    fi
  } >> "$report"

  echo "✅ Report generated: $report"
  # Restore -e
  set -e
}

run_phase2_report() {
  ensure_uv
  load_openai_key
  local outdir="reports/phase2"
  mkdir -p "$outdir"
  local script="phase_2/agentic_workflow.py"
  echo "▶️  Running Phase 2 workflow and capturing outputs in $outdir"
  uv run python "$script" >"$outdir/agentic_workflow.out.txt" 2>"$outdir/agentic_workflow.err.txt"
  echo "$?" >"$outdir/agentic_workflow.exitcode"

  local report="$outdir/report_phase_2.md"
  echo "📝 Generating $report"
  cat > "$report" <<'MD'
# Phase 2 Workflow Report

This report contains the terminal output of the Phase 2 agentic workflow run, aligned with the rubric:

- Imports and instantiates ActionPlanningAgent, KnowledgeAugmentedPromptAgent(s), EvaluationAgent(s), and RoutingAgent
- Loads Product-Spec-Email-Router.txt and builds workflow knowledge
- Executes the workflow: extracts steps, routes each to the appropriate role via routing, evaluates, and prints final result

## Workflow Output

### Stdout
```
MD
  cat "$outdir/agentic_workflow.out.txt" >> "$report"
  echo '```' >> "$report"

  echo "" >> "$report"
  echo "### Exit code" >> "$report"
  echo "$(cat "$outdir/agentic_workflow.exitcode")" >> "$report"

  if [[ -s "$outdir/agentic_workflow.err.txt" ]]; then
    echo "" >> "$report"
    echo "### Stderr" >> "$report"
    echo '```' >> "$report"
    cat "$outdir/agentic_workflow.err.txt" >> "$report"
    echo '```' >> "$report"
  fi

  echo "✅ Report generated: $report"
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
    run_phase_tests "phase_2" python phase_2/agentic_workflow.py
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


