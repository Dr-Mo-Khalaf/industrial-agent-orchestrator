# tests/unit/test_engineering_safety_report.py

import pytest
from pydantic import ValidationError

from app.schemas.safety  import EngineeringSafetyReport


def test_engineering_safety_report_valid():
    report = EngineeringSafetyReport(
        decision_summary="Proceed with controlled pressure increase.",
        calculated_value=125.5,
        unit="PSI",
        risk_level="LOW",
        manual_references=["Manual A p.12", "Safety Spec §4.3"],
    )

    assert report.risk_level == "LOW"
    assert report.calculated_value == 125.5


def test_engineering_safety_report_invalid_risk_level():
    with pytest.raises(ValidationError):
        EngineeringSafetyReport(
            decision_summary="Abort operation immediately.",
            calculated_value=300.0,
            unit="PSI",
            risk_level="CRITICAL",  # ❌ invalid
            manual_references=["Manual B p.99"],
        )
