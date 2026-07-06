#!/usr/bin/env python3
"""CLI for the club recommendation engine."""

from __future__ import annotations

import argparse
import sys

from build_clubs_data import build_weighted_csv
from config import MEETING_PERIODS, WEEKDAYS
from recommender import format_results, load_clubs, recommend
from tag_hierarchy import all_known_tags, display_name


def list_tags() -> None:
    tags = sorted(all_known_tags())
    print("Available tags (select up to 10):\n")
    for i, tag in enumerate(tags, 1):
        print(f"  {display_name(tag):<30} ({tag})")
    print(f"\nTotal: {len(tags)} tags")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Club recommendation engine with hierarchical tag matching."
    )
    parser.add_argument(
        "--tags",
        "-t",
        nargs="+",
        help="User interest tags (e.g. AI programming machine_learning)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild clubs_weighted.csv before recommending",
    )
    parser.add_argument(
        "--list-tags",
        action="store_true",
        help="List all available tags and exit",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of recommendations to show (default: 10)",
    )
    parser.add_argument(
        "--blocked-slots",
        "-b",
        nargs="+",
        help="Busy day:period slots, e.g. monday:period11 tuesday:lunchtime",
    )
    parser.add_argument(
        "--blocked-periods",
        nargs="+",
        choices=list(MEETING_PERIODS),
        help="Block all weekdays for given periods (legacy shorthand)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo with AI / programming / machine_learning interests",
    )

    args = parser.parse_args()

    if args.list_tags:
        list_tags()
        return

    if args.rebuild:
        path = build_weighted_csv()
        print(f"Rebuilt {path}\n", file=sys.stderr)

    if args.demo:
        user_tags = ["AI", "programming", "machine_learning", "game_development"]
        print("Demo user interests:", ", ".join(user_tags), "\n")
        results = recommend(
            user_tags,
            top_n=args.top,
            blocked_slots=args.blocked_slots,
            blocked_periods=args.blocked_periods,
        )
        print(format_results(results))
        return

    if args.tags:
        results = recommend(
            args.tags,
            top_n=args.top,
            blocked_slots=args.blocked_slots,
            blocked_periods=args.blocked_periods,
        )
        print(format_results(results))
        return

    # Interactive mode
    print("Club Recommendation Engine")
    print("Enter up to 10 tags separated by commas (or 'list' to see tags, 'quit' to exit).\n")

    while True:
        try:
            raw = input("Your interests> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue
        if raw.lower() in {"quit", "exit", "q"}:
            break
        if raw.lower() == "list":
            list_tags()
            print()
            continue

        tags = [t.strip() for t in raw.replace(",", " ").split() if t.strip()]
        if not tags:
            continue
        if len(tags) > 10:
            print("Please select at most 10 tags.\n")
            continue

        try:
            results = recommend(
                tags,
                top_n=args.top,
                blocked_slots=args.blocked_slots,
                blocked_periods=args.blocked_periods,
            )
            print(format_results(results))
        except ValueError as exc:
            print(f"Error: {exc}\n")


if __name__ == "__main__":
    main()
