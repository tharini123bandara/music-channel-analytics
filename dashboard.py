"""
Day 3: Streamlit Dashboard for Global Music Channel Analytics.

Run with:  streamlit run dashboard.py
"""

import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

DB_NAME = "music_analytics.db"

# ---- Page config (must be first Streamlit command) ----
st.set_page_config(
    page_title="Music Channel Analytics",
    page_icon="🎵",
    layout="wide",
)


# ---- Data loading (cached so we don't re-query the DB on every click) ----
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_NAME)
    channels_df = pd.read_sql_query("SELECT * FROM channels", conn)
    videos_df = pd.read_sql_query("SELECT * FROM videos", conn)
    conn.close()

    # Convert publish_date text into a real datetime so we can group by month
    videos_df["publish_date"] = pd.to_datetime(videos_df["publish_date"])

    return channels_df, videos_df


channels_df, videos_df = load_data()

# ---- Sidebar navigation ----
st.sidebar.title("🎵 Music Analytics")

if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

page = st.sidebar.radio(
    "Navigate to:",
    ["Executive Overview", "Video Performance", "Channel Comparison", "Upload Activity"],
)

# Let users filter the whole dashboard down to specific channels if they want
all_channels = sorted(channels_df["channel_name"].unique())
selected_channels = st.sidebar.multiselect(
    "Filter by channel:", all_channels, default=all_channels
)

# Apply the channel filter to both tables for every page
channels_filtered = channels_df[channels_df["channel_name"].isin(selected_channels)]
videos_filtered = videos_df[videos_df["channel_name"].isin(selected_channels)]


# =====================================================================
# PAGE 1: EXECUTIVE OVERVIEW
# =====================================================================
if page == "Executive Overview":
    st.title("📊 Executive Overview")
    st.caption("High-level snapshot across all selected channels")

    # ---- KPI row ----
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Subscribers", f"{channels_filtered['subscribers'].sum():,}")
    col2.metric("Total Views (lifetime)", f"{channels_filtered['total_views'].sum():,}")
    col3.metric("Total Videos Ever Uploaded (lifetime)", f"{channels_filtered['video_count'].sum():,}")
    st.caption(
        f"Note: the KPIs above reflect each channel's full lifetime stats. "
        f"All charts and analysis on this dashboard are based on a sample of "
        f"the {len(videos_filtered)} most recent videos across selected channels."
    )

    st.divider()

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Channel Comparison: Subscribers")
        fig = px.bar(
            channels_filtered.sort_values("subscribers", ascending=False),
            x="channel_name", y="subscribers",
            color="channel_name",
            labels={"subscribers": "Subscribers", "channel_name": "Channel"},
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")

    with chart_col2:
        st.subheader("Subscriber Distribution (Share of Total)")
        fig = px.pie(
            channels_filtered, names="channel_name", values="subscribers",
            hole=0.4,
        )
        st.plotly_chart(fig, width="stretch")


# =====================================================================
# PAGE 2: VIDEO PERFORMANCE
# =====================================================================
elif page == "Video Performance":
    st.title("🎬 Video Performance")
    st.caption("Which videos are driving the most views and engagement?")

    top_views = videos_filtered.sort_values("views", ascending=False).head(10)
    top_engagement = videos_filtered.copy()
    top_engagement["engagement"] = top_engagement["likes"] + top_engagement["comments"]
    top_engagement = top_engagement.sort_values("engagement", ascending=False).head(10)

    st.subheader("Top 10 Videos by Views")
    fig = px.bar(
        top_views, x="views", y="video_title", color="channel_name",
        orientation="h",
        labels={"views": "Views", "video_title": "", "channel_name": "Channel"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Top 10 Videos by Engagement (Likes + Comments)")
    fig = px.bar(
        top_engagement, x="engagement", y="video_title", color="channel_name",
        orientation="h",
        labels={"engagement": "Likes + Comments", "video_title": "", "channel_name": "Channel"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("💡 Insights")
    most_viewed = top_views.iloc[0]
    most_engaging = top_engagement.iloc[0]
    st.markdown(f"""
    - **Most successful content by views**: *{most_viewed['video_title']}* ({most_viewed['channel_name']}) with **{most_viewed['views']:,}** views
    - **Highest engagement video**: *{most_engaging['video_title']}* ({most_engaging['channel_name']}) with **{most_engaging['engagement']:,}** combined likes + comments
    - Note: the most-*viewed* video and the most-*engaging* video are not always the same — high view counts don't automatically mean high engagement.
    """)


# =====================================================================
# PAGE 3: CHANNEL COMPARISON
# =====================================================================
elif page == "Channel Comparison":
    st.title("⚖️ Channel Comparison")
    st.caption("Comparing reach and engagement across channels")

    # Aggregate engagement stats per channel from the videos table
    engagement_by_channel = videos_filtered.groupby("channel_name").agg(
        avg_views=("views", "mean"),
        avg_likes=("likes", "mean"),
        avg_comments=("comments", "mean"),
    ).reset_index()

    # Comments per 1,000 views -- a normalized engagement rate so channels
    # of different sizes can be fairly compared
    engagement_by_channel["comments_per_1000_views"] = (
        engagement_by_channel["avg_comments"] * 1000 / engagement_by_channel["avg_views"]
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Views per Video")
        fig = px.bar(
            engagement_by_channel.sort_values("avg_views", ascending=False),
            x="channel_name", y="avg_views", color="channel_name",
            labels={"avg_views": "Avg Views", "channel_name": "Channel"},
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Comments per 1,000 Views")
        fig = px.bar(
            engagement_by_channel.sort_values("comments_per_1000_views", ascending=False),
            x="channel_name", y="comments_per_1000_views", color="channel_name",
            labels={"comments_per_1000_views": "Comments / 1K Views", "channel_name": "Channel"},
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")

    st.subheader("Average Likes per Video")
    fig = px.bar(
        engagement_by_channel.sort_values("avg_likes", ascending=False),
        x="channel_name", y="avg_likes", color="channel_name",
        labels={"avg_likes": "Avg Likes", "channel_name": "Channel"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("💡 Reach vs Engagement Insight")
    highest_reach = channels_filtered.loc[channels_filtered["subscribers"].idxmax()]
    highest_engagement = engagement_by_channel.loc[
        engagement_by_channel["comments_per_1000_views"].idxmax()
    ]
    st.markdown(f"""
    - **Highest reach (subscribers)**: {highest_reach['channel_name']} ({highest_reach['subscribers']:,} subscribers)
    - **Highest engagement rate**: {highest_engagement['channel_name']} ({highest_engagement['comments_per_1000_views']:.2f} comments per 1,000 views)
    - A channel can lead in reach without leading in engagement, and vice versa — both matter for a complete picture of channel health.
    """)


# =====================================================================
# PAGE 4: UPLOAD ACTIVITY
# =====================================================================
elif page == "Upload Activity":
    st.title("📅 Upload Activity")
    st.caption("How often does each channel publish, and what kind of content?")

    videos_filtered = videos_filtered.copy()
    # Drop timezone info before grouping by month -- we only care about the
    # calendar month here, not the exact UTC offset, so this is safe.
    videos_filtered["year_month"] = (
        videos_filtered["publish_date"].dt.tz_localize(None).dt.to_period("M").astype(str)
    )

    monthly_uploads = videos_filtered.groupby(
        ["year_month", "channel_name"]
    ).size().reset_index(name="videos_published")

    st.subheader("Videos Published by Month")
    fig = px.line(
        monthly_uploads, x="year_month", y="videos_published", color="channel_name",
        markers=True,
        labels={"year_month": "Month", "videos_published": "Videos Published", "channel_name": "Channel"},
    )
    st.plotly_chart(fig, width="stretch")

    st.subheader("Content Type Breakdown by Channel")
    if "content_type" in videos_filtered.columns:
        content_breakdown = videos_filtered.groupby(
            ["channel_name", "content_type"]
        ).size().reset_index(name="count")
        fig = px.bar(
            content_breakdown, x="channel_name", y="count", color="content_type",
            labels={"count": "Number of Videos", "channel_name": "Channel", "content_type": "Content Type"},
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Run classify_content.py first to see the content-type breakdown here.")

    st.divider()
    st.subheader("💡 Insights")

    upload_counts = videos_filtered.groupby("channel_name").size().sort_values(ascending=False)
    avg_views_by_channel = videos_filtered.groupby("channel_name")["views"].mean()

    most_active = upload_counts.index[0]
    st.markdown(f"""
    - **Most active channel** (most videos in our sample): {most_active} ({upload_counts.iloc[0]} videos)
    - Use the chart above to visually compare whether channels that upload more frequently also tend to have higher or lower average views — this directly speaks to whether posting *more* content helps or dilutes performance.
    """)