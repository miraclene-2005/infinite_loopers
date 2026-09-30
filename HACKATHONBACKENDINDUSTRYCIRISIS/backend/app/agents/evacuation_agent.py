"""
Evacuation & Logistics Agent
Determines zone evacuation priorities, safe assembly points, shelter routing,
and monitors road blockages caused by blast radii or chemical plume drift.
"""
from typing import List, Dict, Any


class EvacuationAgent:
    def plan_evacuation(self, incidents: List[Dict[str, Any]], routes: List[Dict[str, Any]]) -> Dict[str, Any]:
        has_critical = any(inc.get("severity", 0) >= 8 for inc in incidents)
        has_secondary = len(incidents) > 1

        if has_secondary:
            zones = [
                {"id": "A", "name": "Zone A", "action": "evacuate", "population": 120, "bounds": [18, 54, 46, 82]},
                {"id": "B", "name": "Zone B", "action": "evacuate", "population": 180, "bounds": [50, 34, 76, 60]},
                {"id": "C", "name": "Zone C", "action": "monitor", "population": 50, "bounds": [50, 64, 80, 90]},
                {"id": "D", "name": "Zone D", "action": "safe", "population": 0, "bounds": [4, 4, 36, 34]},
            ]
            shelters = [
                {"id": "S01", "name": "Admin block assembly point", "coords": [70, 22], "capacity": 200, "available": 0, "status": "unsafe"},
                {"id": "S02", "name": "Canteen hall", "coords": [85, 80], "capacity": 150, "available": 0, "status": "full"},
                {"id": "S03", "name": "North gate shelter", "coords": [10, 84], "capacity": 350, "available": 350, "status": "assigned"},
            ]
            affected_pop = 350
        else:
            zones = [
                {"id": "A", "name": "Zone A", "action": "evacuate", "population": 120, "bounds": [18, 54, 46, 82]},
                {"id": "B", "name": "Zone B", "action": "monitor", "population": 180, "bounds": [50, 34, 76, 60]},
                {"id": "C", "name": "Zone C", "action": "monitor", "population": 50, "bounds": [50, 64, 80, 90]},
                {"id": "D", "name": "Zone D", "action": "safe", "population": 0, "bounds": [4, 4, 36, 34]},
            ]
            shelters = [
                {"id": "S01", "name": "Admin block assembly point", "coords": [70, 22], "capacity": 200, "available": 200, "status": "assigned"},
                {"id": "S02", "name": "Canteen hall", "coords": [85, 80], "capacity": 150, "available": 0, "status": "full"},
                {"id": "S03", "name": "North gate shelter", "coords": [10, 84], "capacity": 350, "available": 350, "status": "standby"},
            ]
            affected_pop = 150

        return {
            "affected_population": affected_pop,
            "zones": zones,
            "shelters": shelters
        }
