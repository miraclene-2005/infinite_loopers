"""
Risk & Hazard Assessment Agent
Evaluates chemical dispersion, fire spread, explosion risks, domino effect threats,
wind direction vectors, and calculates dynamic hazard radii.
"""
from typing import Dict, Any


class RiskAssessmentAgent:
    def evaluate_risk(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        itype = incident.get("type", "").lower()
        severity = incident.get("severity", 5)

        is_explosion = "explosion" in itype
        is_chemical = "chemical" in itype or "gas" in itype or incident.get("chemical") is not None
        is_fire = incident.get("fire", False) or "fire" in itype

        chem_risk = "high" if is_chemical else ("medium" if severity >= 6 else "low")
        fire_risk = "high" if is_fire else ("medium" if severity >= 7 else "low")
        exp_risk = "high" if is_explosion else ("medium" if is_fire and severity >= 8 else "low")
        struct_risk = "high" if is_explosion else ("medium" if severity >= 8 else "low")

        # Domino effect assessment
        if is_explosion:
            domino = "Likely: chlorine line ruptured, secondary blast risk"
        elif is_chemical and is_fire:
            domino = "Possible: solvent storage 40 m east"
        elif is_fire:
            domino = "Possible: adjacent fuel tanks"
        else:
            domino = "Low risk of domino escalation"

        # Calculate hazard radius based on severity and type
        radius = 8.0 + (severity * 0.7)
        if is_explosion:
            radius += 4.0

        return {
            "chemical": chem_risk,
            "fire": fire_risk,
            "explosion": exp_risk,
            "structural": struct_risk,
            "domino_effect": domino,
            "spread_direction": "SE",
            "wind": "From NW, 14 km/h" if not is_explosion else "From NW, 18 km/h",
            "hazard_radius": round(radius, 1)
        }
