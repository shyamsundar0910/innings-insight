from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from backend.analytics_engine.queries import (  # noqa: E402
    average_first_innings_score_by_venue,
    average_second_innings_score_by_venue,
    best_economy_rate,
    best_strike_rate,
    death_over_batting_analysis,
    highest_run_scorers,
    most_wickets,
    player_comparison,
    powerplay_team_scoring,
)

from backend.query_router.entity_matcher import (  # noqa: E402
    match_player,
    match_team,
    match_venue,
)


SUPPORTED_INTENTS = {
    "average_first_innings_score_by_venue",
    "average_second_innings_score_by_venue",
    "highest_run_scorers",
    "best_strike_rate",
    "best_economy_rate",
    "most_wickets",
    "powerplay_team_scoring",
    "death_over_batting_analysis",
    "player_comparison",
    "unsupported",
}


def clean_question(question: str) -> str:
    """Normalize user question."""
    return question.lower().strip()


def remove_punctuation(text: str) -> str:
    """Remove basic punctuation."""
    return re.sub(r"[?.,!]+$", "", text.strip())


def extract_after_keywords(question: str, keywords: list[str]) -> str:
    """
    Extract text after the first matching keyword.

    Example:
    "average first innings score at Wankhede"
    keyword = "at"
    result = "Wankhede"
    """
    lower_question = question.lower()

    for keyword in keywords:
        pattern = rf"\b{keyword}\b\s+(.+)"
        match = re.search(pattern, lower_question)

        if match:
            value = match.group(1).strip()
            value = re.sub(r"[?.,!]+$", "", value)
            return value.title()

    return ""


def extract_venue_from_question(question: str) -> str:
    """
    Extract venue from venue-related questions.

    Supports:
    - average first innings score at Wankhede
    - avg batting first score in wankhede
    - chasing average eden
    """
    venue = extract_after_keywords(question, ["at", "in", "for"])

    if venue:
        return match_venue(venue)

    cleaned = re.sub(
        r"(?i)\baverage\b|\bavg\b|\bmean\b|\bfirst innings\b|\bsecond innings\b|"
        r"\b1st innings\b|\b2nd innings\b|\bbatting first\b|\bchasing\b|"
        r"\bscore\b|\bscores\b|\bruns\b|\bat\b|\bin\b|\bfor\b|\?",
        "",
        question,
    ).strip()

    return match_venue(cleaned)


def extract_players_for_comparison(question: str) -> tuple[str, str]:
    """
    Extract two player names from comparison questions.

    Supports:
    - Compare V Kohli and RG Sharma
    - Kohli vs Rohit
    - Virat Kohli versus Rohit Sharma
    """
    question_clean = remove_punctuation(question)

    question_clean = re.sub(r"(?i)\bcompare\b", "", question_clean).strip()
    question_clean = re.sub(r"(?i)\bcomparison\b", "", question_clean).strip()
    question_clean = re.sub(r"(?i)\bipl record\b", "", question_clean).strip()
    question_clean = re.sub(r"(?i)\brecord\b", "", question_clean).strip()

    if " and " in question_clean.lower():
        parts = re.split(r"(?i)\s+and\s+", question_clean)
    elif " vs " in question_clean.lower():
        parts = re.split(r"(?i)\s+vs\s+", question_clean)
    elif " versus " in question_clean.lower():
        parts = re.split(r"(?i)\s+versus\s+", question_clean)
    else:
        return "", ""

    if len(parts) < 2:
        return "", ""

    player_1 = match_player(parts[0].strip())
    player_2 = match_player(parts[1].strip())

    return player_1, player_2


def extract_team_for_powerplay(question: str) -> str:
    """
    Extract team name from powerplay questions.

    Supports:
    - How does Chennai score in the powerplay?
    - Powerplay scoring for Chennai
    - csk powerplay score
    - mi pp scoring
    """
    team = extract_after_keywords(question, ["for", "by", "of"])

    if team:
        return match_team(team)

    cleaned_question = re.sub(
        r"(?i)\bhow does\b|\bhow do\b|\bscore\b|\bscores\b|\bscoring\b|"
        r"\brun rate\b|\brate\b|\bin the\b|\bpowerplay\b|\bpower play\b|\bpp\b|\?",
        "",
        question,
    ).strip()

    return match_team(cleaned_question)


def is_first_innings_question(question_lower: str) -> bool:
    """Detect first-innings / batting-first score questions."""
    first_terms = [
        "first innings",
        "1st innings",
        "batting first",
        "bat first",
        "first inning",
    ]

    score_terms = ["average", "avg", "mean", "score", "runs"]

    return any(term in question_lower for term in first_terms) and any(
        term in question_lower for term in score_terms
    )


def is_second_innings_question(question_lower: str) -> bool:
    """Detect second-innings / chasing score questions."""
    second_terms = [
        "second innings",
        "2nd innings",
        "chasing",
        "chase",
        "batting second",
        "bat second",
        "second inning",
    ]

    score_terms = ["average", "avg", "mean", "score", "runs"]

    return any(term in question_lower for term in second_terms) and any(
        term in question_lower for term in score_terms
    )


def detect_intent(question: str) -> dict[str, Any]:
    """
    Detect intent and parameters from user question.

    This is a hybrid MVP router:
    - keyword/synonym rules for intent
    - fuzzy entity matching for player/team/venue names
    """
    question_lower = clean_question(question)

    if is_first_innings_question(question_lower):
        venue = extract_venue_from_question(question)
        return {
            "intent": "average_first_innings_score_by_venue",
            "parameters": {"venue": venue},
        }

    if is_second_innings_question(question_lower):
        venue = extract_venue_from_question(question)
        return {
            "intent": "average_second_innings_score_by_venue",
            "parameters": {"venue": venue},
        }

    if (
        "highest run" in question_lower
        or "top run" in question_lower
        or "most runs" in question_lower
        or "run scorers" in question_lower
        or "leading run" in question_lower
        or "top batsmen" in question_lower
        or "top batters" in question_lower
    ):
        return {
            "intent": "highest_run_scorers",
            "parameters": {"limit": 10},
        }

    if (
        "best strike rate" in question_lower
        or "highest strike rate" in question_lower
        or "strike rate" in question_lower
        or "fastest scorers" in question_lower
        or "most aggressive batters" in question_lower
    ):
        return {
            "intent": "best_strike_rate",
            "parameters": {"min_balls": 100, "limit": 10},
        }

    if (
        "best economy" in question_lower
        or "lowest economy" in question_lower
        or "economy rate" in question_lower
        or "most economical" in question_lower
        or "economical bowlers" in question_lower
    ):
        return {
            "intent": "best_economy_rate",
            "parameters": {"min_balls": 120, "limit": 10},
        }

    if (
        "most wickets" in question_lower
        or "highest wickets" in question_lower
        or "top wicket" in question_lower
        or "wicket takers" in question_lower
        or "leading wicket" in question_lower
        or "top bowlers" in question_lower
    ):
        return {
            "intent": "most_wickets",
            "parameters": {"limit": 10},
        }

    if (
        "powerplay" in question_lower
        or "power play" in question_lower
        or re.search(r"\bpp\b", question_lower)
    ):
        team = extract_team_for_powerplay(question)
        return {
            "intent": "powerplay_team_scoring",
            "parameters": {"team": team},
        }

    if (
        "death over" in question_lower
        or "death-over" in question_lower
        or "death overs" in question_lower
        or "death batting" in question_lower
        or "death hitters" in question_lower
        or "finishers" in question_lower
    ):
        return {
            "intent": "death_over_batting_analysis",
            "parameters": {"min_balls": 50, "limit": 10},
        }

    if (
        "compare" in question_lower
        or "comparison" in question_lower
        or " vs " in question_lower
        or " versus " in question_lower
    ):
        player_1, player_2 = extract_players_for_comparison(question)

        return {
            "intent": "player_comparison",
            "parameters": {
                "player_1": player_1,
                "player_2": player_2,
            },
        }

    return {
        "intent": "unsupported",
        "parameters": {},
    }


def generate_basic_insight(intent: str, result: pd.DataFrame) -> str:
    """Generate a simple rule-based insight from the result."""
    if result.empty:
        return "No matching result was found. Try using a broader venue, team, or player name."

    if intent == "average_first_innings_score_by_venue":
        row = result.iloc[0]
        avg_score = row["average_first_innings_score"]
        venue = row["venue"]
        innings_count = row["innings_count"]

        if avg_score >= 170:
            return (
                f"{venue} has been a high-scoring first-innings venue, "
                f"with an average of {avg_score} across {innings_count} innings."
            )

        return (
            f"{venue} has an average first-innings score of {avg_score} "
            f"across {innings_count} innings."
        )

    if intent == "average_second_innings_score_by_venue":
        row = result.iloc[0]
        avg_score = row["average_second_innings_score"]
        venue = row["venue"]
        innings_count = row["innings_count"]

        return (
            f"{venue} has an average second-innings score of {avg_score} "
            f"across {innings_count} innings."
        )

    if intent == "highest_run_scorers":
        top_player = result.iloc[0]["player"]
        runs = result.iloc[0]["runs"]
        return f"{top_player} leads the run-scoring list with {runs} IPL runs in this dataset."

    if intent == "best_strike_rate":
        top_player = result.iloc[0]["player"]
        strike_rate = result.iloc[0]["strike_rate"]
        balls = result.iloc[0]["balls_faced"]
        return (
            f"{top_player} has the highest strike rate in this filtered list, "
            f"scoring at {strike_rate} after facing {balls} balls."
        )

    if intent == "best_economy_rate":
        top_player = result.iloc[0]["player"]
        economy = result.iloc[0]["economy_rate"]
        return f"{top_player} has the best economy rate in this filtered list at {economy}."

    if intent == "most_wickets":
        top_player = result.iloc[0]["player"]
        wickets = result.iloc[0]["wickets"]
        return f"{top_player} is the leading wicket-taker in this dataset with {wickets} wickets."

    if intent == "powerplay_team_scoring":
        row = result.iloc[0]
        team = row["batting_team"]
        run_rate = row["powerplay_run_rate"]
        matches = row["matches"]
        return (
            f"{team} has scored at a powerplay run rate of {run_rate} "
            f"across {matches} matches."
        )

    if intent == "death_over_batting_analysis":
        top_player = result.iloc[0]["player"]
        strike_rate = result.iloc[0]["death_strike_rate"]
        return (
            f"{top_player} stands out as the top death-over batter by strike rate, "
            f"scoring at {strike_rate} in the death overs."
        )

    if intent == "player_comparison":
        return "The comparison table shows batting and bowling metrics side by side for both players."

    return "The result was generated from the DuckDB analytics engine."


def answer_question(question: str) -> dict[str, Any]:
    """Main entry point for natural language cricket questions."""
    routed = detect_intent(question)
    intent = routed["intent"]
    parameters = routed["parameters"]

    if intent == "unsupported":
        return {
            "question": question,
            "intent": intent,
            "parameters": parameters,
            "answer": (
                "This question is not supported in the current MVP. "
                "Innings Insight currently supports historical IPL statistical analysis "
                "for venues, players, teams, powerplay scoring, death-over batting, "
                "leaderboards, and player comparison."
            ),
            "table": pd.DataFrame(),
            "insight": "",
        }

    if intent == "average_first_innings_score_by_venue":
        result = average_first_innings_score_by_venue(**parameters)

    elif intent == "average_second_innings_score_by_venue":
        result = average_second_innings_score_by_venue(**parameters)

    elif intent == "highest_run_scorers":
        result = highest_run_scorers(**parameters)

    elif intent == "best_strike_rate":
        result = best_strike_rate(**parameters)

    elif intent == "best_economy_rate":
        result = best_economy_rate(**parameters)

    elif intent == "most_wickets":
        result = most_wickets(**parameters)

    elif intent == "powerplay_team_scoring":
        result = powerplay_team_scoring(**parameters)

    elif intent == "death_over_batting_analysis":
        result = death_over_batting_analysis(**parameters)

    elif intent == "player_comparison":
        result = player_comparison(**parameters)

    else:
        result = pd.DataFrame()

    insight = generate_basic_insight(intent, result)

    return {
        "question": question,
        "intent": intent,
        "parameters": parameters,
        "answer": insight,
        "table": result,
        "insight": insight,
    }


def test_router() -> None:
    """Test the natural language router."""
    questions = [
        "What is the average first innings score at Wankhede?",
        "avg batting first score in wankhede",
        "What is the average second innings score at Eden Gardens?",
        "average chasing score eden",
        "Who are the highest run scorers?",
        "top batters in ipl",
        "Who has the best strike rate?",
        "most aggressive batters",
        "Who has the best economy rate?",
        "most economical bowlers",
        "Who has taken the most wickets?",
        "top wicket takers",
        "How does Chennai score in the powerplay?",
        "csk powerplay score",
        "mi pp scoring",
        "Who are the best death-over batters?",
        "best death hitters",
        "Compare V Kohli and RG Sharma",
        "kohli vs rohit",
        "Who will win tomorrow?",
    ]

    for question in questions:
        print("\n" + "=" * 100)
        print(f"Question: {question}")

        response = answer_question(question)

        print(f"Intent: {response['intent']}")
        print(f"Parameters: {response.get('parameters')}")
        print(f"Answer: {response['answer']}")

        table = response["table"]

        if not table.empty:
            print(table.head(10))


if __name__ == "__main__":
    test_router()