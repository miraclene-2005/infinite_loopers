import streamlit as st


def render(plan):

    changes = plan.get("changes", [])

    if not changes:
        st.markdown(
            """
            <div class="glass-panel">

                <div class="panel-title">
                    SYSTEM CHANGES
                </div>

                <div style="color:#3DD68C">
                    ✓ No changes detected
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        return

    icons = {
        "new_incident": "💥",
        "resource_failure": "☣️",
        "route_blocked": "🚧",
        "hazard_spread": "☢️",
    }

    html = """
    <div class="glass-panel">

        <div class="panel-title">
            ⚠ WHAT CHANGED?
        </div>

        <div class="panel-subtitle">
            Changes detected since previous response plan
        </div>
    """

    for change in changes:

        change_type = change.get(
            "type",
            "manual"
        )

        icon = icons.get(
            change_type,
            "⚠️"
        )

        html += f"""
        <div class="alert-row sev-warn">

            <strong>
                {icon}
                {change.get("message", "System update")}
            </strong>

        </div>
        """

    html += "</div>"

    st.markdown(
        html,
        unsafe_allow_html=True
    )