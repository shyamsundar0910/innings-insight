import streamlit as st
import pandas as pd
import plotly.express as px

from backend.query_router.router import answer_question

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Innings Insight", layout="wide")

# -------------------------------
# CUSTOM UI STYLE (DARK + CLEAN)
# -------------------------------
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
        color: white;
    }
    .stTextInput>div>div>input {
        background-color: #262730;
        color: white;
        border-radius: 8px;
        padding: 10px;
    }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 10px;
        height: 45px;
        width: 100%;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# HEADER
# -------------------------------
st.title("🏏 Innings Insight")
st.markdown("### AI-Powered Cricket Analytics Platform")

st.markdown(
    "Ask any cricket question and get **data-driven insights instantly**."
)

# -------------------------------
# SIDEBAR (SAMPLE QUESTIONS)
# -------------------------------
st.sidebar.header("💡 Try these questions")

sample_questions = [
    "What is the average first innings score at Wankhede?",
    "What is the average second innings score at Eden Gardens?",
    "Who are the highest run scorers?",
    "Who has the best strike rate?",
    "Who has the best economy rate?",
    "Who has taken the most wickets?",
    "How does CSK score in the powerplay?",
    "Who are the best death-over batters?",
    "Compare Kohli vs Rohit"
]

selected_question = st.sidebar.radio("Select a question:", sample_questions)

# -------------------------------
# INPUT SECTION (CLEAN LAYOUT)
# -------------------------------
col1, col2 = st.columns([4, 1])

with col1:
    question = st.text_input(
        "Ask your question:",
        selected_question
    )

with col2:
    analyze = st.button("Analyze")

# -------------------------------
# MAIN LOGIC
# -------------------------------
if analyze:

    with st.spinner("Analyzing IPL data... 🧠"):

        result = answer_question(question)

        # -------------------------------
        # ANSWER
        # -------------------------------
        st.markdown("## 📌 Answer")
        st.success(result["answer"])

        # -------------------------------
        # TABLE
        # -------------------------------
        df = result.get("table", pd.DataFrame())

        if df.empty:
            st.warning("No data found. Try a different query.")
        else:
            st.markdown("### 📊 Data Table")
            st.dataframe(df)

            # -------------------------------
            # VISUALIZATION
            # -------------------------------
            st.markdown("### 📈 Visualization")

            try:
                chart = None

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

                elif "batting_team" in df.columns:
                    chart = px.bar(
                        df,
                        x="batting_team",
                        y=df.columns[1],
                        title="Team Performance"
                    )

                if chart:
                    st.plotly_chart(chart, use_container_width=True)

            except Exception:
                st.warning("Chart could not be generated.")

        # -------------------------------
        # INSIGHT
        # -------------------------------
        if result.get("insight"):
            st.markdown("### 🧠 Insight")
            st.info(result["insight"])

# -------------------------------
# FOOTER
# -------------------------------
st.markdown("---")
st.markdown(
    "Built with ❤️ using Python, DuckDB, and Streamlit | Innings Insight"
)