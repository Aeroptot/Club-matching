"""Configurable constants for the club recommendation engine."""

# Total tag points assigned to each club and user profile.
CLUB_TAG_POINTS = 20
USER_TAG_POINTS = 20
MAX_USER_TAGS = 10

# Hierarchy match coefficients (relationship strength).
HIERARCHY_EXACT = 1.0
HIERARCHY_PARENT_CHILD = 0.6
HIERARCHY_GRANDRELATED = 0.3
HIERARCHY_UNRELATED = 0.0

# Similarity blend: Precision vs Recall.
SIMILARITY_PRECISION_WEIGHT = 0.7
SIMILARITY_RECALL_WEIGHT = 0.3

# Popularity multipliers by member count (inclusive lower bound -> multiplier).
# Top tier capped at 30% bonus (was 50%); lower tiers scaled proportionally.
POPULARITY_TIERS: list[tuple[int, float]] = [
    (51, 1.30),
    (31, 1.21),
    (21, 1.12),
    (11, 1.06),
    (0, 1.00),
]

TOP_N_RESULTS = 10

# Return at least this many clubs when possible (may include scores <= MIN_FINAL_SCORE).
MIN_RESULTS = 5

# Clubs with this many members or fewer are treated as inactive and excluded.
MIN_ACTIVE_MEMBER_COUNT = 3

# Prefer clubs whose final score exceeds this threshold (0–1 scale).
MIN_FINAL_SCORE = 0.50

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday")
MEETING_PERIODS = ("period11", "period12", "lunchtime")

# Column names in the weighted CSV that are not tags.
METADATA_COLUMNS = {"no", "name", "category", "description", "member_count", "day", "period"}
