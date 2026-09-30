"""
FastAPI Backend Application for Crisis Command AI.
Exposes REST and real-time WebSocket endpoints for emergency operations:
incident detection, assessment, hazard prediction, dynamic routing,
GPS fleet tracking, hospital/shelter telemetry, event bus, and closed-loop replanning.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import json
import logging
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.data_loader import data_loader
from services.validation import SAFETY_DISCLAIMER
from services.routing import router_service
from services.event_engine import event_engine, EVENT_TYPES
from services.routing_service import routing_service
from services.tracking_service import tracking_service
from services.state_manager import state_manager
from agents import command_agent

logger = logging.getLogger("crisis_backend")

app = FastAPI(
    title="Crisis Command AI — Emergency Coordination Engine",
    version="2.0.0",
    description="Operational Multi-Agent Emergency Response Engine with Dynamic Routing and Closed-Loop Replanning."
)

# Enable CORS for external frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request Models -----------------

class IncidentCreateRequest(BaseModel):
    incident_id: Optional[str] = None
    incident_type: Optional[str] = Field(default="Chemical_Leak", description="Type of incident")
    location: str = Field(default="Plant B", description="Plant or facility identifier")
    chemical: Optional[str] = Field(default="Sulfur Dioxide", description="Chemical substance involved")
    people_affected: int = Field(default=25, ge=0, description="Estimated count of people in affected area")
    fire: bool = Field(default=False, description="Whether active fire is present")
    explosion: bool = Field(default=False, description="Whether explosion occurred")
    severity: int = Field(default=8, ge=1, le=10, description="Severity rating 1-10")
    x: Optional[float] = Field(default=74.0, description="X coordinate")
    y: Optional[float] = Field(default=45.0, description="Y coordinate")

class ReplanRequest(BaseModel):
    new_events: Optional[List[str]] = Field(default=None, description="New events like 'Road blocked'")
    unavailable_resources: Optional[List[str]] = Field(default=None, description="Resource IDs that failed")
    newly_blocked_roads: Optional[List[str]] = Field(default=None, description="Road IDs obstructed")
    environmental_updates: Optional[Dict[str, Any]] = Field(default=None, description="Wind speed, direction updates")
    escalate_severity: bool = Field(default=False, description="Force severity score increase")

class BlockRoadRequest(BaseModel):
    incident_id: str = Field(default="I001")
    road_id: str = Field(default="R03108")

class ChangeWindRequest(BaseModel):
    incident_id: str = Field(default="I001")
    wind_direction: str = Field(default="W")
    wind_speed_ms: float = Field(default=8.5)

class HospitalSurgeRequest(BaseModel):
    incident_id: str = Field(default="I001")
    hospital_id: str = Field(default="H002")

class ShelterSurgeRequest(BaseModel):
    incident_id: str = Field(default="I001")
    shelter_id: str = Field(default="S001")

class VehicleFailureRequest(BaseModel):
    incident_id: str = Field(default="I001")
    resource_id: str = Field(default="R0433")

class DataModeRequest(BaseModel):
    mode: str = Field(..., description="'LIVE' or 'SIMULATION'")

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="'APPROVE', 'MODIFY', or 'REJECT'")
    modifications: Optional[str] = Field(default=None, description="Commander directives or modifications")

class ResponderStatusRequest(BaseModel):
    status: str = Field(..., description="'ARRIVED', 'ENGAGED', 'SOS', 'EN_ROUTE'")
    notes: Optional[str] = Field(default=None, description="Field notes from responder")

# ----------------- System & Health Endpoints -----------------

@app.get("/", tags=["System"])
def root_index():
    return {
        "title": "Crisis Command AI — Emergency Coordination Engine",
        "status": "online",
        "operational_mode": state_manager.data_mode,
        "documentation": "/docs",
        "health": "/api/health",
        "react_website": "http://localhost:3000"
    }

@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "engine": "Crisis Command Operational Engine",
        "data_mode": state_manager.data_mode,
        "agents_active": 10,
        "active_incidents_tracked": len(state_manager.live_incidents),
        "disclaimer": SAFETY_DISCLAIMER,
        "timestamp": datetime.now().isoformat()
    }

def sanitize_records(df: pd.DataFrame, limit: int = 100) -> List[Dict[str, Any]]:
    subset = df.head(limit).copy()
    subset = subset.where(pd.notnull(subset), None)
    return subset.to_dict(orient="records")

# ----------------- Incident Management -----------------

@app.get("/api/incidents", tags=["Incidents"])
def list_incidents(limit: int = Query(default=50, ge=1, le=500)):
    """Returns active incidents and catalog."""
    df = data_loader.get_incidents()
    records = sanitize_records(df, limit)
    
    # Prepend any currently active dynamic incidents
    active_summaries = []
    for inc_id, st in state_manager.live_incidents.items():
        active_summaries.append({
            "incident_id": inc_id,
            "plant": st["location"],
            "type": st["type"],
            "severity": st["severity_score"],
            "chemical": st["chemical"],
            "people_affected": st.get("people_at_risk", 25),
            "status": st.get("status", "RESPONSE_IN_PROGRESS")
        })

    return {
        "total_active": len(active_summaries),
        "active_incidents": active_summaries,
        "catalog_incidents": records
    }

@app.post("/api/incidents", tags=["Incidents"])
def create_incident(payload: IncidentCreateRequest):
    """
    Creates and initiates emergency response for a new incident.
    Executes: CREATE INCIDENT -> Detection -> Assessment -> Hazard -> Spread -> Resources -> Routing -> Medical -> Command
    """
    inc_id = payload.incident_id or f"I{len(state_manager.live_incidents)+1:03d}"
    inp = payload.model_dump()
    inp["incident_id"] = inc_id

    # Create through central state manager
    new_state = state_manager.get_or_create_state(inc_id, custom_input=inp)
    return {
        "status": "active_response_initiated",
        "incident_id": inc_id,
        "state": new_state
    }

@app.get("/api/incidents/{incident_id}", tags=["Incidents"])
def get_incident_canonical_state(incident_id: str):
    """Retrieves full canonical incident state consumed by all frontend operational views."""
    try:
        return state_manager.get_or_create_state(incident_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load incident {incident_id}: {str(exc)}")

@app.get("/api/incidents/{incident_id}/live-state", tags=["Incidents"])
def get_live_incident_state_alias(incident_id: str):
    """Alias for backwards compatibility with existing UI."""
    return get_incident_canonical_state(incident_id)

@app.post("/api/incidents/{incident_id}/tick-telemetry", tags=["Live System"])
def tick_telemetry(incident_id: str):
    """Advances GPS simulation along road geometry and updates dynamic ETAs."""
    try:
        return state_manager.tick_telemetry(incident_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Telemetry tick failed: {str(exc)}")

# ----------------- Step 10 & 25: Simulation Control Center -----------------

@app.post("/api/simulation/block-road", tags=["Simulation Control"])
def simulate_block_road(payload: BlockRoadRequest):
    """
    Simulates: BLOCK ROAD
    ROAD BLOCKED -> EVENT ENGINE -> COMMAND AGENT -> identify affected responders -> ROUTE AGENT -> calculate alternative -> update ETA -> update map -> notify responder -> audit event
    """
    try:
        return state_manager.simulate_block_road(
            incident_id=payload.incident_id,
            road_id=payload.road_id
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Road block simulation failed: {str(exc)}")

@app.post("/api/simulation/reopen-road", tags=["Simulation Control"])
def simulate_reopen_road(payload: BlockRoadRequest):
    """Simulates: REOPEN ROAD and restores normal ingress route."""
    try:
        return state_manager.simulate_reopen_road(
            incident_id=payload.incident_id,
            road_id=payload.road_id
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Road reopen simulation failed: {str(exc)}")

@app.post("/api/simulation/change-wind", tags=["Simulation Control"])
def simulate_change_wind(payload: ChangeWindRequest):
    """
    Simulates: CHANGE WIND (e.g. NW -> W)
    Wind changed -> Hazard Agent -> Spread Agent -> New GeoJSON -> Hazard zones change -> Routes intersecting checked -> Evacuation recommendation updated -> Command replans
    """
    try:
        return state_manager.simulate_change_wind(
            incident_id=payload.incident_id,
            new_direction=payload.wind_direction,
            new_speed_ms=payload.wind_speed_ms
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Wind change simulation failed: {str(exc)}")

@app.post("/api/simulation/hospital-full", tags=["Simulation Control"])
def simulate_hospital_full(payload: HospitalSurgeRequest):
    """
    Simulates: HOSPITAL FULL
    Hospital FULL -> Medical Agent -> Find alternatives -> Distance + Capacity + ETA -> Update allocation -> Command replans
    """
    try:
        return state_manager.simulate_hospital_full(
            incident_id=payload.incident_id,
            hospital_id=payload.hospital_id
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Hospital saturation simulation failed: {str(exc)}")

@app.post("/api/simulation/shelter-full", tags=["Simulation Control"])
def simulate_shelter_full(payload: ShelterSurgeRequest):
    """
    Simulates: SHELTER FULL
    Shelter FULL -> Evacuation Agent -> Find alternative -> Safe route -> New allocation -> Command replans
    """
    try:
        return state_manager.simulate_shelter_full(
            incident_id=payload.incident_id,
            shelter_id=payload.shelter_id
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Shelter saturation simulation failed: {str(exc)}")

@app.post("/api/simulation/mode", tags=["Simulation Control"])
def set_simulation_mode(payload: DataModeRequest):
    """Toggles between LIVE and SIMULATION data mode."""
    new_mode = state_manager.set_data_mode(payload.mode)
    return {"operational_mode": new_mode}

# ----------------- Step 14: Human-in-the-Loop Gateway -----------------

@app.post("/api/incidents/{incident_id}/approvals/{action_id}/decision", tags=["Human Approval"])
def record_human_approval(
    incident_id: str,
    action_id: str,
    payload: ApprovalDecisionRequest
):
    """
    Human-in-the-Loop Gateway: incident commander authorizes, modifies, or rejects high-consequence AI directives.
    """
    try:
        return state_manager.process_human_approval(
            incident_id=incident_id,
            action_id=action_id,
            decision=payload.decision,
            modifications=payload.modifications
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Approval decision failed: {str(exc)}")

# ----------------- Step 27: Audit & Event Bus -----------------

@app.get("/api/events", tags=["Audit Log"])
def get_audit_events(incident_id: Optional[str] = None, limit: int = 50):
    """Returns chronological audit log of all system events from the central event engine."""
    events = event_engine.get_history(incident_id=incident_id, limit=limit)
    return {
        "total_events": len(events),
        "events": events
    }

# ----------------- Field Responder Terminal -----------------

@app.get("/api/responders", tags=["Field Responder"])
def get_all_responders():
    """Lists all active fleet responders with live telemetry and ETAs."""
    return {"responders": tracking_service.get_all_units()}

@app.get("/api/responder/{resource_id}", tags=["Field Responder"])
def get_responder_terminal_state(resource_id: str):
    """Returns tactical telemetry, turn-by-turn navigation, and hazard radar for field unit."""
    clean_id = resource_id.strip().upper()
    unit = tracking_service.get_unit(clean_id)
    
    # If not in active fleet, register or pull default
    if not unit:
        st = state_manager.get_or_create_state("I001")
        if st.get("responders"):
            unit = st["responders"][0]

    if not unit:
        raise HTTPException(status_code=404, detail=f"Responder unit '{resource_id}' not found.")

    return {
        "unit": unit,
        "incident_overview": state_manager.get_or_create_state("I001"),
        "turn_by_turn": unit.get("turn_by_turn", [])
    }

@app.post("/api/responder/{resource_id}/status", tags=["Field Responder"])
def update_field_responder_status(resource_id: str, payload: ResponderStatusRequest):
    """Updates responder status from the field (ARRIVED, ENGAGED, SOS, EN_ROUTE)."""
    clean_id = resource_id.strip().upper()
    unit = tracking_service.get_unit(clean_id)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Responder '{resource_id}' not found.")

    unit["status"] = payload.status
    if payload.status == "ARRIVED":
        unit["progress_pct"] = 100.0
        unit["eta_minutes"] = 0.0

    event_engine.emit(
        event_type=EVENT_TYPES["GPS_UPDATED"],
        incident_id="I001",
        source=f"Field Unit {clean_id}",
        severity="CRITICAL" if payload.status == "SOS" else "SUCCESS" if payload.status == "ARRIVED" else "INFO",
        data={"unit_id": clean_id, "status": payload.status, "notes": payload.notes}
    )

    return {"success": True, "unit": unit}

# ----------------- Step 21: Public Safety Portal -----------------

@app.get("/api/public/incident/{incident_id}", tags=["Public Safety"])
def get_public_safety_portal_state(incident_id: str):
    """
    Returns civilian-safe advisory: active emergency, danger zone,
    recommended action, designated shelter, emergency contacts.
    """
    st = state_manager.get_or_create_state(incident_id)
    spread = st.get("spread", {})
    shelters = st.get("shelters", [])

    return {
        "incident_id": st.get("incident_id"),
        "status": "ALERT_ACTIVE",
        "emergency_headline": f"CHEMICAL ALERT: {st.get('chemical', 'Toxic Vapor')} at {st.get('location')}",
        "precautionary_instruction": "Shelter indoors if within 1.2km downwind. Close windows, shut HVAC intake. Evacuate immediately if in RED EXCLUSION ZONE.",
        "wind_vector": f"{spread.get('wind_speed_ms', 6.5)} m/s heading {spread.get('wind_direction', 'NW')}",
        "hazard_zones": {
            "red_exclusion": f"{spread.get('red_zone_m', 380)} meters (Immediate Evacuation Required)",
            "orange_buffer": f"{spread.get('orange_zone_m', 620)} meters (Shelter-in-Place)",
            "yellow_advisory": f"{spread.get('yellow_zone_m', 1100)} meters (General Caution)"
        },
        "recommended_shelters": shelters[:2],
        "emergency_helpline": {
            "central_control": "112",
            "poison_control": "1800-425-1111",
            "medical_dispatch": "108"
        },
        "last_updated": st.get("last_updated")
    }

# ----------------- Step 11 & 24: Real-time WebSockets -----------------

@app.websocket("/ws/incidents/{incident_id}")
async def websocket_incident_stream(websocket: WebSocket, incident_id: str):
    """
    Real-time persistent WebSocket connection for incident operations workspace.
    Continuously pushes state updates and events as they occur.
    """
    await websocket.accept()
    q = asyncio.Queue()
    event_engine.register_ws_queue(q)

    # Send initial full state immediately upon connect
    try:
        initial_state = state_manager.get_or_create_state(incident_id)
        await websocket.send_json({"type": "FULL_STATE", "data": initial_state})
    except Exception as e:
        logger.error(f"Error sending initial state: {e}")

    try:
        while True:
            # Wait for event from queue or periodic telemetry ping
            try:
                event = await asyncio.wait_for(q.get(), timeout=2.5)
                # Send event and latest state
                current_state = state_manager.get_or_create_state(incident_id)
                await websocket.send_json({
                    "type": "EVENT_BROADCAST",
                    "event": event,
                    "state": current_state
                })
            except asyncio.TimeoutError:
                # Periodic telemetry heartbeat update
                current_state = state_manager.get_or_create_state(incident_id)
                await websocket.send_json({
                    "type": "HEARTBEAT",
                    "state": current_state
                })
    except (WebSocketDisconnect, ConnectionResetError):
        pass
    finally:
        event_engine.unregister_ws_queue(q)

@app.websocket("/ws/tracking")
async def websocket_fleet_tracking(websocket: WebSocket):
    """Real-time GPS telemetry stream for all responders."""
    await websocket.accept()
    try:
        while True:
            fleet = tracking_service.get_all_units()
            await websocket.send_json({"type": "FLEET_UPDATE", "fleet": fleet})
            await asyncio.sleep(2.5)
    except (WebSocketDisconnect, ConnectionResetError):
        pass

@app.websocket("/ws/events")
async def websocket_event_bus(websocket: WebSocket):
    """Global system event bus stream."""
    await websocket.accept()
    q = asyncio.Queue()
    event_engine.register_ws_queue(q)
    try:
        while True:
            evt = await q.get()
            await websocket.send_json({"type": "SYSTEM_EVENT", "event": evt})
    except (WebSocketDisconnect, ConnectionResetError):
        pass
    finally:
        event_engine.unregister_ws_queue(q)
