
# classifier/base_classifier.py


from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from alerting.incident import RawEvent, Severity

@dataclass
class ClassificationResult:
    
    severity: Severity
    confidence: float
    route: str
    notes: list[str] = field(default_factory=list)


class BaseClassifier(ABC):
    
    #Abstract base for all classifiers.

    @abstractmethod
    def classify(self, event: RawEvent) -> ClassificationResult:
        """
        Evaluate a raw event and return a classification decision.

        Args:
            event: The incoming RawEvent to classify.

        Returns:
            A ClassificationResult with severity, confidence, and reasoning.

        This method must be synchronous and should not mutate the event.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
