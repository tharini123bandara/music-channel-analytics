"""
Day 1: Collect channel-level and video-level data for 5 music channels
using the YouTube Data API, and save results into CSV files.
"""

import os
import time
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

# ---- Setup ----
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

# Number of recent videos to fetch per channel
VIDEOS_PER_CHANNEL = 100

# The 5 channels for this project
CHANNELS = {
    "UCOmHUn--16B90oW2L6FRR3A": "BLACKPINK",
    "UCLkAepWjdylmXSltofFvsYQ": "BANGTANTV (BTS)",
    "UCqECaJ8Gagnn7YCbPEzWH6g": "Taylor Swift",
    "UC0C-w0YjGpqDXGB8IHb662A": "Ed Sheeran",
    "UCIwFjwMjI0y7PDBVEO9-bkQ": "Justin Bieber",
}


def get_channel_stats(channel_id):
    """Fetch subscriber count, total views, and video count for one channel."""
    request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id
    )
    response = request.execute()

    if not response.get("items"):
        print(f"⚠️  No data found for channel {channel_id}")
        return None

    item = response["items"][0]
    return {
        "channel_id": channel_id,
        "channel_name": item["snippet"]["title"],
        "subscribers": int(item["statistics"].get("subscriberCount", 0)),
        "total_views": int(item["statistics"].get("viewCount", 0)),
        "video_count": int(item["statistics"].get("videoCount", 0)),
        "uploads_playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def get_recent_video_ids(uploads_playlist_id, max_videos):
    """Get up to max_videos most recent video IDs from a channel's uploads playlist."""
    video_ids = []
    next_page_token = None

    while len(video_ids) < max_videos:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(50, max_videos - len(video_ids)),  # API max is 50 per call
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break  # no more videos available

    return video_ids


def get_video_stats(video_ids, channel_id, channel_name):
    """Fetch stats (views, likes, comments, publish date) for a list of video IDs.
    The API allows up to 50 video IDs per request, so we batch them."""
    all_video_data = []

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        # "contentDetails" gives us video duration (used to detect Shorts)
        # "snippet" already gives us liveBroadcastContent (used to detect Live videos)
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(batch)
        )
        response = request.execute()

        for item in response.get("items", []):
            stats = item.get("statistics", {})
            all_video_data.append({
                "video_id": item["id"],
                "channel_id": channel_id,
                "channel_name": channel_name,
                "video_title": item["snippet"]["title"],
                "publish_date": item["snippet"]["publishedAt"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),  # some videos hide like count
                "comments": int(stats.get("commentCount", 0)),  # some videos disable comments
                "duration": item["contentDetails"].get("duration", ""),  # e.g. "PT3M45S"
                # "none" = regular upload, "live" = currently live, "upcoming" = scheduled live
                "live_broadcast_content": item["snippet"].get("liveBroadcastContent", "none"),
            })

    return all_video_data


def main():
    channel_records = []
    video_records = []

    for channel_id, channel_name in CHANNELS.items():
        print(f"\n📡 Fetching data for {channel_name}...")

        # 1. Channel-level stats
        channel_data = get_channel_stats(channel_id)
        if not channel_data:
            continue
        channel_records.append(channel_data)
        print(f"   Subscribers: {channel_data['subscribers']:,} | "
              f"Total Views: {channel_data['total_views']:,} | "
              f"Videos: {channel_data['video_count']:,}")

        # 2. Get recent video IDs
        video_ids = get_recent_video_ids(
            channel_data["uploads_playlist_id"], VIDEOS_PER_CHANNEL
        )
        print(f"   Found {len(video_ids)} recent video IDs")

        # 3. Get stats for those videos
        videos = get_video_stats(video_ids, channel_id, channel_name)
        video_records.extend(videos)
        print(f"   ✅ Collected stats for {len(videos)} videos")

        time.sleep(0.5)  # small pause to be polite to the API

    # ---- Save to CSV ----
    os.makedirs("data", exist_ok=True)

    channels_df = pd.DataFrame(channel_records)
    videos_df = pd.DataFrame(video_records)

    channels_df.to_csv("data/channels.csv", index=False)
    videos_df.to_csv("data/videos.csv", index=False)

    # Record exactly when this fetch completed, so the dashboard can later
    # show "Data last updated: ..." instead of leaving people guessing.
    fetched_at = datetime.now(timezone.utc).isoformat()
    with open("data/last_updated.txt", "w") as f:
        f.write(fetched_at)

    print(f"\n🎉 Done! Saved {len(channels_df)} channels and {len(videos_df)} videos to /data")
    print(f"   Fetch timestamp recorded: {fetched_at}")


if __name__ == "__main__":
    main()