"""Incident list, details, and manual incident reporting."""
import pandas as pd
import streamlit as st

from components import incident_card
from components.styles import page_header
from services import api_client as api

page_header("Incidents", "Every reported event in the shared incident picture")

incidents = api.get_incidents()

if incidents:
    df = pd.DataFrame([{
        "ID": i["id"], "Type": i["type"], "Location": i["location"], "Severity": i["severity"],
        "Level": i["severity_label"], "People": i["people_affected"],
        "Confirmed": "yes" if i.get("confirmed", True) else "no", "Reported": i.get("reported_at"),
    } for i in incidents])
    st.dataframe(df, hide_index=True)

    ids = [i["id"] for i in incidents]
    current = st.session_state.get("active_incident")
    chosen = st.selectbox("Incident details", ids, index=ids.index(current) if current in ids else 0)
    inc = next(i for i in incidents if i["id"] == chosen)
    c1, c2 = st.columns(2)
    with c1:
        incident_card.render(inc)
    with c2:
        incident_card.render_risk(inc)
else:
    st.info("No incidents reported yet. Use the form below to report one.")

st.markdown("### Report an incident")
with st.form("report_incident", clear_on_submit=True):
    c1, c2 = st.columns(2)
    itype = c1.selectbox("Type", ["Chemical leak", "Fire", "Explosion", "Equipment failure",
                                  "Structural collapse", "Gas release"])
    location = c2.text_input("Location", placeholder="e.g. Factory C, tank farm")
    severity = c1.slider("Severity", 1, 10, 6)
    people = c2.number_input("People affected (estimate)", min_value=0, value=0, step=1)
    source = c1.selectbox("Source", ["Manual report", "Sensor", "CCTV", "Emergency call", "Worker radio"])
    confirmed = c2.checkbox("Confirmed by site team", value=False)
    if st.form_submit_button("Report incident", type="primary"):
        if not location.strip():
            st.error("Enter a location so teams know where to go.")
        else:
            api.create_incident({"type": itype, "location": location.strip(), "severity": severity,
                                 "people_affected": int(people), "source": source, "confirmed": confirmed})
            st.session_state["flash"] = f"Incident reported at {location.strip()}."
            st.rerun()