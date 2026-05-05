"""
Unit tests for L1 (validate) and L2 (classify).
L3 (route) calls S3 so it is covered by the integration smoke test.

Run locally:
    pip install pytest
    pytest tests/unit/ -v
"""
import importlib
import sys
import os
import pytest

# ── path setup ────────────────────────────────────────────────────────────────

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
VALIDATE_DIR = os.path.join(ROOT, "lambdas", "validate")
CLASSIFY_DIR = os.path.join(ROOT, "lambdas", "classify")


def _load(directory):
    """Import lambda_function.py from a given directory."""
    sys.path.insert(0, os.path.abspath(directory))
    import lambda_function
    importlib.reload(lambda_function)
    sys.path.pop(0)
    return lambda_function.lambda_handler


# ── L1 Validate ───────────────────────────────────────────────────────────────

class TestValidate:
    @pytest.fixture(autouse=True)
    def handler(self):
        self.h = _load(VALIDATE_DIR)

    def _ok(self, **overrides):
        base = dict(
            ticket_id="tk-test",
            customer="test@uag.mx",
            priority_score=75,
            description="System is down completely",
        )
        return {**base, **overrides}

    def test_valid_event_passes(self):
        r = self.h(self._ok(), None)
        assert r["validation_passed"] is True
        assert r["validated_by"] == "validate-lambda"

    def test_original_fields_preserved(self):
        r = self.h(self._ok(), None)
        assert r["ticket_id"] == "tk-test"
        assert r["priority_score"] == 75

    def test_missing_score_raises(self):
        e = self._ok()
        del e["priority_score"]
        with pytest.raises(ValueError, match="Missing priority_score"):
            self.h(e, None)

    def test_score_above_100_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            self.h(self._ok(priority_score=150), None)

    def test_score_below_0_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            self.h(self._ok(priority_score=-1), None)

    def test_non_numeric_score_raises(self):
        with pytest.raises(ValueError, match="must be numeric"):
            self.h(self._ok(priority_score="high"), None)

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="description must not be empty"):
            self.h(self._ok(description="   "), None)

    def test_empty_customer_raises(self):
        with pytest.raises(ValueError, match="customer must not be empty"):
            self.h(self._ok(customer=""), None)

    def test_boundary_score_zero(self):
        assert self.h(self._ok(priority_score=0), None)["validation_passed"]

    def test_boundary_score_hundred(self):
        assert self.h(self._ok(priority_score=100), None)["validation_passed"]

    def test_float_score_accepted(self):
        assert self.h(self._ok(priority_score=72.5), None)["validation_passed"]


# ── L2 Classify ───────────────────────────────────────────────────────────────

class TestClassify:
    @pytest.fixture(autouse=True)
    def handler(self):
        self.h = _load(CLASSIFY_DIR)

    def _ev(self, score, desc):
        return dict(
            ticket_id="tk-classify",
            customer="test@uag.mx",
            priority_score=score,
            description=desc,
            validation_passed=True,
        )

    def test_high_score_is_urgent(self):
        assert self.h(self._ev(90, "Routine update"), None)["severity"] == "urgent"

    def test_low_score_is_low(self):
        assert self.h(self._ev(10, "Just a question"), None)["severity"] == "low"

    def test_mid_score_is_normal(self):
        assert self.h(self._ev(55, "Login page is slow"), None)["severity"] == "normal"

    def test_keyword_raises_normal_to_urgent(self):
        r = self.h(self._ev(50, "Complete outage, system is down"), None)
        assert r["severity"] == "urgent"

    def test_keyword_raises_low_to_normal(self):
        r = self.h(self._ev(25, "Something is not working"), None)
        assert r["severity"] == "normal"

    def test_low_keyword_lowers_normal_to_low(self):
        r = self.h(self._ev(42, "I have a question, just a feature request"), None)
        assert r["severity"] == "low"

    def test_severity_field_always_present(self):
        r = self.h(self._ev(60, "Login broken"), None)
        assert r["severity"] in ("urgent", "normal", "low")

    def test_metadata_present(self):
        r = self.h(self._ev(60, "Server crash"), None)
        m = r["classification_metadata"]
        assert "urgent_keywords_found" in m
        assert m["classified_by"] == "classify-lambda"

    def test_original_fields_preserved(self):
        r = self.h(self._ev(70, "Crash"), None)
        assert r["ticket_id"] == "tk-classify"
        assert r["priority_score"] == 70

    def test_class_e2e_example_from_assignment(self):
        """The exact example JSON from the assignment PDF."""
        event = {
            "ticket_id": "tk-042",
            "customer": "student@uag.mx",
            "priority_score": 85,
            "description": "The system has been unresponsive for 2 hours, this is urgent",
        }
        r = self.h(event, None)
        assert r["severity"] == "urgent"
