"""
Day 2 - Part 2: Run SQL queries against our database to answer
the business questions from the project proposal.
"""

import sqlite3
import pandas as pd

DB_NAME = "music_analytics.db"

conn = sqlite3.connect(DB_NAME)

# pandas can run a SQL query directly against our database connection
# and hand us back a clean table (DataFrame) of the results.

def run_query(title, query):
    print(f"\n{'='*60}")
    print(title)
    print('='*60)
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    return df


# ---------------------------------------------------------
# Q1: Which channel has the highest audience reach?
# (reach = subscribers + total views)
# ---------------------------------------------------------
run_query(
    "Q1: Channel Reach (Subscribers & Total Views)",
    """
    SELECT channel_name, subscribers, total_views
    FROM channels
    ORDER BY subscribers DESC
    """
)


# ---------------------------------------------------------
# Q2: Which channel has the highest engagement rate?
# We define engagement here as average (likes + comments) per video,
# calculated from the videos table, GROUPED BY channel.
# ---------------------------------------------------------
run_query(
    "Q2: Average Engagement per Video, by Channel",
    """
    SELECT
        channel_name,
        COUNT(*) AS videos_analyzed,
        ROUND(AVG(views), 0) AS avg_views,
        ROUND(AVG(likes), 0) AS avg_likes,
        ROUND(AVG(comments), 0) AS avg_comments,
        ROUND(AVG(comments) * 1000.0 / AVG(views), 2) AS comments_per_1000_views
    FROM videos
    GROUP BY channel_name
    ORDER BY avg_likes DESC
    """
)


# ---------------------------------------------------------
# Q3: Which videos generate the strongest audience response?
# Top 10 videos by views, across ALL channels.
# ---------------------------------------------------------
run_query(
    "Q3: Top 10 Videos by Views (All Channels)",
    """
    SELECT channel_name, video_title, views, likes, comments
    FROM videos
    ORDER BY views DESC
    LIMIT 10
    """
)


# ---------------------------------------------------------
# Q3b: Top 10 videos by engagement (likes + comments), not just views
# This can surface different videos than the views ranking --
# a video can be highly "watched" but not very "engaged with".
# ---------------------------------------------------------
run_query(
    "Q3b: Top 10 Videos by Engagement (Likes + Comments)",
    """
    SELECT channel_name, video_title, views, likes, comments,
           (likes + comments) AS total_engagement
    FROM videos
    ORDER BY total_engagement DESC
    LIMIT 10
    """
)


# ---------------------------------------------------------
# Q5: Which channels balance reach and engagement most effectively?
# We compare total_views (reach) against avg engagement per video.
# A channel could have huge reach but low engagement, or vice versa.
# ---------------------------------------------------------
run_query(
    "Q5: Reach vs Engagement Balance",
    """
    SELECT
        c.channel_name,
        c.subscribers,
        c.total_views,
        ROUND(AVG(v.likes), 0) AS avg_likes_per_video,
        ROUND(AVG(v.comments), 0) AS avg_comments_per_video
    FROM channels c
    JOIN videos v ON c.channel_id = v.channel_id
    GROUP BY c.channel_name
    ORDER BY c.subscribers DESC
    """
)

# ---------------------------------------------------------
# Q4a: Upload frequency -- how many videos has each channel
# published per month, going by our sample of their last 100 uploads?
# We use strftime() to pull just the "YYYY-MM" part out of each
# publish_date timestamp, then count rows per channel per month.
# ---------------------------------------------------------
run_query(
    "Q4a: Videos Published per Month, by Channel",
    """
    SELECT
        channel_name,
        strftime('%Y-%m', publish_date) AS year_month,
        COUNT(*) AS videos_published
    FROM videos
    GROUP BY channel_name, year_month
    ORDER BY channel_name, year_month
    """
)


# ---------------------------------------------------------
# Q4b: Does frequent uploading correlate with higher performance?
# For each channel, we compare:
#   - days_spanned: how many days the 100 sampled videos cover
#   - uploads_per_month: rough upload frequency
#   - avg_views_per_video: average performance per video
# If frequent uploaders had consistently lower (or higher) avg_views,
# that would suggest a relationship between frequency and performance.
# ---------------------------------------------------------
run_query(
    "Q4b: Upload Frequency vs Average Performance",
    """
    SELECT
        channel_name,
        COUNT(*) AS videos_in_sample,
        ROUND(
            (JULIANDAY(MAX(publish_date)) - JULIANDAY(MIN(publish_date))), 0
        ) AS days_spanned,
        ROUND(
            COUNT(*) / (
                (JULIANDAY(MAX(publish_date)) - JULIANDAY(MIN(publish_date))) / 30.0
            ), 2
        ) AS uploads_per_month,
        ROUND(AVG(views), 0) AS avg_views_per_video
    FROM videos
    GROUP BY channel_name
    ORDER BY uploads_per_month DESC
    """
)


conn.close()
print("\n✅ All queries complete.")