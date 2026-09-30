"""Full-size plant map with layer controls."""
import streamlit as st

import config
from components import map_view
from components.styles import page_header, pill
from services import api_client as api

iid = st.session_state.get("active_incident", config.DEFAULT_INCIDENT_ID)
page_header("Hazard map", "Simulated plant layout with predicted spread, routes and zones")

layers = st.multiselect("Show on map", map_view.ALL_LAYERS, default=map_view.ALL_LAYERS)

incidents = api.get_incidents()
routes = api.get_routes()
evac = api.get_evacuation(iid)

main, side = st.columns([3, 1])
with main:
    map_view.render(incidents, routes, evac, api.get_resources(), api.get_hospitals(),
                    layers=layers, height=640, key="full_map")
with side:
    with st.container(border=True):
        st.markdown("#### Legend")
        st.markdown(
            "🔥 💥 Incident  \n🔴 Predicted hazard area  \n➡️ Spread direction  \n"
            "Red zone: evacuate  \nYellow zone: monitor  \nGreen zone: safe  \n"
            "🚒 ☣️ 🛟 🚑 Teams  \n🏥 Hospital  \n🏠 Shelter  \nDashed red road: blocked")
    with st.container(border=True):
        st.markdown("#### Routes")
        for r in routes:
            st.markdown(f"**{r['id']}** {pill(r['status'])}  \n<small>{r['name']}. {r.get('reason', '')}</small>",
                        unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### Spread")
        for inc in incidents:
            risk = inc.get("risk", {})
            st.markdown(f"**{inc['location']}**: toward {risk.get('spread_direction', '-')}, "
                        f"wind {risk.get('wind', '-')}")
st.markdown(
    """
    <div style="
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:8px;
    ">

        <div>
            <span style="
                color:#F4F7FA;
                font-weight:700;
            ">
                LIVE PLANT MAP
            </span>

            <span style="
                color:#8A9BAA;
                font-size:11px;
                margin-left:10px;
            ">
                AI PREDICTED HAZARD SPREAD
            </span>
        </div>

        <div style="
            color:#E5484D;
            font-size:11px;
            font-weight:700;
        ">
            ● LIVE
        </div>

    </div>
    """,
    unsafe_allow_html=True
)