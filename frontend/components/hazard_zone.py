"""Geometry for hazard spread areas and zone colours on the plant map."""
import math

from config import COLORS

COMPASS = {"N": 90, "NE": 45, "E": 0, "SE": -45, "S": -90, "SW": -135, "W": 180, "NW": 135}

ZONE_COLOR = {"evacuate": COLORS["danger"], "monitor": COLORS["warn"], "safe": COLORS["ok"]}


def hazard_polygon(incident, points=48):
    """Ellipse around the incident, stretched and shifted in the spread direction."""
    cx, cy = incident["coords"]
    risk = incident.get("risk", {})
    r = float(risk.get("hazard_radius", 10))
    theta = math.radians(COMPASS.get(risk.get("spread_direction", ""), 0))
    major, minor, shift = r * 1.5, r * 0.9, r * 0.6
    ox, oy = cx + shift * math.cos(theta), cy + shift * math.sin(theta)
    xs, ys = [], []
    for i in range(points + 1):
        t = 2 * math.pi * i / points
        ex, ey = major * math.cos(t), minor * math.sin(t)
        xs.append(ox + ex * math.cos(theta) - ey * math.sin(theta))
        ys.append(oy + ex * math.sin(theta) + ey * math.cos(theta))
    return xs, ys


def spread_arrow(incident):
    """Start and end points for the spread-direction arrow."""
    cx, cy = incident["coords"]
    risk = incident.get("risk", {})
    theta = math.radians(COMPASS.get(risk.get("spread_direction", ""), 0))
    length = float(risk.get("hazard_radius", 10)) * 1.9
    return (cx, cy), (cx + length * math.cos(theta), cy + length * math.sin(theta))