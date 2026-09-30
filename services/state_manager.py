"""
Central Incident State & Operational Orchestration Engine.
Maintains the canonical Incident State object consuming data from all 10 AI agents,
manages GPS responder tracking, simulates physical world events (road closures, wind shifts, hospital surges),
and orchestrates closed-loop replanning through Agent 10 with Human-in-the-Loop authorization.
"""
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import uuid
import math
import logging

from services.data_loader import data_loader
from services.event_engine import event_engine, EVENT_TYPES
from services.routing_service import routing_service, STAGING_LOCATIONS
from services.tracking_service import tracking_service
from agents import command_agent

logger = logging.getLogger("state_manager")

class LiveIncidentStateManager:
    def __init__(self):
        # Maps incident_id -> Canonical Incident State Object
        self.live_incidents: Dict[str, Dict[str, Any]] = {}
        # Persistent simulation mode flag: 'LIVE' or 'SIMULATION'
        self.data_mode: str = "SIMULATION"
        # Seed default demonstration incident
        self._bootstrap_default_states()

    def _bootstrap_default_states(self):
        """Pre-seeds the initial chemical leak crisis scenario (I001 Plant B Sulfur Dioxide)."""
        try:
            self.get_or_create_state("I001")
        except Exception as e:
            logger.warning(f"Default state bootstrap deferred: {e}")

    def get_or_create_state(self, incident_id: str, custom_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retrieves or builds the canonical incident state."""
        clean_id = incident_id.strip().upper()
        if clean_id in self.live_incidents:
            return self.live_incidents[clean_id]

        # Generate fresh response plan through 10-Agent Autonomous Pipeline
        raw_plan = command_agent.run_initial_response(incident_id=clean_id, custom_input=custom_input)
        state = self._convert_plan_to_canonical_state(raw_plan)
        self.live_incidents[clean_id] = state

        # Emit INCIDENT_CREATED event
        event_engine.emit(
            event_type=EVENT_TYPES["INCIDENT_CREATED"],
            incident_id=clean_id,
            source="Incident Detection (Agent 1)",
            severity="CRITICAL",
            data={
                "incident_id": clean_id,
                "location": state["location"],
                "chemical": state["hazard"].get("chemical"),
                "severity": state["severity"]
            }
        )

        return state

    def _convert_plan_to_canonical_state(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds the central Incident State object matching specification:
        {
          incident_id, type, location, severity, status, people_at_risk,
          hazard, spread, resources, responders, routes, road_closures,
          hospitals, casualties, shelters, evacuation, communications,
          events, recommendations, approvals, ai_activity, last_updated
        }
        """
        incident = plan.get("incident", {})
        assessment = plan.get("assessment", {})
        hazards = plan.get("hazards", {})
        spread = plan.get("spread", {})
        raw_resources = plan.get("resources", [])
        medical = plan.get("medical", {})
        routes = plan.get("routes", [])
        evacuation = plan.get("evacuation", {})
        comms = plan.get("communications", {})
        replan = plan.get("replanning", {})

        inc_id = incident.get("incident_id", "I001")
        now = datetime.now()
        now_str = now.strftime("%H:%M:%S")

        # Destination coordinates for incident site (Plant B default)
        dest_coords = STAGING_LOCATIONS["PLANT_B"]
        if "plant_a" in str(incident.get("location", "")).lower():
            dest_coords = STAGING_LOCATIONS["PLANT_A"]

        # Responders Telemetry Fleet setup
        responders_fleet = []
        depot_keys = ["DEPOT_A", "DEPOT_B", "DEPOT_A", "DEPOT_B", "DEPOT_A", "DEPOT_B"]

        for i, res in enumerate(raw_resources[:6]):
            res_id = res.get("resource_id", f"R{433 + i*20}")
            r_type = res.get("resource_type", "Hazmat_Team" if i == 0 else "Fire_Team" if i < 3 else "Ambulance")
            depot_key = depot_keys[i % len(depot_keys)]
            depot_coord = {
                "lat": STAGING_LOCATIONS[depot_key]["lat"] + (i * 0.003),
                "lng": STAGING_LOCATIONS[depot_key]["lng"] + (i * 0.002)
            }

            # Register in tracking service
            unit_telemetry = tracking_service.register_or_update_unit(
                resource_id=res_id,
                unit_type=r_type,
                name=f"{r_type.replace('_', ' ')} ({res_id})",
                origin_coords=depot_coord,
                dest_coords={"lat": dest_coords["lat"], "lng": dest_coords["lng"]},
                destination_name=dest_coords["name"],
                initial_progress=15.0 + (i * 12.0)
            )
            responders_fleet.append(unit_telemetry)

        # Standardized Regional Hospitals Network (Step 9 & 12)
        base_hospitals = [
            {"hospital_id": "H001", "name": "Apollo Trauma Center", "status": "ACCEPTING", "emergency_capacity_total": 30, "emergency_capacity_free": 12, "allocated_patients": 18, "icu_total": 10, "icu_free": 6, "distance_km": 4.5, "eta_minutes": 8.0, "lat": 13.0100, "lng": 80.2550},
            {"hospital_id": "H002", "name": "Govt Royapettah Hospital", "status": "LIMITED", "emergency_capacity_total": 25, "emergency_capacity_free": 1, "allocated_patients": 24, "icu_total": 10, "icu_free": 1, "distance_km": 6.8, "eta_minutes": 12.5, "lat": 13.0552, "lng": 80.2648},
            {"hospital_id": "H003", "name": "Rajiv Gandhi General Hospital", "status": "ACCEPTING", "emergency_capacity_total": 45, "emergency_capacity_free": 20, "allocated_patients": 25, "icu_total": 16, "icu_free": 8, "distance_km": 9.2, "eta_minutes": 16.0, "lat": 13.0814, "lng": 80.2772}
        ]

        # Merge with any utilized from medical agent
        agent_hosp_ids = set()
        hospitals_list = []
        for i, h in enumerate(medical.get("hospitals_utilized", [])):
            h_id = h.get("hospital_id", f"H00{i+1}")
            agent_hosp_ids.add(h_id)
            hospitals_list.append({
                "hospital_id": h_id,
                "name": h.get("name", "Regional Trauma Center"),
                "status": "ACCEPTING" if (h.get("emergency_capacity", 30) - h.get("allocated_patients", 6)) > 5 else "LIMITED",
                "emergency_capacity_total": h.get("emergency_capacity", 30),
                "emergency_capacity_free": max(0, h.get("emergency_capacity", 30) - h.get("allocated_patients", 6)),
                "allocated_patients": h.get("allocated_patients", 6),
                "icu_total": h.get("icu_beds", 10),
                "icu_free": max(0, h.get("icu_beds", 10) - 4),
                "distance_km": round(4.2 + (i * 2.8), 1),
                "eta_minutes": round(7.0 + (i * 3.5), 1),
                "lat": 13.0100 + (i * 0.035),
                "lng": 80.2550 + (i * 0.015)
            })

        for bh in base_hospitals:
            if bh["hospital_id"] not in agent_hosp_ids:
                hospitals_list.append(bh)

        # Standardized Shelters list (Step 13 & 20)
        base_shelters = [
            {"shelter_id": "S001", "name": "Anna Nagar Community Hall", "total_capacity": 997, "current_occupancy": 312, "available_capacity": 685, "fill_rate_pct": 31.3, "status": "OPEN", "distance_km": 3.8, "safe_route_status": "CLEAR", "lat": 13.0080, "lng": 80.2720},
            {"shelter_id": "S004", "name": "Velachery Community Hall", "total_capacity": 819, "current_occupancy": 520, "available_capacity": 299, "fill_rate_pct": 63.5, "status": "OPEN", "distance_km": 5.4, "safe_route_status": "CLEAR", "lat": 12.9800, "lng": 80.2250}
        ]

        agent_shelter_ids = set()
        shelters_list = []
        for i, s in enumerate(evacuation.get("assigned_shelters", [])):
            s_id = s.get("shelter_id", f"S00{i+1}")
            agent_shelter_ids.add(s_id)
            s_name = s.get("name", "Community Shelter Hub")
            cap = s.get("total_capacity", 800)
            occ = s.get("current_occupancy", 250)
            avail = max(0, cap - occ)
            shelters_list.append({
                "shelter_id": s_id,
                "name": s_name,
                "total_capacity": cap,
                "current_occupancy": occ,
                "available_capacity": avail,
                "fill_rate_pct": round((occ / max(cap, 1)) * 100, 1),
                "status": "OPEN" if avail > 50 else "FULL",
                "distance_km": round(3.1 + (i * 2.1), 1),
                "safe_route_status": "CLEAR",
                "lat": 13.0080 + (i * 0.015),
                "lng": 80.2720 + (i * 0.012)
            })

        for bs in base_shelters:
            if bs["shelter_id"] not in agent_shelter_ids:
                shelters_list.append(bs)

        # High-Consequence Human Approval Items (Step 14)
        approvals = [
            {
                "action_id": f"AUTH-{uuid.uuid4().hex[:6].upper()}",
                "type": "EVACUATION_MANDATE",
                "title": "Evacuation Recommendation: Red Zone Perimeter",
                "reason": f"ALOHA dispersion plume exceeds {spread.get('red_zone_m', 380)}m threshold with wind {spread.get('wind_direction', 'NW')}.",
                "people_affected": incident.get("people_affected", 25) * 10,
                "recommended_shelters": [s["shelter_id"] for s in shelters_list[:2]],
                "safe_routes_count": 2,
                "status": "PENDING_APPROVAL",
                "risk_level": "HIGH",
                "requested_by": "Agent 8 (Evacuation)",
                "timestamp": now_str
            }
        ]

        # AI Activity Log (Step 22)
        ai_activity = [
            {"time": now_str, "agent": "Detection", "action": "Incident confirmed", "details": f"Toxic leak reported at {incident.get('location', 'Plant B')}", "confidence": 0.98},
            {"time": now_str, "agent": "Assessment", "action": f"Severity {assessment.get('severity', 'HIGH')}", "details": f"Calculated priority {assessment.get('priority', 'URGENT')}", "confidence": 0.94},
            {"time": now_str, "agent": "Hazard", "action": "Toxic exposure identified", "details": f"Substance: {incident.get('chemical', 'Sulfur Dioxide')}", "confidence": 0.96},
            {"time": now_str, "agent": "Spread", "action": f"Zone expanded to {spread.get('red_zone_m', 380)}m", "details": f"Wind heading {spread.get('wind_direction', 'NW')} at {spread.get('wind_speed_ms', 6.5)} m/s", "confidence": 0.91},
            {"time": now_str, "agent": "Resources", "action": f"{responders_fleet[0]['resource_id']} assigned", "details": f"Dispatched {len(responders_fleet)} specialized response units", "confidence": 0.95},
            {"time": now_str, "agent": "Routing", "action": "Safe route calculated", "details": "Ingress corridor R03108 selected bypassing plume buffer", "confidence": 0.93},
            {"time": now_str, "agent": "Medical", "action": "Hospital allocation created", "details": f"Triage coordinated across {len(hospitals_list)} trauma centers", "confidence": 0.92},
            {"time": now_str, "agent": "Command", "action": "Response plan generated", "details": "Response Objective: CONTAIN + PROTECT + EVACUATE", "confidence": 0.97}
        ]

        # Canonical Incident State
        canonical_state = {
            "incident_id": inc_id,
            "type": incident.get("incident_type", incident.get("type", "Chemical_Leak")),
            "location": incident.get("location", incident.get("plant", "Plant B")),
            "chemical": str(incident.get("chemical", "Sulfur Dioxide")).replace("_", " "),
            "severity": assessment.get("severity", "HIGH"),
            "severity_score": int(incident.get("severity", 8)),
            "priority": assessment.get("priority", "URGENT"),
            "status": "RESPONSE_IN_PROGRESS",
            "people_at_risk": incident.get("people_affected", 25) * 10,
            "objective": "CONTAIN + PROTECT + EVACUATE",
            "coordinates": {"lat": dest_coords["lat"], "lng": dest_coords["lng"]},
            "data_mode": self.data_mode,
            
            # Sub-domain operational objects
            "hazard": {
                "chemical": str(incident.get("chemical", "Sulfur Dioxide")).replace("_", " "),
                "fire_present": bool(incident.get("fire", False)),
                "explosion_present": bool(incident.get("explosion", False)),
                "primary_hazards": hazards.get("primary_hazards", ["Toxic Vapor Release", "Respiratory Irritant"]),
                "ppe_required": "Level A Encapsulated Suit + SCBA"
            },
            "spread": {
                "model": "ALOHA-Informed Dispersion",
                "wind_direction": spread.get("wind_direction", "NW"),
                "spread_direction": spread.get("spread_direction", "Northwest"),
                "wind_speed_ms": spread.get("wind_speed_ms", 6.5),
                "red_zone_m": spread.get("red_zone_m", 380),
                "orange_zone_m": spread.get("orange_zone_m", 620),
                "yellow_zone_m": spread.get("yellow_zone_m", 1100),
                "evacuation_radius_m": spread.get("evacuation_radius_m", 1100),
                "data_source": "MODEL"
            },
            "resources": raw_resources,
            "responders": responders_fleet,
            "routes": routes,
            "active_route": responders_fleet[0]["route_geometry"] if responders_fleet else None,
            "road_closures": list(replan.get("changes_detected", [])),
            "hospitals": hospitals_list,
            "casualties": {
                "total_injured": medical.get("total_injured", 14),
                "critical_icu": medical.get("critical_cases", 4),
                "triaged": 14,
                "in_transit": len(responders_fleet)
            },
            "shelters": shelters_list,
            "evacuation": evacuation,
            "communications": comms,
            "events": event_engine.get_history(incident_id=inc_id, limit=30),
            "recommendations": [
                {"id": "REC-1", "action": "Establish 380m Exclusion Perimeter", "status": "MANDATORY"},
                {"id": "REC-2", "action": "Reroute civilian traffic away from Ingress Corridor R03108", "status": "EXECUTING"},
                {"id": "REC-3", "action": "Issue shelter-in-place bulletin for downwind residential sector", "status": "PENDING_APPROVAL"}
            ],
            "approvals": approvals,
            "ai_activity": ai_activity,
            "replanning": replan,
            "last_updated": now_str
        }

        return canonical_state

    def tick_telemetry(self, incident_id: str) -> Dict[str, Any]:
        """Advances responder vehicles along route geometries and triggers ETA recalculations."""
        state = self.get_or_create_state(incident_id)
        now_str = datetime.now().strftime("%H:%M:%S")

        updated_fleet = []
        for unit in state.get("responders", []):
            u_id = unit["resource_id"]
            updated = tracking_service.tick_unit_gps(resource_id=u_id, incident_id=incident_id, step_pct=5.5)
            updated_fleet.append(updated if updated else unit)

        state["responders"] = updated_fleet
        state["last_updated"] = now_str
        return state

    # ----------------- Step 10: Road Closure Simulation -----------------
    def simulate_block_road(self, incident_id: str, road_id: str = "R03108") -> Dict[str, Any]:
        """
        Simulates: ROAD R03108 BLOCKED
        Triggers:
        1. Event Engine: ROAD_BLOCKED event
        2. Command Agent (Agent 10) orchestrator
        3. Identifies affected responders
        4. Route Agent recalculates alternative detour
        5. Updates ETA & polyline
        6. Notifies responder terminal
        7. Records audit event
        """
        state = self.get_or_create_state(incident_id)
        now_str = datetime.now().strftime("%H:%M:%S")

        # 1. Update road closures list
        if road_id not in state["road_closures"]:
            state["road_closures"].append(road_id)

        # 2. Emit ROAD_BLOCKED event
        event_engine.emit(
            event_type=EVENT_TYPES["ROAD_BLOCKED"],
            incident_id=incident_id,
            source="Traffic IoT Sensor / Road Monitor",
            severity="HIGH",
            data={"road_id": road_id, "reason": "Toxic plume obstruction & emergency barrier"}
        )

        # 3. Reroute affected responders
        rerouted_units = []
        for unit in state.get("responders", []):
            rerouted = tracking_service.reroute_unit(
                resource_id=unit["resource_id"],
                incident_id=incident_id,
                blocked_roads=state["road_closures"],
                reason=f"Road {road_id} blocked"
            )
            rerouted_units.append(rerouted if rerouted else unit)

        state["responders"] = rerouted_units
        if rerouted_units:
            state["active_route"] = rerouted_units[0].get("route_geometry")

        # 4. Trigger Agent 10 Replanning
        replan_result = command_agent.replan(
            incident_id=incident_id,
            new_events=[f"Road {road_id} completely blocked by hazardous debris and toxic vapor"],
            newly_blocked_roads=state["road_closures"]
        )

        state["replanning"] = replan_result.get("replanning", {})

        # 5. Append AI Activity
        lead_unit = rerouted_units[0] if rerouted_units else {}
        state["ai_activity"].insert(0, {
            "time": now_str,
            "agent": "Routing",
            "action": f"Route recalculated for {lead_unit.get('resource_id', 'R0433')}",
            "details": f"Detour via Northern Bypass R03204. ETA: {lead_unit.get('eta_display', '11:47')}",
            "confidence": 0.94
        })
        state["ai_activity"].insert(0, {
            "time": now_str,
            "agent": "Command",
            "action": f"Replanned around road closure {road_id}",
            "details": "Rerouted hazardous units; alternative route activated",
            "confidence": 0.97
        })

        # 6. Push notification alert
        event_engine.emit(
            event_type=EVENT_TYPES["ALERT_CREATED"],
            incident_id=incident_id,
            source="Incident Operations Command",
            severity="HIGH",
            data={
                "title": f"⚠ ROUTE CHANGE {lead_unit.get('name', 'R0433 HAZMAT')}",
                "message": f"Previous ETA: 08:21 -> New ETA: {lead_unit.get('eta_display', '11:47')}. Reason: Road {road_id} blocked. Alternative route activated."
            }
        )

        state["last_updated"] = now_str
        self.live_incidents[incident_id] = state
        return state

    def simulate_reopen_road(self, incident_id: str, road_id: str = "R03108") -> Dict[str, Any]:
        """Clears road closure and restores direct primary ingress corridor."""
        state = self.get_or_create_state(incident_id)
        if road_id in state["road_closures"]:
            state["road_closures"].remove(road_id)

        event_engine.emit(
            event_type=EVENT_TYPES["ROAD_REOPENED"],
            incident_id=incident_id,
            source="Road Clearance Team",
            severity="SUCCESS",
            data={"road_id": road_id}
        )

        # Restore units to direct route
        for unit in state.get("responders", []):
            tracking_service.register_or_update_unit(
                resource_id=unit["resource_id"],
                unit_type=unit["type"],
                name=unit["name"],
                origin_coords=unit["current_location"],
                dest_coords=unit["destination_coords"],
                destination_name=unit["destination"],
                blocked_roads=state["road_closures"]
            )

        state["responders"] = tracking_service.get_all_units()
        state["last_updated"] = datetime.now().strftime("%H:%M:%S")
        return state

    # ----------------- Step 11: Wind / Hazard Simulation -----------------
    def simulate_change_wind(
        self,
        incident_id: str,
        new_direction: str = "W",
        new_speed_ms: float = 8.5
    ) -> Dict[str, Any]:
        """
        Simulates: WIND CHANGE (e.g. NW -> W)
        Triggers:
        1. Weather Telemetry -> WIND_CHANGED event
        2. Hazard Agent & Spread Agent recalculate dispersion
        3. Plume geometry GeoJSON updates
        4. Ingress routes intersecting hazard checked
        5. Evacuation recommendations updated
        6. Command Agent replans
        """
        state = self.get_or_create_state(incident_id)
        now_str = datetime.now().strftime("%H:%M:%S")
        prev_dir = state["spread"].get("wind_direction", "NW")

        # 1. Update spread state
        state["spread"]["wind_direction"] = new_direction
        state["spread"]["wind_speed_ms"] = new_speed_ms
        # Slightly expand plume when wind changes
        state["spread"]["red_zone_m"] = int(state["spread"].get("red_zone_m", 380) * 1.15)
        state["spread"]["orange_zone_m"] = int(state["spread"].get("orange_zone_m", 620) * 1.12)
        state["spread"]["yellow_zone_m"] = int(state["spread"].get("yellow_zone_m", 1100) * 1.10)

        # 2. Emit WIND_CHANGED event
        event_engine.emit(
            event_type=EVENT_TYPES["WIND_CHANGED"],
            incident_id=incident_id,
            source="Meteorological Sensor Station",
            severity="WARNING",
            data={
                "previous_direction": prev_dir,
                "new_direction": new_direction,
                "wind_speed_ms": new_speed_ms,
                "new_red_zone_m": state["spread"]["red_zone_m"]
            }
        )

        # 3. Command Agent Closed-Loop Replanning
        command_agent.replan(
            incident_id=incident_id,
            new_events=[f"Wind direction shifted from {prev_dir} to {new_direction} at {new_speed_ms} m/s"],
            environmental_updates={"wind_direction": new_direction, "wind_speed_ms": new_speed_ms}
        )

        # 4. Check affected routes & update evacuation
        state["ai_activity"].insert(0, {
            "time": now_str,
            "agent": "Spread",
            "action": f"Plume cone re-oriented to {new_direction}",
            "details": f"Red zone expanded to {state['spread']['red_zone_m']}m towards western industrial sector",
            "confidence": 0.92
        })
        state["ai_activity"].insert(0, {
            "time": now_str,
            "agent": "Evacuation",
            "action": "Evacuation corridor shifted",
            "details": "Designated Shelter S004 (Velachery) prioritized to avoid toxic downwind cone",
            "confidence": 0.95
        })

        # 5. Create Human Approval entry for updated evacuation boundary
        state["approvals"].insert(0, {
            "action_id": f"AUTH-{uuid.uuid4().hex[:6].upper()}",
            "type": "EVACUATION_EXPANSION",
            "title": f"Approve Expanded Evacuation Perimeter ({new_direction} Vector)",
            "reason": f"Wind shifted to {new_direction}. Plume expanded to {state['spread']['red_zone_m']}m.",
            "people_affected": state["people_at_risk"] + 450,
            "recommended_shelters": ["S004", "S001"],
            "safe_routes_count": 2,
            "status": "PENDING_APPROVAL",
            "risk_level": "URGENT",
            "requested_by": "Agent 10 (Command)",
            "timestamp": now_str
        })

        state["last_updated"] = now_str
        self.live_incidents[incident_id] = state
        return state

    # ----------------- Step 12: Hospital Dynamic State -----------------
    def simulate_hospital_full(self, incident_id: str, hospital_id: str = "H002") -> Dict[str, Any]:
        """
        Simulates: HOSPITAL CAPACITY FULL
        Triggers:
        1. Hospital marked FULL (0 free beds)
        2. Medical Agent finds alternative hospitals
        3. Distance + capacity + ETA recalculated
        4. Casualties reallocated
        5. Command Agent updates response plan
        """
        state = self.get_or_create_state(incident_id)
        now_str = datetime.now().strftime("%H:%M:%S")

        target_hosp = None
        alt_hosp = None
        for h in state.get("hospitals", []):
            if h["hospital_id"] == hospital_id:
                h["status"] = "FULL"
                h["emergency_capacity_free"] = 0
                h["icu_free"] = 0
                target_hosp = h
            elif h["status"] != "FULL" and not alt_hosp:
                alt_hosp = h

        # Emit event
        event_engine.emit(
            event_type=EVENT_TYPES["HOSPITAL_CAPACITY_CHANGED"],
            incident_id=incident_id,
            source="Regional Trauma Network",
            severity="HIGH",
            data={
                "hospital_id": hospital_id,
                "hospital_name": target_hosp.get("name") if target_hosp else hospital_id,
                "status": "FULL",
                "diverted_to": alt_hosp.get("name") if alt_hosp else "Secondary Centers"
            }
        )

        state["ai_activity"].insert(0, {
            "time": now_str,
            "agent": "Medical",
            "action": f"Trauma divert: {target_hosp.get('name') if target_hosp else hospital_id} FULL",
            "details": f"Diverted critical casualties to {alt_hosp.get('name') if alt_hosp else 'General Hospital'} (ETA: {alt_hosp.get('eta_minutes') if alt_hosp else 14}m)",
            "confidence": 0.96
        })

        state["last_updated"] = now_str
        return state

    # ----------------- Step 13: Shelter Dynamic State -----------------
    def simulate_shelter_full(self, incident_id: str, shelter_id: str = "S001") -> Dict[str, Any]:
        """
        Simulates: SHELTER CAPACITY FULL
        Triggers:
        1. Shelter S001 marked FULL (occupancy == capacity)
        2. Evacuation Agent finds alternative safe shelters
        3. Safe route assigned
        4. New allocation proposed
        """
        state = self.get_or_create_state(incident_id)
        now_str = datetime.now().strftime("%H:%M:%S")

        target_shelter = None
        alt_shelter = None
        for s in state.get("shelters", []):
            if s["shelter_id"] == shelter_id:
                s["status"] = "FULL"
                s["current_occupancy"] = s["total_capacity"]
                s["available_capacity"] = 0
                s["fill_rate_pct"] = 100.0
                target_shelter = s
            elif s["status"] != "FULL" and not alt_shelter:
                alt_shelter = s

        event_engine.emit(
            event_type=EVENT_TYPES["SHELTER_CAPACITY_CHANGED"],
            incident_id=incident_id,
            source="Disaster Management Authority",
            severity="WARNING",
            data={
                "shelter_id": shelter_id,
                "status": "FULL",
                "alternative_shelter": alt_shelter.get("name") if alt_shelter else "Secondary Hub"
            }
        )

        state["ai_activity"].insert(0, {
            "time": now_str,
            "agent": "Evacuation",
            "action": f"Shelter {shelter_id} capacity saturated",
            "details": f"Evacuation overflow redirected to {alt_shelter.get('name') if alt_shelter else 'Shelter S004'}",
            "confidence": 0.95
        })

        state["last_updated"] = now_str
        return state

    # ----------------- Step 14: Human-in-the-Loop Approval Gateway -----------------
    def process_human_approval(
        self,
        incident_id: str,
        action_id: str,
        decision: str, # "APPROVE", "MODIFY", "REJECT"
        modifications: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        High-consequence authorization gateway.
        Only after explicit commander approval is an action authorized.
        """
        state = self.get_or_create_state(incident_id)
        now_str = datetime.now().strftime("%H:%M:%S")

        target_approval = None
        for item in state.get("approvals", []):
            if item["action_id"] == action_id:
                target_approval = item
                break

        if not target_approval:
            target_approval = {"action_id": action_id, "title": "Operational Action"}
            state["approvals"].append(target_approval)

        target_approval["status"] = "AUTHORIZED" if decision == "APPROVE" else "MODIFIED" if decision == "MODIFY" else "REJECTED"
        target_approval["decided_at"] = now_str
        target_approval["modifications"] = modifications

        # Emit audit event
        event_engine.emit(
            event_type=EVENT_TYPES["APPROVAL_DECIDED"],
            incident_id=incident_id,
            source="Incident Commander",
            severity="SUCCESS" if decision in ["APPROVE", "MODIFY"] else "WARNING",
            data={
                "action_id": action_id,
                "title": target_approval.get("title"),
                "decision": decision,
                "modifications": modifications
            }
        )

        state["ai_activity"].insert(0, {
            "time": now_str,
            "agent": "Command",
            "action": f"Commander {decision}: {target_approval.get('title')}",
            "details": f"Directive authorized by operational command." + (f" Directive notes: {modifications}" if modifications else ""),
            "confidence": 1.0
        })

        state["last_updated"] = now_str
        return state

    def set_data_mode(self, mode: str) -> str:
        """Toggles between LIVE and SIMULATION operational modes."""
        self.data_mode = "LIVE" if mode.upper() == "LIVE" else "SIMULATION"
        for st in self.live_incidents.values():
            st["data_mode"] = self.data_mode
        return self.data_mode

# Singleton instance
state_manager = LiveIncidentStateManager()
