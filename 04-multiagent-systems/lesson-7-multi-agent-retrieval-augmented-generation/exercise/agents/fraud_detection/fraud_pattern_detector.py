"""Lightweight detector for matching transactions to fraud patterns."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, Iterable, List

import re


class FraudPatternDetector:
    """Compute similarity between transactions and known fraud patterns."""

    def __init__(self, patterns: Iterable[Dict]) -> None:
        self.patterns: List[Dict] = []
        self.update_patterns(patterns)

    def update_patterns(self, patterns: Iterable[Dict]) -> None:
        """Refresh the detector with a new list of pattern definitions."""

        self.patterns = list(patterns)

    def _pattern_to_text(self, pattern: Dict) -> str:
        """Combine the pattern metadata into a single text corpus."""

        signals = " ".join(pattern.get("signals", []))
        text_parts = [pattern.get("id", ""), pattern.get("name", ""), pattern.get("description", ""), signals]
        text = " ".join(part for part in text_parts if part)
        return re.sub(r"\s+", " ", text).strip().lower()

    def detect_fraud_indicators(self, transaction_summary: str, threshold: float = 0.22) -> List[Dict]:
        """Return similarity matches for a transaction summary."""

        if not transaction_summary:
            return []

        summary = re.sub(r"\s+", " ", transaction_summary).strip().lower()

        matches: List[Dict] = []
        for pattern in self.patterns:
            pattern_text = self._pattern_to_text(pattern)
            if not pattern_text:
                continue
            score = SequenceMatcher(None, summary, pattern_text).ratio()
            if float(score) >= threshold:
                matches.append(
                    {
                        "pattern_id": pattern.get("id"),
                        "pattern_name": pattern.get("name"),
                        "similarity_score": float(score),
                        "risk_weight": float(pattern.get("risk_weight", 0.2)),
                    }
                )

        matches.sort(key=lambda item: item["similarity_score"], reverse=True)
        return matches

    @staticmethod
    def compute_similarity_score(matches: List[Dict]) -> float:
        """Aggregate a list of pattern matches into a single risk score."""

        if not matches:
            return 0.0
        scores = [match["similarity_score"] * match.get("risk_weight", 0.2) for match in matches]
        total = sum(scores)
        if total < 0.0:
            return 0.0
        if total > 1.0:
            return 1.0
        return float(total)


