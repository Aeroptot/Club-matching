#!/usr/bin/env python3
"""Build static site in docs/ for GitHub Pages."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from config import (
    CLUB_TAG_POINTS,
    HIERARCHY_EXACT,
    HIERARCHY_GRANDRELATED,
    HIERARCHY_PARENT_CHILD,
    MAX_USER_TAGS,
    MIN_ACTIVE_MEMBER_COUNT,
    MIN_FINAL_SCORE,
    MIN_RESULTS,
    POPULARITY_TIERS,
    SIMILARITY_PRECISION_WEIGHT,
    SIMILARITY_RECALL_WEIGHT,
    TOP_N_RESULTS,
    USER_TAG_POINTS,
)
from recommender import load_clubs
from tag_hierarchy import PARENT_MAP, TAG_TREE, all_known_tags, display_name
from tag_quiz import TOP_LEVEL

BASE = Path(__file__).parent
DOCS = BASE / "docs"
STATIC = BASE / "static"


def build_pages() -> Path:
    data_dir = DOCS / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    clubs = load_clubs()
    clubs_payload = [
        {
            "no": c.no,
            "name": c.name,
            "category": c.category,
            "description": c.description,
            "member_count": c.member_count,
            "day": c.day,
            "period": c.period,
            "tags": c.tags,
        }
        for c in clubs
    ]

    site_payload = {
        "config": {
            "CLUB_TAG_POINTS": CLUB_TAG_POINTS,
            "USER_TAG_POINTS": USER_TAG_POINTS,
            "MAX_USER_TAGS": MAX_USER_TAGS,
            "HIERARCHY_EXACT": HIERARCHY_EXACT,
            "HIERARCHY_PARENT_CHILD": HIERARCHY_PARENT_CHILD,
            "HIERARCHY_GRANDRELATED": HIERARCHY_GRANDRELATED,
            "MIN_ACTIVE_MEMBER_COUNT": MIN_ACTIVE_MEMBER_COUNT,
            "MIN_FINAL_SCORE": MIN_FINAL_SCORE,
            "MIN_RESULTS": MIN_RESULTS,
            "TOP_N_RESULTS": TOP_N_RESULTS,
            "SIMILARITY_PRECISION_WEIGHT": SIMILARITY_PRECISION_WEIGHT,
            "SIMILARITY_RECALL_WEIGHT": SIMILARITY_RECALL_WEIGHT,
            "POPULARITY_TIERS": POPULARITY_TIERS,
        },
        "parentMap": PARENT_MAP,
        "tagTree": TAG_TREE,
        "topLevel": TOP_LEVEL,
        "tags": [
            {"id": tag, "label": display_name(tag)}
            for tag in sorted(all_known_tags(), key=lambda t: display_name(t).lower())
        ],
    }

    (data_dir / "clubs.json").write_text(
        json.dumps(clubs_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "site.json").write_text(
        json.dumps(site_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if DOCS.exists():
        for item in DOCS.iterdir():
            if item.name == "data":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    else:
        DOCS.mkdir()

    for name in ("index.html", "styles.css", "app.js", "engine.js"):
        shutil.copy2(STATIC / name, DOCS / name)

    (DOCS / ".nojekyll").touch()

    index = (DOCS / "index.html").read_text(encoding="utf-8")
    if "engine.js" not in index:
        index = index.replace(
            '<script src="app.js"></script>',
            '<script src="engine.js"></script>\n  <script src="app.js"></script>',
        )
        (DOCS / "index.html").write_text(index, encoding="utf-8")

    return DOCS


if __name__ == "__main__":
    path = build_pages()
    print(f"Built GitHub Pages site at {path}")
