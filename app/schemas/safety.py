from pydantic import BaseModel, Field
from typing import List

class EngineeringSafetyReport(BaseModel):
    """Structured output for industrial safety validation."""
    decision_summary: str = Field(description="The core recommendation for the engineer.")
    calculated_value: float = Field(description="The numeric result from the engineering tool.")
    unit: str = Field(description="The unit of measurement (e.g., PSI, Celsius).")
    risk_level: str = Field(..., pattern='^(LOW|MEDIUM|HIGH)$', description="Categorization: LOW, MEDIUM, HIGH.")
    manual_references: List[str] = Field(description="List of specific pages or sections from the RAG tool.")
