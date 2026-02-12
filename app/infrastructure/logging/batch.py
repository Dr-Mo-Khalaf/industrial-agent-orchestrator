"""
Batch Logger (Phase 4: Governance)
"""

import json
import datetime

class BatchLogger:
    def log(self, data: dict):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            **data
        }
        print(f"[AUDIT LOG]: {json.dumps(entry)}")

# ---------------------------------------------------------
# CRITICAL: This line creates the object for main.py
# ---------------------------------------------------------
batch_logger = BatchLogger()