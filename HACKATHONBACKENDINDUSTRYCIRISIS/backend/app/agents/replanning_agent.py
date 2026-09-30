"""
Dynamic Replanning Agent
Triggers multi-agent re-assessment whenever crisis state changes, team availability shifts,
or operators request manual plan updates.
"""
from typing import Dict, Any, List
from .command_agent import CommandAgent


class ReplanningAgent:
    def __init__(self):
        self.command_agent = CommandAgent()

    def replan_crisis(self, incident_id: str, current_version: int, event: Dict[str, Any] = None) -> Dict[str, Any]:
        event_type = event.get("type") if event else "scenario"
        
        if event_type == "scenario":
            # Mid-incident change scenario: Factory B explosion + Hazmat breach + Road blocked
            return self.command_agent.build_plan(
                incident_id=incident_id,
                incidents=[],
                phase=1,
                version=current_version + 1,
                status="pending_approval"
            )
        else:
            # Manual operator replanning
            message = event.get("message", "Operator requested a fresh response plan") if event else "Replanning triggered"
            plan = self.command_agent.build_plan(
                incident_id=incident_id,
                incidents=[],
                phase=0,
                version=current_version + 1,
                status="pending_approval"
            )
            plan["changes"] = [{"type": "manual", "message": message}]
            plan["approval_items"] = [f"Confirm action items for: {message}"]
            return plan
