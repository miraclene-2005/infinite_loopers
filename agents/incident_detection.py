"""
Agent 1: Incident Detection Agent
Detects and registers an incident from incidents.csv, scenarios dataset, or direct API input.
"""
from typing import Dict, Any, Optional
import uuid
import pandas as pd
from services.data_loader import data_loader

class IncidentDetectionAgent:
    def __init__(self):
        self.data_loader = data_loader

    def detect_incident(
        self,
        incident_id: Optional[str] = None,
        custom_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detects and normalizes an incident record.
        1. If incident_id is given, check incidents.csv first, then scenarios.
        2. If custom_input is provided, parse and override/fill missing values.
        """
        incidents_df = self.data_loader.get_incidents()
        scenarios_df = self.data_loader.get_scenarios()

        record: Dict[str, Any] = {}

        if incident_id:
            # Check incidents.csv
            match_inc = incidents_df[incidents_df["incident_id"].str.upper() == str(incident_id).strip().upper()]
            if not match_inc.empty:
                r = match_inc.iloc[0]
                record = {
                    "incident_id": str(r["incident_id"]),
                    "incident_type": str(r.get("type", "Unknown")),
                    "location": str(r.get("plant", "Industrial Site")),
                    "chemical": str(r.get("chemical", "Unknown")),
                    "people_affected": int(r.get("people_affected", 0)),
                    "fire": bool(int(r.get("fire", 0))),
                    "explosion": bool(int(r.get("explosion", 0))),
                    "severity": int(r.get("severity", 5)),
                    "x": float(r.get("x", 50)),
                    "y": float(r.get("y", 50)),
                    "source": "incidents.csv"
                }
            else:
                # Check scenarios
                match_scen = scenarios_df[scenarios_df["incident_id"].str.upper() == str(incident_id).strip().upper()]
                if not match_scen.empty:
                    s = match_scen.iloc[0]
                    # Map severity string to integer
                    sev_map = {"low": 3, "medium": 5, "high": 8, "critical": 10}
                    sev_str = str(s.get("severity", "Medium")).lower()
                    sev_num = sev_map.get(sev_str, 5)
                    
                    record = {
                        "incident_id": str(s["incident_id"]),
                        "incident_type": str(s.get("incident_type", "Industrial Hazard")),
                        "location": str(s.get("incident_node", "Plant Area")),
                        "chemical": str(s.get("chemical", "Unknown")),
                        "people_affected": int(s.get("evacuation_priority", 1)) * 25,
                        "fire": "fire" in str(s.get("incident_type", "")).lower(),
                        "explosion": "explosion" in str(s.get("incident_type", "")).lower(),
                        "severity": sev_num,
                        "x": 45.0,
                        "y": 45.0,
                        "source": "emergency_incident_scenarios_5000.csv"
                    }

        # Override or populate with custom input
        if custom_input:
            if not record:
                record = {
                    "incident_id": str(custom_input.get("incident_id") or f"INC-{uuid.uuid4().hex[:6].upper()}"),
                    "incident_type": str(custom_input.get("incident_type") or custom_input.get("type") or "Chemical_Leak"),
                    "location": str(custom_input.get("location") or custom_input.get("plant") or "Plant_A"),
                    "chemical": str(custom_input.get("chemical") or "Unknown"),
                    "people_affected": int(custom_input.get("people_affected") or 0),
                    "fire": bool(custom_input.get("fire", False)),
                    "explosion": bool(custom_input.get("explosion", False)),
                    "severity": int(custom_input.get("severity") or 5),
                    "x": float(custom_input.get("x") or 50.0),
                    "y": float(custom_input.get("y") or 50.0),
                    "source": "api_input"
                }
            else:
                for k, v in custom_input.items():
                    if v is not None:
                        record[k] = v

        if not record:
            # Fallback default from first incident in incidents.csv
            first_row = incidents_df.iloc[0]
            record = {
                "incident_id": str(first_row["incident_id"]),
                "incident_type": str(first_row.get("type", "Chemical_Leak")),
                "location": str(first_row.get("plant", "Plant_B")),
                "chemical": str(first_row.get("chemical", "Sulfur_Dioxide")),
                "people_affected": int(first_row.get("people_affected", 25)),
                "fire": bool(int(first_row.get("fire", 0))),
                "explosion": bool(int(first_row.get("explosion", 0))),
                "severity": int(first_row.get("severity", 3)),
                "x": float(first_row.get("x", 74)),
                "y": float(first_row.get("y", 45)),
                "source": "default_fallback"
            }

        # Normalize types
        return {
            "incident_id": record["incident_id"],
            "incident_type": record["incident_type"],
            "location": record["location"],
            "chemical": record["chemical"],
            "people_affected": int(record["people_affected"]),
            "fire": bool(record["fire"]),
            "explosion": bool(record["explosion"]),
            "severity": int(record["severity"]),
            "x": float(record["x"]),
            "y": float(record["y"])
        }
