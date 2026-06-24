"""
Content Type Classification (V2 enhancement)

Classifies each video into one of:
  - Short
  - Live
  - Music Video
  - Behind-the-scenes
  - Interview / Promotion
  - Other  (fallback when nothing matches confidently)

Detection strategy, cheapest/most reliable first:
  1. Duration & live-status come straight from the YouTube API (no guessing).
  2. Everything else is detected with keyword rules on the video title.
     This is "rule-based NLP" -- simple, explainable, and surprisingly
     accurate for music-industry titles, which follow predictable patterns.
"""

import re
import sqlite3
import pandas as pd

DB_NAME = "music_analytics.db"


def parse_duration_to_seconds(duration_str):
    """Convert YouTube's ISO 8601 duration format (e.g. 'PT3M45S') into seconds.
    Returns None if the duration is missing or unparseable."""
    if not isinstance(duration_str, str) or not duration_str.startswith("PT"):
        return None

    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
    if not match:
        return None

    hours, minutes, seconds = (int(x) if x else 0 for x in match.groups())
    return hours * 3600 + minutes * 60 + seconds


# ---- Keyword rules for title-based classification ----
# Order matters: we check Music Video first since it's the most common
# and has the most distinctive, reliable title patterns for these channels.

# ---- Keyword rules for title-based classification ----
# Order matters: we check Music Video first since it's the most common
# and has the most distinctive, reliable title patterns for these channels.
# These were refined by inspecting ACTUAL titles in our dataset (not guessed
# upfront) -- rule-based NLP is iterative: write rules, check real
# misclassifications, expand the rules, repeat.

MUSIC_VIDEO_KEYWORDS = [
    "official music video", "official video", "(official video)",
    "m/v", "official mv", "(amazon music songline)",
    "lyric video", "official lyric video", "visualizer",
    "(audio)", "official audio", "dance practice", "choreography",
    "performance video",
]

BEHIND_THE_SCENES_KEYWORDS = [
    "behind the scenes", "behind-the-scenes", "making of",
    "sketch", "diary", "diaries", "vlog",
    "rehearsal", "studio session", "in the studio",
    "director's commentary", "bts ver", "bts cam",
]

INTERVIEW_PROMO_KEYWORDS = [
    "interview", "talks about", "on the tonight show", "on jimmy",
    "on ellen", "press conference", "q&a", "ask me anything",
    "trailer", "teaser", "announcement", "out now", "pre-order",
    "remix)", "live from", "live at", "live clip",
]


def classify_video(row):
    # --- Rule 1: Shorts (duration <= 60 seconds) ---
    duration_seconds = parse_duration_to_seconds(row["duration"])
    if duration_seconds is not None and duration_seconds <= 60:
        return "Short"

    # --- Rule 2: Live videos (flagged directly by the API) ---
    if row["live_broadcast_content"] in ("live", "upcoming"):
        return "Live"

    title_lower = str(row["video_title"]).lower()

    # --- Rule 3: Behind-the-scenes (checked BEFORE Music Video, since titles
    # like "Dance Practice Sketch" or "MV Behind the Scenes" contain both
    # signals -- behind-the-scenes is the more specific/informative label) ---
    if any(keyword in title_lower for keyword in BEHIND_THE_SCENES_KEYWORDS):
        return "Behind-the-scenes"

    # --- Rule 4: Music Video ---
    if any(keyword in title_lower for keyword in MUSIC_VIDEO_KEYWORDS):
        return "Music Video"

    # --- Rule 5: Interview / Promotion ---
    if any(keyword in title_lower for keyword in INTERVIEW_PROMO_KEYWORDS):
        return "Interview/Promotion"

    # --- Fallback: doesn't confidently match any rule ---
    return "Other"


def main():
    conn = sqlite3.connect(DB_NAME)
    videos_df = pd.read_sql_query("SELECT * FROM videos", conn)

    videos_df["content_type"] = videos_df.apply(classify_video, axis=1)

    # Save the updated table back into the database (now with content_type)
    videos_df.to_sql("videos", conn, if_exists="replace", index=False)
    conn.commit()

    # Quick summary so we can sanity-check the classification results
    print("Content type breakdown (all channels):\n")
    print(videos_df["content_type"].value_counts().to_string())

    print("\nContent type breakdown by channel:\n")
    breakdown = videos_df.groupby(["channel_name", "content_type"]).size().unstack(fill_value=0)
    print(breakdown.to_string())

    conn.close()
    print(f"\n✅ Classified {len(videos_df)} videos and saved content_type into {DB_NAME}")


if __name__ == "__main__":
    main()