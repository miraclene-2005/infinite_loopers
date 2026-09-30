"""Emergency teams and hospital capacity."""
import streamlit as st

import config
from components import resource_status
from components.styles import page_header, pill
from services import api_client as api


@st.fragment(run_every=config.REFRESH_SECONDS if st.session_state.get("auto_refresh") else None)
def view():
    page_header("Resources", "Team availability and hospital capacity")
    resources = api.get_resources()
    resource_status.render_summary(resources)

    types = sorted({r["type"] for r in resources})
    pick = st.segmented_control("Filter", ["All"] + types, default="All") or "All"
    shown = resources if pick == "All" else [r for r in resources if r["type"] == pick]
    with st.container(border=True):
        resource_status.render_table(shown)

    st.markdown("### Hospitals")
    for h in api.get_hospitals():
        with st.container(border=True):
            c1, c2 = st.columns([2, 1])
            c1.markdown(f"**{h['name']}** {pill(h['status'])}  \n"
                        f"{h['travel_min']} min away. Burn unit: {'yes' if h.get('burn_unit') else 'no'}",
                        unsafe_allow_html=True)
            c2.metric("Beds free", f"{h['available_beds']} / {h['capacity']}")
            st.progress(h["available_beds"] / max(h["capacity"], 1))


view()