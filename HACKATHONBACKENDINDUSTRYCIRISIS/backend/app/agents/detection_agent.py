"""
Detection & Classification Agent
Analyzes telemetry, sensor triggers, CCTV feeds, and manual reports.
Validates incident status, determines severity levels, and flags missing or uncertain data.
"""
from typing import Dict, Any


class DetectionAgent:
    def process_incident(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        itype = raw_data.get("type") or raw_data.get("incident_type") or "Unknown accident"
        location = raw_data.get("location", "Unspecified plant zone")
        severity = raw_data.get("severity", 5)
        
        # Severity labeling
        if severity >= 8:
            sev_label = "critical"
        elif severity >= 6:
            sev_label = "high"
        elif severity >= 4:
            sev_label = "medium"
        else:
            sev_label = "low"

        people = raw_data.get("people_affected", 0)
        source = raw_data.get("source", "Sensor telemetry")
        confirmed = raw_data.get("confirmed", True)

        uncertain_fields = []
        if not confirmed:
            uncertain_fields.append("people_affected")
        if not raw_data.get("chemical") and "chemical" in itype.lower():
            uncertain_fields.append("chemical_composition")

        return {
            "type": itype,
            "location": location,
            "severity": severity,
            "severity_label": sev_label,
            "people_affected": people,
            "source": source,
            "confirmed": confirmed,
            "uncertain_fields": uncertain_fields,
            "fire": raw_data.get("fire", "fire" in itype.lower()),
            "chemical": raw_data.get("chemical", "Solvent/Gas" if "chemical" in itype.lower() else None)
        }
