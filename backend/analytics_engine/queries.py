from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "innings_insight.duckdb"


def get_connection() -> duckdb.DuckDBPyConnection:
    """Create DuckDB connection."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DATABASE_PATH}. "
            "Run backend/data_pipeline/prepare_ipl_data.py first."
        )

    return duckdb.connect(str(DATABASE_PATH))


def run_query(query: str, params: Optional[dict] = None) -> pd.DataFrame:
    """Run SQL query and return dataframe."""
    connection = get_connection()

    try:
        if params:
            result = connection.execute(query, params).fetchdf()
        else:
            result = connection.execute(query).fetchdf()
    finally:
        connection.close()

    return result


def average_first_innings_score_by_venue(
    venue: str,
    min_innings: int = 5,
) -> pd.DataFrame:
    """Average first innings score for a venue."""
    query = """
        SELECT
            venue,
            ROUND(AVG(innings_runs), 2) AS average_first_innings_score,
            COUNT(*) AS innings_count,
            MAX(innings_runs) AS highest_score,
            MIN(innings_runs) AS lowest_score
        FROM innings_summary
        WHERE innings = 1
          AND LOWER(venue) LIKE LOWER(?)
        GROUP BY venue
        HAVING COUNT(*) >= ?
        ORDER BY innings_count DESC
    """

    return run_query(query, [f"%{venue}%", min_innings])


def average_second_innings_score_by_venue(
    venue: str,
    min_innings: int = 5,
) -> pd.DataFrame:
    """Average second innings score for a venue."""
    query = """
        SELECT
            venue,
            ROUND(AVG(innings_runs), 2) AS average_second_innings_score,
            COUNT(*) AS innings_count,
            MAX(innings_runs) AS highest_score,
            MIN(innings_runs) AS lowest_score
        FROM innings_summary
        WHERE innings = 2
          AND LOWER(venue) LIKE LOWER(?)
        GROUP BY venue
        HAVING COUNT(*) >= ?
        ORDER BY innings_count DESC
    """

    return run_query(query, [f"%{venue}%", min_innings])


def highest_run_scorers(limit: int = 10) -> pd.DataFrame:
    """Top IPL run scorers."""
    query = """
        SELECT
            player,
            runs,
            balls_faced,
            strike_rate,
            fours,
            sixes,
            innings
        FROM player_batting_summary
        WHERE player IS NOT NULL
          AND player != ''
        ORDER BY runs DESC
        LIMIT ?
    """

    return run_query(query, [limit])


def best_strike_rate(
    min_balls: int = 100,
    limit: int = 10,
) -> pd.DataFrame:
    """Best batting strike rate with minimum balls filter."""
    query = """
        SELECT
            player,
            runs,
            balls_faced,
            strike_rate,
            fours,
            sixes,
            innings
        FROM player_batting_summary
        WHERE balls_faced >= ?
          AND player IS NOT NULL
          AND player != ''
        ORDER BY strike_rate DESC
        LIMIT ?
    """

    return run_query(query, [min_balls, limit])


def best_economy_rate(
    min_balls: int = 120,
    limit: int = 10,
) -> pd.DataFrame:
    """Best economy rate with minimum balls filter."""
    query = """
        SELECT
            player,
            balls_bowled,
            ROUND(overs_bowled, 2) AS overs_bowled,
            runs_conceded,
            wickets,
            economy_rate,
            balls_per_wicket,
            matches
        FROM player_bowling_summary
        WHERE balls_bowled >= ?
          AND player IS NOT NULL
          AND player != ''
        ORDER BY economy_rate ASC
        LIMIT ?
    """

    return run_query(query, [min_balls, limit])


def most_wickets(limit: int = 10) -> pd.DataFrame:
    """Top IPL wicket takers."""
    query = """
        SELECT
            player,
            wickets,
            balls_bowled,
            ROUND(overs_bowled, 2) AS overs_bowled,
            runs_conceded,
            economy_rate,
            balls_per_wicket,
            matches
        FROM player_bowling_summary
        WHERE player IS NOT NULL
          AND player != ''
        ORDER BY wickets DESC
        LIMIT ?
    """

    return run_query(query, [limit])


def powerplay_team_scoring(team: str) -> pd.DataFrame:
    """Powerplay batting performance for a team."""
    query = """
        SELECT
            batting_team,
            COUNT(DISTINCT match_id) AS matches,
            SUM(total_runs) AS total_powerplay_runs,
            SUM(legal_delivery) AS legal_balls,
            ROUND(SUM(total_runs) * 6.0 / NULLIF(SUM(legal_delivery), 0), 2)
                AS powerplay_run_rate,
            ROUND(AVG(total_runs), 2) AS runs_per_ball
        FROM deliveries
        WHERE phase = 'Powerplay'
          AND LOWER(batting_team) LIKE LOWER(?)
        GROUP BY batting_team
        ORDER BY total_powerplay_runs DESC
    """

    return run_query(query, [f"%{team}%"])


def death_over_batting_analysis(
    min_balls: int = 50,
    limit: int = 10,
) -> pd.DataFrame:
    """Best death-over batters."""
    query = """
        SELECT
            batter AS player,
            SUM(runs_off_bat) AS death_runs,
            SUM(batter_ball) AS balls_faced,
            ROUND(SUM(runs_off_bat) * 100.0 / NULLIF(SUM(batter_ball), 0), 2)
                AS death_strike_rate,
            SUM(CASE WHEN runs_off_bat = 4 THEN 1 ELSE 0 END) AS fours,
            SUM(CASE WHEN runs_off_bat = 6 THEN 1 ELSE 0 END) AS sixes
        FROM deliveries
        WHERE phase = 'Death'
          AND batter IS NOT NULL
          AND batter != ''
        GROUP BY batter
        HAVING SUM(batter_ball) >= ?
        ORDER BY death_strike_rate DESC
        LIMIT ?
    """

    return run_query(query, [min_balls, limit])


def player_comparison(player_1: str, player_2: str) -> pd.DataFrame:
    """Compare two players' batting and bowling records."""
    query = """
        WITH batting AS (
            SELECT
                player,
                runs,
                balls_faced,
                strike_rate,
                fours,
                sixes,
                innings
            FROM player_batting_summary
            WHERE LOWER(player) IN (LOWER(?), LOWER(?))
        ),

        bowling AS (
            SELECT
                player,
                balls_bowled,
                ROUND(overs_bowled, 2) AS overs_bowled,
                runs_conceded,
                wickets,
                economy_rate,
                balls_per_wicket,
                matches
            FROM player_bowling_summary
            WHERE LOWER(player) IN (LOWER(?), LOWER(?))
        )

        SELECT
            COALESCE(batting.player, bowling.player) AS player,
            batting.runs,
            batting.balls_faced,
            batting.strike_rate,
            batting.fours,
            batting.sixes,
            batting.innings,
            bowling.balls_bowled,
            bowling.overs_bowled,
            bowling.runs_conceded,
            bowling.wickets,
            bowling.economy_rate,
            bowling.balls_per_wicket,
            bowling.matches
        FROM batting
        FULL OUTER JOIN bowling
            ON batting.player = bowling.player
    """

    return run_query(query, [player_1, player_2, player_1, player_2])


def venue_list(search_text: str = "") -> pd.DataFrame:
    """Search available venues."""
    query = """
        SELECT DISTINCT venue
        FROM innings_summary
        WHERE LOWER(venue) LIKE LOWER(?)
        ORDER BY venue
    """

    return run_query(query, [f"%{search_text}%"])


def team_list(search_text: str = "") -> pd.DataFrame:
    """Search available teams."""
    query = """
        SELECT DISTINCT batting_team AS team
        FROM deliveries
        WHERE LOWER(batting_team) LIKE LOWER(?)
        ORDER BY batting_team
    """

    return run_query(query, [f"%{search_text}%"])


def player_list(search_text: str = "") -> pd.DataFrame:
    """Search available players."""
    query = """
        SELECT DISTINCT player
        FROM player_batting_summary
        WHERE LOWER(player) LIKE LOWER(?)
        ORDER BY player
    """

    return run_query(query, [f"%{search_text}%"])


def test_queries() -> None:
    """Quick test function."""
    print("\nAverage first innings score at Wankhede:")
    print(average_first_innings_score_by_venue("Wankhede"))

    print("\nTop run scorers:")
    print(highest_run_scorers())

    print("\nBest strike rate:")
    print(best_strike_rate())

    print("\nBest economy rate:")
    print(best_economy_rate())

    print("\nMost wickets:")
    print(most_wickets())

    print("\nPowerplay scoring for Chennai:")
    print(powerplay_team_scoring("Chennai"))

    print("\nDeath-over batting:")
    print(death_over_batting_analysis())

    print("\nPlayer comparison:")
    print(player_comparison("V Kohli", "RG Sharma"))


if __name__ == "__main__":
    test_queries()