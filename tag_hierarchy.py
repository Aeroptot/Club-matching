"""Tag hierarchy tree and relationship matching."""

from __future__ import annotations

from config import (
    HIERARCHY_EXACT,
    HIERARCHY_GRANDRELATED,
    HIERARCHY_PARENT_CHILD,
    HIERARCHY_UNRELATED,
)

# Nested hierarchy: parent -> {child: subtree, ...}
# Tags not listed here are standalone roots (match only themselves).
TAG_TREE: dict[str, dict] = {
    "STEM": {
        "math": {},
        "biology": {},
        "chemistry": {},
        "physics": {},
        "astronomy": {},
        "medicine": {},
        "environment": {},
        "experiments": {},
        "research": {},
        "engineering": {
            "robotics": {},
            "aerospace": {},
            "drones": {},
            "hands_on": {},
        },
        "computer_science": {
            "programming": {},
            "algorithms": {},
            "web_development": {},
            "game_development": {},
            "cybersecurity": {},
            "data_science": {},
            "AI": {
                "machine_learning": {},
            },
        },
        "technology": {},
    },
    "social_sciences": {
        "economics": {},
        "psychology": {},
        "anthropology": {},
        "politics": {},
        "linguistics": {},
        "debate": {},
        "law": {},
    },
    "humanities": {
        "philosophy": {},
        "history": {},
        "literature": {},
        "writing": {},
        "academic": {},
    },
    "business": {
        "finance": {},
        "investment": {},
        "entrepreneurship": {},
    },
    "creative_arts": {
        "visual_arts": {},
        "photography": {},
        "design": {},
        "fashion": {},
        "craftsmanship": {},
    },
    "performing_arts": {
        "music": {},
        "dance": {},
        "theater": {},
    },
    "media": {
        "film": {},
        "journalism": {},
        "anime": {},
    },
    "sports": {
        "fitness": {},
        "team_sports": {},
        "racquet_sports": {},
        "martial_arts": {},
        "outdoor_sports": {},
        "winter_sports": {},
        "water_sports": {},
    },
    "volunteer": {
        "teaching": {},
        "charity": {},
        "community_service": {},
        "animal_welfare": {},
        "peer_support": {},
    },
    "health": {
        "mental_health": {},
        "wellness": {},
        "nutrition": {},
    },
    "gaming": {
        "board_games": {},
        "strategy": {},
    },
    "culture": {
        "chinese_culture": {},
        "language_learning": {},
    },
    "hobbies": {},
    "competition": {},
    "academic_support": {},
}


def _build_parent_map(
    tree: dict[str, dict], parent: str | None = None, out: dict[str, str | None] | None = None
) -> dict[str, str | None]:
    if out is None:
        out = {}
    for node, children in tree.items():
        out[node] = parent
        if children:
            _build_parent_map(children, node, out)
    return out


PARENT_MAP: dict[str, str | None] = _build_parent_map(TAG_TREE)


def ancestor_chain(tag: str) -> list[str]:
    """Return [tag, parent, grandparent, ...]."""
    chain = [tag]
    current = tag
    while PARENT_MAP.get(current) is not None:
        current = PARENT_MAP[current]  # type: ignore[assignment]
        chain.append(current)
    return chain


def hierarchy_distance(tag_a: str, tag_b: str) -> int | None:
    """Shortest path distance in the hierarchy tree, or None if unrelated."""
    if tag_a == tag_b:
        return 0
    chain_a = ancestor_chain(tag_a)
    chain_b = ancestor_chain(tag_b)
    best: int | None = None
    for i, ancestor in enumerate(chain_a):
        if ancestor in chain_b:
            j = chain_b.index(ancestor)
            distance = i + j
            if distance <= 2 and (best is None or distance < best):
                best = distance
    return best


def hierarchy_coefficient(tag_a: str, tag_b: str) -> float:
    distance = hierarchy_distance(tag_a, tag_b)
    if distance is None:
        return HIERARCHY_UNRELATED
    if distance == 0:
        return HIERARCHY_EXACT
    if distance == 1:
        return HIERARCHY_PARENT_CHILD
    if distance == 2:
        return HIERARCHY_GRANDRELATED
    return HIERARCHY_UNRELATED


def display_name(tag: str) -> str:
    """Human-readable tag label."""
    special = {
        "AI": "AI",
        "STEM": "STEM",
        "anime": "Anime",
    }
    if tag in special:
        return special[tag]
    return tag.replace("_", " ").title()


def all_known_tags() -> set[str]:
    return set(PARENT_MAP.keys())
