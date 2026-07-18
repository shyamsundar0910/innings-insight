import streamlit as st
import pandas as pd
import plotly.express as px

# Import backend logic
from backend.query_router.router import answer_question

# ------------------ UI CONFIG ------------------
st.set_page_config(
    page_title="Innings Insight",
    page_icon="🏏",
    layout="wide"
)

# ------------------ HEADER ------------------
st.title("🏏 Innings Insight")
st.subheader("Natural Language Cricket Analytics Platform")

st.write(
    "Ask IPL cricket analytics questions in plain English and get insights, tables, and visualizations."
)

# ------------------ SAMPLE QUESTIONS ------------------
st.sidebar.header("Sample Questions")

sample_questions = [
    "avg batting first score in wankhede",
    "average chasing score eden",
    "top wicket takers",
    "csk powerplay score",
    "mi pp scoring",
    "best death hitters",
    "kohli vs rohit",
    "dhoni vs kohli"
]

selected_question = st.sidebar.radio("Try one:", sample_questions)

# ------------------ INPUT ------------------
st.write("### Ask a cricket question:")

user_input = st.text_input(
    "",
    value=selected_question
)

# ------------------ BUTTON ------------------
if st.button("Analyze"):

    if user_input.strip() == "":
        st.warning("Please enter a question.")
    else:
        try:
            result = answer_question(user_input)

            # ------------------ OUTPUT ------------------
            st.write("### Answer")
            st.success(result["answer"])

            # Show table if exists
            if "table" in result and result["table"] is not None:
                df = result["table"]
                st.write("### Supporting Table")
                st.dataframe(df)

            # Show visualization if numeric data
            if "table" in result and result["table"] is not None:
                df = result["table"]

                # Try simple chart if possible
                numeric_cols = df.select_dtypes(include=['number']).columns

                if len(numeric_cols) >= 1:
                    st.write("### Visualization")
                    fig = px.bar(df, y=numeric_cols[0])
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {str(e)}")