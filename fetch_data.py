"""
Step 1: Test that our YouTube API key works.
This script fetches basic stats for ONE channel (BLACKPINK) to confirm
everything is wired up correctly before we scale to all 5 channels.
"""

import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load the API key from our .env file (keeps it out of the code itself)
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

# Build the YouTube API client
youtube = build("youtube", "v3", developerKey=API_KEY)

# BLACKPINK's official channel ID (every channel has a unique one)
# We can find this from the channel's URL or "About" page
CHANNEL_ID = "UCOmHUn--16B90oW2L6FRR3A"  # BLACKPINK Official

def get_channel_stats(channel_id):
    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )
    response = request.execute()

    if not response.get("items"):
        print("No data found. Check your channel ID or API key.")
        return None

    item = response["items"][0]
    stats = {
        "channel_name": item["snippet"]["title"],
        "subscribers": item["statistics"].get("subscriberCount"),
        "total_views": item["statistics"].get("viewCount"),
        "video_count": item["statistics"].get("videoCount"),
    }
    return stats

if __name__ == "__main__":
    data = get_channel_stats(CHANNEL_ID)
    if data:
        print("✅ API key works! Here's what we got:\n")
        for key, value in data.items():
            print(f"{key}: {value}")