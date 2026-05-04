"""
Live Music Analytics Dashboard
Connects to Snowflake mart tables for descriptive and diagnostic analytics.
"""

import streamlit as st
import snowflake.connector
import pandas as pd

st.set_page_config(page_title="Live Music Analytics", layout="wide")


@st.cache_resource
def get_connection():
    """Connect to Snowflake using Streamlit secrets."""
    return snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"]["role"],
    )


@st.cache_data(ttl=600)
def run_query(query):
    """Execute a query and return a DataFrame."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    return pd.DataFrame(data, columns=columns)


# ── Load data from mart tables ───────────────────────────────────────────────

fact_events = run_query("""
    SELECT f.EVENT_ID, f.EVENT_NAME, f.EVENT_DATE, f.EVENT_TIME,
           f.SALE_STATUS, f.PRICE_MIN, f.PRICE_MAX, f.PRICE_AVG, f.CURRENCY,
           a.ARTIST_NAME, a.GENRE, a.MONTHLY_LISTENERS, a.SPOTIFY_URL,
           v.VENUE_NAME, v.CITY, v.STATE,
           d.DAY_NAME, d.MONTH_NAME, d.YEAR, d.QUARTER, d.IS_WEEKEND
    FROM RAW_MARTS.FACT_EVENTS f
    LEFT JOIN RAW_MARTS.DIM_ARTISTS a ON f.ARTIST_KEY = a.ARTIST_KEY
    LEFT JOIN RAW_MARTS.DIM_VENUES v ON f.VENUE_KEY = v.VENUE_KEY
    LEFT JOIN RAW_MARTS.DIM_DATES d ON f.DATE_KEY = d.DATE_KEY
""")

# ── Sidebar filters ──────────────────────────────────────────────────────────

st.sidebar.header("Filters")

genres = sorted(fact_events["GENRE"].dropna().unique())
selected_genres = st.sidebar.multiselect("Genre", genres, default=genres)

states = sorted(fact_events["STATE"].dropna().unique())
selected_states = st.sidebar.multiselect("State", states, default=states)

price_min_val = float(fact_events["PRICE_AVG"].min() or 0)
price_max_val = float(fact_events["PRICE_AVG"].max() or 500)
price_range = st.sidebar.slider(
    "Avg Price Range ($)",
    min_value=price_min_val,
    max_value=price_max_val,
    value=(price_min_val, price_max_val),
)

# Apply filters
df = fact_events.copy()
df = df[df["GENRE"].isin(selected_genres) | df["GENRE"].isna()]
df = df[df["STATE"].isin(selected_states) | df["STATE"].isna()]
df = df[
    (df["PRICE_AVG"].isna())
    | ((df["PRICE_AVG"] >= price_range[0]) & (df["PRICE_AVG"] <= price_range[1]))
]

# ── Header ────────────────────────────────────────────────────────────────────

st.title("Live Music Analytics Dashboard")
st.markdown("Combining Ticketmaster event data with Spotify streaming metrics for entertainment BI insights.")

# ── Section 1: Event Overview ─────────────────────────────────────────────────

st.header("Event Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Events", f"{len(df):,}")
col2.metric("Unique Artists", f"{df['ARTIST_NAME'].nunique():,}")
col3.metric("Unique Venues", f"{df['VENUE_NAME'].nunique():,}")
avg_price = df["PRICE_AVG"].mean()
col4.metric("Avg Ticket Price", f"${avg_price:,.2f}" if pd.notna(avg_price) else "N/A")

genre_counts = df.groupby("GENRE").size().reset_index(name="count").sort_values("count", ascending=False)
st.subheader("Events by Genre")
st.bar_chart(genre_counts.set_index("GENRE")["count"])

# ── Section 2: Pricing Analytics ─────────────────────────────────────────────

st.header("Pricing Analytics")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Average Price by Genre")
    price_by_genre = (
        df.groupby("GENRE")["PRICE_AVG"]
        .mean()
        .reset_index()
        .sort_values("PRICE_AVG", ascending=False)
    )
    st.bar_chart(price_by_genre.set_index("GENRE")["PRICE_AVG"])

with col2:
    st.subheader("Price Distribution")
    price_data = df["PRICE_AVG"].dropna()
    if not price_data.empty:
        st.bar_chart(price_data.value_counts(bins=20).sort_index())

# ── Section 3: Artist Insights (Diagnostic) ──────────────────────────────────

st.header("Artist Insights")
st.markdown("**Diagnostic:** Do streaming-popular artists have more live events?")

artist_stats = (
    df.groupby("ARTIST_NAME")
    .agg(event_count=("EVENT_ID", "count"), monthly_listeners=("MONTHLY_LISTENERS", "first"))
    .reset_index()
    .dropna(subset=["monthly_listeners"])
)

if not artist_stats.empty:
    st.scatter_chart(
        artist_stats,
        x="monthly_listeners",
        y="event_count",
        size="event_count",
    )
    st.caption("Each dot is an artist. X-axis = Spotify monthly listeners, Y-axis = number of live events.")
else:
    st.info("No artists with both event and Spotify data available.")

# ── Section 4: Venue & Geography ─────────────────────────────────────────────

st.header("Venue & Geography")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Events by State")
    state_counts = df.groupby("STATE").size().reset_index(name="count").sort_values("count", ascending=False)
    st.bar_chart(state_counts.set_index("STATE")["count"])

with col2:
    st.subheader("Top 10 Venues")
    top_venues = (
        df.groupby(["VENUE_NAME", "CITY", "STATE"])
        .size()
        .reset_index(name="Events")
        .sort_values("Events", ascending=False)
        .head(10)
    )
    st.dataframe(top_venues, use_container_width=True, hide_index=True)

# ── Section 5: Time Trends ───────────────────────────────────────────────────

st.header("Time Trends")

col1, col2 = st.columns(2)

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

with col1:
    st.subheader("Events by Day of Week")
    dow_counts = df.groupby("DAY_NAME").size().reset_index(name="count")
    dow_counts["DAY_NAME"] = pd.Categorical(dow_counts["DAY_NAME"], categories=day_order, ordered=True)
    dow_counts = dow_counts.sort_values("DAY_NAME")
    st.bar_chart(dow_counts.set_index("DAY_NAME")["count"])

with col2:
    st.subheader("Weekend vs Weekday")
    weekend_counts = df.groupby("IS_WEEKEND").size().reset_index(name="count")
    weekend_counts["IS_WEEKEND"] = weekend_counts["IS_WEEKEND"].map({True: "Weekend", False: "Weekday"})
    st.bar_chart(weekend_counts.set_index("IS_WEEKEND")["count"])
