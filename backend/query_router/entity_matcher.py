from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from backend.analytics_engine.queries import player_list, team_list, venue_list  # noqa: E402


TEAM_ALIASES = {
    "csk": "Chennai Super Kings",
    "chennai": "Chennai Super Kings",
    "mi": "Mumbai Indians",
    "mumbai": "Mumbai Indians",
    "rcb": "Royal Challengers Bangalore",
    "bangalore": "Royal Challengers Bangalore",
    "bengaluru": "Royal Challengers Bengaluru",
    "kkr": "Kolkata Knight Riders",
    "kolkata": "Kolkata Knight Riders",
    "srh": "Sunrisers Hyderabad",
    "hyderabad": "Sunrisers Hyderabad",
    "rr": "Rajasthan Royals",
    "rajasthan": "Rajasthan Royals",
    "dc": "Delhi Capitals",
    "delhi": "Delhi Capitals",
    "kxip": "Kings XI Punjab",
    "pbks": "Punjab Kings",
    "punjab": "Punjab Kings",
    "gt": "Gujarat Titans",
    "gujarat": "Gujarat Titans",
    "lsg": "Lucknow Super Giants",
    "lucknow": "Lucknow Super Giants",
    "rps": "Rising Pune Supergiant",
    "pune": "Rising Pune Supergiant",
    "deccan": "Deccan Chargers",
    "gl": "Gujarat Lions",
}


PLAYER_ALIASES = {
    "kohli": "V Kohli",
    "virat": "V Kohli",
    "virat kohli": "V Kohli",
    "rohit": "RG Sharma",
    "rohit sharma": "RG Sharma",
    "dhoni": "MS Dhoni",
    "ms dhoni": "MS Dhoni",
    "abd": "AB de Villiers",
    "ab de villiers": "AB de Villiers",
    "gayle": "CH Gayle",
    "chris gayle": "CH Gayle",
    "bumrah": "JJ Bumrah",
    "jasprit bumrah": "JJ Bumrah",
    "jadeja": "RA Jadeja",
    "ravindra jadeja": "RA Jadeja",
    "raina": "SK Raina",
    "suresh raina": "SK Raina",
    "warner": "DA Warner",
    "david warner": "DA Warner",
    "russell": "AD Russell",
    "andre russell": "AD Russell",
    "narine": "SP Narine",
    "sunil narine": "SP Narine",
    "chahal": "YS Chahal",
    "yuzvendra chahal": "YS Chahal",
    "ashwin": "R Ashwin",
    "rashid": "Rashid Khan",
    "rashid khan": "Rashid Khan",
    "pant": "RR Pant",
    "rishabh pant": "RR Pant",
    "kl rahul": "KL Rahul",
    "rahul": "KL Rahul",
}


VENUE_ALIASES = {
    "wankhede": "Wankhede Stadium",
    "eden": "Eden Gardens",
    "eden gardens": "Eden Gardens",
    "chinnaswamy": "M Chinnaswamy Stadium",
    "chepauk": "MA Chidambaram Stadium, Chepauk",
    "chennai stadium": "MA Chidambaram Stadium, Chepauk",
    "motera": "Narendra Modi Stadium, Ahmedabad",
    "narendra modi": "Narendra Modi Stadium, Ahmedabad",
    "ahmedabad": "Narendra Modi Stadium, Ahmedabad",
    "kotla": "Arun Jaitley Stadium",
    "arun jaitley": "Arun Jaitley Stadium",
    "delhi stadium": "Arun Jaitley Stadium",
    "hyderabad stadium": "Rajiv Gandhi International Stadium",
    "uppal": "Rajiv Gandhi International Stadium",
    "mohali": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "jaipur": "Sawai Mansingh Stadium",
    "pune": "Maharashtra Cricket Association Stadium",
}


def normalize_text(value: str) -> str:
    """Normalize text for matching."""
    return value.lower().strip()


@lru_cache(maxsize=1)
def get_teams() -> list[str]:
    """Load available teams from database."""
    df = team_list()

    if df.empty:
        return []

    return sorted(df["team"].dropna().astype(str).unique().tolist())


@lru_cache(maxsize=1)
def get_players() -> list[str]:
    """Load available players from database."""
    df = player_list()

    if df.empty:
        return []

    return sorted(df["player"].dropna().astype(str).unique().tolist())


@lru_cache(maxsize=1)
def get_venues() -> list[str]:
    """Load available venues from database."""
    df = venue_list()

    if df.empty:
        return []

    return sorted(df["venue"].dropna().astype(str).unique().tolist())


def fuzzy_match(
    user_text: str,
    choices: list[str],
    score_cutoff: int = 70,
) -> str:
    """Return best fuzzy match from available choices."""
    if not user_text or not choices:
        return user_text

    match = process.extractOne(
        user_text,
        choices,
        scorer=fuzz.WRatio,
        score_cutoff=score_cutoff,
    )

    if not match:
        return user_text

    return str(match[0])


def match_team(user_text: str) -> str:
    """Match user team input to database team name."""
    normalized = normalize_text(user_text)

    if normalized in TEAM_ALIASES:
        return TEAM_ALIASES[normalized]

    return fuzzy_match(user_text, get_teams(), score_cutoff=65)


def match_player(user_text: str) -> str:
    """Match user player input to database player name."""
    normalized = normalize_text(user_text)

    if normalized in PLAYER_ALIASES:
        return PLAYER_ALIASES[normalized]

    return fuzzy_match(user_text, get_players(), score_cutoff=65)


def match_venue(user_text: str) -> str:
    """Match user venue input to database venue name."""
    normalized = normalize_text(user_text)

    if normalized in VENUE_ALIASES:
        return VENUE_ALIASES[normalized]

    return fuzzy_match(user_text, get_venues(), score_cutoff=65)


def test_entity_matcher() -> None:
    """Quick tests for entity matching."""
    tests = [
        ("team", "csk", match_team),
        ("team", "mi", match_team),
        ("team", "rcb", match_team),
        ("player", "kohli", match_player),
        ("player", "rohit", match_player),
        ("player", "dhoni", match_player),
        ("venue", "wankhede", match_venue),
        ("venue", "eden", match_venue),
        ("venue", "chinnaswamy", match_venue),
    ]

    for category, value, matcher in tests:
        print(f"{category}: {value} -> {matcher(value)}")


if __name__ == "__main__":
    test_entity_matcher()