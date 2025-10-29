from __future__ import annotations

from agents.fraud_detection.fraud_pattern_detector import FraudPatternDetector


def test_detect_fraud_indicators_returns_sorted_matches() -> None:
    patterns = [
        {
            "id": "FP-A",
            "name": "High Amount",
            "description": "Large transaction amount",
            "signals": ["amount", "high"],
            "risk_weight": 0.4,
        },
        {
            "id": "FP-B",
            "name": "Duplicate Claim",
            "description": "Repeated procedure",
            "signals": ["duplicate", "procedure"],
            "risk_weight": 0.6,
        },
    ]

    detector = FraudPatternDetector(patterns)

    summary = "This duplicate procedure has a high amount and looks suspicious"
    matches = detector.detect_fraud_indicators(summary)

    assert len(matches) == 2
    # Ensure matches are sorted by similarity descending
    assert matches[0]["similarity_score"] >= matches[1]["similarity_score"]

    score = detector.compute_similarity_score(matches)
    assert 0.0 < score <= 1.0

