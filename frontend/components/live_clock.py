import streamlit as st
from datetime import datetime


def render():

    now = datetime.now()

    st.markdown(
        f"""
        <div style="
            text-align:right;
            color:#8A9BAA;
            font-size:11px;
            letter-spacing:.05em;
        ">

            <span style="color:#D9E2EA;">
                {now.strftime("%d %b %Y")}
            </span>

            &nbsp; • &nbsp;

            <span style="color:#F2A900;font-weight:700;">
                {now.strftime("%H:%M:%S")}
            </span>

            &nbsp; IST

        </div>
        """,
        unsafe_allow_html=True
    )