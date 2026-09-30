"""Pipeline status and human approval controls for the response plan."""
import streamlit as st

from components.styles import pill
from services import api_client as api


def render_pipeline(plan):
    with st.container(border=True):
        st.markdown("#### Response status")
        for step in plan.get("pipeline", []):
            st.markdown(f'<div class="stage"><span>{step["stage"]}</span>{pill(step["status"])}</div>',
                        unsafe_allow_html=True)


def approve(incident_id, version):
    api.approve_plan(incident_id)
    st.session_state["flash"] = f"Plan v{version} approved. Orders sent to teams."
    st.rerun()


def render(plan, incident_id, key_prefix="ap", show_review=True):
    with st.container(border=True):
        st.markdown(f"#### Response plan v{plan.get('version', '-')}")
        if plan.get("status") == "pending_approval":
            st.markdown(pill("Approval required", "danger"), unsafe_allow_html=True)
            for ch in plan.get("changes", []):
                st.markdown(f"⚠️ {ch['message']}")
            if plan.get("approval_items"):
                st.markdown("**Needs your sign-off**")
                st.markdown("\n".join(f"- {item}" for item in plan["approval_items"]))
            c1, c2 = st.columns(2)
            if c1.button("Approve plan", type="primary", key=f"{key_prefix}_approve"):
                approve(incident_id, plan.get("version"))
            if show_review and c2.button("Review details", key=f"{key_prefix}_review"):
                st.switch_page("pages/response_plan.py")
        else:
            st.markdown(pill("Approved", "ok"), unsafe_allow_html=True)
            st.caption(f"Approved by {plan.get('approved_by') or '-'} at {plan.get('approved_at') or '-'}")