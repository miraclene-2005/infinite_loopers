"""Evacuation zones and shelter capacity."""
import streamlit as st

import config
from components.styles import page_header, pill
from services import api_client as api

iid = st.session_state.get("active_incident", config.DEFAULT_INCIDENT_ID)
page_header("Evacuation", "Zones to clear and where people should go")

ev = api.get_evacuation(iid)
zones, shelters = ev.get("zones", []), ev.get("shelters", [])

c1, c2, c3 = st.columns(3)
c1.metric("Affected population", ev.get("affected_population", 0))
c2.metric("Zones to evacuate", sum(z["action"] == "evacuate" for z in zones))
c3.metric("Shelter places free", sum(s["available"] for s in shelters))

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.markdown("#### Zones")
        rows = "".join(f"<tr><td>{z['name']}</td><td>{pill(z['action'])}</td><td>{z['population']}</td></tr>"
                       for z in zones)
        st.markdown('<table class="cc-table"><tr><th>Zone</th><th>Action</th><th>People</th></tr>'
                    + rows + "</table>", unsafe_allow_html=True)
with right:
    with st.container(border=True):
        st.markdown("#### Shelters")
        for s in shelters:
            st.markdown(f"**{s['id']}** {s['name']} {pill(s['status'])}", unsafe_allow_html=True)
            st.progress(s["available"] / max(s["capacity"], 1),
                        text=f"{s['available']} of {s['capacity']} places free")