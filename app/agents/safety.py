# we have to consider Data Privacy (GDPR/PII).
# This ensures that if the Master Agent accidentally includes a name or phone number
# in a log file, the Guardrails library automatically redacts it before it hits the 
# audit logs. This separates our 'Safety Rules' from our 'Python Code', which is 
# a cleaner architecture for compliance."

from guardrails import Guard
import os

# Path to the RAIL file
RAIL_FILE_PATH = os.path.join(os.path.dirname(__file__), "../guardrails/safety_spec.rail")

class SafetyCritic:
    def __init__(self):
        # Initialize the Guard from the RAIL file
        # This gives us PII masking + Schema validation in one step
        try:
            self.guard = Guard.from_rail(RAIL_FILE_PATH)
        except Exception as e:
            raise RuntimeError(f"Failed to load RAIL file: {e}")

    def validate(self, master_agent_draft: str) -> dict:
        """
        Validates the Master Agent's draft.
        Uses RAIL for PII masking and Schema enforcement.
        """
        try:
            # 1. Parse and Validate
            # The Guard will automatically:
            #   - Check if JSON is valid
            #   - Check if risk_level is LOW/MEDIUM/HIGH
            #   - Mask any PII found in the text (e.g., "Call John" -> "Call <PERSON>")
            validation = self.guard.parse(master_agent_draft)

            # 2. Handle Response (Robustly checking for tuple or object)
            if isinstance(validation, tuple):
                validated_data = validation[1] 
            else:
                validated_data = validation.validated_output

            # 3. Convert to dict for the Orchestrator
            if hasattr(validated_data, 'model_dump'):
                data_dict = validated_data.model_dump()
            else:
                data_dict = validated_data

            return {
                "status": "APPROVED",
                "data": data_dict,
                "log": "Passed RAIL validation: Schema valid, PII sanitized."
            }

        except Exception as e:
            # If validation fails (bad schema OR unfixable PII), we reject
            return {
                "status": "REJECTED",
                "reason": f"RAIL Safety Violation: {str(e)}",
                "log": "Rejection triggered by RAIL Guard."
            }