"""
In-memory mock backend used when FastAPI is not reachable.

The dictionaries returned here are the JSON shapes the frontend expects from
the real API, so the backend team can use this file as the response contract.

Map coordinates use a simulated plant grid from 0 to 100 on both axes (y = north).
"""
import copy
from datetime import datetime

import streamlit as st


def _now():
    return datetime.now().strftime("%H:%M:%S")


class MockBackend:
    def __init__(self):
        self.reset()

    # ------------------------------------------------------------------ state
    def reset(self):
        self.phase = 0  # 0 = initial plan, 1 = after mid-incident change
        t = _now()

        self.incidents = [
            {
                "id": "INC-001",
                "type": "Chemical leak and fire",
                "location": "Factory A",
                "coords": [30, 65],
                "severity": 8,
                "severity_label": "critical",
                "people_affected": 35,
                "status": "active",
                "source": "Gas sensor GS-14, CCTV cam 7",
                "reported_at": t,
                "confirmed": True,
                "uncertain_fields": [],
                "risk": {
                    "chemical": "high",
                    "fire": "high",
                    "explosion": "medium",
                    "structural": "low",
                    "domino_effect": "Possible: solvent storage 40 m east",
                    "spread_direction": "SE",
                    "wind": "From NW, 14 km/h",
                    "hazard_radius": 11,
                },
            }
        ]

        self.resources = [
            self._res("F01", "Fire Team 01", "Fire", "busy", "INC-001", [30, 58]),
            self._res("F02", "Fire Team 02", "Fire", "available", None, [10, 8]),
            self._res("F03", "Fire Team 03", "Fire", "available", None, [12, 8]),
            self._res("F04", "Fire Team 04", "Fire", "available", None, [14, 8]),
            self._res("H01", "Hazmat Team 01", "Hazmat", "busy", "INC-001", [34, 58]),
            self._res("H02", "Hazmat Team 02", "Hazmat", "available", None, [10, 11]),
            self._res("R01", "Rescue Team 01", "Rescue", "busy", "INC-001", [26, 58]),
            self._res("R02", "Rescue Team 02", "Rescue", "available", None, [12, 11]),
            self._res("R03", "Rescue Team 03", "Rescue", "available", None, [14, 11]),
            self._res("A01", "Ambulance 01", "Ambulance", "busy", "INC-001", [22, 60]),
            self._res("A02", "Ambulance 02", "Ambulance", "available", None, [16, 8]),
            self._res("A03", "Ambulance 03", "Ambulance", "available", None, [18, 8]),
            self._res("A04", "Ambulance 04", "Ambulance", "available", None, [16, 11]),
            self._res("A05", "Ambulance 05", "Ambulance", "available", None, [18, 11]),
            self._res("A06", "Ambulance 06", "Ambulance", "available", None, [20, 11]),
        ]

        self.hospitals = [
            {"id": "HSP-1", "name": "City General Hospital", "coords": [95, 94],
             "capacity": 40, "available_beds": 12, "burn_unit": True,
             "travel_min": 14, "status": "accepting"},
            {"id": "HSP-2", "name": "Metro Care Hospital", "coords": [5, 95],
             "capacity": 25, "available_beds": 9, "burn_unit": False,
             "travel_min": 11, "status": "accepting"},
        ]

        self.routes = [
            {"id": "R1", "name": "Main gate to Junction 1", "path": [[5, 15], [30, 15]],
             "status": "open", "travel_min": 2, "reason": ""},
            {"id": "R2", "name": "Junction 1 to Factory A (central road)",
             "path": [[30, 15], [52, 38], [36, 58]], "status": "open", "travel_min": 4, "reason": ""},
            {"id": "R3", "name": "Junction 1 to Factory A (west road)",
             "path": [[30, 15], [18, 40], [26, 60]], "status": "open", "travel_min": 5, "reason": ""},
            {"id": "R4", "name": "Junction 1 to Factory B (east ring)",
             "path": [[30, 15], [78, 15], [78, 45], [66, 48]], "status": "open", "travel_min": 6, "reason": ""},
        ]

        self.evacuation = {
            "incident_id": "INC-001",
            "affected_population": 150,
            "zones": [
                {"id": "A", "name": "Zone A", "action": "evacuate", "population": 120, "bounds": [18, 54, 46, 82]},
                {"id": "B", "name": "Zone B", "action": "monitor", "population": 180, "bounds": [50, 34, 76, 60]},
                {"id": "C", "name": "Zone C", "action": "monitor", "population": 50, "bounds": [50, 64, 80, 90]},
                {"id": "D", "name": "Zone D", "action": "safe", "population": 0, "bounds": [4, 4, 36, 34]},
            ],
            "shelters": [
                {"id": "S01", "name": "Admin block assembly point", "coords": [70, 22],
                 "capacity": 200, "available": 200, "status": "assigned"},
                {"id": "S02", "name": "Canteen hall", "coords": [85, 80],
                 "capacity": 150, "available": 0, "status": "full"},
                {"id": "S03", "name": "North gate shelter", "coords": [10, 84],
                 "capacity": 350, "available": 350, "status": "standby"},
            ],
        }

        self.alerts = [
            self._alert("control_room", "critical", "Chemical leak and fire confirmed at Factory A. Severity 8/10."),
            self._alert("hazmat", "high", "H01 dispatched to Factory A via R1 and R2. Full encapsulation suits required."),
            self._alert("fire", "high", "F01 on scene at Factory A. Protect solvent storage to the east."),
            self._alert("medical", "medium", "A01 staged at Factory A. City General notified: 12 beds available."),
            self._alert("public", "high", "Zone A workers: evacuate to Admin block assembly point (S01) now."),
        ]

        self.plan = {
            "incident_id": "INC-001",
            "version": 1,
            "status": "approved",
            "generated_at": t,
            "approved_by": "Control room operator",
            "approved_at": t,
            "pipeline": self._pipeline("approved"),
            "changes": [],
            "approval_items": [],
            "previous": [],
            "current": [
                self._act("Fire", "F01 to Factory A", "Nearest available fire team"),
                self._act("Hazmat", "H01 to Factory A", "Chemical leak needs Hazmat containment"),
                self._act("Rescue", "R01 to Factory A", "35 workers inside affected area"),
                self._act("Route", "R1 then R2", "Shortest open route, 6 min"),
                self._act("Medical", "A01 to City General", "Burn unit available"),
                self._act("Evacuation", "Zone A", "Inside predicted spread area"),
                self._act("Shelter", "S01 Admin block", "Closest shelter with capacity"),
            ],
        }

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _res(rid, name, rtype, status, assigned, pos):
        return {"id": rid, "name": name, "type": rtype, "status": status,
                "assigned_to": assigned, "position": pos, "note": "", "changed": False}

    @staticmethod
    def _alert(audience, severity, message):
        return {"time": _now(), "audience": audience, "severity": severity, "message": message}

    @staticmethod
    def _act(category, assignment, reason):
        return {"category": category, "assignment": assignment, "reason": reason}

    @staticmethod
    def _pipeline(approval_state):
        return [
            {"stage": "Detection", "status": "complete"},
            {"stage": "Assessment", "status": "complete"},
            {"stage": "Replanning", "status": "complete"},
            {"stage": "Approval", "status": approval_state},
        ]

    def _set_resource(self, rid, **fields):
        for r in self.resources:
            if r["id"] == rid:
                r.update(fields, changed=True)

    # -------------------------------------------------------------- scenario
    def _apply_mid_incident_change(self):
        """New explosion at Factory B + Hazmat H01 fails + R2 blocked + spread grows."""
        self.phase = 1
        t = _now()

        self.incidents.append({
            "id": "INC-002",
            "type": "Explosion",
            "location": "Factory B",
            "coords": [64, 48],
            "severity": 9,
            "severity_label": "critical",
            "people_affected": 20,
            "status": "active",
            "source": "Worker radio report, pressure sensor PS-3",
            "reported_at": t,
            "confirmed": False,
            "uncertain_fields": ["people_affected"],
            "risk": {
                "chemical": "high", "fire": "high", "explosion": "high", "structural": "high",
                "domino_effect": "Likely: chlorine line ruptured",
                "spread_direction": "SE", "wind": "From NW, 18 km/h", "hazard_radius": 13,
            },
        })
        a = self.incidents[0]
        a["risk"]["explosion"] = "high"
        a["risk"]["hazard_radius"] = 15
        a["people_affected"] = 48

        self._set_resource("H01", status="unavailable", assigned_to=None,
                           note="Suit breach, team withdrawn for decontamination")
        self._set_resource("H02", status="busy", assigned_to="INC-002", position=[68, 44])
        self._set_resource("F02", status="busy", assigned_to="INC-002", position=[60, 44])
        self._set_resource("R02", status="busy", assigned_to="INC-002", position=[64, 42])
        self._set_resource("A02", status="busy", assigned_to="INC-002", position=[72, 42])
        self._set_resource("A03", status="busy", assigned_to="INC-002", position=[74, 42])

        for r in self.routes:
            if r["id"] == "R2":
                r.update(status="blocked", reason="Passes through Factory B blast zone")

        self.hospitals[0]["available_beds"] = 6

        ev = self.evacuation
        ev["affected_population"] = 350
        for z in ev["zones"]:
            if z["id"] == "B":
                z["action"] = "evacuate"
        for s in ev["shelters"]:
            if s["id"] == "S01":
                s.update(status="unsafe", available=0)
            if s["id"] == "S03":
                s.update(status="assigned", available=350)

        self.alerts = [
            self._alert("control_room", "critical", "New explosion at Factory B. Casualty count unconfirmed."),
            self._alert("control_room", "high", "Hazmat Team H01 unavailable: suit breach."),
            self._alert("hazmat", "critical", "H02 redirect to Factory B via R1 and R4. Toxic gas spreading toward Zone C."),
            self._alert("fire", "high", "F02 to Factory B. F01 hold foam cover at Factory A."),
            self._alert("medical", "high", "Expect burn and inhalation cases. Route A01 to Metro Care, A02 and A03 to City General."),
            self._alert("public", "critical", "Zone A and Zone B: evacuate to North gate shelter (S03). Avoid central road."),
        ] + self.alerts

        prev = copy.deepcopy(self.plan["current"])
        self.plan = {
            "incident_id": "INC-001",
            "version": self.plan["version"] + 1,
            "status": "pending_approval",
            "generated_at": t,
            "approved_by": None,
            "approved_at": None,
            "pipeline": self._pipeline("required"),
            "changes": [
                {"type": "new_incident", "message": "New explosion at Factory B"},
                {"type": "resource_failure", "message": "Hazmat Team H01 unavailable"},
                {"type": "route_blocked", "message": "Route R2 blocked by blast zone"},
                {"type": "hazard_spread", "message": "Hazard spread increased toward the south-east"},
            ],
            "approval_items": [
                "Public evacuation of Zone B (180 people)",
                "Commit last Hazmat team (H02) to Factory B",
                "Request district Hazmat mutual aid for Factory A",
            ],
            "previous": prev,
            "current": [
                self._act("Fire", "F01 at Factory A, F02 to Factory B", "Two active fires; F01 already on scene"),
                self._act("Hazmat", "H02 to Factory B", "H01 out of service; ruptured chlorine line is the larger exposure"),
                self._act("Rescue", "R01 at Factory A, R02 to Factory B", "Workers trapped at both sites"),
                self._act("Route", "R1 then R4", "R2 blocked; east ring avoids the blast zone"),
                self._act("Medical", "A01 to Metro Care, A02 and A03 to City General",
                          "City General down to 6 beds; split load"),
                self._act("Evacuation", "Zone A and Zone B", "Zone B now inside the Factory B blast and gas area"),
                self._act("Shelter", "S03 North gate", "S01 lies in the new spread path"),
            ],
        }

    # ------------------------------------------------------------- endpoints
    def get_incidents(self):
        return copy.deepcopy(self.incidents)

    def create_incident(self, payload):
        new = {
            "id": f"INC-{len(self.incidents) + 1:03d}",
            "coords": [50, 50],
            "status": "active",
            "reported_at": _now(),
            "uncertain_fields": [] if payload.get("confirmed", True) else ["people_affected"],
            "risk": {"chemical": "unknown", "fire": "unknown", "explosion": "unknown",
                     "structural": "unknown", "domino_effect": "Assessment pending",
                     "spread_direction": "SE", "wind": "From NW", "hazard_radius": 8},
            **payload,
        }
        sev = new.get("severity", 5)
        new.setdefault("severity_label", "critical" if sev >= 8 else "high" if sev >= 6 else "medium" if sev >= 4 else "low")
        self.incidents.append(new)
        self.alerts.insert(0, self._alert("control_room", "high",
                                          f"New incident reported: {new['type']} at {new['location']}."))
        return copy.deepcopy(new)

    def get_resources(self):
        return copy.deepcopy(self.resources)

    def get_hospitals(self):
        return copy.deepcopy(self.hospitals)

    def get_routes(self):
        return copy.deepcopy(self.routes)

    def get_evacuation(self, incident_id):
        return copy.deepcopy(self.evacuation)

    def get_alerts(self, incident_id):
        return copy.deepcopy(self.alerts)

    def get_response_plan(self, incident_id):
        return copy.deepcopy(self.plan)

    def replan(self, incident_id, event):
        if self.phase == 0 and event.get("type") == "scenario":
            self._apply_mid_incident_change()
        else:
            prev = copy.deepcopy(self.plan["current"])
            self.plan.update(
                version=self.plan["version"] + 1, status="pending_approval", generated_at=_now(),
                approved_by=None, approved_at=None, pipeline=self._pipeline("required"),
                previous=prev,
                changes=[{"type": "manual", "message": event.get("message", "Operator requested a fresh plan")}],
            )
        return copy.deepcopy(self.plan)

    def approve_plan(self, incident_id, operator):
        self.plan.update(status="approved", approved_by=operator, approved_at=_now(),
                         pipeline=self._pipeline("approved"))
        self.alerts.insert(0, self._alert("control_room", "medium",
                                          f"Response plan v{self.plan['version']} approved by {operator}. Orders sent to teams."))
        for r in self.resources:
            r["changed"] = False
        return copy.deepcopy(self.plan)


def get_mock_backend() -> MockBackend:
    if "_mock_backend" not in st.session_state:
        st.session_state["_mock_backend"] = MockBackend()
    return st.session_state["_mock_backend"]