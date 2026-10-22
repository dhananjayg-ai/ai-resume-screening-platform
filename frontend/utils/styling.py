"""Shared visual styling helpers for the Streamlit frontend.

Every page imports `apply_global_styles()` and calls it once near the top
(right after `st.set_page_config`) to get a consistent color palette, a
gradient page background, a styled sidebar, styled buttons, and the colored
"metric card" / badge / header-banner building blocks used throughout the
app. Keeping all of this in one module means every page reads from the same
design language instead of styling itself ad hoc.

This is plain CSS injected via `st.markdown(..., unsafe_allow_html=True)` --
no extra frontend framework, just the color system that backs
`.streamlit/config.toml`.
"""
import html

import streamlit as st

# ---------------------------------------------------------------------------
# Palette -- keep in sync with .streamlit/config.toml
# ---------------------------------------------------------------------------
PRIMARY = "#6D28D9"        # violet-700
PRIMARY_DARK = "#4C1D95"   # violet-900
PRIMARY_LIGHT = "#A78BFA"  # violet-400
ACCENT_BG = "#EDE9FE"      # violet-100
PAGE_BG = "#F7F6FB"
TEXT_DARK = "#1E1B2E"

# Extra decorative accents -- used only for non-data-encoding flourishes (a
# metric card's left border, an icon) so the dashboard reads as more than one
# flat shade of violet. Never used to encode chart data identity -- charts use
# the status palette below (for good/bad meaning) or a single brand hue (for a
# single-series nominal measure), per the dataviz skill's color formula.
ACCENT_TEAL = "#0F766E"    # teal-700
ACCENT_TEAL_LIGHT = "#5EEAD4"
ACCENT_PINK = "#BE185D"    # pink-700
ACCENT_PINK_LIGHT = "#F9A8D4"

SUCCESS = "#15803D"   # green-700
SUCCESS_BG = "#DCFCE7"
WARNING = "#B45309"   # amber-700
WARNING_BG = "#FEF3C7"
DANGER = "#B91C1C"    # red-700
DANGER_BG = "#FEE2E2"
INFO = "#1D4ED8"      # blue-700
INFO_BG = "#DBEAFE"

# Score bands used by score_badge() / score_band_color() -- shared by both
# the Candidate Rankings cards and the ranking bar chart so the colors mean
# the same thing everywhere in the app.
SCORE_BAND_HIGH = 75.0   # >= this -> strong match (green)
SCORE_BAND_MID = 50.0    # >= this -> moderate match (amber); below -> weak (red)


def score_band_color(score: float) -> str:
    """Return the hex color for a 0-100 match score band."""
    if score >= SCORE_BAND_HIGH:
        return SUCCESS
    if score >= SCORE_BAND_MID:
        return WARNING
    return DANGER


def score_band_label(score: float) -> str:
    """Return a short text label for a 0-100 match score band (used so color
    never carries meaning alone -- every badge pairs a color with a label)."""
    if score >= SCORE_BAND_HIGH:
        return "Strong match"
    if score >= SCORE_BAND_MID:
        return "Moderate match"
    return "Weak match"


# ---------------------------------------------------------------------------
# Status palette -- a small, fixed, reserved scale (good / neutral / warning /
# critical) reused everywhere a *state* (not a data series) is shown: interview
# status, notification send status, duplicate-resume flags. Keeping this in
# one map means the same status string always renders the same color + icon
# across every page and every chart.
# ---------------------------------------------------------------------------
_STATUS_ROLE = {
    # interview statuses
    "scheduled": "info",
    "completed": "green",
    "cancelled": "red",
    "rescheduled": "amber",
    "no_show": "red",
    # notification statuses
    "sent": "green",
    "failed": "red",
    "failed_no_candidate_email": "red",
    "skipped_no_smtp_config": "amber",
    # duplicate-resume flag
    "duplicate": "amber",
    "not_duplicate": "green",
    # generic SMTP test-connection statuses
    "ok": "green",
    "not_configured": "amber",
    "auth_error": "red",
    "connection_error": "red",
    "smtp_error": "red",
}
_ROLE_CLASS = {
    "green": "app-badge-green",
    "amber": "app-badge-amber",
    "red": "app-badge-red",
    "info": "app-badge-info",
}
_ROLE_ICON = {
    "green": "✅",   # check mark
    "amber": "⚠️",  # warning sign
    "red": "❌",     # cross mark
    "info": "ℹ️",   # info sign
}
_ROLE_HEX = {
    "green": SUCCESS,
    "amber": WARNING,
    "red": DANGER,
    "info": INFO,
}


def status_role(status: str) -> str:
    """Map a raw status string to one of 'green'/'amber'/'red'/'info'."""
    return _STATUS_ROLE.get(status, "info")


def status_hex(status: str) -> str:
    """Return the solid hex color for a status string (for Plotly markers)."""
    return _ROLE_HEX[status_role(status)]


def apply_global_styles() -> None:
    """Inject the shared CSS. Call once per page, right after set_page_config."""
    st.markdown(
        f"""
        <style>
        :root {{
            --app-primary: {PRIMARY};
            --app-primary-dark: {PRIMARY_DARK};
            --app-primary-light: {PRIMARY_LIGHT};
            --app-accent-bg: {ACCENT_BG};
            --app-page-bg: {PAGE_BG};
            --app-text: {TEXT_DARK};
        }}

        /* Page background: soft violet-tinted gradient instead of flat white */
        .stApp {{
            background: linear-gradient(160deg, {PAGE_BG} 0%, #FFFFFF 45%, {ACCENT_BG} 100%);
        }}

        /* Sidebar: deep indigo/violet gradient, visually distinct from the page */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(195deg, {PRIMARY_DARK} 0%, {PRIMARY} 100%);
        }}
        section[data-testid="stSidebar"] * {{
            color: #F5F3FF !important;
        }}
        section[data-testid="stSidebar"] svg {{
            fill: #F5F3FF !important;
        }}
        section[data-testid="stSidebar"] a {{
            color: #E9D5FF !important;
        }}

        /* Buttons */
        .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
            background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1.25rem;
            transition: transform 0.05s ease-in-out, box-shadow 0.15s ease-in-out;
            box-shadow: 0 2px 6px rgba(76, 29, 149, 0.25);
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {{
            box-shadow: 0 4px 12px rgba(76, 29, 149, 0.35);
            color: #FFFFFF;
            border: none;
        }}
        .stButton > button:active, .stFormSubmitButton > button:active {{
            transform: scale(0.98);
        }}

        /* Tabs / expanders: subtle violet accent */
        .streamlit-expanderHeader {{
            background-color: {ACCENT_BG};
            border-radius: 8px;
        }}
        div[data-testid="stExpander"] {{
            border: 1px solid {ACCENT_BG};
            border-radius: 10px;
            overflow: hidden;
        }}

        /* Inputs: rounded corners matching the rest of the theme */
        div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] {{
            border-radius: 8px !important;
        }}

        /* Headings */
        h1, h2, h3 {{
            color: {TEXT_DARK};
        }}

        /* --- Custom components (built from plain divs, styled below) --- */

        .app-header-banner {{
            padding: 1.4rem 1.8rem;
            border-radius: 14px;
            background: linear-gradient(120deg, {PRIMARY_DARK} 0%, {PRIMARY} 60%, {PRIMARY_LIGHT} 100%);
            color: #FFFFFF;
            margin-bottom: 1.4rem;
            box-shadow: 0 6px 20px rgba(76, 29, 149, 0.25);
        }}
        .app-header-banner h1 {{
            color: #FFFFFF;
            margin: 0;
            font-size: 1.8rem;
        }}
        .app-header-banner p {{
            color: #EDE9FE;
            margin: 0.3rem 0 0 0;
            font-size: 1.0rem;
        }}

        .app-metric-row {{
            display: flex;
            gap: 0.9rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }}
        .app-metric-card {{
            flex: 1 1 160px;
            background: #FFFFFF;
            border-radius: 12px;
            border-left: 6px solid {PRIMARY};
            padding: 0.9rem 1.1rem;
            box-shadow: 0 2px 10px rgba(30, 27, 46, 0.08);
        }}
        .app-metric-card .app-metric-label {{
            font-size: 0.82rem;
            font-weight: 600;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .app-metric-card .app-metric-value {{
            font-size: 1.7rem;
            font-weight: 700;
            color: {TEXT_DARK};
            margin-top: 0.15rem;
        }}

        .app-candidate-card {{
            background: #FFFFFF;
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            margin-bottom: 1rem;
            box-shadow: 0 3px 14px rgba(30, 27, 46, 0.08);
            border-top: 5px solid {PRIMARY};
        }}

        .app-badge {{
            display: inline-block;
            padding: 0.22rem 0.75rem;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.92rem;
            letter-spacing: 0.01em;
        }}
        .app-badge-green {{ background: {SUCCESS_BG}; color: {SUCCESS}; }}
        .app-badge-amber {{ background: {WARNING_BG}; color: {WARNING}; }}
        .app-badge-red   {{ background: {DANGER_BG}; color: {DANGER}; }}
        .app-badge-info  {{ background: {INFO_BG}; color: {INFO}; }}

        .app-section-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.55rem 1rem;
            margin: 1.5rem 0 0.9rem 0;
            border-left: 4px solid {PRIMARY};
            background: {ACCENT_BG};
            border-radius: 8px;
            font-weight: 700;
            font-size: 1.15rem;
            color: {TEXT_DARK};
        }}

        .app-empty-state {{
            text-align: center;
            padding: 2.2rem 1.5rem;
            border-radius: 14px;
            background: {ACCENT_BG};
            border: 1px dashed {PRIMARY_LIGHT};
            color: {TEXT_DARK};
            margin: 0.8rem 0 1.2rem 0;
        }}
        .app-empty-state .app-empty-icon {{
            font-size: 2.2rem;
            margin-bottom: 0.4rem;
        }}

        /* Dark-mode-forced browsers: keep banner/cards legible even though the
           app's documented theme is the light palette above. */
        @media (prefers-color-scheme: dark) {{
            .app-metric-card, .app-candidate-card {{
                background: #251F38;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
            }}
            .app-metric-card .app-metric-value {{
                color: #F5F3FF;
            }}
            .app-metric-card .app-metric-label {{
                color: #C4B5FD;
            }}
            .app-section-header {{
                background: #2E2547;
                color: #F5F3FF;
                border-left-color: {PRIMARY_LIGHT};
            }}
            .app-empty-state {{
                background: #2E2547;
                color: #E9E4FB;
                border-color: {PRIMARY_LIGHT};
            }}
            .app-badge-green {{ background: rgba(21, 128, 61, 0.35); color: #86EFAC; }}
            .app-badge-amber {{ background: rgba(180, 83, 9, 0.35); color: #FDE68A; }}
            .app-badge-red   {{ background: rgba(185, 28, 28, 0.35); color: #FCA5A5; }}
            .app-badge-info  {{ background: rgba(29, 78, 216, 0.35); color: #93C5FD; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """Render a colored gradient header banner at the top of a page."""
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle) if subtitle else ""
    icon_html = f"{icon} " if icon else ""
    subtitle_html = f"<p>{safe_subtitle}</p>" if safe_subtitle else ""
    st.markdown(
        f"""
        <div class="app-header-banner">
            <h1>{icon_html}{safe_title}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_cards(items: list[tuple[str, str] | tuple[str, str, str]]) -> None:
    """Render a row of colored KPI tiles.

    `items` is a list of (label, value) or (label, value, accent_color_hex)
    tuples, e.g. [("Jobs posted", "4", PRIMARY), ("Candidates screened", "12", INFO)].
    The accent color is purely decorative (left border) -- it never carries
    data meaning on its own, so it's safe to vary per card.
    """
    cards_html_parts = []
    for item in items:
        if len(item) == 3:
            label, value, color = item
        else:
            label, value = item
            color = PRIMARY
        cards_html_parts.append(
            f"""
            <div class="app-metric-card" style="border-left-color: {color};">
                <div class="app-metric-label">{html.escape(label)}</div>
                <div class="app-metric-value">{html.escape(str(value))}</div>
            </div>
            """
        )
    st.markdown(f'<div class="app-metric-row">{"".join(cards_html_parts)}</div>', unsafe_allow_html=True)


def section_header(title: str, icon: str = "") -> None:
    """Render a colored sub-section header (used below the page's main
    gradient banner to break a page into clearly labeled parts)."""
    icon_html = f"{icon} " if icon else ""
    st.markdown(
        f'<div class="app-section-header">{icon_html}{html.escape(title)}</div>',
        unsafe_allow_html=True,
    )


def empty_state(message: str, icon: str = "\U0001F4ED") -> None:
    """Render a friendly empty-state panel instead of a bare st.info() --
    used wherever a list/chart has no data yet."""
    st.markdown(
        f"""
        <div class="app-empty-state">
            <div class="app-empty-icon">{icon}</div>
            <div>{html.escape(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def score_badge(score: float, label: str | None = None) -> str:
    """Return an HTML badge span color-coded by score band (green/amber/red).

    Caller renders it with st.markdown(badge_html, unsafe_allow_html=True).
    """
    if score >= SCORE_BAND_HIGH:
        css_class = "app-badge-green"
    elif score >= SCORE_BAND_MID:
        css_class = "app-badge-amber"
    else:
        css_class = "app-badge-red"
    text = label if label is not None else f"{score:.1f} / 100"
    return f'<span class="app-badge {css_class}">{html.escape(text)}</span>'


def info_badge(text: str) -> str:
    """Return a neutral info-colored badge (used for statuses that aren't a score)."""
    return f'<span class="app-badge app-badge-info">{html.escape(text)}</span>'


def status_badge(status: str, label: str | None = None) -> str:
    """Return an HTML badge span color-coded by the shared status palette
    (interview status, notification status, duplicate-resume flag, SMTP test
    result, ...). Always pairs the color with an icon + text label so meaning
    never rests on color alone.

    Caller renders it with st.markdown(badge_html, unsafe_allow_html=True).
    """
    role = status_role(status)
    css_class = _ROLE_CLASS[role]
    icon = _ROLE_ICON[role]
    text = label if label is not None else status.replace("_", " ").title()
    return f'<span class="app-badge {css_class}">{icon} {html.escape(text)}</span>'
