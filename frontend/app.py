"""
Entry point. Run from the frontend folder:
    streamlit run app.py
"""
import streamlit as st

import config
from components import styles
from services import api_client as api

st.set_page_config(page_title="Aptly", page_icon="◌", layout="wide")
styles.inject()

st.markdown(
    """
    <style>
        header[data-testid="stHeader"] {display: none !important;}
        div[data-testid="stToolbar"] {display: none !important;}
        [data-testid="stSidebar"] {display: none !important;}
        section[data-testid="stMain"] > div {padding-left: 0; padding-right: 0;}
        .block-container {padding-top: 0.75rem;}
        body, .stApp {background: #e7e1d9 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state.setdefault("active_incident", config.DEFAULT_INCIDENT_ID)
st.session_state.setdefault("auto_refresh", False)

if msg := st.session_state.pop("flash", None):
    st.toast(msg, icon="✅")

pages = [
    st.Page("pages/dashboard.py", title="Dashboard", icon="🛡️", default=True),
    st.Page("pages/incidents.py", title="Incidents", icon="🚨"),
    st.Page("pages/hazard_map.py", title="Hazard map", icon="🗺️"),
    st.Page("pages/resources.py", title="Resources", icon="🚒"),
    st.Page("pages/evacuation.py", title="Evacuation", icon="🏠"),
    st.Page("pages/response_plan.py", title="Response plan", icon="🔄"),
]
nav = st.navigation(pages)
nav.run()