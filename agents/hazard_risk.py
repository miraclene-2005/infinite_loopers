"""
Agent 3: Hazard & Risk Assessment Agent
Identifies primary and secondary industrial accident hazards and domino effects.
"""
from typing import Dict, Any, List

class HazardRiskAgent:
    def assess_hazards(self, incident: Dict[str, Any], assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines primary and secondary hazards based on chemical properties,
        fire/explosion presence, infrastructure proximity, and severity.
        """
        chemical = str(incident.get("chemical", "None")).replace("_", " ").title()
        has_fire = bool(incident.get("fire", False))
        has_explosion = bool(incident.get("explosion", False))
        severity = str(assessment.get("severity", "MEDIUM")).upper()
        people_affected = int(incident.get("people_affected", 0))

        # Toxic / Flammable classifications
        toxic_chemicals = {"Chlorine", "Hydrogen Sulfide", "Sulfur Dioxide", "Ammonia", "Nitrogen Dioxide"}
        flammable_chemicals = {"Benzene", "Methane", "Hydrogen Sulfide", "Propane"}

        is_toxic = any(t in chemical for t in toxic_chemicals)
        is_flammable = any(f in chemical for f in flammable_chemicals)

        primary_hazards: List[Dict[str, Any]] = []
        secondary_hazards: List[Dict[str, Any]] = []

        # Evaluate Primary Hazards
        if is_toxic:
            primary_hazards.append({
                "hazard": "Toxic Exposure",
                "risk_level": "High" if severity in ["HIGH", "CRITICAL"] else "Medium",
                "agent": chemical,
                "description": f"Airborne toxic gas dispersion from {chemical} release."
            })
            primary_hazards.append({
                "hazard": "Environmental Contamination",
                "risk_level": "High",
                "description": "Ground level plume deposition and persistent chemical contamination."
            })

        if has_fire or is_flammable:
            primary_hazards.append({
                "hazard": "Fire Hazard",
                "risk_level": "Critical" if has_fire else "High",
                "description": "Active thermal radiation or high vapor flammability hazard."
            })

        if has_explosion:
            primary_hazards.append({
                "hazard": "Overpressure Explosion",
                "risk_level": "Critical",
                "description": "Blast wave, airborne fragmentation, and acoustic impulse shock."
            })
            primary_hazards.append({
                "hazard": "Structural Collapse",
                "risk_level": "High",
                "description": "Structural failure of adjacent piping racks and containment vessels."
            })
        elif has_fire and severity == "CRITICAL":
            primary_hazards.append({
                "hazard": "Structural Danger",
                "risk_level": "Medium",
                "description": "Thermal degradation of steel frames and support infrastructure."
            })

        if not primary_hazards:
            primary_hazards.append({
                "hazard": "Industrial Equipment Malfunction",
                "risk_level": "Low",
                "description": "Mechanical integrity risk requiring engineering inspection."
            })

        # Evaluate Secondary Hazards
        if has_fire and not has_explosion and is_flammable:
            secondary_hazards.append({
                "hazard": "Secondary Vapor Cloud Explosion (BLEVE)",
                "probability": "Medium",
                "description": "Pressurized vessel rupture due to engulfing flame."
            })

        if has_fire:
            secondary_hazards.append({
                "hazard": "Fire Spread / Radiant Heat Transfer",
                "probability": "High",
                "description": "Downwind thermal ignition of adjacent chemical storage units."
            })

        if is_toxic or has_fire:
            secondary_hazards.append({
                "hazard": "Off-Site Worker and Public Exposure",
                "probability": "High" if people_affected > 20 else "Medium",
                "description": "Atmospheric advection of toxic combustion byproducts into occupied zones."
            })
            secondary_hazards.append({
                "hazard": "Evacuation Road Contamination",
                "probability": "High",
                "description": "Toxic plume cutting off internal perimeter access corridors."
            })

        # Domino Incidents
        domino_risk = "High: adjacent pressurized solvents within 50m" if (has_fire or has_explosion) else "Low: isolated containment"
        secondary_hazards.append({
            "hazard": "Domino Incidents",
            "probability": "High" if (has_fire or has_explosion) else "Low",
            "description": domino_risk
        })

        return {
            "chemical": chemical,
            "primary_hazards": primary_hazards,
            "secondary_hazards": secondary_hazards,
            "composite_hazard_index": 8.5 if severity == "CRITICAL" else (6.5 if severity == "HIGH" else 4.0),
            "containment_required": is_toxic or has_fire or has_explosion
        }
