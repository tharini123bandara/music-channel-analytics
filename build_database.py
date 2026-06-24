"""
Day 2 - Part 1: Create a SQLite database and load our CSV data into it.

This turns our two flat CSV files into proper SQL tables we can query.
"""

import sqlite3
import pandas as pd

DB_NAME = "music_analytics.db"


def create_database():
    # Connect to (or create) the database file
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ---- Create channels table ----
    # "TEXT PRIMARY KEY" means channel_id uniquely identifies each row,
    # like a row's ID card -- no two channels can share one.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT,
            subscribers INTEGER,
            total_views INTEGER,
            video_count INTEGER
        )
    """)

    # ---- Create videos table ----
    # "channel_id" here links back to the channels table (a "foreign key"
    # relationship) -- this is how we'll join videos to their channel info.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT,
            channel_name TEXT,
            video_title TEXT,
            publish_date TEXT,
            views INTEGER,
            likes INTEGER,
            comments INTEGER,
            FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
        )
    """)

    conn.commit()
    return conn


def load_csv_into_tables(conn):
    # Read our CSVs back into pandas DataFrames
    channels_df = pd.read_csv("data/channels.csv")
    videos_df = pd.read_csv("data/videos.csv")

    # The channels CSV also has an "uploads_playlist_id" column we used
    # internally to fetch videos -- we don't need it in the database,
    # so we drop it before inserting.
    channels_df = channels_df.drop(columns=["uploads_playlist_id"], errors="ignore")

    # pandas .to_sql() inserts a whole DataFrame into a SQL table in one go.
    # if_exists="replace" means: if we run this script again, wipe and reload
    # fresh data instead of duplicating rows.
    channels_df.to_sql("channels", conn, if_exists="replace", index=False)
    videos_df.to_sql("videos", conn, if_exists="replace", index=False)

    print(f"✅ Loaded {len(channels_df)} channels and {len(videos_df)} videos into {DB_NAME}")


if __name__ == "__main__":
    conn = create_database()
    load_csv_into_tables(conn)
    conn.close()