"""Incident cards for the dashboard and incident details page."""
import streamlit as st

from components.styles import pill


def render(incident):
    with st.container(border=True):
        st.markdown(f"### {incident['id']} • {incident['type']}")
        st.caption(f"{incident['location']} • reported {incident.get('reported_at', '-')}")
        st.markdown(pill(incident.get('status', 'active'), 'ok' if incident.get('status') == 'active' else 'warn'),
                    unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        c1.metric("Severity", f"{incident.get('severity', 0)}/10")
        c2.metric("People", incident.get('people_affected', 0))

        st.caption(f"Level: {incident.get('severity_label', '-')} • Confirmed: {'yes' if incident.get('confirmed', True) else 'no'}")
        if incident.get('uncertain_fields'):
            st.caption(f"Uncertain: {', '.join(incident['uncertain_fields'])}")
        if incident.get('source'):
            st.caption(f"Source: {incident['source']}")


def render_risk(incident):
    with st.container(border=True):
        st.markdown("#### Risk picture")
        risk = incident.get('risk', {})

        st.markdown(
            f"**Spread:** {risk.get('spread_direction', '-')}  \n**Wind:** {risk.get('wind', '-')}  \n"
            f"**Radius:** {risk.get('hazard_radius', '-')}")

        for label in ["chemical", "fire", "explosion", "structural"]:
            val = risk.get(label, "unknown")
            if val not in {None, ""}:
                kind = "danger" if val in {"high", "critical"} else "warn" if val == "medium" else "info"
                st.markdown(f"- {label.title()}: {pill(val, kind)}", unsafe_allow_html=True)

        if risk.get('domino_effect'):
            st.caption(f"Domino effect: {risk['domino_effect']}")