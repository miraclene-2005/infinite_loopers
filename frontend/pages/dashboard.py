"""
Modern control-room dashboard with a premium, realistic crisis command layout.
Integrates live multi-agent AI response, hazard map, alert feed, and plan approvals.
"""
import streamlit as st

import config
from components import alert_panel, approval_panel, incident_card, map_view, resource_status
from components.styles import page_header, pill, metric_card
from services import api_client as api

iid = st.session_state.get("active_incident", config.DEFAULT_INCIDENT_ID)

# Fetch live backend data via multi-agent API client
incidents = api.get_incidents()
resources = api.get_resources()
hospitals = api.get_hospitals()
routes = api.get_routes()
evacuation = api.get_evacuation(iid)
alerts = api.get_alerts(iid)
plan = api.get_response_plan(iid)

source = api.data_source()
source_pill = pill("API Live", "ok") if source == "live" else pill("Mock", "warn")

page_header("Industrial Crisis Command Center",
            f"Riverside Chemical Complex • Multi-Agent AI System Active",
            status_html=f"Backend status: {source_pill}")

# ---------------------------------------------------------------- KPIs
c1, c2, c3, c4, c5 = st.columns(5)
active_count = len(incidents)
c1.metric("Active Incidents", active_count, f"{'CRITICAL' if active_count > 1 else 'ELEVATED'}")

max_sev = max((i.get("severity", 0) for i in incidents), default=0)
c2.metric("Threat Level", f"{max_sev}/10", "HIGH RISK" if max_sev >= 8 else "MODERATE")

plan_status = plan.get("status", "pending_approval")
c3.metric("Response Plan", f"v{plan.get('version', 1)}", plan_status.replace("_", " ").upper())

busy_teams = sum(1 for r in resources if r.get("status") == "busy")
total_teams = len(resources)
c4.metric("Teams Deployed", f"{busy_teams} / {total_teams}", f"{total_teams - busy_teams} available")

free_beds = sum(h.get("available_beds", 0) for h in hospitals)
c5.metric("Hospital Beds", f"{free_beds} free", f"{len(hospitals)} facilities")

st.markdown("---")

# -------------------------------------------------------- Action Toolbar
act_col1, act_col2, act_col3 = st.columns([2, 1, 1])

with act_col1:
    st.markdown("**⚡ Multi-Agent Scenario Trigger**")
    if st.button("🔥 Simulate Escalation Scenario (Factory B Explosion & Hazmat Breach)", type="primary"):
        api.trigger_replan(iid, {"type": "scenario"})
        st.session_state["flash"] = "Scenario triggered! Agents re-assessing crisis..."
        st.rerun()

with act_col2:
    st.markdown("**🔄 Manual Replanning**")
    if st.button("Request Fresh Agent Plan"):
        api.trigger_replan(iid, {"type": "manual", "message": "Manual re-evaluation requested"})
        st.session_state["flash"] = "Agents triggered for fresh plan."
        st.rerun()

with act_col3:
    st.markdown("**⚙️ System Control**")
    if st.button("Reset Crisis State"):
        api.reset_demo()
        st.session_state["flash"] = "State reset."
        st.rerun()

# -------------------------------------------------------- Main Dashboard Layout
main_col, side_col = st.columns([2.3, 1.0])

with main_col:
    st.markdown("#### 🗺️ Live Plant Map & AI Predicted Hazard Spread")
    map_view.render(incidents, routes, evacuation, resources, hospitals, height=520, key="dash_map")

    st.markdown("#### 🚨 Active Incident Details")
    if incidents:
        selected_inc = incidents[0]
        ic1, ic2 = st.columns(2)
        with ic1:
            incident_card.render(selected_inc)
        with ic2:
            incident_card.render_risk(selected_inc)

with side_col:
    # Plan Approval Panel
    approval_panel.render(plan, iid, key_prefix="dash_ap")

    # Alert Feed Panel
    alert_panel.render(alerts, limit=5)

    # Resource Status Summary
    st.markdown("#### 🚒 Emergency Unit Status")
    resource_status.render_summary(resources)