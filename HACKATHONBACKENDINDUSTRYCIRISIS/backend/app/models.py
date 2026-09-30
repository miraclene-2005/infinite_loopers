# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, Float, String, Boolean, Text
from datetime import datetime
from .database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True)
    incident_type = Column(String, nullable=False)
    location = Column(String, nullable=False)
    coords_x = Column(Float, default=30.0)
    coords_y = Column(Float, default=65.0)
    severity = Column(Integer, nullable=False)
    severity_label = Column(String, default="critical")
    people_affected = Column(Integer, default=0)
    chemical = Column(String, nullable=True)
    fire = Column(Boolean, default=False)
    status = Column(String, default="active")
    source = Column(String, default="Sensor")
    reported_at = Column(String, default="")
    confirmed = Column(Boolean, default=True)

    risk_chemical = Column(String, default="high")
    risk_fire = Column(String, default="high")
    risk_explosion = Column(String, default="medium")
    risk_structural = Column(String, default="low")
    domino_effect = Column(String, default="Possible: solvent storage 40 m east")
    spread_direction = Column(String, default="SE")
    wind = Column(String, default="From NW, 14 km/h")
    hazard_radius = Column(Float, default=11.0)


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    location = Column(String, default="On site")
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    available = Column(Boolean, default=True)
    status = Column(String, default="available")  # available, busy, unavailable
    assigned_to = Column(String, nullable=True)
    note = Column(String, default="")
    changed = Column(Boolean, default=False)


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    coords_x = Column(Float, default=0.0)
    coords_y = Column(Float, default=0.0)
    capacity = Column(Integer, default=50)
    available_beds = Column(Integer, default=10)
    burn_unit = Column(Boolean, default=False)
    travel_min = Column(Integer, default=10)
    status = Column(String, default="accepting")


class Route(Base):
    __tablename__ = "routes"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    path_json = Column(Text, default="[]")  # JSON string of coordinates [[x,y],...]
    status = Column(String, default="open")  # open, blocked
    travel_min = Column(Integer, default=5)
    reason = Column(String, default="")


class EvacuationZone(Base):
    __tablename__ = "evacuation_zones"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    action = Column(String, default="monitor")  # evacuate, monitor, safe
    population = Column(Integer, default=0)
    bounds_json = Column(Text, default="[0,0,0,0]")  # JSON string [x0, y0, x1, y1]
    incident_id = Column(String, default="INC-001")


class Shelter(Base):
    __tablename__ = "shelters"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    coords_x = Column(Float, default=0.0)
    coords_y = Column(Float, default=0.0)
    capacity = Column(Integer, default=100)
    available = Column(Integer, default=100)
    status = Column(String, default="standby")  # assigned, full, standby, unsafe
    incident_id = Column(String, default="INC-001")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(String, default="INC-001")
    time = Column(String, default="")
    audience = Column(String, default="control_room")
    severity = Column(String, default="medium")
    message = Column(String, nullable=False)


class ResponsePlanModel(Base):
    __tablename__ = "response_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(String, default="INC-001", index=True)
    version = Column(Integer, default=1)
    status = Column(String, default="approved")
    generated_at = Column(String, default="")
    approved_by = Column(String, nullable=True)
    approved_at = Column(String, nullable=True)
    pipeline_json = Column(Text, default="[]")
    changes_json = Column(Text, default="[]")
    approval_items_json = Column(Text, default="[]")
    previous_json = Column(Text, default="[]")
    current_json = Column(Text, default="[]")