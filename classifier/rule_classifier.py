# classifier/rule_classifier.py

import logging
import re
from pathlib import Path
from typing import Any
import yaml
from alerting.incident import RawEvent, Severity
from classifier.base_classifier import BaseClassifier, ClassificationResult
from config.settings import settings

logger = logging.getLogger(__name__)

class RuleClassifier(BaseClassifier):

    # How much each match type contributes to the raw score
    KEYWORD_MATCH_BONUS: float = 0.10
    PATTERN_MATCH_BONUS: float = 0.15

    def __init__(self) -> None:
        # Load and parse the YAML config once at startup
        rules_data = self._load_rules(settings.RULES_FILE_PATH)

        # Pull out the two top-level sections
        self._severity_config: dict[str, Any] = rules_data["severity_levels"]
        self._source_weights: dict[str, float] = rules_data["source_weights"]

        # Pre-compile all regex patterns so we pay the compilation cost once
        self._compiled_rules = self._compile_rules(self._severity_config)

        logger.info(
            "RuleClassifier loaded | levels=%s",
            list(self._compiled_rules.keys())
        )

    # BaseClassifier interface
    def classify(self, event: RawEvent) -> ClassificationResult:

        notes: list[str] = []
        message_lower = event.message.lower()

        # Look up the trust weight for this source, fallback to unknown if not found
        source_key = event.source.value
        source_weight = self._source_weights.get(
            source_key,
            self._source_weights.get("unknown", 0.3)
        )
        notes.append(f"Source '{source_key}' base weight: {source_weight:.2f}")

        # Walk severity tiers from highest to lowest
        severity_order = ["P1", "P2", "P3", "P4"]

        for level_name in severity_order:
            if level_name not in self._compiled_rules:
                continue

            level_config = self._compiled_rules[level_name]
            threshold    = level_config["threshold"]

            # Count keyword matches
            matched_keywords = [
                kw for kw in level_config["keywords"]
                if kw in message_lower
            ]
            for kw in matched_keywords:
                notes.append(f"[{level_name}] Keyword matched: '{kw}'")

            # Count pattern matches
            matched_patterns = []
            for pattern_str, compiled_pattern in level_config["patterns"]:
                if compiled_pattern.search(message_lower):
                    matched_patterns.append(pattern_str)
                    notes.append(f"[{level_name}] Pattern matched: '{pattern_str}'")

            # Build the raw score from matches only.
            # source_weight is NOT included here — it only affects confidence output,
            # not the threshold decision. Including it in raw_score would mean even
            # zero-match messages score above zero, causing low-severity events to
            # incorrectly trigger higher severity levels.
            raw_score = (
                len(matched_keywords) * self.KEYWORD_MATCH_BONUS
                + len(matched_patterns) * self.PATTERN_MATCH_BONUS
            )

            # Normalize against the theoretical maximum for this level
            normalized_score = self._normalize_score(
                raw_score=raw_score,
                total_keywords=len(level_config["keywords"]),
                total_patterns=len(level_config["patterns"]),
                level_name=level_name,
                notes=notes,
            )

            # Threshold check
            if normalized_score >= threshold:
                # Blend normalized match score with source trust for final confidence
                confidence = round(normalized_score * source_weight, 3)
                notes.append(
                    f"Normalized {normalized_score:.3f} >= threshold {threshold}"
                    f" → classified as {level_name} (confidence={confidence})"
                )
                return ClassificationResult(
                    severity=Severity(level_name),
                    confidence=confidence,
                    route="rule_classifier",
                    notes=notes,
                )

        notes.append("No threshold met — defaulting to P4")
        return ClassificationResult(
            severity=Severity.P4,
            confidence=round(source_weight, 3),  # at least shows source trust
            route="rule_classifier",
            notes=notes,
        )

    # Private helpers
    def _normalize_score(
        self,
        raw_score: float,
        total_keywords: int,
        total_patterns: int,
        level_name: str,
        notes: list[str],
    ) -> float:
        """Normalize raw_score against the maximum possible score for this level."""
        max_possible = (
            total_keywords * self.KEYWORD_MATCH_BONUS
            + total_patterns * self.PATTERN_MATCH_BONUS
        )

        if max_possible == 0:
            notes.append(f"[{level_name}] max_possible=0, returning 0.0")
            return 0.0

        normalized = raw_score / max_possible

        notes.append(
            f"[{level_name}] raw={raw_score:.3f} / max_possible={max_possible:.3f}"
            f" = normalized={normalized:.3f}"
        )
        return max(0.0, min(normalized, 1.0))

    def _load_rules(self, rules_path: str) -> dict[str, Any]:
        """Read and parse the YAML rules file."""
        path = Path(rules_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Rules file not found at: {rules_path}\n"
                f"Check the RULES_FILE_PATH setting in config/settings.py"
            )

        with open(path, "r") as fh:
            data = yaml.safe_load(fh)

        logger.debug("Rules file loaded from: %s", rules_path)
        return data

    def _compile_rules(
        self, severity_config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Walk through the severity config from YAML, pre-compile every regex
        pattern string to a compiled pattern object.
        """
        compiled: dict[str, Any] = {}

        for level_name, level_data in severity_config.items():
            compiled_patterns = []

            for pattern_str in level_data.get("patterns", []):
                try:
                    compiled_patterns.append(
                        (pattern_str, re.compile(pattern_str, re.IGNORECASE))
                    )
                except re.error as exc:
                    logger.warning(
                        "Invalid regex in YAML for level %s: '%s' — %s",
                        level_name, pattern_str, exc
                    )

            keywords = [kw.lower() for kw in level_data.get("keywords", [])]

            compiled[level_name] = {
                "threshold": level_data["threshold"],
                "keywords":  keywords,
                # patterns is a list of (original_string, compiled_pattern) tuples
                "patterns":  compiled_patterns,
            }

        return compiled
