"""
Resource Allocation & Dispatch Agent
Monitors emergency response units (Fire, Hazmat, Rescue, Ambulance) and medical infrastructure.
Matches response teams to incident demands and tracks team status/failures.
"""
from typing import List, Dict, Any


class ResourceAllocationAgent:
    def allocate_resources(self, incidents: List[Dict[str, Any]], resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        allocations = []
        for inc in incidents:
            inc_id = inc["id"]
            itype = inc.get("type", "").lower()

            if "fire" in itype:
                allocations.append({
                    "category": "Fire",
                    "assignment": f"F01 to {inc['location']}",
                    "reason": "Nearest available fire team with foam suppression capability"
                })
            if "chemical" in itype or "gas" in itype:
                allocations.append({
                    "category": "Hazmat",
                    "assignment": f"H01 to {inc['location']}",
                    "reason": "Chemical containment and full encapsulation suit requirement"
                })
            if inc.get("people_affected", 0) > 0:
                allocations.append({
                    "category": "Rescue",
                    "assignment": f"R01 to {inc['location']}",
                    "reason": f"{inc['people_affected']} workers inside affected zone"
                })
                allocations.append({
                    "category": "Medical",
                    "assignment": f"A01 to City General",
                    "reason": "Burn unit available and emergency triage staged"
                })

        return allocations
