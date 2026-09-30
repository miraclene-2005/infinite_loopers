"""
Agent 10: Command & Replanning Agent (Central Orchestrator)
Coordinates all specialized agents in sequence to produce a unified response plan,
and dynamically replans when conditions change (new explosions, resource failures, road blocks).
"""
from typing import Dict, Any, Optional, Set, List
from datetime import datetime

from agents.incident_detection import IncidentDetectionAgent
from agents.incident_assessment import IncidentAssessmentAgent
from agents.hazard_risk import HazardRiskAgent
from agents.hazard_spread import HazardSpreadAgent
from agents.resource_allocation import ResourceAllocationAgent
from agents.medical_response import MedicalResponseAgent
from agents.route_logistics import RouteLogisticsAgent
from agents.evacuation_shelter import EvacuationShelterAgent
from agents.communication import CommunicationAgent

class CommandReplanningAgent:
    def __init__(self):
        self.detection_agent = IncidentDetectionAgent()
        self.assessment_agent = IncidentAssessmentAgent()
        self.hazard_agent = HazardRiskAgent()
        self.spread_agent = HazardSpreadAgent()
        self.resource_agent = ResourceAllocationAgent()
        self.medical_agent = MedicalResponseAgent()
        self.route_agent = RouteLogisticsAgent()
        self.evacuation_agent = EvacuationShelterAgent()
        self.communication_agent = CommunicationAgent()

        # Shared state storage for active incidents
        self.active_plans: Dict[str, Dict[str, Any]] = {}

    def run_initial_response(
        self,
        incident_id: Optional[str] = None,
        custom_input: Optional[Dict[str, Any]] = None,
        environmental_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes the initial linear multi-agent workflow:
        Detection -> Assessment -> Hazard -> Spread -> Resource -> Medical -> Route -> Evacuation -> Communication
        """
        # 1. Detection
        incident = self.detection_agent.detect_incident(incident_id, custom_input)
        inc_id = incident["incident_id"]

        # 2. Assessment
        assessment = self.assessment_agent.assess(incident)

        # 3. Hazard & Risk
        hazards = self.hazard_agent.assess_hazards(incident, assessment)

        # 4. Spread Prediction
        spread = self.spread_agent.predict_spread(incident, environmental_params)

        # 5. Resource Allocation
        resources = self.resource_agent.allocate(incident, hazards)

        # 6. Medical Response
        medical = self.medical_agent.coordinate_medical_response(incident, resources)

        # 7. Route & Logistics
        routes = self.route_agent.plan_routes(incident, spread)

        # 8. Evacuation & Shelter
        evacuation = self.evacuation_agent.plan_evacuation(incident, spread)

        # 9. Communication
        communications = self.communication_agent.generate_communications(
            incident, assessment, hazards, spread, resources, medical, evacuation
        )

        response_plan = {
            "incident": incident,
            "assessment": assessment,
            "severity": assessment, # alias for frontend compatibility
            "hazards": hazards,
            "spread_prediction": spread,
            "spread": spread, # alias
            "resources": resources.get("assignments", []),
            "resource_summary": resources,
            "medical": medical,
            "routes": routes.get("routes", []),
            "routes_summary": routes,
            "evacuation": evacuation,
            "communications": communications,
            "replanning": {
                "is_replanned": False,
                "version": 1,
                "status": "APPROVED",
                "changes_detected": [],
                "affected_decisions": []
            },
            "timestamp": datetime.now().isoformat()
        }

        self.active_plans[inc_id] = response_plan
        return response_plan

    def replan(
        self,
        incident_id: str,
        new_events: Optional[List[str]] = None,
        unavailable_resources: Optional[List[str]] = None,
        newly_blocked_roads: Optional[List[str]] = None,
        environmental_updates: Optional[Dict[str, Any]] = None,
        escalate_severity: bool = False
    ) -> Dict[str, Any]:
        """
        Dynamic Replanning workflow:
        1. Identifies what changed
        2. Re-assesses severity if escalated or new explosion reported
        3. Re-predicts spread if environmental conditions changed
        4. Re-allocates resources excluding newly failed/unavailable units
        5. Re-calculates medical distribution if casualty numbers increased
        6. Re-routes logistics around newly blocked roads
        7. Re-plans evacuation zones and shelters
        8. Generates updated communication alerts
        """
        existing = self.active_plans.get(incident_id)
        if not existing:
            # Fall back to initial response first
            existing = self.run_initial_response(incident_id)

        incident = dict(existing["incident"])
        changes_detected: List[str] = list(new_events or [])
        affected_decisions: List[str] = []

        # 1. Check for incident escalation (e.g. new explosion)
        has_new_explosion = any("explosion" in str(e).lower() for e in changes_detected)
        if has_new_explosion or escalate_severity:
            incident["explosion"] = True
            incident["severity"] = min(10, incident.get("severity", 5) + 2)
            incident["people_affected"] = int(incident.get("people_affected", 0)) + 35
            affected_decisions.append("Incident severity escalated; casualty count increased.")

        # Re-assess
        assessment = self.assessment_agent.assess(incident)
        hazards = self.hazard_agent.assess_hazards(incident, assessment)

        # 2. Spread recalculation
        if environmental_updates or has_new_explosion:
            spread = self.spread_agent.predict_spread(incident, environmental_updates)
            affected_decisions.append("Hazard spread recalculated with new environmental/source inputs.")
        else:
            spread = existing.get("spread_prediction", existing.get("spread"))

        # 3. Resource reallocation
        unavail_set: Set[str] = set(unavailable_resources or [])
        if unavail_set:
            changes_detected.append(f"Resource failure/unavailability: {', '.join(unavail_set)}")
            affected_decisions.append("Resource assignments recalculated to substitute unavailable response teams.")

        resources = self.resource_agent.allocate(
            incident,
            hazards,
            unavailable_resource_ids=unavail_set
        )

        # 4. Medical reallocation
        medical = self.medical_agent.coordinate_medical_response(incident, resources)

        # 5. Route recalculation
        blocked_roads_set: Set[str] = set(newly_blocked_roads or [])
        if blocked_roads_set:
            changes_detected.append(f"Road network obstruction: {', '.join(blocked_roads_set)}")
            affected_decisions.append("Emergency route replanned: rerouted around blocked segments.")

        routes = self.route_agent.plan_routes(
            incident,
            spread,
            blocked_roads=blocked_roads_set
        )

        # 6. Evacuation replanning
        evacuation = self.evacuation_agent.plan_evacuation(incident, spread)

        # 7. Communications update
        communications = self.communication_agent.generate_communications(
            incident, assessment, hazards, spread, resources, medical, evacuation
        )

        prev_version = existing.get("replanning", {}).get("version", 1)
        new_version = prev_version + 1

        revised_plan = {
            "incident": incident,
            "assessment": assessment,
            "severity": assessment,
            "hazards": hazards,
            "spread_prediction": spread,
            "spread": spread,
            "resources": resources.get("assignments", []),
            "resource_summary": resources,
            "medical": medical,
            "routes": routes.get("routes", []),
            "routes_summary": routes,
            "evacuation": evacuation,
            "communications": communications,
            "replanning": {
                "is_replanned": True,
                "version": new_version,
                "status": "REQUIRES_HUMAN_APPROVAL",
                "changes_detected": changes_detected,
                "affected_decisions": affected_decisions,
                "previous_version": prev_version
            },
            "timestamp": datetime.now().isoformat()
        }

        self.active_plans[incident_id] = revised_plan
        return revised_plan

command_agent = CommandReplanningAgent()
