from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "ipl_male_csv"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"

DUCKDB_PATH = DATABASE_DIR / "innings_insight.duckdb"


BOWLER_WICKET_TYPES = {
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "stumped",
    "hit wicket",
}


VENUE_STANDARDIZATION_MAP = {
    "Wankhede Stadium, Mumbai": "Wankhede Stadium",
    "Eden Gardens, Kolkata": "Eden Gardens",
    "M Chinnaswamy Stadium, Bengaluru": "M Chinnaswamy Stadium",
    "M.Chinnaswamy Stadium": "M Chinnaswamy Stadium",
    "MA Chidambaram Stadium, Chepauk, Chennai": "MA Chidambaram Stadium",
    "MA Chidambaram Stadium, Chepauk": "MA Chidambaram Stadium",
    "MA Chidambaram Stadium": "MA Chidambaram Stadium",
    "Narendra Modi Stadium, Ahmedabad": "Narendra Modi Stadium",
    "Arun Jaitley Stadium, Delhi": "Arun Jaitley Stadium",
    "Feroz Shah Kotla": "Arun Jaitley Stadium",
    "Feroz Shah Kotla Ground": "Arun Jaitley Stadium",
    "Rajiv Gandhi International Stadium, Uppal": "Rajiv Gandhi International Stadium",
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad": "Rajiv Gandhi International Stadium",
    "Rajiv Gandhi International Stadium": "Rajiv Gandhi International Stadium",
    "Punjab Cricket Association IS Bindra Stadium, Mohali": "PCA IS Bindra Stadium",
    "Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh": "PCA IS Bindra Stadium",
    "Punjab Cricket Association Stadium, Mohali": "PCA IS Bindra Stadium",
    "Punjab Cricket Association Stadium, Mohali, Chandigarh": "PCA IS Bindra Stadium",
    "Sawai Mansingh Stadium, Jaipur": "Sawai Mansingh Stadium",
    "Maharashtra Cricket Association Stadium, Pune": "Maharashtra Cricket Association Stadium",
    "Dr DY Patil Sports Academy, Mumbai": "Dr DY Patil Sports Academy",
    "Dr. DY Patil Sports Academy": "Dr DY Patil Sports Academy",
    "Dr DY Patil Sports Academy": "Dr DY Patil Sports Academy",
    "Brabourne Stadium, Mumbai": "Brabourne Stadium",
    "Brabourne Stadium": "Brabourne Stadium",
    "Dubai International Cricket Stadium": "Dubai International Cricket Stadium",
    "Sharjah Cricket Stadium": "Sharjah Cricket Stadium",
    "Sheikh Zayed Stadium, Abu Dhabi": "Sheikh Zayed Stadium",
    "Sheikh Zayed Stadium": "Sheikh Zayed Stadium",
    "Zayed Cricket Stadium, Abu Dhabi": "Sheikh Zayed Stadium",
    "Himachal Pradesh Cricket Association Stadium, Dharamsala": "HPCA Stadium",
    "Himachal Pradesh Cricket Association Stadium": "HPCA Stadium",
    "Barsapara Cricket Stadium, Guwahati": "Barsapara Cricket Stadium",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam": "ACA-VDCA Cricket Stadium",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium": "ACA-VDCA Cricket Stadium",
    "ACA-VDCA Stadium": "ACA-VDCA Cricket Stadium",
}


def standardize_venue_name(venue: str) -> str:
    """Standardize duplicate IPL venue names."""
    if not venue:
        return ""

    venue = venue.strip()
    return VENUE_STANDARDIZATION_MAP.get(venue, venue)


def safe_get(row: list[str], index: int, default: str = "") -> str:
    """Safely get a value from a CSV row."""
    if index < len(row):
        return row[index].strip()
    return default


def to_int(value: Any, default: int = 0) -> int:
    """Convert a value to integer safely."""
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def detect_delimiter(file_path: Path) -> str:
    """Detect whether the file is comma-separated or tab-separated."""
    sample = file_path.read_text(errors="ignore")[:4096]

    if sample.count("\t") > sample.count(","):
        return "\t"

    return ","


def get_over_number(ball_value: str) -> int:
    """Convert ball value like '17.5' into over number 17."""
    try:
        return int(str(ball_value).split(".")[0])
    except (ValueError, IndexError):
        return -1


def get_phase(over_number: int) -> str:
    """
    T20 phase classification.

    Overs 0-5 = Powerplay
    Overs 6-14 = Middle
    Overs 15-19 = Death
    """
    if 0 <= over_number <= 5:
        return "Powerplay"
    if 6 <= over_number <= 14:
        return "Middle"
    if 15 <= over_number <= 19:
        return "Death"
    return "Unknown"


def parse_match_file(file_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Parse one Cricsheet CSV match file.

    The file contains:
    - info rows for metadata
    - ball rows for delivery-level data
    """
    delimiter = detect_delimiter(file_path)

    metadata: dict[str, Any] = {
        "source_file": file_path.name,
        "match_id": file_path.stem,
        "competition_name": "Indian Premier League",
    }

    teams: list[str] = []
    deliveries: list[dict[str, Any]] = []

    with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)

        for row in reader:
            if not row:
                continue

            row_type = safe_get(row, 0)

            if row_type == "info":
                key = safe_get(row, 1)
                values = [value.strip() for value in row[2:] if value.strip()]

                if key == "team" and values:
                    teams.append(values[0])

                elif key in {
                    "season",
                    "date",
                    "event",
                    "match_id",
                    "match_type",
                    "venue",
                    "city",
                    "toss_winner",
                    "toss_decision",
                    "winner",
                    "winner_runs",
                    "winner_wickets",
                    "gender",
                    "overs",
                }:
                    if key == "venue":
                        metadata[key] = standardize_venue_name(values[0]) if values else ""
                    else:
                        metadata[key] = values[0] if values else ""

            elif row_type == "ball":
                innings = to_int(safe_get(row, 1))
                ball = safe_get(row, 2)
                batting_team = safe_get(row, 3)
                batter = safe_get(row, 4)
                non_striker = safe_get(row, 5)
                bowler = safe_get(row, 6)

                runs_off_bat = to_int(safe_get(row, 7))
                extras = to_int(safe_get(row, 8))
                wides = to_int(safe_get(row, 9))
                noballs = to_int(safe_get(row, 10))
                byes = to_int(safe_get(row, 11))
                legbyes = to_int(safe_get(row, 12))
                penalty = to_int(safe_get(row, 13))

                wicket_type = safe_get(row, 14)
                player_dismissed = safe_get(row, 15)

                total_runs = runs_off_bat + extras
                over_number = get_over_number(ball)

                bowling_team = ""
                if len(teams) == 2:
                    bowling_team = teams[1] if batting_team == teams[0] else teams[0]

                is_wicket = 1 if wicket_type else 0
                is_bowler_wicket = 1 if wicket_type in BOWLER_WICKET_TYPES else 0

                legal_delivery = 0 if wides > 0 or noballs > 0 else 1
                batter_ball = 0 if wides > 0 else 1

                deliveries.append(
                    {
                        "match_id": str(metadata.get("match_id", file_path.stem)),
                        "source_file": file_path.name,
                        "season": metadata.get("season", ""),
                        "date": metadata.get("date", ""),
                        "competition_name": metadata.get("event", "Indian Premier League"),
                        "match_type": metadata.get("match_type", "T20"),
                        "venue": metadata.get("venue", ""),
                        "city": metadata.get("city", ""),
                        "winner": metadata.get("winner", ""),
                        "team_1": teams[0] if len(teams) > 0 else "",
                        "team_2": teams[1] if len(teams) > 1 else "",
                        "innings": innings,
                        "ball": ball,
                        "over_number": over_number,
                        "phase": get_phase(over_number),
                        "batting_team": batting_team,
                        "bowling_team": bowling_team,
                        "batter": batter,
                        "non_striker": non_striker,
                        "bowler": bowler,
                        "runs_off_bat": runs_off_bat,
                        "extras": extras,
                        "wides": wides,
                        "noballs": noballs,
                        "byes": byes,
                        "legbyes": legbyes,
                        "penalty": penalty,
                        "total_runs": total_runs,
                        "wicket_type": wicket_type,
                        "player_dismissed": player_dismissed,
                        "is_wicket": is_wicket,
                        "is_bowler_wicket": is_bowler_wicket,
                        "legal_delivery": legal_delivery,
                        "batter_ball": batter_ball,
                    }
                )

    metadata["team_1"] = teams[0] if len(teams) > 0 else ""
    metadata["team_2"] = teams[1] if len(teams) > 1 else ""

    if "venue" in metadata:
        metadata["venue"] = standardize_venue_name(metadata["venue"])

    return metadata, deliveries


def build_deliveries_and_matches() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read all match CSV files and create deliveries and matches dataframes."""
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data folder not found: {RAW_DATA_DIR}")

    csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found inside: {RAW_DATA_DIR}")

    all_matches: list[dict[str, Any]] = []
    all_deliveries: list[dict[str, Any]] = []

    logging.info("Found %s CSV files", len(csv_files))

    for index, file_path in enumerate(csv_files, start=1):
        try:
            metadata, deliveries = parse_match_file(file_path)
            all_matches.append(metadata)
            all_deliveries.extend(deliveries)

            if index % 100 == 0:
                logging.info("Processed %s/%s files", index, len(csv_files))

        except Exception as error:
            logging.warning("Failed to process %s: %s", file_path.name, error)

    matches_df = pd.DataFrame(all_matches)
    deliveries_df = pd.DataFrame(all_deliveries)

    if deliveries_df.empty:
        raise ValueError("No delivery rows were parsed. Check the CSV format.")

    deliveries_df["venue"] = deliveries_df["venue"].apply(standardize_venue_name)

    if "venue" in matches_df.columns:
        matches_df["venue"] = matches_df["venue"].apply(standardize_venue_name)

    deliveries_df["date"] = pd.to_datetime(deliveries_df["date"], errors="coerce")
    matches_df["date"] = pd.to_datetime(
        matches_df.get("date", pd.Series(dtype=str)), errors="coerce"
    )

    return deliveries_df, matches_df


def build_innings_summary(deliveries_df: pd.DataFrame) -> pd.DataFrame:
    """Create innings-level summary."""
    innings_summary = (
        deliveries_df.groupby(
            [
                "match_id",
                "season",
                "date",
                "venue",
                "innings",
                "batting_team",
                "bowling_team",
            ],
            dropna=False,
        )
        .agg(
            innings_runs=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
            legal_balls=("legal_delivery", "sum"),
            balls_recorded=("ball", "count"),
        )
        .reset_index()
    )

    innings_summary["overs_batted"] = innings_summary["legal_balls"] / 6

    return innings_summary


def build_batting_summary(deliveries_df: pd.DataFrame) -> pd.DataFrame:
    """Create player batting summary."""
    batting_summary = (
        deliveries_df.groupby("batter", dropna=False)
        .agg(
            runs=("runs_off_bat", "sum"),
            balls_faced=("batter_ball", "sum"),
            fours=("runs_off_bat", lambda x: (x == 4).sum()),
            sixes=("runs_off_bat", lambda x: (x == 6).sum()),
            innings=("match_id", "nunique"),
        )
        .reset_index()
        .rename(columns={"batter": "player"})
    )

    batting_summary["strike_rate"] = (
        batting_summary["runs"] / batting_summary["balls_faced"] * 100
    ).round(2)

    batting_summary["strike_rate"] = batting_summary["strike_rate"].fillna(0)

    return batting_summary.sort_values("runs", ascending=False)


def build_bowling_summary(deliveries_df: pd.DataFrame) -> pd.DataFrame:
    """Create player bowling summary."""
    bowling_df = deliveries_df.copy()

    bowling_df["bowler_runs_conceded"] = (
        bowling_df["total_runs"] - bowling_df["byes"] - bowling_df["legbyes"]
    )

    bowling_summary = (
        bowling_df.groupby("bowler", dropna=False)
        .agg(
            balls_bowled=("legal_delivery", "sum"),
            runs_conceded=("bowler_runs_conceded", "sum"),
            wickets=("is_bowler_wicket", "sum"),
            matches=("match_id", "nunique"),
        )
        .reset_index()
        .rename(columns={"bowler": "player"})
    )

    bowling_summary["overs_bowled"] = bowling_summary["balls_bowled"] / 6
    bowling_summary["economy_rate"] = (
        bowling_summary["runs_conceded"] / bowling_summary["overs_bowled"]
    ).round(2)

    bowling_summary["balls_per_wicket"] = (
        bowling_summary["balls_bowled"] / bowling_summary["wickets"]
    ).round(2)

    bowling_summary["economy_rate"] = bowling_summary["economy_rate"].fillna(0)
    bowling_summary["balls_per_wicket"] = bowling_summary[
        "balls_per_wicket"
    ].replace([float("inf")], 0)

    return bowling_summary.sort_values("wickets", ascending=False)


def build_venue_summary(innings_summary: pd.DataFrame) -> pd.DataFrame:
    """Create venue-level summary."""
    venue_summary = (
        innings_summary.groupby(["venue", "innings"], dropna=False)
        .agg(
            average_score=("innings_runs", "mean"),
            innings_count=("match_id", "count"),
            highest_score=("innings_runs", "max"),
            lowest_score=("innings_runs", "min"),
        )
        .reset_index()
    )

    venue_summary["average_score"] = venue_summary["average_score"].round(2)

    return venue_summary


def save_processed_files(
    deliveries_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    innings_summary: pd.DataFrame,
    batting_summary: pd.DataFrame,
    bowling_summary: pd.DataFrame,
    venue_summary: pd.DataFrame,
) -> None:
    """Save processed dataframes as CSV files."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    deliveries_df.to_csv(PROCESSED_DATA_DIR / "deliveries.csv", index=False)
    matches_df.to_csv(PROCESSED_DATA_DIR / "matches.csv", index=False)
    innings_summary.to_csv(PROCESSED_DATA_DIR / "innings_summary.csv", index=False)
    batting_summary.to_csv(PROCESSED_DATA_DIR / "player_batting_summary.csv", index=False)
    bowling_summary.to_csv(PROCESSED_DATA_DIR / "player_bowling_summary.csv", index=False)
    venue_summary.to_csv(PROCESSED_DATA_DIR / "venue_summary.csv", index=False)

    logging.info("Processed CSV files saved to: %s", PROCESSED_DATA_DIR)


def create_duckdb_database(
    deliveries_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    innings_summary: pd.DataFrame,
    batting_summary: pd.DataFrame,
    bowling_summary: pd.DataFrame,
    venue_summary: pd.DataFrame,
) -> None:
    """Create DuckDB database from processed data."""
    try:
        import duckdb
    except ImportError:
        logging.warning("DuckDB is not installed. Skipping database creation.")
        return

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DUCKDB_PATH))

    connection.register("deliveries_df", deliveries_df)
    connection.register("matches_df", matches_df)
    connection.register("innings_summary_df", innings_summary)
    connection.register("batting_summary_df", batting_summary)
    connection.register("bowling_summary_df", bowling_summary)
    connection.register("venue_summary_df", venue_summary)

    connection.execute("CREATE OR REPLACE TABLE deliveries AS SELECT * FROM deliveries_df")
    connection.execute("CREATE OR REPLACE TABLE matches AS SELECT * FROM matches_df")
    connection.execute(
        "CREATE OR REPLACE TABLE innings_summary AS SELECT * FROM innings_summary_df"
    )
    connection.execute(
        "CREATE OR REPLACE TABLE player_batting_summary AS SELECT * FROM batting_summary_df"
    )
    connection.execute(
        "CREATE OR REPLACE TABLE player_bowling_summary AS SELECT * FROM bowling_summary_df"
    )
    connection.execute(
        "CREATE OR REPLACE TABLE venue_summary AS SELECT * FROM venue_summary_df"
    )

    connection.close()

    logging.info("DuckDB database created at: %s", DUCKDB_PATH)


def main() -> None:
    """Run the full IPL data preparation pipeline."""
    logging.info("Starting Innings Insight IPL data preparation")

    deliveries_df, matches_df = build_deliveries_and_matches()

    logging.info("Deliveries shape: %s", deliveries_df.shape)
    logging.info("Matches shape: %s", matches_df.shape)

    innings_summary = build_innings_summary(deliveries_df)
    batting_summary = build_batting_summary(deliveries_df)
    bowling_summary = build_bowling_summary(deliveries_df)
    venue_summary = build_venue_summary(innings_summary)

    save_processed_files(
        deliveries_df=deliveries_df,
        matches_df=matches_df,
        innings_summary=innings_summary,
        batting_summary=batting_summary,
        bowling_summary=bowling_summary,
        venue_summary=venue_summary,
    )

    create_duckdb_database(
        deliveries_df=deliveries_df,
        matches_df=matches_df,
        innings_summary=innings_summary,
        batting_summary=batting_summary,
        bowling_summary=bowling_summary,
        venue_summary=venue_summary,
    )

    logging.info("Data preparation completed successfully")


if __name__ == "__main__":
    main()