"""Entry point for the Lesson 7 fraud detection exercise."""

from __future__ import annotations

from core import database_service
from demos import run_llm_demos
from workflow import demonstrate_fraud_detection


def main() -> None:
    print("Initializing and populating database...")
    database_service.reset_all()
    database_service.populate_random_demo_data(
        num_patients=20,
        num_claims=50,
        num_complaints=10,
    )
    counts = database_service.get_entity_counts()
    print(
        "Database contains "
        f"{counts['patients']} patients, {counts['claims']} claims, "
        f"and {counts['complaints']} complaints"
    )

    print("\n=== Insurance Claim Fraud Detection Demo ===\n")
    demonstrate_fraud_detection()

    print("\n=== LLM-Powered Demonstrations ===\n")
    demo_results = run_llm_demos()
    for name, result in demo_results.items():
        print(f"\nDemo: {name}")
        deterministic = result.get("deterministic")
        if isinstance(deterministic, dict) and deterministic:
            if "report" in deterministic:
                print(f"Deterministic report: {deterministic['report']}")
            else:
                print(f"Deterministic outcome: {deterministic}")
        else:
            print("Deterministic outcome unavailable.")

        fallback_used = result.get("fallback_used")
        if fallback_used:
            print("Fallback applied: True")
            if result.get("fallback_reason"):
                print(f"Fallback reason: {result['fallback_reason']}")
        logs = result.get("llm_calls", []) or []
        if logs:
            print("LLM tool calls:")
            for log in logs:
                print(f"  - {log.get('name')}: {log.get('arguments')}")
        else:
            print("LLM tool calls: none recorded")


if __name__ == "__main__":
    main()


