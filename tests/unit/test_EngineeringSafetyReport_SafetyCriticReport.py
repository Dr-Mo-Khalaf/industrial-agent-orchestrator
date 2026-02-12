"""
Test Suite for: Phase 3 - Industrial Safety (The Critic)
File: /tests/test_safety.py

Purpose:
    Validates that the SafetyCritic correctly interprets the Master Agent's draft
    and enforces the EngineeringSafetyReport schema (e.g., Risk Levels).
"""

import pytest
from app.agents.safety import validate_critic_output, SafetyCritic
from app.schemas.safety import EngineeringSafetyReport
from guardrails import Guard

# --- 1. Test Fixtures (Mocking the "Safety Rules") ---

@pytest.fixture
def safety_critic():
    """Initializes the SafetyCritic instance."""
    return SafetyCritic()

@pytest.fixture
def valid_draft_json():
    """A perfect, compliant response from the Master Agent."""
    return """
    {
        "summary": "Pressure is within safe operating limits.",
        "risk_level": "LOW",
        "recommended_action": "Proceed with standard monitoring.",
        "is_safe": true
    }
    """

@pytest.fixture
def high_risk_draft_json():
    """A compliant JSON, but flags a HIGH risk scenario."""
    return """
    {
        "summary": "Pressure exceeds maximum allowable limits.",
        "risk_level": "HIGH",
        "recommended_action": "IMMEDIATE SHUTDOWN required.",
        "is_safe": false
    }
    """

@pytest.fixture
def malformed_draft_text():
    """A non-JSON response (Hallucination or formatting error)."""
    return "The pressure looks okay, just go ahead and open the valve."

@pytest.fixture
def invalid_schema_draft():
    """JSON format, but wrong data types (e.g., risk_level is not LOW/MEDIUM/HIGH)."""
    return """
    {
        "summary": "Unknown status.",
        "risk_level": "SUPER_HIGH", 
        "recommended_action": "Check manually.",
        "is_safe": "maybe"
    }
    """

# --- 2. Test Cases ---

class TestSafetyCritic:
    
    def test_happy_path_low_risk(self, safety_critic, valid_draft_json):
        """
        SCENARIO: Master Agent returns a valid, safe JSON.
        EXPECTED: Critic validates successfully and returns APPROVED.
        """
        result = safety_critic.validate(valid_draft_json)
        
        assert result["status"] == "APPROVED"
        assert result["data"]["risk_level"] == "LOW"
        assert result["data"]["is_safe"] is True
        assert "Safety constraints verified" in result["log"]

    def test_happy_path_high_risk_detection(self, safety_critic, high_risk_draft_json):
        """
        SCENARIO: Master Agent detects a HIGH risk situation correctly.
        EXPECTED: Critic validates the SCHEMA (it is valid JSON), 
                  but logic elsewhere might handle the 'is_safe=False'.
                  *Note: The Critic validates structure, the Orchestrator handles the action.*
        """
        result = safety_critic.validate(high_risk_draft_json)
        
        # The Schema is valid, so the Critic "Approves" the data structure.
        # The Orchestrator will see "is_safe": false and loop back or alert.
        assert result["status"] == "APPROVED" 
        assert result["data"]["risk_level"] == "HIGH"
        assert result["data"]["is_safe"] is False

    def test_malformed_input_rejection(self, safety_critic, malformed_draft_text):
        """
        SCENARIO: Master Agent hallucinates plain text instead of JSON.
        EXPECTED: Guardrails fails parsing -> REJECTED.
        """
        result = safety_critic.validate(malformed_draft_text)
        
        assert result["status"] == "REJECTED"
        assert "Safety schema violation" in result["reason"]
        assert "re-synthesis" in result["log"]

    def test_schema_violation_rejection(self, safety_critic, invalid_schema_draft):
        """
        SCENARIO: Master Agent uses an invalid Enum value ("SUPER_HIGH").
        EXPECTED: Guardrails Pydantic validation fails -> REJECTED.
        """
        result = safety_critic.validate(invalid_schema_draft)
        
        assert result["status"] == "REJECTED"
        # Pydantic usually raises a ValidationError for literal enums
        assert "literal" in result["reason"].lower() or "validation" in result["reason"].lower()
