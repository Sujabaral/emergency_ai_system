
# alerting/deduplicator.py

import hashlib
import logging
import re
from alerting.incident import RawEvent
from config.settings import settings
from storage.cache import event_cache


logger = logging.getLogger(__name__)


class Deduplicator:
    
    _NOISE_PATTERNS: list[tuple[str, str]] = [
        
        (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?", ""), # ISO-8601 timestamps
        (r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ""), # UUIDs: 
        (r"0x[0-9a-fA-F]+", ""),# Hex memory addresses:
        (r"\b\d+\b", ""), # Standalone numbers 
        (r"\s+", " "), # Collapse multiple whitespace into single space 
    ]

    def __init__(self) -> None:
        # Pre-compile the regex patterns once at init time 
        self._compiled = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self._NOISE_PATTERNS
        ]

    def is_duplicate(self, event: RawEvent) -> bool:
        
        fingerprint = self._generate_fingerprint(event)

        # Check the cache returns None if key is missing or expired
        existing = event_cache.get(fingerprint)

        if existing is not None:
            # We've seen this fingerprint within the dedup window
            logger.debug(
                "Duplicate suppressed | fingerprint=%s source=%s",
                fingerprint[:16] + "...",   # truncate for readability in logs
                event.source
            )
            return True

        # First time seeing this fingerprint so register it
        event_cache.set(
            key=fingerprint,
            value=event.source,  # store source for debugging; value isn't used
            ttl_seconds=settings.DEDUP_WINDOW_SECONDS,
        )

        logger.debug(
            "New unique event registered | fingerprint=%s source=%s ttl=%ds",
            fingerprint[:16] + "...",
            event.source,
            settings.DEDUP_WINDOW_SECONDS,
        )

        return False

    # Private helpers

    def _normalize_message(self, message: str) -> str:
        """
        Strip volatile data from a message so that repeated alerts about the same underlying issue produce the same hash.
        """
        normalized = message.lower().strip()

        for pattern, replacement in self._compiled:
            normalized = pattern.sub(replacement, normalized)

        return normalized.strip()

    def _generate_fingerprint(self, event: RawEvent) -> str:
        """
        Build a stable string that uniquely identifies this class of alert.
        """
        clean_message = self._normalize_message(event.message)
        fingerprint_input = f"{event.source.value}::{clean_message}"
        # SHA-256 gives a fixed-length, collision-resistant identifier
        return hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
