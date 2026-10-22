"""Visual dashboard: candidates per job, match-score distribution, top
candidates overall, and interview / notification status breakdowns.

All data comes from the existing backend API (frontend/utils/api_client.py).
Every chart degrades gracefully to a friendly empty state when there isn't
enough data yet, instead of crashing on an empty dataframe.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.styling import (
    INFO,
    PRIMARY,
    SUCCESS,
    apply_global_styles,
    empty_state,
    metric_cards,
    page_header,
    score_band_color,
    score_band_label,
    section_header,
    status_hex,
)
import utils.styling as styling

st.set_page_config(page_title="Dashboard", page_icon="\U0001F4CA", layout="wide")
apply_global_styles()

page_header(
    "Dashboard",
    "A visual overview of every job, candidate, interview and notification in the system.",
    icon="\U0001F4CA",
)

# Chart chrome shared by every Plotly figure below, so they all read as one
# consistent system rather than each picking its own fonts/background.
_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", color=styling.TEXT_DARK, size=13),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)


def _style_axes(fig: go.Figure) -> go.Figure:
    fig.update_xaxes(showgrid=False, zeroline=False, showline=True, linecolor="#D8D3EC")
    fig.update_yaxes(showgrid=True, gridcolor="#EDE9FE", zeroline=False, showline=False)
    fig.update_layout(**_LAYOUT_DEFAULTS)
    return fig


# ---------------------------------------------------------------------------
# Load data (every call isolated so one failing endpoint doesn't blank the
# whole dashboard).
# ---------------------------------------------------------------------------
try:
    jobs = api_client.list_jobs()
except ApiError as exc:
    st.error(f"Could not load jobs: {exc}")
    jobs = []

try:
    candidates = api_client.list_candidates()
except ApiError as exc:
    st.error(f"Could not load candidates: {exc}")
    candidates = []

try:
    all_scores = api_client.list_all_match_scores()
except ApiError as exc:
    st.error(f"Could not load match scores: {exc}")
    all_scores = []

try:
    interviews = api_client.list_interviews()
except ApiError as exc:
    st.error(f"Could not load interviews: {exc}")
    interviews = []

try:
    notifications = api_client.list_notifications()
except ApiError as exc:
    st.error(f"Could not load notifications: {exc}")
    notifications = []

if not jobs and not candidates:
    empty_state(
        "No data yet -- post a job and upload a resume or two to see the dashboard come alive.",
        icon="\U0001F4CA",
    )
    st.stop()

jobs_by_id = {j["id"]: j for j in jobs}
candidates_by_id = {c["id"]: c for c in candidates}

avg_score = f"{(sum(s['score'] for s in all_scores) / len(all_scores)):.1f}" if all_scores else "--"

metric_cards(
    [
        ("Jobs posted", len(jobs), PRIMARY),
        ("Candidates screened", len(candidates), INFO),
        ("Avg. match score", avg_score, SUCCESS),
        ("Notifications sent", len(notifications), styling.ACCENT_PINK),
    ]
)

col1, col2 = st.columns(2)

# ---------------------------------------------------------------------------
# 1. Candidates per job (bar) -- one nominal series (candidate count) across
#    job categories, so per the color formula it's a single brand hue, not a
#    rainbow of per-bar colors.
# ---------------------------------------------------------------------------
with col1:
    section_header("Candidates per job", icon="\U0001F4BC")
    if not jobs:
        empty_state("No jobs posted yet.", icon="\U0001F4BC")
    else:
        counts_by_job = {}
        for s in all_scores:
            counts_by_job.setdefault(s["job_id"], set()).add(s["candidate_id"])
        rows = [
            {"title": j["title"], "count": len(counts_by_job.get(j["id"], set()))}
            for j in jobs
        ]
        df = pd.DataFrame(rows)
        fig = go.Figure(
            go.Bar(
                x=df["title"],
                y=df["count"],
                marker_color=PRIMARY,
                text=df["count"],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Candidates matched: %{y}<extra></extra>",
            )
        )
        fig.update_layout(bargap=0.3, yaxis_title="Candidates matched", xaxis_title=None)
        _style_axes(fig)
        st.plotly_chart(fig, use_container_width=True)
        if not all_scores:
            st.caption(
                "All zero -- run matching on a job (Candidate Rankings page) to compute scores."
            )

# ---------------------------------------------------------------------------
# 2. Match score distribution (histogram), colored by score band -- color
#    here carries real good/bad meaning, so it uses the app's fixed status
#    palette (green/amber/red), the same one used on every score badge.
# ---------------------------------------------------------------------------
with col2:
    section_header("Match score distribution", icon="\U0001F4C8")
    if not all_scores:
        empty_state("No match scores yet -- run matching for a job first.", icon="\U0001F4C8")
    else:
        df = pd.DataFrame(all_scores)
        df["band"] = df["score"].apply(score_band_label)
        band_order = ["Strong match", "Moderate match", "Weak match"]
        color_map = {
            "Strong match": SUCCESS,
            "Moderate match": styling.WARNING,
            "Weak match": styling.DANGER,
        }
        fig = go.Figure()
        for band in band_order:
            subset = df[df["band"] == band]
            if subset.empty:
                continue
            fig.add_trace(
                go.Histogram(
                    x=subset["score"],
                    name=band,
                    marker_color=color_map[band],
                    xbins=dict(start=0, end=100, size=10),
                    hovertemplate=f"<b>{band}</b><br>Score range: %{{x}}<br>Count: %{{y}}<extra></extra>",
                )
            )
        fig.update_layout(barmode="stack", bargap=0.1, xaxis_title="Match score", yaxis_title="Candidates")
        _style_axes(fig)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 3. Top candidates overall by score (horizontal bar), colored by score band.
# ---------------------------------------------------------------------------
section_header("Top candidates overall", icon="\U0001F3C6")
if not all_scores:
    empty_state("No match scores yet -- run matching for a job first.", icon="\U0001F3C6")
else:
    top_n = sorted(all_scores, key=lambda s: s["score"], reverse=True)[:10]
    rows = []
    for s in top_n:
        cand = candidates_by_id.get(s["candidate_id"])
        job = jobs_by_id.get(s["job_id"])
        cand_name = (cand["name"] or cand["email"] or f"Candidate #{s['candidate_id']}") if cand else f"Candidate #{s['candidate_id']}"
        job_title = job["title"] if job else f"Job #{s['job_id']}"
        rows.append({"label": f"{cand_name} -- {job_title}", "score": s["score"]})
    df = pd.DataFrame(rows).sort_values("score", ascending=True)
    fig = go.Figure(
        go.Bar(
            x=df["score"],
            y=df["label"],
            orientation="h",
            marker_color=[score_band_color(v) for v in df["score"]],
            text=[f"{v:.1f}" for v in df["score"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="Match score",
        yaxis_title=None,
        height=max(320, 42 * len(df)),
        showlegend=False,
    )
    _style_axes(fig)
    st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)

# ---------------------------------------------------------------------------
# 4. Interview status breakdown (donut), colored by status (good/neutral/bad).
# ---------------------------------------------------------------------------
with col3:
    section_header("Interview status breakdown", icon="\U0001F5D3️")
    if not interviews:
        empty_state("No interviews scheduled yet.", icon="\U0001F5D3️")
    else:
        counts = pd.Series([i["status"] for i in interviews]).value_counts()
        fig = go.Figure(
            go.Pie(
                labels=[s.replace("_", " ").title() for s in counts.index],
                values=counts.values,
                hole=0.55,
                marker=dict(colors=[status_hex(s) for s in counts.index]),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
            )
        )
        fig.update_layout(**_LAYOUT_DEFAULTS)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 5. Notification send status breakdown (donut), colored by status.
# ---------------------------------------------------------------------------
with col4:
    section_header("Notification status breakdown", icon="\U0001F4E7")
    if not notifications:
        empty_state("No notifications sent yet.", icon="\U0001F4E7")
    else:
        counts = pd.Series([n["status"] for n in notifications]).value_counts()
        fig = go.Figure(
            go.Pie(
                labels=[s.replace("_", " ").title() for s in counts.index],
                values=counts.values,
                hole=0.55,
                marker=dict(colors=[status_hex(s) for s in counts.index]),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
            )
        )
        fig.update_layout(**_LAYOUT_DEFAULTS)
        st.plotly_chart(fig, use_container_width=True)
