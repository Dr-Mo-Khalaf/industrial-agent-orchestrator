"""
Engineering Simulator Tool
Phase 2: Execution & Calculation

Purpose: Provides deterministic physics calculations (e.g., Pressure, Temperature)
to the Master Agent. This ensures mathematical accuracy that LLMs cannot guarantee.
"""

from typing import TypedDict, Optional
import math

class SimulationResult(TypedDict):
    """
    Strict output structure for the Orchestrator.
    Using TypedDict helps with code completion and validation.
    """
    input_flow_rate: float
    estimated_pressure_psi: float
    status: str
    warning: Optional[str]

def calc_pressure_flow(flow_rate: float, viscosity: float = 0.9) -> SimulationResult:
    """
    Simulates pressure dynamics based on flow rate.
    
    Args:
        flow_rate (float): The fluid flow rate in m³/h.
        viscosity (float): Fluid viscosity (default 0.9 for light crude).
        
    Returns:
        SimulationResult: A dictionary containing the calculated pressure.
    """
    
    # 1. Input Validation (Safety First)
    if flow_rate < 0:
        return {
            "input_flow_rate": flow_rate,
            "estimated_pressure_psi": 0.0,
            "status": "ERROR",
            "warning": "Flow rate cannot be negative."
        }

    # 2. Physics Logic (Simplified Darcy-Weisbach / Bernoulli approximation)
    # In a real prodcution app, this would call an external solver like AspenTech or OLGA.
    # P = (f * (L/D) * (rho * v^2) / 2)
    # For the prototype, we use a simplified polynomial relation.
    
    # Mock constants
    FRICTION_FACTOR = 0.02
    PIPE_DIAMETER_M = 0.1
    FLUID_DENSITY_KG_M3 = 850
    
    # Convert flow rate (m³/h) to velocity (m/s)
    area = math.pi * (PIPE_DIAMETER_M / 2) ** 2
    velocity = flow_rate / (area * 3600) # 3600 sec/hr
    
    # Calculate Pressure Drop (Delta P)
    # dP = f * (1/D) * (0.5 * rho * v^2)
    delta_p_pascal = FRICTION_FACTOR * (1 / PIPE_DIAMETER_M) * (0.5 * FLUID_DENSITY_KG_M3 * velocity**2)
    delta_p_psi = delta_p_pascal * 0.000145038 # Convert Pa to PSI
    
    # Add a baseline pressure
    TOTAL_PRESSURE_PSI = 1000 + delta_p_psi
    
    # 3. Status Logic
    status = "NOMINAL"
    warning = None
    
    if TOTAL_PRESSURE_PSI > 1200:
        status = "HIGH_PRESSURE_WARNING"
        warning = "Approaching relief valve threshold."

    return {
        "input_flow_rate": flow_rate,
        "estimated_pressure_psi": round(TOTAL_PRESSURE_PSI, 2),
        "status": status,
        "warning": warning
    }

# --- Helper function to allow direct execution for testing ---
if __name__ == "__main__":
    result = calc_pressure_flow(200)
    print(f"Simulation Result: {result}")