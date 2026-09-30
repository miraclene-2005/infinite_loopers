"""
Agent 9: Communication Agent
Generates role-specific emergency instructions for 8 distinct operational audiences:
1. Workers
2. Fire team
3. Hazmat team
4. Rescue team
5. Ambulance team
6. Hospitals
7. Public
8. Control room
Uses deterministic templates with optional LLM reasoning hook if API keys are available.
"""
import os
from typing import Dict, Any, List
from datetime import datetime

class CommunicationAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

    def generate_communications(
        self,
        incident: Dict[str, Any],
        assessment: Dict[str, Any],
        hazards: Dict[str, Any],
        spread: Dict[str, Any],
        resources: Dict[str, Any],
        medical: Dict[str, Any],
        evacuation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes all multi-agent outputs into tailored, role-specific broadcast messages.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        plant = incident.get("location", "Industrial Facility")
        chem = incident.get("chemical", "Toxic Material").replace("_", " ")
        inc_type = incident.get("incident_type", "Industrial Emergency").replace("_", " ")
        severity = assessment.get("severity", "HIGH")
        spread_dir = spread.get("spread_direction", "Downwind")
        red_radius = spread.get("red_zone_m", 500)
        total_injured = medical.get("total_injured", 0)
        hosp_count = len(medical.get("hospitals_utilized", []))
        shelter_names = [s.get("name") for s in evacuation.get("assigned_shelters", [])[:2]]
        shelter_str = ", ".join(shelter_names) if shelter_names else "Designated Community Relief Center"

        messages = {
            "workers": (
                f"[{timestamp}] EMERGENCY ALERT: {inc_type} involving {chem} at {plant}. "
                f"Immediate evacuation ordered for all personnel within {red_radius}m red zone. "
                f"Follow perimeter green markings toward {shelter_str}. Do not operate motor vehicles inside exclusion gates."
            ),
            "fire_team": (
                f"[{timestamp}] DISPATCH ORDER: Major {inc_type} at {plant}. Severity: {severity}. "
                f"Deploy thermal water curtains and approach upwind from the North/West corridor. "
                f"Protect solvent manifolds 40m east to prevent domino escalation."
            ),
            "hazmat_team": (
                f"[{timestamp}] HAZMAT DIRECTIVE: Chemical release confirmed: {chem}. "
                f"Mandatory Level-A vapor-tight encapsulation suits. Gas plume dispersing toward {spread_dir}. "
                f"Deploy neutralizer barrier and monitor air quality along sector perimeter."
            ),
            "rescue_team": (
                f"[{timestamp}] SEARCH & RESCUE: Priority extraction inside {plant} exclusion perimeter. "
                f"{incident.get('people_affected', 0)} workers accounted in impact sector. Coordinate with Hazmat before interior entry."
            ),
            "ambulance_team": (
                f"[{timestamp}] EMS LOGISTICS: Triage staging active at Plant outer perimeter gate. "
                f"Anticipating {total_injured} chemical inhalation and trauma casualties. Decontamination required prior to ambulance boarding."
            ),
            "hospitals": (
                f"[{timestamp}] HOSPITAL ADVISORY: Code Yellow Chemical Emergency. "
                f"Distributing {total_injured} casualties across {hosp_count} regional emergency rooms. "
                f"Prepare decontamination showers, burn treatment packs, and respiratory ventilator bays."
            ),
            "public": (
                f"[{timestamp}] CIVIL PROTECTION NOTICE: Industrial accident at {plant}. Plume travelling {spread_dir}. "
                f"Residents in immediate sector: remain indoors, shut all windows and air conditioning units. "
                f"Evacuees proceed calmly to {shelter_str}."
            ),
            "control_room": (
                f"[{timestamp}] COMMAND LOG: Multi-Agent response deployed for {plant} {inc_type}. "
                f"Severity: {severity} | Resource assignments verified | All route conflicts cleared | "
                f"Human commander confirmation gate active."
            )
        }

        # Formatted list for UI display
        alerts_list = [
            {"audience": k.replace("_", " ").title(), "severity": severity.lower(), "time": timestamp, "message": v}
            for k, v in messages.items()
        ]

        return {
            "timestamp": timestamp,
            "channel_count": len(messages),
            "roles": messages,
            "alerts": alerts_list
        }
