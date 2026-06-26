"""
Single-page Streamlit Dashboard for Global Music Channel Analytics.

Run with:  streamlit run dashboard.py
"""

import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

DB_NAME = "music_analytics.db"

st.set_page_config(page_title="Music Channel Analytics", page_icon=None, layout="wide")

# ---- Design tokens ----
BG = "#F4F5FA"
CARD = "#FFFFFF"
BORDER = "#E7E8F0"
TEXT = "#1A1D29"
TEXT_MUTED = "#8A8DA0"
PRIMARY = "#5B5FE8"

ARTIST_COLORS = {
    "BLACKPINK": "#E84393",
    "BANGTANTV (BTS)": "#7C5CFC",
    "Taylor Swift": "#3D7DFF",
    "Justin Bieber": "#16BFA6",
    "Ed Sheeran": "#FF9F40",
}
DEFAULT_PALETTE = ["#E84393", "#7C5CFC", "#3D7DFF", "#16BFA6", "#FF9F40", "#FF6B6B"]
CONTENT_TYPE_COLORS = {
    "Music Video": "#3D7DFF",
    "Short": "#7C5CFC",
    "Behind-the-scenes": "#16BFA6",
    "Interview/Promotion": "#FF9F40",
    "Live": "#E84393",
    "Other": "#C7C9D6",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=CARD,
    plot_bgcolor=CARD,
    font=dict(family="Inter, -apple-system, sans-serif", color=TEXT, size=12),
    margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
GRID_COLOR = "#EEEFF5"


def style_fig(fig, showlegend=True, height=None):
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=showlegend)
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, linecolor=BORDER)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, linecolor=BORDER)
    return fig


def artist_color_map(names):
    mapping = {}
    fallback_i = 0
    for n in names:
        if n in ARTIST_COLORS:
            mapping[n] = ARTIST_COLORS[n]
        else:
            mapping[n] = DEFAULT_PALETTE[fallback_i % len(DEFAULT_PALETTE)]
            fallback_i += 1
    return mapping


def fmt_compact(n):
    """Format large numbers compactly: 381900000 -> 381.9M"""
    n = float(n)
    for unit, div in [("B", 1e9), ("M", 1e6), ("K", 1e3)]:
        if abs(n) >= div:
            return f"{n/div:.1f}{unit}"
    return f"{n:.0f}"


# ---- Global CSS ----
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', -apple-system, sans-serif; }}

.page-title {{ font-size: 1.9rem; font-weight: 800; color: {TEXT}; margin: 0; line-height: 1.1; }}
.page-subtitle {{ color: {TEXT_MUTED}; font-size: 0.92rem; margin-bottom: 1.2rem; }}

.kpi-row {{ display: flex; gap: 14px; margin-bottom: 1.2rem; flex-wrap: wrap; }}
.kpi-card {{
    flex: 1; min-width: 200px; background: {CARD}; border: 1px solid {BORDER};
    border-radius: 12px; padding: 16px 18px;
}}
.kpi-icon {{
    width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center;
    justify-content: center; margin-bottom: 10px; font-size: 16px;
    background: var(--tint, #EEF); color: var(--accent, {PRIMARY});
}}
.kpi-label {{ font-size: 0.8rem; font-weight: 600; color: {TEXT}; margin-bottom: 2px; }}
.kpi-value {{ font-size: 1.6rem; font-weight: 800; color: {TEXT}; letter-spacing: -0.01em; }}
.kpi-sub {{ font-size: 0.74rem; color: {TEXT_MUTED}; margin-top: 2px; }}

.section-card {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
    padding: 18px 20px 6px 20px; margin-bottom: 1.1rem;
}}
.section-title {{ font-size: 0.98rem; font-weight: 700; color: {TEXT}; margin-bottom: 2px; }}
.section-sub {{ font-size: 0.78rem; color: {TEXT_MUTED}; margin-bottom: 0.8rem; }}

.insight-box {{
    background: #F1F0FF; border: 1px solid #DEDBFF; border-radius: 10px;
    padding: 14px 18px; margin-top: 0.4rem;
}}
.insight-title {{ font-size: 0.75rem; font-weight: 700; letter-spacing: 0.04em;
    text-transform: uppercase; color: {PRIMARY}; margin-bottom: 8px; }}
.insight-box ul {{ margin: 0; padding-left: 1.1rem; color: {TEXT}; font-size: 0.88rem; line-height: 1.6; }}
.insight-box li {{ margin-bottom: 4px; }}

.rank-row {{
    display: flex; align-items: center; gap: 12px; padding: 9px 0;
    border-bottom: 1px solid {BORDER};
}}
.rank-row:last-child {{ border-bottom: none; }}
.rank-badge {{
    width: 24px; height: 24px; border-radius: 7px; background: var(--accent, {PRIMARY});
    color: white; font-size: 0.74rem; font-weight: 700; display: flex;
    align-items: center; justify-content: center; flex-shrink: 0;
}}
.rank-name {{ flex: 1; font-size: 0.88rem; font-weight: 600; color: {TEXT}; }}
.rank-value {{ font-size: 0.88rem; font-weight: 700; color: var(--accent, {PRIMARY}); }}

[data-testid="stSidebar"] {{ background: {CARD}; border-right: 1px solid {BORDER}; }}
.sidebar-brand {{ font-size: 1.05rem; font-weight: 800; color: {TEXT}; }}
.sidebar-brand span {{ color: {PRIMARY}; }}
.sidebar-meta {{ font-size: 0.74rem; color: {TEXT_MUTED}; line-height: 1.5; }}
.sidebar-section-label {{
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
    color: {TEXT_MUTED}; margin: 14px 0 6px 0;
}}
hr {{ border-color: {BORDER}; }}
</style>
""", unsafe_allow_html=True)


def kpi_card(icon, label, value, sub, accent, tint):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon" style="--accent:{accent}; --tint:{tint};">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def section(title, sub="", body_html=""):
    """Render a complete section card as ONE markdown call: open div, title,
    subtitle, inner content, and closing div all in a single HTML string.
    Use this for sections containing ONLY HTML content (like the ranked
    list) -- it avoids ever leaving a <div> open across separate
    st.markdown calls, which was silently hiding the list's first row."""
    sub_html = f'<div class="section-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="section-card">'
        f'<div class="section-title">{title}</div>'
        f'{sub_html}'
        f'{body_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_start(title, sub=""):
    """For sections that contain a Plotly chart (st.plotly_chart renders as
    its own component, not raw HTML, so the open/close split here is safe)."""
    sub_html = f'<div class="section-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="section-card"><div class="section-title">{title}</div>{sub_html}', unsafe_allow_html=True)


def section_end():
    st.markdown('</div>', unsafe_allow_html=True)


def insight_box(title, bullets):
    items = "".join(f"<li>{b}</li>" for b in bullets)
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">{title}</div>
        <ul>{items}</ul>
    </div>
    """, unsafe_allow_html=True)


def ranked_list_html(df, name_col, value_col, value_fmt, colors_map):
    """Build the ranked list as a single HTML string (does not render directly).
    Returning a string -- rather than calling st.markdown per row -- lets the
    caller combine this with section_start/section_end into ONE complete,
    properly-closed HTML block. Splitting an open <div> across multiple
    separate st.markdown() calls causes browsers to auto-close it at an
    unpredictable point, which was silently hiding the first row."""
    rows_html = ""
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        accent = colors_map.get(row[name_col], PRIMARY)
        name = str(row[name_col])
        value = value_fmt(row[value_col])
        rows_html += (
            f'<div class="rank-row">'
            f'<div class="rank-badge" style="--accent:{accent}">{i}</div>'
            f'<div class="rank-name">{name}</div>'
            f'<div class="rank-value" style="--accent:{accent}">{value}</div>'
            f'</div>'
        )
    return rows_html


# ---- Data loading ----
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_NAME)
    channels_df = pd.read_sql_query("SELECT * FROM channels", conn)
    videos_df = pd.read_sql_query("SELECT * FROM videos", conn)
    try:
        metadata_df = pd.read_sql_query("SELECT value FROM metadata WHERE key = 'last_updated'", conn)
        last_updated_raw = metadata_df["value"].iloc[0] if len(metadata_df) > 0 else None
    except Exception:
        last_updated_raw = None
    conn.close()
    videos_df["publish_date"] = pd.to_datetime(videos_df["publish_date"])
    return channels_df, videos_df, last_updated_raw


channels_df, videos_df, last_updated_raw = load_data()

# ---- Sidebar ----
st.sidebar.markdown(
    '<div class="sidebar-brand">CHANNEL<span>METRICS</span></div>'
    '<div class="sidebar-meta" style="margin-top:2px;">Global Music Analytics Dashboard</div>',
    unsafe_allow_html=True,
)

if st.sidebar.button("Refresh data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if last_updated_raw and last_updated_raw != "unknown":
    fetched_dt = pd.to_datetime(last_updated_raw)
    st.sidebar.markdown(
        f'<div class="sidebar-meta" style="margin-top:8px;">Data last updated<br>'
        f'<strong>{fetched_dt.strftime("%b %d, %Y &middot; %H:%M UTC")}</strong></div>',
        unsafe_allow_html=True,
    )

st.sidebar.markdown('<div class="sidebar-section-label">Select Channels</div>', unsafe_allow_html=True)
all_channels = sorted(channels_df["channel_name"].unique())
selected_channels = st.sidebar.multiselect(
    "Filter by channel:", all_channels, default=all_channels, label_visibility="collapsed"
)
if not selected_channels:
    selected_channels = all_channels  # avoid an empty dashboard if everything gets cleared

channels_filtered = channels_df[channels_df["channel_name"].isin(selected_channels)]
videos_filtered = videos_df[videos_df["channel_name"].isin(selected_channels)].copy()
colors = artist_color_map(selected_channels)

st.sidebar.markdown('<div class="sidebar-section-label">Quick Stats</div>', unsafe_allow_html=True)
st.sidebar.markdown(f"""
<div class="kpi-card" style="margin-bottom:8px;">
    <div class="kpi-value" style="font-size:1.3rem;">{len(selected_channels)}</div>
    <div class="kpi-sub">Channels analyzed</div>
</div>
<div class="kpi-card" style="margin-bottom:8px;">
    <div class="kpi-value" style="font-size:1.3rem;">{len(videos_filtered)}</div>
    <div class="kpi-sub">Videos in sample</div>
</div>
""", unsafe_allow_html=True)


# =====================================================================
# MAIN PAGE
# =====================================================================
st.markdown('<div class="page-title">Executive Overview</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">High-level overview across all selected channels</div>',
    unsafe_allow_html=True,
)

# ---- KPI row ----
total_views_sample = videos_filtered["views"].sum()
total_likes_sample = videos_filtered["likes"].sum()
total_comments_sample = videos_filtered["comments"].sum()
engagement_rate = (
    (total_likes_sample + total_comments_sample) / total_views_sample * 100
    if total_views_sample > 0 else 0
)

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("●", "Total Subscribers", fmt_compact(channels_filtered["subscribers"].sum()),
              "Across selected channels", "#5B5FE8", "#EEEDFF")
with k2:
    kpi_card("◎", "Total Views", fmt_compact(channels_filtered["total_views"].sum()),
              "Lifetime views", "#16BFA6", "#E6FBF7")
with k3:
    kpi_card("▣", "Total Videos", f"{channels_filtered['video_count'].sum():,}",
              "Lifetime uploads", "#3D7DFF", "#E8F0FF")
with k4:
    kpi_card("▲", "Avg. Engagement Rate", f"{engagement_rate:.2f}%",
              "(Likes + Comments) / Views, sample", "#FF9F40", "#FFF1E0")

st.caption(
    f"KPIs reflect each channel's full lifetime stats except Engagement Rate, which is "
    f"calculated from the {len(videos_filtered)}-video sample shown throughout this dashboard."
)

# ---- Row: Subscribers bar + donut ----
col1, col2 = st.columns([1.2, 1])
with col1:
    section_start("Subscribers by Channel")
    sorted_channels = channels_filtered.sort_values("subscribers", ascending=False)
    fig = px.bar(
        sorted_channels, x="subscribers", y="channel_name", orientation="h",
        color="channel_name", color_discrete_map=colors,
        labels={"subscribers": "Subscribers", "channel_name": ""},
        text="subscribers",
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(style_fig(fig, showlegend=False, height=280), use_container_width=True)
    section_end()

with col2:
    section_start("Subscribers Share")
    fig = px.pie(
        channels_filtered, names="channel_name", values="subscribers",
        hole=0.6, color="channel_name", color_discrete_map=colors,
    )
    fig.update_traces(marker=dict(line=dict(color=CARD, width=2)), textinfo="percent")
    fig.add_annotation(
        text=f"{fmt_compact(channels_filtered['subscribers'].sum())}<br><span style='font-size:11px;color:{TEXT_MUTED}'>Total</span>",
        showarrow=False, font=dict(size=16, color=TEXT),
    )
    st.plotly_chart(style_fig(fig, height=280), use_container_width=True)
    section_end()

# ---- Bubble chart: Subscribers vs Total Views ----
section_start("Subscribers vs Total Views", "Bubble size represents number of videos uploaded (lifetime)")
fig = px.scatter(
    channels_filtered, x="subscribers", y="total_views", size="video_count",
    color="channel_name", color_discrete_map=colors, text="channel_name",
    size_max=55, labels={"subscribers": "Subscribers", "total_views": "Total Views"},
)
fig.update_traces(textposition="top center")
st.plotly_chart(style_fig(fig, showlegend=False, height=380), use_container_width=True)
section_end()

# ---- Row: Ranked engagement list + content type donut ----
engagement_by_channel = videos_filtered.groupby("channel_name").agg(
    avg_views=("views", "mean"), avg_likes=("likes", "mean"), avg_comments=("comments", "mean"),
).reset_index()
engagement_by_channel["engagement_rate"] = (
    (engagement_by_channel["avg_likes"] + engagement_by_channel["avg_comments"])
    / engagement_by_channel["avg_views"] * 100
)
engagement_ranked = engagement_by_channel.sort_values("engagement_rate", ascending=False)

col3, col4 = st.columns([1, 1])
with col3:
    rows_html = ranked_list_html(engagement_ranked, "channel_name", "engagement_rate", lambda v: f"{v:.2f}%", colors)
    section("Channels by Avg. Engagement Rate", "(Likes + Comments) / Views, per video average", rows_html)

with col4:
    if "content_type" in videos_filtered.columns:
        section_start("Content Type Distribution", "All selected channels")
        type_counts = videos_filtered["content_type"].value_counts().reset_index()
        type_counts.columns = ["content_type", "count"]
        fig = px.pie(
            type_counts, names="content_type", values="count", hole=0.6,
            color="content_type", color_discrete_map=CONTENT_TYPE_COLORS,
        )
        fig.update_traces(marker=dict(line=dict(color=CARD, width=2)), textinfo="percent")
        fig.add_annotation(
            text=f"{len(videos_filtered)}<br><span style='font-size:11px;color:{TEXT_MUTED}'>Total Videos</span>",
            showarrow=False, font=dict(size=16, color=TEXT),
        )
        st.plotly_chart(style_fig(fig, height=280), use_container_width=True)
        section_end()
    else:
        section_start("Content Type Distribution")
        st.info("Run classify_content.py to see this breakdown.")
        section_end()

# ---- Upload activity trend ----
# Limit to the last 12 months of activity. Without this, channels that upload
# infrequently (their 100-video sample can stretch back years) create long
# diagonal "staircase" lines connecting distant months with no real data
# between them -- misleading rather than informative.
videos_filtered["publish_date_naive"] = videos_filtered["publish_date"].dt.tz_localize(None)
cutoff = videos_filtered["publish_date_naive"].max() - pd.DateOffset(months=12)
recent_videos = videos_filtered[videos_filtered["publish_date_naive"] >= cutoff].copy()
recent_videos["year_month"] = recent_videos["publish_date_naive"].dt.to_period("M").astype(str)

monthly_uploads = recent_videos.groupby(["year_month", "channel_name"]).size().reset_index(name="videos_published")

section_start("Upload Activity Over Time", "Videos published per month, by channel (last 12 months)")
fig = px.line(
    monthly_uploads.sort_values("year_month"), x="year_month", y="videos_published", color="channel_name",
    markers=True, color_discrete_map=colors,
    labels={"year_month": "Month", "videos_published": "Videos Published", "channel_name": "Channel"},
)
fig.update_xaxes(type="category")  # treat months as discrete categories, not a continuous date axis
st.plotly_chart(style_fig(fig, height=320), use_container_width=True)
section_end()

# ---- Video performance: top 10 by views & engagement ----
top_views = videos_filtered.sort_values("views", ascending=False).head(10)
top_engagement_df = videos_filtered.copy()
top_engagement_df["engagement"] = top_engagement_df["likes"] + top_engagement_df["comments"]
top_engagement_df = top_engagement_df.sort_values("engagement", ascending=False).head(10)

col5, col6 = st.columns(2)
with col5:
    section_start("Top 10 Videos by Views", "Best individual videos across all selected channels combined")
    fig = px.bar(
        top_views, x="views", y="video_title", orientation="h", color="channel_name",
        color_discrete_map=colors, labels={"views": "Views", "video_title": "", "channel_name": "Channel"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(style_fig(fig, height=360), use_container_width=True)
    section_end()

with col6:
    section_start("Top 10 Videos by Engagement", "Likes + Comments, across all selected channels combined")
    fig = px.bar(
        top_engagement_df, x="engagement", y="video_title", orientation="h", color="channel_name",
        color_discrete_map=colors, labels={"engagement": "Likes + Comments", "video_title": "", "channel_name": "Channel"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(style_fig(fig, height=360), use_container_width=True)
    section_end()

# ---- Final insights summary ----
highest_reach = channels_filtered.loc[channels_filtered["subscribers"].idxmax()]
highest_engagement = engagement_ranked.iloc[0]
most_active = videos_filtered.groupby("channel_name").size().sort_values(ascending=False)
most_viewed_video = top_views.iloc[0]

insight_box("Key Insights", [
    f"<strong>{highest_reach['channel_name']}</strong> leads in reach with "
    f"{highest_reach['subscribers']:,} subscribers.",
    f"<strong>{highest_engagement['channel_name']}</strong> has the highest engagement rate at "
    f"{highest_engagement['engagement_rate']:.2f}% (likes + comments per view).",
    f"<strong>{most_viewed_video['channel_name']}</strong>'s \"{most_viewed_video['video_title']}\" "
    f"is the top-performing video by views ({most_viewed_video['views']:,}).",
    f"<strong>{most_active.index[0]}</strong> published the most videos in this sample "
    f"({most_active.iloc[0]} videos) &mdash; compare this against engagement rate above to see "
    f"whether frequent uploading helps or dilutes performance.",
    "Reach and engagement don't always move together: the channel with the most subscribers "
    "is not necessarily the one whose audience engages the most per view.",
])