"""
Stream Logger (Phase 4: Real-time Traceability)
"""

import datetime

class StreamLogger:
    def log(self, message: str):
        """Simulates a WebSocket stream to the UI."""
        timestamp = datetime.datetime.utcnow().isoformat()
        print(f"[STREAM {timestamp}]: {message}")

# ---------------------------------------------------------
# CRITICAL: This line MUST exist at the bottom of the file.
# It creates the object that 'orchestrator.py' is trying to import.
# ---------------------------------------------------------
stream_logger = StreamLogger()