import pandas as pd
import plotly.express as px
import streamlit as st

from backend.query_router.router import answer_question


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Innings Insight",
    page_icon="🏏",
    layout="wide",
)


# --------------------------------------------------
# CUSTOM UI
# --------------------------------------------------
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0e1117;
        }

        .stTextInput input {
            background-color: #262730;
            color: white;
            border-radius: 8px;
        }

        .stButton > button {
            background-color: #ff4b4b;
            color: white;
            border: none;
            border-radius: 10px;
            height: 45px;
            width: 100%;
            font-weight: 700;
        }

        .stButton > button:hover {
            background-color: #ff6b6b;
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def create_chart(df: pd.DataFrame):
    """Create a chart when the returned table contains usable columns."""
    if df is None or df.empty or len(df.columns) < 2:
        return None

    x_column = None

    for candidate in [
        "venue",
        "player",
        "batter",
        "bowler",
        "batting_team",
        "team",
        "name",
    ]:
        if candidate in df.columns:
            x_column = candidate
            break

    if x_column is None:
        x_column = df.columns[0]

    numeric_columns = [
        column
        for column in df.columns
        if column != x_column and pd.api.types.is_numeric_dtype(df[column])
    ]

    if not numeric_columns:
        return None

    y_column = numeric_columns[0]
    chart_data = df.head(15).copy()

    return px.bar(
        chart_data,
        x=x_column,
        y=y_column,
        title=f"{y_column.replace('_', ' ').title()} by "
        f"{x_column.replace('_', ' ').title()}",
    )


# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🏏 Innings Insight")
st.markdown("### Natural-Language Cricket Analytics Platform")
st.write(
    "Ask a question about IPL players, teams, venues, phases, "
    "batting, or bowling and receive a data-driven answer."
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.header("💡 Sample questions")

sample_questions = [
    "What is the average first innings score at Wankhede?",
    "What is the average second innings score at Eden Gardens?",
    "Who are the highest run scorers?",
    "Who has the best strike rate?",
    "Who has the best economy rate?",
    "Who has taken the most wickets?",
    "How does CSK score in the powerplay?",
    "Who are the best death-over batters?",
    "Compare Kohli vs Rohit",
]

selected_question = st.sidebar.radio(
    "Choose a question:",
    sample_questions,
)


# --------------------------------------------------
# INPUT
# --------------------------------------------------
input_column, button_column = st.columns([4, 1])

with input_column:
    question = st.text_input(
        "Ask your question:",
        value=selected_question,
    )

with button_column:
    st.write("")
    st.write("")
    analyze = st.button("Analyze", use_container_width=True)


# --------------------------------------------------
# MAIN LOGIC
# --------------------------------------------------
if analyze:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("Analyzing IPL data..."):
                result = answer_question(question.strip())

            if not isinstance(result, dict):
                raise TypeError(
                    "The backend must return a dictionary containing "
                    "'answer', 'table', and optionally 'insight'."
                )

            answer = result.get(
                "answer",
                "The query completed, but no written answer was returned.",
            )

            table = result.get("table", pd.DataFrame())

            if table is None:
                table = pd.DataFrame()
            elif not isinstance(table, pd.DataFrame):
                table = pd.DataFrame(table)

            st.markdown("## 📌 Answer")
            st.success(str(answer))

            if table.empty:
                st.info("No supporting table was returned for this question.")
            else:
                st.markdown("### 📊 Data")
                st.dataframe(
                    table,
                    use_container_width=True,
                    hide_index=True,
                )

                chart = create_chart(table)

                if chart is not None:
                    st.markdown("### 📈 Visualisation")
                    st.plotly_chart(
                        chart,
                        use_container_width=True,
                    )

            insight = result.get("insight")

            if insight:
                st.markdown("### 🧠 Insight")
                st.info(str(insight))

        except Exception as error:
            st.error("The application could not complete this query.")
            st.exception(error)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption(
    "Built with Python, DuckDB, Plotly, and Streamlit | Innings Insight"
)
