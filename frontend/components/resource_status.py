"""Resource summary counters and detailed status table."""
import streamlit as st

from components.styles import pill

ICONS = {"Fire": "🚒", "Hazmat": "☣️", "Rescue": "🛟", "Ambulance": "🚑"}


def render_summary(resources):
    types = list(dict.fromkeys(r["type"] for r in resources))
    cols = st.columns(len(types) or 1)
    for col, rtype in zip(cols, types):
        group = [r for r in resources if r["type"] == rtype]
        free = sum(r["status"] == "available" for r in group)
        down = sum(r["status"] == "unavailable" for r in group)
        with col.container(border=True):
            st.metric(f"{ICONS.get(rtype, '•')} {rtype} available", f"{free} / {len(group)}",
                      delta=f"{down} out of service" if down else None, delta_color="inverse")


def render_table(resources):
    rows = []
    for r in resources:
        cls = ' class="changed"' if r.get("changed") else ""
        note = f"<br><small>{r['note']}</small>" if r.get("note") else ""
        rows.append(
            f"<tr{cls}><td>{ICONS.get(r['type'], '')} {r['name']}</td><td>{r['id']}</td>"
            f"<td>{pill(r['status'])}{note}</td><td>{r.get('assigned_to') or '-'}</td></tr>")
    st.markdown(
        '<table class="cc-table"><tr><th>Resource</th><th>ID</th><th>Status</th><th>Assigned to</th></tr>'
        + "".join(rows) + "</table>", unsafe_allow_html=True)
    changed = [r for r in resources if r.get("changed")]
    if changed:
        st.caption("Highlighted rows changed since the last approved plan.")
