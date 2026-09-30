"""Simulated plant map built with Plotly (0-100 grid, north is up)."""
import plotly.graph_objects as go
import streamlit as st

from components.hazard_zone import ZONE_COLOR, hazard_polygon, spread_arrow
from components.resource_status import ICONS
from config import COLORS

ROUTE_COLOR = {"open": COLORS["info"], "blocked": COLORS["danger"], "hazard": COLORS["warn"]}
ALL_LAYERS = ["Zones", "Hazards", "Routes", "Teams", "Hospitals", "Shelters"]


def _text_markers(fig, items, name, hover):
    if not items:
        return
    fig.add_trace(go.Scatter(
        x=[i["xy"][0] for i in items], y=[i["xy"][1] for i in items], mode="text",
        text=[i["icon"] for i in items], textfont=dict(size=20),
        hovertext=[hover(i) for i in items], hoverinfo="text", name=name))


def build_figure(incidents, routes, evacuation, resources, hospitals, layers=None, height=480):
    layers = set(layers or ALL_LAYERS)
    fig = go.Figure()

    if "Zones" in layers:
        for z in evacuation.get("zones", []):
            x0, y0, x1, y1 = z["bounds"]
            color = ZONE_COLOR.get(z["action"], COLORS["muted"])
            fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, layer="below",
                          fillcolor=color, opacity=0.13, line=dict(color=color, width=1, dash="dot"))
            fig.add_annotation(x=x0 + 1, y=y1 - 1.5, text=f"{z['name']}: {z['action']}",
                               showarrow=False, xanchor="left", yanchor="top",
                               font=dict(color=color, size=11))

    if "Hazards" in layers:
        for inc in incidents:
            xs, ys = hazard_polygon(inc)
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines", fill="toself", fillcolor="rgba(229,72,77,0.25)",
                line=dict(color=COLORS["danger"], width=1), hoverinfo="text",
                hovertext=f"Predicted hazard area: {inc['location']}", name=f"Hazard {inc['location']}"))
            (x0, y0), (x1, y1) = spread_arrow(inc)
            fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                               showarrow=True, arrowhead=3, arrowwidth=2, arrowcolor=COLORS["warn"], text="")

    if "Routes" in layers:
        for r in routes:
            status = r.get("status", "open")
            fig.add_trace(go.Scatter(
                x=[p[0] for p in r["path"]], y=[p[1] for p in r["path"]], mode="lines",
                line=dict(color=ROUTE_COLOR.get(status, COLORS["muted"]), width=4 if status == "blocked" else 3,
                          dash="dash" if status == "blocked" else "solid"),
                hoverinfo="text", hovertext=f"{r['id']} {r['name']}: {status} {r.get('reason', '')}",
                name=f"{r['id']} ({status})"))
            mid = r["path"][len(r["path"]) // 2]
            fig.add_annotation(x=mid[0], y=mid[1], text=r["id"], showarrow=False,
                               font=dict(size=11, color=COLORS["text"]), bgcolor=COLORS["bg"])

    _text_markers(fig, [{"xy": i["coords"], "icon": "🔥" if "fire" in i["type"].lower() else "💥", **i}
                        for i in incidents],
                  "Incidents", lambda i: f"{i['id']} {i['type']} at {i['location']} (severity {i['severity']})")

    if "Teams" in layers:
        _text_markers(fig, [{"xy": r["position"], "icon": ICONS.get(r["type"], "•"), **r}
                            for r in resources if r.get("position") and r["status"] != "unavailable"],
                      "Teams", lambda r: f"{r['name']}: {r['status']}")
    if "Hospitals" in layers:
        _text_markers(fig, [{"xy": h["coords"], "icon": "🏥", **h} for h in hospitals],
                      "Hospitals", lambda h: f"{h['name']}: {h['available_beds']} beds free")
    if "Shelters" in layers:
        _text_markers(fig, [{"xy": s["coords"], "icon": "🏠", **s} for s in evacuation.get("shelters", [])],
                      "Shelters", lambda s: f"{s['id']} {s['name']}: {s['status']}, {s['available']} places")

    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=COLORS["panel"],
        xaxis=dict(range=[0, 100], visible=False, fixedrange=True),
        yaxis=dict(range=[0, 100], visible=False, scaleanchor="x", fixedrange=True),
        hoverlabel=dict(bgcolor=COLORS["bg"], font_color=COLORS["text"]),
    )
    return fig


def render(incidents, routes, evacuation, resources, hospitals, layers=None, height=480, key="map"):
    fig = build_figure(incidents, routes, evacuation, resources, hospitals, layers, height)
    st.plotly_chart(fig, key=key, config={"displayModeBar": False})