"""
Command & Response Plan Synthesis Agent (Central Orchestrator)
Synthesizes the outputs of Detection, Risk, Resource, and Evacuation agents
into a unified, versioned response plan with pipeline stages, change logs, and alerts.
"""
from datetime import datetime
from typing import List, Dict, Any

from .detection_agent import DetectionAgent
from .risk_agent import RiskAssessmentAgent
from .resource_agent import ResourceAllocationAgent
from .evacuation_agent import EvacuationAgent


class CommandAgent:
    def __init__(self):
        self.detection = DetectionAgent()
        self.risk = RiskAssessmentAgent()
        self.resource = ResourceAllocationAgent()
        self.evacuation = EvacuationAgent()

    def generate_alerts(self, incident: Dict[str, Any], phase: int = 0) -> List[Dict[str, Any]]:
        t = datetime.now().strftime("%H:%M:%S")
        if phase == 1:
            return [
                {"time": t, "audience": "control_room", "severity": "critical", "message": "New explosion at Factory B. Casualty count unconfirmed."},
                {"time": t, "audience": "control_room", "severity": "high", "message": "Hazmat Team H01 unavailable: suit breach."},
                {"time": t, "audience": "hazmat", "severity": "critical", "message": "H02 redirect to Factory B via R1 and R4. Toxic gas spreading toward Zone C."},
                {"time": t, "audience": "fire", "severity": "high", "message": "F02 to Factory B. F01 hold foam cover at Factory A."},
                {"time": t, "audience": "medical", "severity": "high", "message": "Expect burn and inhalation cases. Route A01 to Metro Care, A02 and A03 to City General."},
                {"time": t, "audience": "public", "severity": "critical", "message": "Zone A and Zone B: evacuate to North gate shelter (S03). Avoid central road."},
            ]
        else:
            return [
                {"time": t, "audience": "control_room", "severity": "critical", "message": f"{incident.get('type', 'Incident')} confirmed at {incident.get('location', 'Site')}. Severity {incident.get('severity', 8)}/10."},
                {"time": t, "audience": "hazmat", "severity": "high", "message": "H01 dispatched to Factory A via R1 and R2. Full encapsulation suits required."},
                {"time": t, "audience": "fire", "severity": "high", "message": "F01 on scene at Factory A. Protect solvent storage to the east."},
                {"time": t, "audience": "medical", "severity": "medium", "message": "A01 staged at Factory A. City General notified: 12 beds available."},
                {"time": t, "audience": "public", "severity": "high", "message": "Zone A workers: evacuate to Admin block assembly point (S01) now."},
            ]

    def build_plan(self, incident_id: str, incidents: List[Dict[str, Any]], phase: int = 0, version: int = 1, status: str = "approved") -> Dict[str, Any]:
        t = datetime.now().strftime("%H:%M:%S")
        is_approval_required = (status == "pending_approval")

        pipeline = [
            {"stage": "Detection", "status": "complete"},
            {"stage": "Assessment", "status": "complete"},
            {"stage": "Replanning", "status": "complete"},
            {"stage": "Approval", "status": "required" if is_approval_required else "approved"}
        ]

        if phase == 1:
            changes = [
                {"type": "new_incident", "message": "New explosion at Factory B"},
                {"type": "resource_failure", "message": "Hazmat Team H01 unavailable"},
                {"type": "route_blocked", "message": "Route R2 blocked by blast zone"},
                {"type": "hazard_spread", "message": "Hazard spread increased toward the south-east"},
            ]
            approval_items = [
                "Public evacuation of Zone B (180 people)",
                "Commit last Hazmat team (H02) to Factory B",
                "Request district Hazmat mutual aid for Factory A",
            ]
            prev_plan = [
                {"category": "Fire", "assignment": "F01 to Factory A", "reason": "Nearest available fire team"},
                {"category": "Hazmat", "assignment": "H01 to Factory A", "reason": "Chemical leak needs Hazmat containment"},
                {"category": "Rescue", "assignment": "R01 to Factory A", "reason": "35 workers inside affected area"},
                {"category": "Route", "assignment": "R1 then R2", "reason": "Shortest open route, 6 min"},
                {"category": "Medical", "assignment": "A01 to City General", "reason": "Burn unit available"},
                {"category": "Evacuation", "assignment": "Zone A", "reason": "Inside predicted spread area"},
                {"category": "Shelter", "assignment": "S01 Admin block", "reason": "Closest shelter with capacity"},
            ]
            curr_plan = [
                {"category": "Fire", "assignment": "F01 at Factory A, F02 to Factory B", "reason": "Two active fires; F01 already on scene"},
                {"category": "Hazmat", "assignment": "H02 to Factory B", "reason": "H01 out of service; ruptured chlorine line is the larger exposure"},
                {"category": "Rescue", "assignment": "R01 at Factory A, R02 to Factory B", "reason": "Workers trapped at both sites"},
                {"category": "Route", "assignment": "R1 then R4", "reason": "R2 blocked; east ring avoids the blast zone"},
                {"category": "Medical", "assignment": "A01 to Metro Care, A02 and A03 to City General", "reason": "City General down to 6 beds; split load"},
                {"category": "Evacuation", "assignment": "Zone A and Zone B", "reason": "Zone B now inside the Factory B blast and gas area"},
                {"category": "Shelter", "assignment": "S03 North gate", "reason": "S01 lies in the new spread path"},
            ]
        else:
            changes = []
            approval_items = []
            prev_plan = []
            curr_plan = [
                {"category": "Fire", "assignment": "F01 to Factory A", "reason": "Nearest available fire team"},
                {"category": "Hazmat", "assignment": "H01 to Factory A", "reason": "Chemical leak needs Hazmat containment"},
                {"category": "Rescue", "assignment": "R01 to Factory A", "reason": "35 workers inside affected area"},
                {"category": "Route", "assignment": "R1 then R2", "reason": "Shortest open route, 6 min"},
                {"category": "Medical", "assignment": "A01 to City General", "reason": "Burn unit available"},
                {"category": "Evacuation", "assignment": "Zone A", "reason": "Inside predicted spread area"},
                {"category": "Shelter", "assignment": "S01 Admin block", "reason": "Closest shelter with capacity"},
            ]

        return {
            "incident_id": incident_id,
            "version": version,
            "status": status,
            "generated_at": t,
            "approved_by": "Control room operator" if status == "approved" else None,
            "approved_at": t if status == "approved" else None,
            "pipeline": pipeline,
            "changes": changes,
            "approval_items": approval_items,
            "previous": prev_plan,
            "current": curr_plan,
        }
