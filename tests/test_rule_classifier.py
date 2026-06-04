import unittest
from datetime import datetime
from classifier.rule_classifier import RuleClassifier
from alerting.incident import RawEvent, Severity


class DummySource:
    def __init__(self, value):
        self.value = value


class TestRuleClassifier(unittest.TestCase):

    def setUp(self):
        self.classifier = RuleClassifier()

    def make_event(self, msg, source="logs"):
        return RawEvent(
            message=msg,
            source=DummySource(source),
            timestamp = datetime.utcnow()
            
        )

    # -------------------------
    # P1 TESTS (critical)
    # -------------------------
    def test_p1_fatal_crash(self):
        event = self.make_event(
            "fatal crash database down oom outage"
        )
        result = self.classifier.classify(event)

        self.assertEqual(result.severity, Severity.P1)

    def test_p1_security_breach_pattern(self):
        event = self.make_event(
            "system security breach detected exploit vulnerability"
        )
        result = self.classifier.classify(event)

        self.assertEqual(result.severity, Severity.P1)

    # -------------------------
    # P2 TESTS (high severity)
    # -------------------------
    def test_p2_error_exception(self):
        event = self.make_event(
            "error exception connection failed timeout"
        )
        result = self.classifier.classify(event)

        self.assertIn(result.severity, [Severity.P2, Severity.P3])

    def test_p2_connection_refused_pattern(self):
        event = self.make_event(
            "connection refused error occurred"
        )
        result = self.classifier.classify(event)

        self.assertIn(result.severity, [Severity.P2, Severity.P3])

    # -------------------------
    # P3 TESTS (warning level)
    # -------------------------
    def test_p3_warning_latency(self):
        event = self.make_event(
            "warning slow latency degraded response time high"
        )
        result = self.classifier.classify(event)

        self.assertIn(result.severity, [Severity.P3, Severity.P4])

    # -------------------------
    # P4 TESTS (default)
    # -------------------------
    def test_p4_clean_event(self):
        event = self.make_event(
            "user deployed new feature successfully"
        )
        result = self.classifier.classify(event)

        self.assertEqual(result.severity, Severity.P4)

    def test_p4_low_signal(self):
        event = self.make_event(
            "info scheduled maintenance notice"
        )
        result = self.classifier.classify(event)

        self.assertEqual(result.severity, Severity.P4)

    # -------------------------
    # SOURCE WEIGHT TESTS
    # -------------------------
    def test_source_weight_effect(self):
        high_source = self.make_event("error crash", source="sentry")
        low_source = self.make_event("error crash", source="unknown")

        r1 = self.classifier.classify(high_source)
        r2 = self.classifier.classify(low_source)

        # higher trust source should not score lower
        self.assertGreaterEqual(r1.confidence, r2.confidence)

    # -------------------------
    # EDGE CASES
    # -------------------------
    def test_empty_message(self):
        event = self.make_event("")
        result = self.classifier.classify(event)

        self.assertEqual(result.severity, Severity.P4)

    def test_notes_exist(self):
        event = self.make_event("fatal crash database down")
        result = self.classifier.classify(event)

        self.assertTrue(len(result.notes) > 0)


if __name__ == "__main__":
    unittest.main()