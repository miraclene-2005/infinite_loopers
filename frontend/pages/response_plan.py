"""Before vs after response plan, what changed, and human approval."""
import streamlit as st

import config
from components import approval_panel
from components.styles import page_header, pill
from services import api_client as api

iid = st.session_state.get("active_incident", config.DEFAULT_INCIDENT_ID)
plan = api.get_response_plan(iid)

page_header("Response plan", f"Version {plan.get('version')} generated at {plan.get('generated_at', '-')}",
            pill(plan.get("status", "unknown")))

prev = {a["category"]: a for a in plan.get("previous", [])}
curr = {a["category"]: a for a in plan.get("current", [])}
categories = list(dict.fromkeys(list(prev) + list(curr)))

left, right = st.columns([2.4, 1])
with left:
    with st.container(border=True):
        st.markdown("#### Previous plan and new plan")
        if not prev:
            st.caption("This is the first plan for the incident. Nothing to compare yet.")
        rows = []
        for cat in categories:
            before = prev.get(cat, {}).get("assignment", "-")
            after = curr.get(cat, {}).get("assignment", "-")
            changed = bool(prev) and before != after
            row_class = ' class="changed"' if changed else ""
            reason = curr.get(cat, {}).get("reason", "")
            rows.append(f"<tr{row_class}><td>{cat}</td><td>{before}</td><td>{after}</td>"
                        f"<td><small>{reason}</small></td></tr>")
        st.markdown('<table class="cc-table"><tr><th>Area</th><th>Previous</th><th>New</th><th>Why</th></tr>'
                    + "".join(rows) + "</table>", unsafe_allow_html=True)

with right:
    with st.container(border=True):
        st.markdown("#### What changed")
        changes = plan.get("changes", [])
        if changes:
            for ch in changes:
                st.markdown(f"⚠️ {ch['message']}")
        else:
            st.caption("No changes since the plan was created.")
    approval_panel.render_pipeline(plan)

approval_panel.render(plan, iid, key_prefix="plan", show_review=False)

with st.expander("Request a fresh plan"):
    reason = st.text_input("What should the agents reconsider?", placeholder="e.g. wind shifted to the east")
    if st.button("Replan now"):
        api.trigger_replan(iid, {"type": "manual", "message": reason or "Operator requested a fresh plan"})
        st.session_state["flash"] = "Replanning requested."
        st.rerun()