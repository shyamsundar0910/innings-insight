import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Innings Insight", layout="wide")

# -------------------------------
# TITLE
# -------------------------------
st.title("🏏 Innings Insight")
st.subheader("Natural Language Cricket Analytics Platform")

st.write("Ask cricket analytics questions in plain English.")

# -------------------------------
# SAMPLE DATA (Replace later with real dataset)
# -------------------------------
data = {
    "venue": ["Wankhede Stadium"],
    "average_first_innings_score": [173.13],
    "innings_count": [132],
    "highest_score": [243],
    "lowest_score": [67]
}

df = pd.DataFrame(data)

# -------------------------------
# INPUT
# -------------------------------
question = st.text_input(
    "Ask a cricket question:",
    "What is the average first innings score at Wankhede?"
)

# -------------------------------
# BUTTON
# -------------------------------
if st.button("Analyze"):

    # Simulated answer (replace with backend later)
    answer = (
        "Wankhede Stadium has been a high-scoring first-innings venue, "
        "with an average of 173.13 across 132 innings."
    )

    st.markdown("## Answer")
    st.success(answer)

    # -------------------------------
    # METRIC
    # -------------------------------
    st.markdown("### Average First Innings Score")
    st.metric(label="Score", value=173.13)

    # -------------------------------
    # TABLE
    # -------------------------------
    st.markdown("### Supporting Table")
    st.dataframe(df)

    # -------------------------------
    # CHART
    # -------------------------------
    st.markdown("### Visualization")

    chart = px.bar(
        df,
        x="venue",
        y="average_first_innings_score",
        title="Average First Innings Score by Venue"
    )

    if chart:
        st.plotly_chart(chart)

    # -------------------------------
    # INSIGHT
    # -------------------------------
    st.markdown("### Insight")
    st.info(answer)