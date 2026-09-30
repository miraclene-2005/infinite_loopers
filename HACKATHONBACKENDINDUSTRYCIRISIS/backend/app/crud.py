import json
from datetime import datetime
from sqlalchemy.orm import Session

from .models import (
    Incident, Resource, Hospital, Route, EvacuationZone, Shelter, Alert, ResponsePlanModel
)
from .agents import DetectionAgent, RiskAssessmentAgent, CommandAgent, ReplanningAgent


def _now():
    return datetime.now().strftime("%H:%M:%S")


def seed_database_if_empty(db: Session):
    if db.query(Incident).first():
        return

    t = _now()

    # 1. Default Incident
    inc = Incident(
        id="INC-001",
        incident_type="Chemical leak and fire",
        location="Factory A",
        coords_x=30.0,
        coords_y=65.0,
        severity=8,
        severity_label="critical",
        people_affected=35,
        chemical="Solvent / Volatile chemical",
        fire=True,
        status="active",
        source="Gas sensor GS-14, CCTV cam 7",
        reported_at=t,
        confirmed=True,
        risk_chemical="high",
        risk_fire="high",
        risk_explosion="medium",
        risk_structural="low",
        domino_effect="Possible: solvent storage 40 m east",
        spread_direction="SE",
        wind="From NW, 14 km/h",
        hazard_radius=11.0
    )
    db.add(inc)

    # 2. Resources
    resources_data = [
        ("F01", "Fire Team 01", "Fire", "busy", "INC-001", 30.0, 58.0),
        ("F02", "Fire Team 02", "Fire", "available", None, 10.0, 8.0),
        ("F03", "Fire Team 03", "Fire", "available", None, 12.0, 8.0),
        ("F04", "Fire Team 04", "Fire", "available", None, 14.0, 8.0),
        ("H01", "Hazmat Team 01", "Hazmat", "busy", "INC-001", 34.0, 58.0),
        ("H02", "Hazmat Team 02", "Hazmat", "available", None, 10.0, 11.0),
        ("R01", "Rescue Team 01", "Rescue", "busy", "INC-001", 26.0, 58.0),
        ("R02", "Rescue Team 02", "Rescue", "available", None, 12.0, 11.0),
        ("R03", "Rescue Team 03", "Rescue", "available", None, 14.0, 11.0),
        ("A01", "Ambulance 01", "Ambulance", "busy", "INC-001", 22.0, 60.0),
        ("A02", "Ambulance 02", "Ambulance", "available", None, 16.0, 8.0),
        ("A03", "Ambulance 03", "Ambulance", "available", None, 18.0, 8.0),
        ("A04", "Ambulance 04", "Ambulance", "available", None, 16.0, 11.0),
        ("A05", "Ambulance 05", "Ambulance", "available", None, 18.0, 11.0),
        ("A06", "Ambulance 06", "Ambulance", "available", None, 20.0, 11.0),
    ]
    for rid, name, rtype, status, assigned, px, py in resources_data:
        db.add(Resource(
            id=rid, name=name, resource_type=rtype, status=status,
            available=(status == "available"), assigned_to=assigned,
            position_x=px, position_y=py, location="Factory A" if assigned else "Base Station"
        ))

    # 3. Hospitals
    db.add(Hospital(id="HSP-1", name="City General Hospital", coords_x=95.0, coords_y=94.0, capacity=40, available_beds=12, burn_unit=True, travel_min=14, status="accepting"))
    db.add(Hospital(id="HSP-2", name="Metro Care Hospital", coords_x=5.0, coords_y=95.0, capacity=25, available_beds=9, burn_unit=False, travel_min=11, status="accepting"))

    # 4. Routes
    routes_data = [
        ("R1", "Main gate to Junction 1", [[5, 15], [30, 15]], "open", 2, ""),
        ("R2", "Junction 1 to Factory A (central road)", [[30, 15], [52, 38], [36, 58]], "open", 4, ""),
        ("R3", "Junction 1 to Factory A (west road)", [[30, 15], [18, 40], [26, 60]], "open", 5, ""),
        ("R4", "Junction 1 to Factory B (east ring)", [[30, 15], [78, 15], [78, 45], [66, 48]], "open", 6, ""),
    ]
    for r_id, r_name, r_path, r_status, r_min, r_reason in routes_data:
        db.add(Route(id=r_id, name=r_name, path_json=json.dumps(r_path), status=r_status, travel_min=r_min, reason=r_reason))

    # 5. Evacuation Zones
    zones_data = [
        ("A", "Zone A", "evacuate", 120, [18, 54, 46, 82]),
        ("B", "Zone B", "monitor", 180, [50, 34, 76, 60]),
        ("C", "Zone C", "monitor", 50, [50, 64, 80, 90]),
        ("D", "Zone D", "safe", 0, [4, 4, 36, 34]),
    ]
    for zid, zname, zact, zpop, zbounds in zones_data:
        db.add(EvacuationZone(id=zid, name=zname, action=zact, population=zpop, bounds_json=json.dumps(zbounds), incident_id="INC-001"))

    # 6. Shelters
    shelters_data = [
        ("S01", "Admin block assembly point", 70.0, 22.0, 200, 200, "assigned"),
        ("S02", "Canteen hall", 85.0, 80.0, 150, 0, "full"),
        ("S03", "North gate shelter", 10.0, 84.0, 350, 350, "standby"),
    ]
    for sid, sname, sx, sy, scap, savail, sstat in shelters_data:
        db.add(Shelter(id=sid, name=sname, coords_x=sx, coords_y=sy, capacity=scap, available=savail, status=sstat, incident_id="INC-001"))

    # 7. Alerts
    cmd = CommandAgent()
    initial_alerts = cmd.generate_alerts({"type": "Chemical leak and fire", "location": "Factory A", "severity": 8}, phase=0)
    for a in initial_alerts:
        db.add(Alert(incident_id="INC-001", time=a["time"], audience=a["audience"], severity=a["severity"], message=a["message"]))

    # 8. Response Plan
    plan_dict = cmd.build_plan(incident_id="INC-001", incidents=[], phase=0, version=1, status="approved")
    db.add(ResponsePlanModel(
        incident_id="INC-001",
        version=plan_dict["version"],
        status=plan_dict["status"],
        generated_at=plan_dict["generated_at"],
        approved_by=plan_dict["approved_by"],
        approved_at=plan_dict["approved_at"],
        pipeline_json=json.dumps(plan_dict["pipeline"]),
        changes_json=json.dumps(plan_dict["changes"]),
        approval_items_json=json.dumps(plan_dict["approval_items"]),
        previous_json=json.dumps(plan_dict["previous"]),
        current_json=json.dumps(plan_dict["current"]),
    ))

    db.commit()


def get_all_incidents(db: Session):
    seed_database_if_empty(db)
    records = db.query(Incident).all()
    out = []
    for r in records:
        out.append({
            "id": r.id,
            "type": r.incident_type,
            "location": r.location,
            "coords": [r.coords_x, r.coords_y],
            "severity": r.severity,
            "severity_label": r.severity_label,
            "people_affected": r.people_affected,
            "status": r.status,
            "source": r.source,
            "reported_at": r.reported_at or _now(),
            "confirmed": r.confirmed,
            "uncertain_fields": [] if r.confirmed else ["people_affected"],
            "risk": {
                "chemical": r.risk_chemical,
                "fire": r.risk_fire,
                "explosion": r.risk_explosion,
                "structural": r.risk_structural,
                "domino_effect": r.domino_effect,
                "spread_direction": r.spread_direction,
                "wind": r.wind,
                "hazard_radius": r.hazard_radius
            }
        })
    return out


def create_incident_with_agents(db: Session, data: dict):
    seed_database_if_empty(db)
    
    # 1. Detection Agent
    detection_agent = DetectionAgent()
    processed = detection_agent.process_incident(data)

    # 2. Risk Assessment Agent
    risk_agent = RiskAssessmentAgent()
    risk = risk_agent.evaluate_risk(processed)

    # Count existing incidents to assign ID
    count = db.query(Incident).count()
    new_id = f"INC-{count + 1:03d}"

    t = _now()
    coords = data.get("coords") or [50.0, 50.0]

    inc = Incident(
        id=new_id,
        incident_type=processed["type"],
        location=processed["location"],
        coords_x=coords[0],
        coords_y=coords[1],
        severity=processed["severity"],
        severity_label=processed["severity_label"],
        people_affected=processed["people_affected"],
        chemical=processed.get("chemical"),
        fire=processed.get("fire", False),
        status="active",
        source=processed["source"],
        reported_at=t,
        confirmed=processed["confirmed"],
        risk_chemical=risk["chemical"],
        risk_fire=risk["fire"],
        risk_explosion=risk["explosion"],
        risk_structural=risk["structural"],
        domino_effect=risk["domino_effect"],
        spread_direction=risk["spread_direction"],
        wind=risk["wind"],
        hazard_radius=risk["hazard_radius"]
    )
    db.add(inc)

    # Add Alert
    alert_msg = f"New incident reported by {processed['source']}: {processed['type']} at {processed['location']}."
    db.add(Alert(incident_id=new_id, time=t, audience="control_room", severity=processed["severity_label"], message=alert_msg))

    db.commit()
    db.refresh(inc)

    return {
        "id": inc.id,
        "type": inc.incident_type,
        "location": inc.location,
        "coords": [inc.coords_x, inc.coords_y],
        "severity": inc.severity,
        "severity_label": inc.severity_label,
        "people_affected": inc.people_affected,
        "status": inc.status,
        "source": inc.source,
        "reported_at": inc.reported_at,
        "confirmed": inc.confirmed,
        "uncertain_fields": [] if inc.confirmed else ["people_affected"],
        "risk": risk
    }


def get_all_resources(db: Session):
    seed_database_if_empty(db)
    records = db.query(Resource).all()
    return [{
        "id": r.id,
        "name": r.name,
        "type": r.resource_type,
        "status": r.status,
        "assigned_to": r.assigned_to,
        "position": [r.position_x, r.position_y],
        "note": r.note or "",
        "changed": r.changed
    } for r in records]


def get_all_hospitals(db: Session):
    seed_database_if_empty(db)
    records = db.query(Hospital).all()
    return [{
        "id": h.id,
        "name": h.name,
        "coords": [h.coords_x, h.coords_y],
        "capacity": h.capacity,
        "available_beds": h.available_beds,
        "burn_unit": h.burn_unit,
        "travel_min": h.travel_min,
        "status": h.status
    } for h in records]


def get_all_routes(db: Session):
    seed_database_if_empty(db)
    records = db.query(Route).all()
    return [{
        "id": r.id,
        "name": r.name,
        "path": json.loads(r.path_json),
        "status": r.status,
        "travel_min": r.travel_min,
        "reason": r.reason or ""
    } for r in records]


def get_evacuation_data(db: Session, incident_id: str):
    seed_database_if_empty(db)
    zones = db.query(EvacuationZone).all()
    shelters = db.query(Shelter).all()
    affected = sum(z.population for z in zones if z.action == "evacuate")
    return {
        "incident_id": incident_id,
        "affected_population": affected if affected > 0 else 150,
        "zones": [{
            "id": z.id,
            "name": z.name,
            "action": z.action,
            "population": z.population,
            "bounds": json.loads(z.bounds_json)
        } for z in zones],
        "shelters": [{
            "id": s.id,
            "name": s.name,
            "coords": [s.coords_x, s.coords_y],
            "capacity": s.capacity,
            "available": s.available,
            "status": s.status
        } for s in shelters]
    }


def get_alerts_data(db: Session, incident_id: str):
    seed_database_if_empty(db)
    alerts = db.query(Alert).order_by(Alert.id.desc()).all()
    return [{
        "time": a.time,
        "audience": a.audience,
        "severity": a.severity,
        "message": a.message
    } for a in alerts]


def get_response_plan_data(db: Session, incident_id: str):
    seed_database_if_empty(db)
    plan = db.query(ResponsePlanModel).order_by(ResponsePlanModel.version.desc()).first()
    if not plan:
        cmd = CommandAgent()
        plan_dict = cmd.build_plan(incident_id=incident_id, incidents=[], phase=0, version=1, status="approved")
        return plan_dict

    return {
        "incident_id": plan.incident_id,
        "version": plan.version,
        "status": plan.status,
        "generated_at": plan.generated_at,
        "approved_by": plan.approved_by,
        "approved_at": plan.approved_at,
        "pipeline": json.loads(plan.pipeline_json),
        "changes": json.loads(plan.changes_json),
        "approval_items": json.loads(plan.approval_items_json),
        "previous": json.loads(plan.previous_json),
        "current": json.loads(plan.current_json),
    }


def trigger_replanning_workflow(db: Session, incident_id: str, event: dict):
    seed_database_if_empty(db)
    current_plan = db.query(ResponsePlanModel).order_by(ResponsePlanModel.version.desc()).first()
    curr_v = current_plan.version if current_plan else 1

    replanning_agent = ReplanningAgent()

    if event and event.get("type") == "scenario":
        # Mid-incident simulation scenario
        t = _now()
        # 1. Add Factory B Explosion
        exp = Incident(
            id="INC-002",
            incident_type="Explosion",
            location="Factory B",
            coords_x=64.0,
            coords_y=48.0,
            severity=9,
            severity_label="critical",
            people_affected=20,
            chemical="Chlorine line rupture",
            fire=True,
            status="active",
            source="Worker radio report, pressure sensor PS-3",
            reported_at=t,
            confirmed=False,
            risk_chemical="high",
            risk_fire="high",
            risk_explosion="high",
            risk_structural="high",
            domino_effect="Likely: chlorine line ruptured",
            spread_direction="SE",
            wind="From NW, 18 km/h",
            hazard_radius=13.0
        )
        db.merge(exp)

        # 2. Hazmat H01 failure
        h01 = db.query(Resource).filter(Resource.id == "H01").first()
        if h01:
            h01.status = "unavailable"
            h01.available = False
            h01.assigned_to = None
            h01.note = "Suit breach, team withdrawn for decontamination"
            h01.changed = True

        # 3. Route R2 blocked
        r2 = db.query(Route).filter(Route.id == "R2").first()
        if r2:
            r2.status = "blocked"
            r2.reason = "Passes through Factory B blast zone"

        # 4. Shelters & Zones update
        s01 = db.query(Shelter).filter(Shelter.id == "S01").first()
        if s01:
            s01.status = "unsafe"
            s01.available = 0
        s03 = db.query(Shelter).filter(Shelter.id == "S03").first()
        if s03:
            s03.status = "assigned"
            s03.available = 350

        # Add alerts
        cmd = CommandAgent()
        new_alerts = cmd.generate_alerts({}, phase=1)
        for a in new_alerts:
            db.add(Alert(incident_id=incident_id, time=a["time"], audience=a["audience"], severity=a["severity"], message=a["message"]))

        # Build plan
        plan_dict = replanning_agent.replan_crisis(incident_id=incident_id, current_version=curr_v, event={"type": "scenario"})
    else:
        # Manual replan
        plan_dict = replanning_agent.replan_crisis(incident_id=incident_id, current_version=curr_v, event=event)

    new_plan_row = ResponsePlanModel(
        incident_id=incident_id,
        version=plan_dict["version"],
        status=plan_dict["status"],
        generated_at=plan_dict["generated_at"],
        approved_by=plan_dict["approved_by"],
        approved_at=plan_dict["approved_at"],
        pipeline_json=json.dumps(plan_dict["pipeline"]),
        changes_json=json.dumps(plan_dict["changes"]),
        approval_items_json=json.dumps(plan_dict["approval_items"]),
        previous_json=json.dumps(plan_dict["previous"]),
        current_json=json.dumps(plan_dict["current"]),
    )
    db.add(new_plan_row)
    db.commit()

    return plan_dict


def approve_response_plan(db: Session, incident_id: str, operator: str = "Control room operator"):
    seed_database_if_empty(db)
    plan = db.query(ResponsePlanModel).order_by(ResponsePlanModel.version.desc()).first()
    if plan:
        t = _now()
        plan.status = "approved"
        plan.approved_by = operator
        plan.approved_at = t
        
        # update pipeline
        pipeline = json.loads(plan.pipeline_json)
        for p in pipeline:
            if p["stage"] == "Approval":
                p["status"] = "approved"
        plan.pipeline_json = json.dumps(pipeline)

        # clear changed flag on resources
        for r in db.query(Resource).all():
            r.changed = False

        db.add(Alert(
            incident_id=incident_id,
            time=t,
            audience="control_room",
            severity="medium",
            message=f"Response plan v{plan.version} approved by {operator}. Orders sent to teams."
        ))

        db.commit()
        return get_response_plan_data(db, incident_id)

    return {}


def reset_crisis_state(db: Session):
    db.query(Incident).delete()
    db.query(Resource).delete()
    db.query(Hospital).delete()
    db.query(Route).delete()
    db.query(EvacuationZone).delete()
    db.query(Shelter).delete()
    db.query(Alert).delete()
    db.query(ResponsePlanModel).delete()
    db.commit()
    seed_database_if_empty(db)
    return {"status": "Database reset to initial crisis command state"}