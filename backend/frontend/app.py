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


def create_chart(intent: str, table: pd.DataFrame):
    """Create Plotly chart based on detected intent."""
    if table.empty:
        return None

    if intent == "highest_run_scorers":
        return px.bar(
            table,
            x="player",
            y="runs",
            title="Top IPL Run Scorers",
            text="runs",
        )

    if intent == "best_strike_rate":
        return px.bar(
            table,
            x="player",
            y="strike_rate",
            title="Best Batting Strike Rate",
            text="strike_rate",
        )

    if intent == "best_economy_rate":
        return px.bar(
            table,
            x="player",
            y="economy_rate",
            title="Best Economy Rate",
            text="economy_rate",
        )

    if intent == "most_wickets":
        return px.bar(
            table,
            x="player",
            y="wickets",
            title="Top IPL Wicket Takers",
            text="wickets",
        )

    if intent == "powerplay_team_scoring":
        return px.bar(
            table,
            x="batting_team",
            y="powerplay_run_rate",
            title="Powerplay Run Rate",
            text="powerplay_run_rate",
        )

    if intent == "death_over_batting_analysis":
        return px.bar(
            table,
            x="player",
            y="death_strike_rate",
            title="Best Death-Over Batters",
            text="death_strike_rate",
        )

    if intent == "player_comparison":
        available_columns = [
            column
            for column in ["runs", "strike_rate", "wickets", "economy_rate"]
            if column in table.columns
        ]

        if not available_columns:
            return None

        melted_df = table.melt(
            id_vars="player",
            value_vars=available_columns,
            var_name="metric",
            value_name="value",
        )

        return px.bar(
            melted_df,
            x="metric",
            y="value",
            color="player",
            barmode="group",
            title="Player Comparison",
            text="value",
        )

    if intent in {
        "average_first_innings_score_by_venue",
        "average_second_innings_score_by_venue",
    }:
        score_column = (
            "average_first_innings_score"
            if intent == "average_first_innings_score_by_venue"
            else "average_second_innings_score"
        )

        return px.bar(
            table,
            x="venue",
            y=score_column,
            title="Average Innings Score by Venue",
            text=score_column,
        )

    return None


def show_metric_card(intent: str, table: pd.DataFrame) -> None:
    """Display key metric card."""
    if table.empty:
        return

    row = table.iloc[0]

    if intent == "average_first_innings_score_by_venue":
        st.metric(
            label="Average First Innings Score",
            value=row["average_first_innings_score"],
        )

    elif intent == "average_second_innings_score_by_venue":
        st.metric(
            label="Average Second Innings Score",
            value=row["average_second_innings_score"],
        )

    elif intent == "highest_run_scorers":
        st.metric(
            label="Leading Run Scorer",
            value=row["player"],
            delta=f"{row['runs']} runs",
        )

    elif intent == "best_strike_rate":
        st.metric(
            label="Best Strike Rate",
            value=row["player"],
            delta=row["strike_rate"],
        )

    elif intent == "best_economy_rate":
        st.metric(
            label="Best Economy Rate",
            value=row["player"],
            delta=row["economy_rate"],
        )

    elif intent == "most_wickets":
        st.metric(
            label="Leading Wicket Taker",
            value=row["player"],
            delta=f"{row['wickets']} wickets",
        )

    elif intent == "powerplay_team_scoring":
        st.metric(
            label="Powerplay Run Rate",
            value=row["powerplay_run_rate"],
            delta=row["batting_team"],
        )

    elif intent == "death_over_batting_analysis":
        st.metric(
            label="Best Death-Over Strike Rate",
            value=row["player"],
            delta=row["death_strike_rate"],
        )


def main() -> None:
    st.title("🏏 Innings Insight")
    st.subheader("Natural Language Cricket Analytics Platform")

    st.markdown(
        """
        Ask cricket analytics questions in plain English.  
        The current MVP uses historical IPL ball-by-ball data from Cricsheet.
        """
    )

    with st.sidebar:
        st.header("Sample Questions")

        sample_questions = [
            "What is the average first innings score at Wankhede?",
            "What is the average second innings score at Eden Gardens?",
            "Who are the highest run scorers?",
            "Who has the best strike rate?",
            "Who has the best economy rate?",
            "Who has taken the most wickets?",
            "How does Chennai score in the powerplay?",
            "Powerplay scoring for Mumbai Indians",
            "Who are the best death-over batters?",
            "Compare V Kohli and RG Sharma",
        ]

        selected_question = st.radio(
            "Try one:",
            sample_questions,
            index=0,
        )

        st.markdown("---")
        st.caption(
            "MVP scope: IPL historical stats, venue analysis, player leaderboards, "
            "powerplay scoring, death-over batting, and player comparison."
        )

    question = st.text_input(
        "Ask a cricket question:",
        value=selected_question,
        placeholder="Example: Who has taken the most wickets?",
    )

    ask_button = st.button("Analyze", type="primary")

    if ask_button and question:
        response = answer_question(question)

        intent = response["intent"]
        table = response["table"]
        answer = response["answer"]

        st.markdown("---")

        st.caption(f"Detected intent: `{intent}`")

        if intent == "unsupported":
            st.warning(answer)
            return

        st.markdown("## Answer")
        st.success(answer)

        if not table.empty:
            col1, col2 = st.columns([1, 2])

            with col1:
                show_metric_card(intent, table)

            with col2:
                st.markdown("### Supporting Table")
                st.dataframe(table, use_container_width=True)

            chart = create_chart(intent, table)

            if chart is not None:
                st.markdown("### Visualization")
                chart.update_layout(xaxis_tickangle=-35)
                st.plotly_chart(chart, use_container_width=True)

            st.markdown("### Insight")
            st.info(response["insight"])

        else:
            st.warning(
                "No result found. Try a broader name, for example: "
                "`Wankhede`, `Chennai`, `Mumbai`, `V Kohli`, or `RG Sharma`."
            )


if __name__ == "__main__":
    main()