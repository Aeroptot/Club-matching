#!/usr/bin/env python3
"""Parse club-data.md, assign tags from a shared vocabulary, export ML-ready CSV."""

import csv
import json
import re
from pathlib import Path

from config import EXCLUDED_CLUB_NOS

BASE = Path(__file__).parent

TAG_VOCABULARY = [
    "academic", "STEM", "humanities", "social_sciences", "business", "technology",
    "health", "creative_arts", "performing_arts", "media", "sports", "fitness",
    "volunteer", "culture", "gaming", "hobbies",
    "math", "computer_science", "programming", "AI", "data_science", "algorithms",
    "web_development", "game_development", "cybersecurity", "robotics", "engineering",
    "biology", "chemistry", "physics", "medicine", "environment", "astronomy", "research",
    "economics", "finance", "psychology", "philosophy", "history", "politics",
    "linguistics", "literature", "anthropology", "debate", "law",
    "mental_health", "wellness", "nutrition",
    "music", "dance", "theater", "film", "photography", "visual_arts", "fashion",
    "design", "writing", "journalism",
    "team_sports", "racquet_sports", "martial_arts", "outdoor_sports", "winter_sports",
    "water_sports",
    "teaching", "charity", "community_service", "animal_welfare",
    "chinese_culture", "language_learning", "anime",
    "experiments", "hands_on", "competition", "strategy", "board_games",
    "craftsmanship", "food", "peer_support", "academic_support",
    "entrepreneurship", "investment", "aerospace", "drones",
]

CLUB_TAGS: dict[str, list[str]] = {
    "1": ["music", "performing_arts", "creative_arts"],
    "2": ["AI", "technology", "social_sciences", "STEM"],
    "3": ["AI", "programming", "game_development", "computer_science", "competition"],
    "4": ["social_sciences", "media", "research", "culture"],
    "5": ["math", "strategy", "competition", "STEM"],
    "6": ["sports", "hobbies", "craftsmanship"],
    "7": ["medicine", "health", "chinese_culture", "community_service"],
    "8": ["economics", "math", "academic", "STEM"],
    "9": ["engineering", "robotics", "aerospace", "programming", "hands_on"],
    "10": ["physics", "engineering", "aerospace", "STEM", "hands_on"],
    "11": ["chinese_culture", "history", "creative_arts", "media"],
    "12": ["volunteer", "animal_welfare", "charity", "community_service"],
    "13": ["music", "anime", "performing_arts"],
    "14": ["anthropology", "social_sciences", "culture", "academic"],
    "15": ["culture", "food", "hobbies"],
    "16": ["programming", "web_development", "AI", "computer_science", "hands_on"],
    "17": ["team_sports", "sports", "competition"],
    "18": ["team_sports", "sports", "competition"],
    "19": ["film", "creative_arts", "media"],
    "20": ["film", "creative_arts", "media"],
    "21": ["racquet_sports", "sports", "fitness"],
    "22": ["food", "culture", "hobbies"],
    "23": ["team_sports", "sports", "competition"],
    "24": ["volunteer", "charity", "community_service", "fitness"],
    "25": ["volunteer", "teaching", "charity", "culture"],
    "26": ["biology", "chemistry", "experiments", "STEM"],
    "27": ["biology", "chemistry", "experiments", "STEM", "research"],
    "28": ["biology", "data_science", "computer_science", "research"],
    "29": ["biology", "competition", "academic", "STEM"],
    "30": ["STEM", "programming", "research", "hands_on"],
    "31": ["film", "hobbies"],
    "32": ["board_games", "strategy", "hobbies", "social_sciences"],
    "33": ["mental_health", "wellness", "community_service", "peer_support"],
    "34": ["business", "economics", "finance", "competition", "entrepreneurship"],
    "35": ["finance", "investment", "economics", "business"],
    "36": ["programming", "algorithms", "competition", "computer_science"],
    "37": ["martial_arts", "sports", "fitness"],
    "38": ["chinese_culture", "visual_arts", "craftsmanship", "hobbies"],
    "39": ["media", "journalism", "volunteer"],
    "40": ["dance", "performing_arts", "sports", "fitness"],
    "41": ["chemistry", "experiments", "STEM", "academic"],
    "42": ["chemistry", "experiments", "engineering", "hands_on"],
    "43": ["chemistry", "experiments", "engineering", "hands_on"],
    "44": ["dance", "chinese_culture", "performing_arts"],
    "45": ["martial_arts", "chinese_culture", "wellness", "fitness"],
    "46": ["history", "technology", "research", "STEM"],
    "47": ["gaming", "strategy", "competition", "hobbies"],
    "48": ["linguistics", "computer_science", "AI", "STEM"],
    "49": ["business", "finance", "economics", "hands_on"],
    "50": ["astronomy", "physics", "STEM", "research"],
    "51": ["anime", "craftsmanship", "performing_arts", "photography"],
    "52": ["food", "nutrition", "chemistry", "health"],
    "53": ["medicine", "volunteer", "health", "community_service"],
    "54": ["cybersecurity", "computer_science", "technology"],
    "56": ["gaming", "economics", "strategy", "hobbies"],
    "57": ["psychology", "strategy", "hobbies", "social_sciences"],
    "58": ["team_sports", "sports", "fitness"],
    "59": ["gaming", "writing", "creative_arts", "hobbies"],
    "60": ["volunteer", "teaching", "community_service"],
    "72": ["psychology", "literature", "writing", "mental_health"],
    "73": ["dance", "performing_arts", "culture", "music"],
    "77": ["writing", "physics", "biology", "STEM", "creative_arts"],
    "78": ["literature", "astronomy", "culture", "humanities"],
    "79": ["biology", "environment", "STEM"],
    "80": ["economics", "social_sciences", "academic"],
    "81": ["environment", "biology", "STEM"],
    "82": ["music", "creative_arts", "media"],
    "83": ["engineering", "programming", "technology", "hands_on"],
    "84": ["engineering", "technology", "STEM"],
    "85": ["volunteer", "teaching", "language_learning", "community_service"],
    "86": ["entrepreneurship", "business", "finance"],
    "87": ["drones", "engineering", "programming", "aerospace", "hands_on"],
    "88": ["fashion", "performing_arts", "design", "creative_arts"],
    "89": ["culture", "social_sciences", "volunteer"],
    "90": ["engineering", "technology", "STEM", "hands_on"],
    "91": ["finance", "investment", "economics"],
    "92": ["outdoor_sports", "team_sports", "sports", "fitness"],
    "94": ["biology", "medicine", "STEM", "research"],
    "95": ["sports", "hobbies", "strategy"],
    "96": ["sports", "hobbies"],
    "97": ["film", "language_learning", "culture"],
    "98": ["wellness", "peer_support", "hobbies"],
    "99": ["experiments", "STEM", "hands_on"],
    "102": ["visual_arts", "creative_arts", "volunteer", "environment"],
    "105": ["environment", "hobbies", "craftsmanship"],
    "106": ["academic_support", "STEM"],
    "107": ["social_sciences", "STEM", "academic"],
    "108": ["volunteer", "charity", "community_service"],
    "110": ["wellness", "creative_arts", "media"],
    "111": ["volunteer", "animal_welfare", "charity"],
    "112": ["environment", "research", "biology"],
    "113": ["environment", "health", "research"],
    "114": ["psychology", "humanities", "academic"],
    "115": ["craftsmanship", "mental_health", "charity"],
    "116": ["music", "performing_arts"],
    "117": ["fitness", "wellness", "sports"],
    "118": ["mental_health", "peer_support", "wellness", "community_service"],
    "119": ["humanities", "literature", "philosophy"],
    "120": ["language_learning", "culture"],
    "121": ["history", "music", "humanities"],
    "122": ["animal_welfare", "wellness", "hobbies"],
    "123": ["volunteer", "community_service", "teaching"],
    "125": ["astronomy", "physics", "STEM"],
    "126": ["academic_support", "language_learning", "teaching"],
    "127": ["academic_support", "competition"],
    "128": ["history", "academic_support"],
    "130": ["writing", "game_development", "creative_arts"],
    "132": ["finance", "business", "competition"],
    "133": ["design", "visual_arts", "history", "creative_arts"],
    "134": ["finance", "investment", "economics", "business"],
    "135": ["culture", "social_sciences", "anime"],
    "136": ["anime", "film", "language_learning", "culture"],
    "137": ["anime", "culture", "social_sciences"],
    "138": ["medicine", "fitness", "sports", "health"],
    "139": ["game_development", "programming", "creative_arts"],
    "140": ["psychology", "gaming", "social_sciences"],
    "141": ["language_learning", "history", "humanities"],
    "142": ["programming", "competition", "computer_science", "algorithms"],
    "143": ["craftsmanship", "design", "hobbies"],
    "144": ["biology", "chemistry", "health", "STEM"],
    "145": ["literature", "writing", "creative_arts"],
    "146": ["literature", "humanities", "culture"],
    "147": ["game_development", "visual_arts", "creative_arts"],
    "148": ["math", "academic_support", "competition"],
    "149": ["AI", "computer_science", "programming", "STEM"],
    "150": ["music", "hobbies"],
    "151": ["performing_arts", "hobbies", "creative_arts"],
    "152": ["math", "computer_science", "algorithms"],
    "153": ["math", "academic_support", "teaching"],
    "154": ["math", "competition", "academic"],
    "155": ["math", "competition", "academic", "teaching"],
    "156": ["math", "competition", "research", "STEM"],
    "157": ["math", "computer_science", "academic"],
    "158": ["math", "strategy", "board_games", "algorithms"],
    "159": ["volunteer", "teaching", "STEM", "community_service"],
    "160": ["medicine", "health", "biology", "humanities"],
    "161": ["media", "technology", "creative_arts"],
    "162": ["psychology", "mental_health", "health", "academic"],
    "163": ["gaming", "programming", "technology"],
    "164": ["debate", "politics", "competition", "social_sciences"],
    "165": ["debate", "politics", "competition", "social_sciences"],
    "166": ["music", "mental_health", "health", "research"],
    "167": ["theater", "performing_arts", "music"],
    "168": ["history", "research", "competition", "academic"],
    "169": ["biology", "history", "STEM"],
    "170": ["psychology", "social_sciences", "volunteer"],
    "171": ["psychology", "biology", "STEM", "research"],
    "172": ["team_sports", "sports", "competition", "fitness"],
    "173": ["social_sciences", "research", "politics"],
    "174": ["debate", "competition", "social_sciences"],
    "175": ["politics", "economics", "photography", "film"],
    "176": ["academic_support", "competition"],
    "177": ["aerospace", "physics", "craftsmanship", "hobbies"],
    "178": ["craftsmanship", "visual_arts", "hobbies"],
    "179": ["literature", "writing", "humanities"],
    "180": ["math", "academic", "STEM"],
    "181": ["philosophy", "research", "humanities"],
    "182": ["philosophy", "culture", "humanities"],
    "183": ["physics", "academic_support", "STEM"],
    "184": ["music", "creative_arts"],
    "185": ["math", "STEM", "research"],
    "186": ["psychology", "mental_health", "social_sciences"],
    "187": ["music", "performing_arts"],
    "188": ["engineering", "hands_on", "technology", "STEM"],
    "191": ["music", "creative_arts", "hobbies"],
    "192": ["volunteer", "craftsmanship", "charity", "environment"],
    "193": ["volunteer", "charity", "mental_health", "community_service"],
    "194": ["research", "social_sciences", "academic"],
    "195": ["outdoor_sports", "fitness", "sports"],
    "197": ["volunteer", "teaching", "community_service"],
    "198": ["language_learning", "linguistics", "academic"],
    "199": ["volunteer", "peer_support", "community_service"],
    "200": ["medicine", "biology", "STEM", "academic"],
    "201": ["aerospace", "photography", "hobbies"],
    "202": ["music", "performing_arts", "hobbies"],
    "203": ["debate", "competition", "social_sciences"],
    "204": ["racquet_sports", "sports", "competition"],
    "205": ["team_sports", "sports", "fitness"],
    "206": ["music", "performing_arts", "creative_arts"],
    "207": ["team_sports", "sports", "fitness"],
    "208": ["debate", "competition", "language_learning"],
    "210": ["outdoor_sports", "fitness", "sports"],
    "211": ["programming", "web_development", "game_development", "computer_science", "cybersecurity"],
    "212": ["debate", "competition", "social_sciences"],
    "213": ["performing_arts", "media", "creative_arts"],
    "214": ["economics", "finance", "business", "academic"],
    "215": ["visual_arts", "creative_arts", "anime"],
    "216": ["martial_arts", "sports", "competition"],
    "217": ["dance", "sports", "performing_arts", "fitness"],
    "218": ["fitness", "wellness", "sports"],
    "219": ["gaming", "STEM"],
    "220": ["outdoor_sports", "sports", "fitness"],
    "221": ["music", "performing_arts", "hobbies"],
    "222": ["martial_arts", "culture", "fitness", "sports"],
    "223": ["engineering", "technology", "hands_on"],
    "224": ["journalism", "writing", "media", "creative_arts"],
    "225": ["strategy", "competition", "hobbies"],
    "226": ["martial_arts", "culture", "sports", "fitness"],
    "227": ["linguistics", "language_learning", "academic"],
    "228": ["music", "performing_arts", "creative_arts"],
    "229": ["strategy", "competition", "hobbies"],
    "230": ["law", "debate", "competition", "social_sciences"],
    "232": ["music", "performing_arts", "creative_arts"],
    "233": ["philosophy", "humanities", "academic"],
    "234": ["philosophy", "debate", "humanities"],
    "235": ["photography", "visual_arts", "creative_arts"],
    "236": ["racquet_sports", "sports", "fitness"],
    "237": ["craftsmanship", "visual_arts", "hands_on"],
    "238": ["strategy", "competition", "hobbies"],
    "239": ["gaming", "music", "hobbies"],
    "240": ["water_sports", "team_sports", "fitness", "sports"],
    "241": ["research", "engineering", "competition", "STEM"],
    "244": ["music", "performing_arts"],
    "245": ["water_sports", "sports", "fitness", "competition"],
    "246": ["racquet_sports", "sports"],
    "247": ["martial_arts", "chinese_culture", "wellness", "fitness"],
    "248": ["racquet_sports", "sports", "fitness"],
    "250": ["programming", "computer_science", "technology"],
    "251": ["music", "anime", "culture"],
    "253": ["finance", "business", "economics", "investment"],
    "254": ["robotics", "engineering", "competition", "programming", "STEM"],
    "255": ["gaming", "craftsmanship", "board_games", "hobbies"],
    "256": ["mental_health", "health", "volunteer", "community_service"],
    "260": ["STEM", "volunteer", "academic"],
    "261": ["technology", "social_sciences", "STEM"],
    "262": ["film", "creative_arts", "humanities"],
    "263": ["math", "computer_science", "academic", "STEM"],
    "264": ["STEM", "writing", "volunteer"],
    "265": ["STEM", "writing", "journalism"],
    "266": ["water_sports", "environment", "fitness", "outdoor_sports"],
    "267": ["animal_welfare", "volunteer", "biology"],
    "268": ["team_sports", "sports", "hobbies"],
    "269": ["winter_sports", "sports", "fitness", "competition"],
    "271": ["drones", "photography", "engineering", "media"],
    "272": ["history", "social_sciences", "research"],
    "273": ["board_games", "strategy", "hobbies"],
    "274": ["chinese_culture", "philosophy", "humanities"],
    "275": ["language_learning", "culture"],
    "276": ["dance", "performing_arts", "sports", "competition"],
    "277": ["strategy", "competition", "hobbies"],
    "278": ["theater", "music", "creative_arts"],
    "281": ["business", "entrepreneurship", "economics"],
    "284": ["environment", "hands_on", "biology"],
    "288": ["gaming", "strategy", "board_games", "hobbies"],
    "289": ["media", "debate", "performing_arts"],
    "290": ["dance", "performing_arts", "culture", "anime"],
    "291": ["volunteer", "teaching", "community_service"],
    "294": ["team_sports", "sports", "fitness"],
    "298": ["physics", "STEM", "research"],
    "299": ["performing_arts", "creative_arts", "media"],
    "303": ["politics", "social_sciences", "research"],
    "304": ["dance", "performing_arts", "fitness", "culture"],
    "305": ["mental_health", "wellness", "peer_support", "community_service"],
    "307": ["sports", "hobbies", "strategy"],
    "308": ["music", "performing_arts", "creative_arts"],
    "310": ["politics", "humanities", "social_sciences", "debate"],
    "311": ["mental_health", "peer_support", "health", "wellness"],
    "312": ["volunteer", "charity", "community_service", "environment"],
    "314": ["math", "research", "academic", "STEM"],
    "315": ["volunteer", "health", "charity", "community_service"],
    "316": ["physics", "math", "academic", "STEM"],
    "317": ["social_sciences", "research", "hands_on"],
    "318": ["gaming", "literature", "creative_arts"],
    "319": ["team_sports", "sports", "fitness"],
    "322": ["music", "performing_arts", "creative_arts"],
    "323": ["culture", "anthropology", "social_sciences"],
    "324": ["craftsmanship", "visual_arts", "hobbies"],
    "325": ["wellness", "fitness", "martial_arts"],
    "326": ["biology", "environment", "hobbies"],
    "327": ["gaming", "economics", "strategy", "social_sciences"],
    "328": ["game_development", "programming", "creative_arts"],
    "329": ["music", "performing_arts", "chinese_culture"],
    "331": ["health", "volunteer", "community_service", "humanities"],
    "332": ["biology", "research", "competition", "STEM", "engineering"],
    "333": ["medicine", "biology", "psychology", "health", "competition"],
    "336": ["math", "academic_support", "teaching", "academic"],
}


def parse_clubs(md_path: Path) -> list[dict]:
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    clubs = []
    i = 2
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and re.match(r"\|\d+\|", line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:
                desc_lines = []
                i += 1
                while i < len(lines) and not (
                    lines[i].strip().startswith("|")
                    and re.match(r"\|\d+\|", lines[i].strip())
                ):
                    if lines[i].strip():
                        desc_lines.append(lines[i].strip())
                    i += 1
                clubs.append(
                    {
                        "no": parts[1],
                        "name": parts[2],
                        "leader": parts[3],
                        "category": parts[5]
                        .replace("<br>", " ")
                        .replace("  ", " ")
                        .strip(),
                        "description": " ".join(desc_lines),
                    }
                )
                continue
        i += 1
    return clubs


def validate_tags() -> None:
    vocab = set(TAG_VOCABULARY)
    for no, tags in CLUB_TAGS.items():
        if len(tags) > 5:
            raise ValueError(f"Club {no} has {len(tags)} tags (max 5)")
        unknown = set(tags) - vocab
        if unknown:
            raise ValueError(f"Club {no} uses unknown tags: {unknown}")


def main() -> None:
    validate_tags()
    clubs = parse_clubs(BASE / "club-data.md")

    missing = [
        c["no"]
        for c in clubs
        if c["no"] not in CLUB_TAGS and c["no"] not in EXCLUDED_CLUB_NOS
    ]
    if missing:
        raise SystemExit(f"Missing tag assignments for club numbers: {missing}")

    csv_path = BASE / "clubs_tagged.csv"
    fieldnames = ["no", "name", "category", "description"] + TAG_VOCABULARY

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for club in clubs:
            if club["no"] in EXCLUDED_CLUB_NOS:
                continue
            row = {
                "no": club["no"],
                "name": club["name"],
                "category": club["category"],
                "description": club["description"],
            }
            tags = set(CLUB_TAGS[club["no"]])
            for tag in TAG_VOCABULARY:
                row[tag] = 1 if tag in tags else 0
            writer.writerow(row)

    summary = {
        "total_clubs": len(clubs),
        "total_tag_columns": len(TAG_VOCABULARY),
        "tags": TAG_VOCABULARY,
        "clubs_per_tag": {
            tag: sum(1 for c in clubs if tag in CLUB_TAGS[c["no"]])
            for tag in TAG_VOCABULARY
        },
    }
    with open(BASE / "clubs_tag_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Wrote {csv_path}")
    print(f"  {len(clubs)} clubs x {len(TAG_VOCABULARY)} tag columns")
    top_tags = sorted(
        summary["clubs_per_tag"].items(), key=lambda x: -x[1]
    )[:10]
    print("  Most common tags:", ", ".join(f"{t}({n})" for t, n in top_tags))


if __name__ == "__main__":
    main()
