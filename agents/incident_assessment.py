"""
Agent 2: Incident Assessment Agent
Evaluates severity, priority, and recommended actions using rule-based reasoning
with extensible ML hooks.
"""
from typing import Dict, Any

class IncidentAssessmentAgent:
    def __init__(self, use_ml_model: bool = False):
        self.use_ml_model = use_ml_model

    def assess(self, incident: Dict[str, Any]) -> Dict[str, str]:
        """
        Calculates severity, response priority, and recommended action.
        Considers:
        - people affected
        - fire / explosion presence
        - chemical hazard level
        - base severity score
        - release amount and duration (if provided)
        """
        if self.use_ml_model:
            return self._ml_assessment(incident)
        return self._rule_based_assessment(incident)

    def _rule_based_assessment(self, inc: Dict[str, Any]) -> Dict[str, str]:
        people = int(inc.get("people_affected", 0))
        fire = bool(inc.get("fire", False))
        explosion = bool(inc.get("explosion", False))
        raw_sev = int(inc.get("severity", 5))
        chemical = str(inc.get("chemical", "")).lower()
        release_amount = float(inc.get("release_amount_kg", 0.0))

        # Toxic chemicals with higher inherent hazard
        high_risk_chemicals = ["chlorine", "hydrogen_sulfide", "hydrogen sulfide", "ammonia", "benzene", "sulfur_dioxide", "sulfur dioxide"]
        is_high_risk_chem = any(c in chemical for c in high_risk_chemicals)

        # Composite risk points calculation
        points = raw_sev * 10
        if explosion:
            points += 30
        if fire:
            points += 20
        if is_high_risk_chem:
            points += 25
        if people > 50:
            points += 30
        elif people > 15:
            points += 15
        if release_amount > 200:
            points += 15

        # Determine Severity
        if points >= 75 or explosion or (fire and is_high_risk_chem and people > 20):
            severity = "CRITICAL"
        elif points >= 50 or fire or people > 10:
            severity = "HIGH"
        elif points >= 30:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Determine Priority
        if severity == "CRITICAL" or explosion or people >= 40:
            priority = "IMMEDIATE"
        elif severity == "HIGH":
            priority = "URGENT"
        elif severity == "MEDIUM":
            priority = "STANDARD"
        else:
            priority = "MONITOR"

        # Determine Recommended Action
        if severity == "CRITICAL":
            recommended_action = "EVACUATE"
        elif severity == "HIGH":
            recommended_action = "CONTAIN_AND_SHELTER"
        elif severity == "MEDIUM":
            recommended_action = "DEPLOY_HAZMAT_AND_MONITOR"
        else:
            recommended_action = "INVESTIGATE"

        return {
            "severity": severity,
            "priority": priority,
            "recommended_action": recommended_action
        }

    def _ml_assessment(self, inc: Dict[str, Any]) -> Dict[str, str]:
        """Placeholder for trained neural or tree model if activated."""
        return self._rule_based_assessment(inc)
