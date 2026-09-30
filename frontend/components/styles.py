"""Modern industrial command-center styling."""

import streamlit as st
from config import COLORS


_LEVELS = {
    "danger": {
        "critical", "high", "unavailable", "blocked", "evacuate",
        "full", "required", "unsafe", "pending_approval"
    },
    "warn": {
        "medium", "busy", "monitor", "in_progress",
        "partial", "standby", "unknown"
    },
    "ok": {
        "low", "available", "open", "safe", "complete",
        "approved", "assigned", "accepting", "live"
    },
}


def level_of(value):
    value = str(value).lower()

    for level, words in _LEVELS.items():
        if value in words:
            return level

    return "info"


def pill(text, level=None):
    level = level or level_of(text)

    return (
        f'<span class="pill pill-{level}">'
        f'{str(text).replace("_", " ")}'
        f'</span>'
    )


def inject():

    st.markdown(
        f"""
        <style>

        @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800;900&family=Barlow+Condensed:wght@500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Barlow', sans-serif;
            background: #e7e1d9;
            color: #1b1d1f;
        }}

        h1, h2, h3, h4 {{
            font-family: 'Barlow Condensed', sans-serif !important;
            letter-spacing: -0.04em;
        }}

        .block-container {{
            max-width: 1200px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }}

        div[data-testid="stVerticalBlock"] {{
            gap: 0.8rem;
        }}

        .editorial-shell {{
            background: rgba(255,255,255,0.15);
            border-radius: 28px;
            padding: 0 0 20px;
        }}

        .editorial-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            background: rgba(255,255,255,0.22);
            border: 1px solid rgba(17,24,22,0.06);
            border-radius: 18px;
            padding: 14px 18px;
            margin-bottom: 18px;
            box-shadow: 0 8px 20px rgba(10,10,10,0.03);
        }}

        .brand-wrap {{
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 120px;
        }}

        .brand-mark {{
            width: 18px;
            height: 18px;
            border-radius: 50%;
            border: 2px solid #111;
            position: relative;
            display: inline-block;
            background: transparent;
        }}

        .brand-mark::before {{
            content: "";
            position: absolute;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: rgba(24,32,35,0.9);
            left: 4px;
            top: 4px;
        }}

        .brand-text {{
            font-size: 18px;
            font-weight: 700;
            letter-spacing: -0.04em;
            color: #181c1e;
        }}

        .editorial-nav {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 28px;
            flex: 1;
            color: rgba(26, 30, 33, 0.72);
            font-size: 13px;
            font-weight: 600;
        }}

        .header-button {{
            border: 1px solid rgba(17,24,22,0.1);
            background: rgba(255,255,255,0.3);
            color: #1c1b1a;
            border-radius: 999px;
            padding: 10px 18px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .editorial-hero {{
            display: grid;
            grid-template-columns: 1.28fr 0.72fr;
            gap: 18px;
            align-items: stretch;
            background: rgba(247,245,242,0.72);
            border: 1px solid rgba(17,24,22,0.06);
            border-radius: 28px;
            padding: 26px 24px 18px;
            min-height: 500px;
        }}

        .hero-copy {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 12px 6px 12px 14px;
        }}

        .eyebrow {{
            align-self: flex-start;
            background: rgba(154, 187, 145, 0.18);
            color: #415d3f;
            border: 1px solid rgba(80,123,71,0.12);
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.18em;
            padding: 8px 14px;
            margin-bottom: 18px;
        }}

        .hero-copy h1 {{
            margin: 0;
            font-size: clamp(3.2rem, 5vw, 8rem);
            line-height: 0.9;
            color: #151516;
            letter-spacing: -0.07em;
            max-width: 600px;
        }}

        .hero-copy p {{
            max-width: 560px;
            margin: 24px 0 0;
            color: rgba(22, 26, 32, 0.72);
            font-size: 1.04rem;
            line-height: 1.7;
        }}

        .hero-actions {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-top: 28px;
            flex-wrap: wrap;
        }}

        .primary-action, .secondary-action {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            border-radius: 12px;
            padding: 14px 18px;
            font-size: 0.9rem;
            font-weight: 700;
            transition: transform 0.2s ease;
        }}

        .primary-action {{
            background: #183b3a;
            color: #f8f7f4;
            box-shadow: 0 12px 24px rgba(18, 53, 55, 0.12);
        }}

        .secondary-action {{
            background: rgba(17,24,22,0.04);
            color: #1a1d1f;
            border: 1px solid rgba(17,24,22,0.08);
        }}

        .primary-action:hover, .secondary-action:hover {{
            transform: translateY(-1px);
        }}

        .micro-details {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 22px;
            color: rgba(20, 24, 28, 0.75);
            font-size: 12px;
            font-weight: 600;
        }}

        .hero-visual {{
            display: flex;
            align-items: end;
            justify-content: center;
            min-height: 440px;
        }}

        .visual-frame {{
            position: relative;
            width: 100%;
            height: 100%;
            min-height: 320px;
            background: linear-gradient(180deg, rgba(186, 208, 175, 0.2), rgba(255,255,255,0.18));
            border-radius: 24px;
            border: 1px solid rgba(17,24,22,0.05);
            overflow: hidden;
        }}

        .illustration {{
            position: absolute;
            inset: 30px 18px 10px 18px;
            display: flex;
            align-items: end;
            justify-content: center;
        }}

        .pot {{
            position: absolute;
            bottom: 8px;
            width: 190px;
            height: 80px;
            background: linear-gradient(180deg, #dfe6df, #b6c0b2);
            border-radius: 20px 20px 26px 26px;
            box-shadow: inset 0 10px 18px rgba(255,255,255,0.4);
            border: 1px solid rgba(17,24,22,0.08);
        }}

        .leaf {{
            position: absolute;
            bottom: 84px;
            width: 110px;
            height: 170px;
            background: linear-gradient(180deg, #a5d38c, #6ca26b 65%, #4f7853);
            border-radius: 52% 48% 52% 48% / 57% 43% 57% 43%;
            box-shadow: inset -18px -18px 22px rgba(41,70,42,0.18);
            transform-origin: bottom center;
        }}

        .leaf-one {{
            left: 46%;
            transform: translateX(-50%) rotate(-18deg);
        }}

        .leaf-two {{
            left: 56%;
            transform: translateX(-50%) rotate(18deg);
            height: 150px;
        }}

        .leaf-three {{
            left: 40%;
            transform: translateX(-50%) rotate(-38deg);
            height: 145px;
        }}

        .leaf-four {{
            left: 63%;
            transform: translateX(-50%) rotate(38deg);
            height: 145px;
        }}

        @media (max-width: 900px) {{
            .editorial-header {{
                flex-wrap: wrap;
            }}

            .editorial-nav {{
                order: 3;
                width: 100%;
                justify-content: flex-start;
                overflow-x: auto;
                padding-bottom: 4px;
            }}

            .editorial-hero {{
                grid-template-columns: 1fr;
            }}

            .hero-copy h1 {{
                max-width: 100%;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

    return None


# =========================================================
# Legacy helpers kept for compatibility with the rest of the app
# =========================================================


def page_header(title, subtitle="", status_html=""):
    st.markdown(
        f"""
        <div class="command-header">
            <div>
                <div class="command-title">🛡 {title}</div>
                <div class="command-subtitle">{subtitle}</div>
            </div>
            <div class="live-status"><span class="live-dot"></span>SYSTEM ONLINE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if status_html:
        st.markdown(f'<div style="margin-top:-8px; margin-bottom:12px; text-align:right;">{status_html}</div>', unsafe_allow_html=True)


def metric_card(label, value, description="", level="info"):
    st.markdown(
        f"""
        <div class="metric-card {level}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def crisis_card(level="CRITICAL", percentage=90):
    st.markdown(
        f"""
        <div class="crisis-card">
            <div class="crisis-head">
                <div>
                    <div class="crisis-name">CURRENT CRISIS LEVEL</div>
                    <div class="crisis-level">{level}</div>
                </div>
                <div>🔴</div>
            </div>
            <div class="crisis-bar"><div class="crisis-fill" style="width:{percentage}%"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def timeline(items):
    html = '<div class="glass-panel"><div class="panel-title">Incident Timeline</div><div class="timeline">'
    for item in items:
        html += f"<div class='timeline-item'><div class='timeline-dot'></div><div class='timeline-time'>{item['time']}</div><div class='timeline-text'>{item['message']}</div></div>"
    html += '</div></div>'
    st.markdown(html, unsafe_allow_html=True)

