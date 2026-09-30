"""Role-specific alert feed."""
import streamlit as st

from components.styles import level_of

AUDIENCE = {
    "control_room": "🚨 Control room",
    "hazmat": "☣️ Hazmat team",
    "fire": "🚒 Fire team",
    "medical": "🚑 Medical",
    "rescue": "🛟 Rescue team",
    "public": "👥 Public and workers",
}


def render(alerts, limit=None, audience_filter=None):
    with st.container(border=True):
        st.markdown("#### Alerts")
        items = [a for a in alerts if not audience_filter or a["audience"] in audience_filter]
        if not items:
            st.caption("No alerts for this selection.")
            return
        for a in items[:limit]:
            st.markdown(
                f'<div class="alert-row sev-{level_of(a["severity"])}">'
                f'<div class="alert-meta">{a["time"]} &nbsp; {AUDIENCE.get(a["audience"], a["audience"])}</div>'
                f'{a["message"]}</div>', unsafe_allow_html=True)