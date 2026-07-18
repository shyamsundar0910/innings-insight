import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from backend.query_router.router import answer_question  # noqa: E402


st.set_page_config(
    page_title="Innings Insight",
    page_icon="🏏",
    layout="wide",
)


DATASET_MATCHES = "1,243"
DATASET_DELIVERIES = "295,732"
DATASET_SEASONS = "19"


def apply_custom_css() -> None:
    """Apply custom styling."""
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 111, 0, 0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(0, 180, 216, 0.16), transparent 28%),
                linear-gradient(135deg, #07111f 0%, #101827 45%, #0b1320 100%);
            color: #f8fafc;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #101827 0%, #111827 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        section[data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }

        .hero-card {
            padding: 34px 38px;
            border-radius: 24px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.14), rgba(255,255,255,0.05));
            border: 1px solid rgba(255,255,255,0.18);
            box-shadow: 0 20px 60px rgba(0,0,0,0.35);
            margin-bottom: 24px;
        }

        .hero-title {
            font-size: 54px;
            font-weight: 900;
            line-height: 1.05;
            margin-bottom: 8px;
            color: #ffffff;
        }

        .hero-subtitle {
            font-size: 24px;
            font-weight: 700;
            color: #facc15;
            margin-bottom: 18px;
        }

        .hero-description {
            font-size: 17px;
            color: #dbeafe;
            max-width: 950px;
            line-height: 1.6;
        }

        .stat-card {
            padding: 22px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.82));
            border: 1px solid rgba(148, 163, 184, 0.28);
            box-shadow: 0 12px 32px rgba(0,0,0,0.25);
            text-align: center;
        }

        .stat-label {
            font-size: 14px;
            color: #93c5fd;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .stat-value {
            font-size: 34px;
            font-weight: 900;
            color: #ffffff;
            margin-top: 6px;
        }

        .section-card {
            padding: 24px;
            border-radius: 20px;
            background: rgba(255,255,255,0.92);
            color: #111827;
            border: 1px solid rgba(255,255,255,0.14);
            margin-top: 18px;
        }

        .answer-box {
            padding: 18px 22px;
            border-radius: 16px;
            background: linear-gradient(135deg, #dcfce7, #bbf7d0);
            color: #14532d;
            font-weight: 700;
            border-left: 6px solid #22c55e;
        }

        .intent-pill {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(250, 204, 21, 0.16);
            color: #fde68a;
            border: 1px solid rgba(250, 204, 21, 0.35);
            font-size: 13px;
            font-weight: 700;
        }

        h1, h2, h3, h4 {
            color: #ffffff;
        }

        .section-card h2,
        .section-card h3,
        .section-card h4 {
            color: #111827;
        }

        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.95);
            padding: 18px;
            border-radius: 16px;
            border: 1px solid rgba(15,23,42,0.08);
            box-shadow: 0 8px 24px rgba(15,23,42,0.12);
        }

        div[data-testid="stMetric"] label {
            color: #334155 !important;
        }

        div[data-testid="stMetric"] div {
            color: #0f172a !important;
        }

        .stTextInput input {
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.25);
            padding: 14px;
        }

        .stButton > button {
            border-radius: 14px;
            padding: 12px 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #f97316, #ef4444);
            border: none;
            color: white;
        }

        .stDataFrame {
            border-radius: 16px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_chart(intent: str, table: pd.DataFrame):
    """Create Plotly chart based on detected intent."""
    if table.empty:
        return None

    color_sequence = ["#f97316", "#22c55e", "#38bdf8", "#facc15", "#a78bfa"]

    if intent == "highest_run_scorers":
        fig = px.bar(
            table,
            x="player",
            y="runs",
            title="Top IPL Run Scorers",
            text="runs",
            color_discrete_sequence=color_sequence,
        )

    elif intent == "best_strike_rate":
        fig = px.bar(
            table,
            x="player",
            y="strike_rate",
            title="Best Batting Strike Rate",
            text="strike_rate",
            color_discrete_sequence=color_sequence,
        )

    elif intent == "best_economy_rate":
        fig = px.bar(
            table,
            x="player",
            y="economy_rate",
            title="Best Economy Rate",
            text="economy_rate",
            color_discrete_sequence=color_sequence,
        )

    elif intent == "most_wickets":
        fig = px.bar(
            table,
            x="player",
            y="wickets",
            title="Top IPL Wicket Takers",
            text="wickets",
            color_discrete_sequence=color_sequence,
        )

    elif intent == "powerplay_team_scoring":
        fig = px.bar(
            table,
            x="batting_team",
            y="powerplay_run_rate",
            title="Powerplay Run Rate",
            text="powerplay_run_rate",
            color_discrete_sequence=color_sequence,
        )

    elif intent == "death_over_batting_analysis":
        fig = px.bar(
            table,
            x="player",
            y="death_strike_rate",
            title="Best Death-Over Batters",
            text="death_strike_rate",
            color_discrete_sequence=color_sequence,
        )

    elif intent == "player_comparison":
        cols = [
            col
            for col in ["runs", "strike_rate", "wickets", "economy_rate"]
            if col in table.columns
        ]

        if not cols:
            return None

        melted = table.melt(
            id_vars="player",
            value_vars=cols,
            var_name="metric",
            value_name="value",
        )

        fig = px.bar(
            melted,
            x="metric",
            y="value",
            color="player",
            barmode="group",
            title="Player Comparison",
            text="value",
            color_discrete_sequence=color_sequence,
        )

    elif intent in [
        "average_first_innings_score_by_venue",
        "average_second_innings_score_by_venue",
    ]:
        score_col = (
            "average_first_innings_score"
            if intent == "average_first_innings_score_by_venue"
            else "average_second_innings_score"
        )

        fig = px.bar(
            table,
            x="venue",
            y=score_col,
            title="Average Innings Score by Venue",
            text=score_col,
            color_discrete_sequence=color_sequence,
        )

    else:
        return None

    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=500,
        xaxis_tickangle=-30,
        margin=dict(l=30, r=30, t=70, b=80),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#111827"),
        title_font=dict(size=22, color="#111827"),
    )

    return fig


def show_metric_card(intent: str, table: pd.DataFrame) -> None:
    """Display key metric card."""
    if table.empty:
        return

    row = table.iloc[0]

    if intent == "average_first_innings_score_by_venue":
        st.metric("Average First Innings Score", row["average_first_innings_score"])
        st.caption(f"{row['innings_count']} innings analyzed")

    elif intent == "average_second_innings_score_by_venue":
        st.metric("Average Second Innings Score", row["average_second_innings_score"])
        st.caption(f"{row['innings_count']} innings analyzed")

    elif intent == "highest_run_scorers":
        st.metric("Leading Run Scorer", row["player"], f"{row['runs']} runs")
        st.caption(f"Strike rate: {row['strike_rate']}")

    elif intent == "best_strike_rate":
        st.metric("Best Strike Rate", row["player"], row["strike_rate"])
        st.caption(f"{row['runs']} runs from {row['balls_faced']} balls")

    elif intent == "best_economy_rate":
        st.metric("Best Economy Rate", row["player"], row["economy_rate"])
        st.caption(f"{row['wickets']} wickets")

    elif intent == "most_wickets":
        st.metric("Leading Wicket Taker", row["player"], f"{row['wickets']} wickets")
        st.caption(f"Economy rate: {row['economy_rate']}")

    elif intent == "powerplay_team_scoring":
        st.metric("Powerplay Run Rate", row["powerplay_run_rate"], row["batting_team"])
        st.caption(f"{row['matches']} matches analyzed")

    elif intent == "death_over_batting_analysis":
        st.metric("Best Death-Over Strike Rate", row["player"], row["death_strike_rate"])
        st.caption(f"{row['death_runs']} runs from {row['balls_faced']} balls")


def render_header() -> None:
    """Render app header."""
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">🏏 Innings Insight</div>
            <div class="hero-subtitle">Natural Language Cricket Analytics Platform</div>
            <div class="hero-description">
                Ask cricket questions in plain English and get verified statistics,
                supporting tables, visualizations, and short analytical insights.
                Built with a structured analytics engine instead of guessed chatbot answers.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Matches</div>
                <div class="stat-value">{DATASET_MATCHES}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Deliveries</div>
                <div class="stat-value">{DATASET_DELIVERIES}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Seasons</div>
                <div class="stat-value">{DATASET_SEASONS}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar() -> str:
    """Render sidebar and return selected question."""
    with st.sidebar:
        st.header("Sample Questions")

        sample_questions = [
            "avg batting first score in wankhede",
            "average chasing score eden",
            "Who are the highest run scorers?",
            "Who has the best strike rate?",
            "Who has the best economy rate?",
            "top wicket takers",
            "csk powerplay score",
            "mi pp scoring",
            "best death hitters",
            "kohli vs rohit",
            "dhoni vs kohli",
        ]

        selected_question = st.radio(
            "Try one:",
            sample_questions,
            index=0,
        )

        st.markdown("---")

        st.markdown("### Supported Analytics")
        st.markdown(
            """
            - Venue innings averages  
            - Run-scorer leaderboards  
            - Strike rate rankings  
            - Economy rate rankings  
            - Wicket leaderboards  
            - Powerplay team scoring  
            - Death-over batting  
            - Player comparison  
            """
        )

        st.markdown("---")
        st.caption(
            "All numbers are calculated using Python and DuckDB. Natural language is used for routing."
        )

    return selected_question


def main() -> None:
    apply_custom_css()
    render_header()

    selected_question = render_sidebar()

    st.markdown("<br>", unsafe_allow_html=True)

    question = st.text_input(
        "Ask a cricket question:",
        value=selected_question,
        placeholder="Example: kohli vs rohit",
    )

    analyze_clicked = st.button("Analyze", type="primary")

    if analyze_clicked and question:
        response = answer_question(question)

        intent = response["intent"]
        table = response["table"]
        answer = response["answer"]

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<span class="intent-pill">Detected intent: {intent}</span>', unsafe_allow_html=True)

        if intent == "unsupported":
            st.warning(answer)
            return

        st.markdown("## Answer")
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

        if table.empty:
            st.warning(
                "No result found. Try a broader venue, team, or player name. "
                "Examples: Wankhede, Eden, CSK, MI, Kohli, Rohit."
            )
            return

        metric_col, table_col = st.columns([1, 2])

        with metric_col:
            st.markdown("### Key Metric")
            show_metric_card(intent, table)

        with table_col:
            st.markdown("### Supporting Table")
            st.dataframe(table, width="stretch")

        chart = create_chart(intent, table)

        if chart is not None:
            st.markdown("### Visualization")
            st.plotly_chart(chart, width="stretch")

        st.markdown("### Insight")
        st.info(response["insight"])

        st.caption(
            "Result generated from structured ball-by-ball data. "
            "Natural language is used only for intent routing and explanation."
        )


if __name__ == "__main__":
    main()