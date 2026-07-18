import streamlit as st
import pandas as pd
import plotly.express as px

from backend.query_router.router import answer_question

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Innings Insight", layout="wide")

st.title("🏏 Innings Insight")
st.subheader("Natural Language Cricket Analytics Platform")

st.write("Ask cricket analytics questions in plain English.")

# -------------------------------
# SAMPLE QUESTIONS
# -------------------------------
st.sidebar.header("Sample Questions")

sample_questions = [
    "What is the average first innings score at Wankhede?",
    "Who are the highest run scorers?",
    "Who has the best strike rate?",
    "Who has taken the most wickets?",
    "Compare V Kohli and RG Sharma"
]

selected_question = st.sidebar.radio("Try one:", sample_questions)

# -------------------------------
# INPUT
# -------------------------------
question = st.text_input(
    "Ask a cricket question:",
    selected_question
)

# -------------------------------
# BUTTON
# -------------------------------
if st.button("Analyze"):

    with st.spinner("Analyzing your question..."):

        result = answer_question(question)

        # -------------------------------
        # ANSWER
        # -------------------------------
        st.markdown("## Answer")
        st.success(result["answer"])

        # -------------------------------
        # TABLE
        # -------------------------------
        df = result.get("table", pd.DataFrame())

        if not df.empty:
            st.markdown("### Supporting Table")
            st.dataframe(df)

            # -------------------------------
            # CHART
            # -------------------------------
            st.markdown("### Visualization")

            try:
                if "venue" in df.columns:
                    chart = px.bar(
                        df,
                        x="venue",
                        y=df.columns[1],
                        title="Venue Analysis"
                    )

                elif "player" in df.columns:
                    chart = px.bar(
                        df.head(10),
                        x="player",
                        y=df.columns[1],
                        title="Player Performance"
                    )

                else:
                    chart = None

                if chart:
                    st.plotly_chart(chart)

            except Exception:
                st.warning("Chart could not be generated.")

        # -------------------------------
        # INSIGHT
        # -------------------------------
        if result.get("insight"):
            st.markdown("### Insight")
            st.info(result["insight"])