"""Build clubs_weighted.csv from club-data.md and tag assignments."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from config import CLUB_TAG_POINTS, METADATA_COLUMNS, WEEKDAYS
from generate_club_tags import CLUB_TAGS, TAG_VOCABULARY, parse_clubs

BASE = Path(__file__).parent

# Optional per-club weight overrides (must sum to CLUB_TAG_POINTS).
CLUB_WEIGHT_OVERRIDES: dict[str, dict[str, int]] = {
    "3": {  # AI Game Bot
        "AI": 6,
        "programming": 5,
        "machine_learning": 4,
        "algorithms": 3,
        "game_development": 2,
    },
}


def distribute_weights(tag_count: int, total: int = CLUB_TAG_POINTS) -> list[int]:
    """Distribute points unevenly by importance (first tag = highest weight)."""
    if tag_count == 0:
        return []
    raw = list(range(tag_count, 0, -1))
    raw_sum = sum(raw)
    weights = [round(total * w / raw_sum) for w in raw]
    diff = total - sum(weights)
    weights[0] += diff
    return weights


def parse_member_counts(md_path: Path) -> dict[str, int]:
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    counts: dict[str, int] = {}
    i = 2
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and re.match(r"\|\d+\|", line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 8:
                no = parts[1]
                try:
                    counts[no] = int(parts[7])
                except ValueError:
                    counts[no] = 0
            i += 1
            while i < len(lines) and not (
                lines[i].strip().startswith("|") and re.match(r"\|\d+\|", lines[i].strip())
            ):
                i += 1
            continue
        i += 1
    return counts


def parse_meeting_time(raw: str) -> tuple[str, str]:
    """Return (weekday, period) parsed from the Period column."""
    cleaned = raw.replace("<br>", " ").lower()
    compact = re.sub(r"\s+", "", cleaned)

    day = "unknown"
    for weekday in WEEKDAYS:
        if weekday in cleaned:
            day = weekday
            break

    if "period11" in compact:
        period = "period11"
    elif "period12" in compact:
        period = "period12"
    elif "lunchtime" in compact or compact.endswith("lunch"):
        period = "lunchtime"
    elif "period13" in compact:
        period = "period13"
    else:
        period = "unknown"

    return day, period


def parse_periods(md_path: Path) -> dict[str, str]:
    """Legacy helper: period only."""
    return {no: meeting[1] for no, meeting in parse_meeting_times(md_path).items()}


def parse_meeting_times(md_path: Path) -> dict[str, tuple[str, str]]:
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    meeting_times: dict[str, tuple[str, str]] = {}
    i = 2
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and re.match(r"\|\d+\|", line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 9:
                no = parts[1]
                meeting_times[no] = parse_meeting_time(parts[8])
            i += 1
            while i < len(lines) and not (
                lines[i].strip().startswith("|") and re.match(r"\|\d+\|", lines[i].strip())
            ):
                i += 1
            continue
        i += 1
    return meeting_times


def club_weighted_tags(club_no: str) -> dict[str, int]:
    if club_no in CLUB_WEIGHT_OVERRIDES:
        weights = CLUB_WEIGHT_OVERRIDES[club_no]
        if sum(weights.values()) != CLUB_TAG_POINTS:
            raise ValueError(
                f"Club {club_no} override weights must sum to {CLUB_TAG_POINTS}"
            )
        return weights
    tags = CLUB_TAGS[club_no]
    weights = distribute_weights(len(tags))
    return dict(zip(tags, weights))


def build_weighted_csv(
    output_path: Path | None = None,
    md_path: Path | None = None,
) -> Path:
    output_path = output_path or BASE / "clubs_weighted.csv"
    md_path = md_path or BASE / "club-data.md"

    clubs = parse_clubs(md_path)
    member_counts = parse_member_counts(md_path)
    meeting_times = parse_meeting_times(md_path)

    # Include machine_learning in export columns (used in hierarchy / user selection).
    export_tags = sorted(set(TAG_VOCABULARY) | {"machine_learning"})

    fieldnames = ["no", "name", "category", "description", "member_count", "day", "period"] + export_tags

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for club in clubs:
            no = club["no"]
            weighted = club_weighted_tags(no)
            day, period = meeting_times.get(no, ("unknown", "unknown"))
            row = {
                "no": no,
                "name": club["name"],
                "category": club["category"],
                "description": club["description"],
                "member_count": member_counts.get(no, 0),
                "day": day,
                "period": period,
            }
            for tag in export_tags:
                row[tag] = weighted.get(tag, 0)
            writer.writerow(row)

    return output_path


if __name__ == "__main__":
    path = build_weighted_csv()
    print(f"Wrote {path}")
