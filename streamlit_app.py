"""
Live Music Analytics Dashboard
Multi-page dashboard connecting to Snowflake mart tables.
"""

import streamlit as st
import snowflake.connector
import pandas as pd
import traceback

st.set_page_config(page_title="Live Music Analytics", layout="wide")

# ── US City Geocoding Lookup ─────────────────────────────────────────────────

CITY_COORDS = {
    ("New York", "NY"): (40.7128, -74.0060), ("Los Angeles", "CA"): (34.0522, -118.2437),
    ("Chicago", "IL"): (41.8781, -87.6298), ("Houston", "TX"): (29.7604, -95.3698),
    ("Phoenix", "AZ"): (33.4484, -112.0740), ("Philadelphia", "PA"): (39.9526, -75.1652),
    ("San Antonio", "TX"): (29.4241, -98.4936), ("San Diego", "CA"): (32.7157, -117.1611),
    ("Dallas", "TX"): (32.7767, -96.7970), ("San Jose", "CA"): (37.3382, -121.8863),
    ("Austin", "TX"): (30.2672, -97.7431), ("Jacksonville", "FL"): (30.3322, -81.6557),
    ("Fort Worth", "TX"): (32.7555, -97.3308), ("Columbus", "OH"): (39.9612, -82.9988),
    ("Charlotte", "NC"): (35.2271, -80.8431), ("San Francisco", "CA"): (37.7749, -122.4194),
    ("Indianapolis", "IN"): (39.7684, -86.1581), ("Seattle", "WA"): (47.6062, -122.3321),
    ("Denver", "CO"): (39.7392, -104.9903), ("Washington", "DC"): (38.9072, -77.0369),
    ("Nashville", "TN"): (36.1627, -86.7816), ("Oklahoma City", "OK"): (35.4676, -97.5164),
    ("El Paso", "TX"): (31.7619, -106.4850), ("Boston", "MA"): (42.3601, -71.0589),
    ("Portland", "OR"): (45.5152, -122.6784), ("Las Vegas", "NV"): (36.1699, -115.1398),
    ("Memphis", "TN"): (35.1495, -90.0490), ("Louisville", "KY"): (38.2527, -85.7585),
    ("Baltimore", "MD"): (39.2904, -76.6122), ("Milwaukee", "WI"): (43.0389, -87.9065),
    ("Albuquerque", "NM"): (35.0844, -106.6504), ("Tucson", "AZ"): (32.2226, -110.9747),
    ("Fresno", "CA"): (36.7378, -119.7871), ("Mesa", "AZ"): (33.4152, -111.8315),
    ("Sacramento", "CA"): (38.5816, -121.4944), ("Atlanta", "GA"): (33.7490, -84.3880),
    ("Kansas City", "MO"): (39.0997, -94.5786), ("Colorado Springs", "CO"): (38.8339, -104.8214),
    ("Omaha", "NE"): (41.2565, -95.9345), ("Raleigh", "NC"): (35.7796, -78.6382),
    ("Miami", "FL"): (25.7617, -80.1918), ("Cleveland", "OH"): (41.4993, -81.6944),
    ("Tulsa", "OK"): (36.1540, -95.9928), ("Oakland", "CA"): (37.8044, -122.2712),
    ("Minneapolis", "MN"): (44.9778, -93.2650), ("Tampa", "FL"): (27.9506, -82.4572),
    ("Arlington", "TX"): (32.7357, -97.1081), ("New Orleans", "LA"): (29.9511, -90.0715),
    ("Wichita", "KS"): (37.6872, -97.3301), ("Bakersfield", "CA"): (35.3733, -119.0187),
    ("Aurora", "CO"): (39.7294, -104.8319), ("Anaheim", "CA"): (33.8366, -117.9143),
    ("Honolulu", "HI"): (21.3069, -157.8583), ("Santa Ana", "CA"): (33.7455, -117.8677),
    ("Riverside", "CA"): (33.9534, -117.3962), ("Corpus Christi", "TX"): (27.8006, -97.3964),
    ("Pittsburgh", "PA"): (40.4406, -79.9959), ("Lexington", "KY"): (38.0406, -84.5037),
    ("Anchorage", "AK"): (61.2181, -149.9003), ("Stockton", "CA"): (37.9577, -121.2908),
    ("St. Louis", "MO"): (38.6270, -90.1994), ("Cincinnati", "OH"): (39.1031, -84.5120),
    ("St. Paul", "MN"): (44.9537, -93.0900), ("Greensboro", "NC"): (36.0726, -79.7920),
    ("Orlando", "FL"): (28.5383, -81.3792), ("Irvine", "CA"): (33.6846, -117.8265),
    ("Newark", "NJ"): (40.7357, -74.1724), ("Detroit", "MI"): (42.3314, -83.0458),
    ("Salt Lake City", "UT"): (40.7608, -111.8910), ("Birmingham", "AL"): (33.5207, -86.8025),
    ("Boise", "ID"): (43.6150, -116.2023), ("Richmond", "VA"): (37.5407, -77.4360),
    ("Spokane", "WA"): (47.6588, -117.4260), ("Des Moines", "IA"): (41.5868, -93.6250),
    ("Montgomery", "AL"): (32.3668, -86.3000), ("Modesto", "CA"): (37.6391, -120.9969),
    ("Baton Rouge", "LA"): (30.4515, -91.1871), ("Rochester", "NY"): (43.1566, -77.6088),
    ("Tacoma", "WA"): (47.2529, -122.4443), ("Shreveport", "LA"): (32.5252, -93.7502),
    ("Knoxville", "TN"): (35.9606, -83.9207), ("Worcester", "MA"): (42.2626, -71.8023),
    ("Providence", "RI"): (41.8240, -71.4128), ("Newport News", "VA"): (37.0871, -76.4730),
    ("Huntsville", "AL"): (34.7304, -86.5861), ("Tempe", "AZ"): (33.4255, -111.9400),
    ("Brownsville", "TX"): (25.9017, -97.4975), ("Fayetteville", "NC"): (35.0527, -78.8784),
    ("Chattanooga", "TN"): (35.0456, -85.3097), ("Fort Lauderdale", "FL"): (26.1224, -80.1373),
    ("Savannah", "GA"): (32.0809, -81.0912), ("Inglewood", "CA"): (33.9617, -118.3531),
    ("Noblesville", "IN"): (40.0456, -86.0086), ("Bristow", "VA"): (38.7232, -77.5389),
    ("Holmdel", "NJ"): (40.3873, -74.1854), ("Mansfield", "MA"): (42.0334, -71.2190),
    ("Tinley Park", "IL"): (41.5731, -87.7845), ("Maryland Heights", "MO"): (38.7131, -90.4263),
    ("West Palm Beach", "FL"): (26.7153, -80.0534), ("Woodlands", "TX"): (30.1658, -95.4613),
    ("Burgettstown", "PA"): (40.3823, -80.3923), ("Clarkston", "MI"): (42.7356, -83.4188),
    ("Chula Vista", "CA"): (32.6401, -117.0842), ("Wheatland", "CA"): (38.9983, -121.4261),
    ("Gilford", "NH"): (43.5476, -71.4067), ("Saratoga Springs", "NY"): (43.0831, -73.7846),
    ("George", "WA"): (47.0790, -119.8522), ("Alpine", "CA"): (32.8351, -116.7664),
    ("Morrison", "CO"): (39.6536, -105.1911), ("Pelham", "AL"): (33.2859, -86.8097),
    ("Rosemont", "IL"): (41.9953, -87.8706), ("Wantagh", "NY"): (40.6834, -73.5101),
    ("Camden", "NJ"): (39.9259, -75.1196), ("Virginia Beach", "VA"): (36.8529, -75.9780),
    ("Cuyahoga Falls", "OH"): (41.1340, -81.4846), ("West Valley City", "UT"): (40.6916, -112.0011),
    ("Columbia", "MD"): (39.2037, -76.8610), ("Bridgeport", "CT"): (41.1865, -73.1952),
    ("Paso Robles", "CA"): (35.6267, -120.6910), ("Scranton", "PA"): (41.4090, -75.6624),
    ("Bethel", "NY"): (41.6693, -74.9260), ("Council Bluffs", "IA"): (41.2619, -95.8608),
}

# ── Snowflake Connection ─────────────────────────────────────────────────────

@st.cache_resource
def get_connection():
    if "snowflake" in st.secrets:
        sf = st.secrets["snowflake"]
    else:
        sf = st.secrets
    return snowflake.connector.connect(
        account=sf["account"],
        user=sf["user"],
        password=sf["password"],
        warehouse=sf["warehouse"],
        database=sf["database"],
        schema=sf["schema"],
        role=sf["role"],
    )


@st.cache_data(ttl=600)
def run_query(query):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    return pd.DataFrame(data, columns=columns)


def geocode(city, state):
    """Look up lat/long for a city/state pair."""
    if pd.isna(city) or pd.isna(state):
        return None, None
    key = (str(city).strip(), str(state).strip())
    coords = CITY_COORDS.get(key)
    if coords:
        return coords
    # Try partial match on city name
    for (c, s), (lat, lon) in CITY_COORDS.items():
        if s == key[1] and key[0].lower() in c.lower():
            return lat, lon
    return None, None


# ── Load Data ────────────────────────────────────────────────────────────────

try:
    df = run_query("""
        SELECT f.EVENT_ID, f.EVENT_NAME,
               f.EVENT_DATE::VARCHAR as EVENT_DATE,
               f.EVENT_TIME,
               f.SALE_STATUS,
               f.PRICE_MIN::FLOAT as PRICE_MIN,
               f.PRICE_MAX::FLOAT as PRICE_MAX,
               f.PRICE_AVG::FLOAT as PRICE_AVG,
               f.CURRENCY,
               a.ARTIST_NAME, a.GENRE,
               a.MONTHLY_LISTENERS::FLOAT as MONTHLY_LISTENERS,
               a.SPOTIFY_URL,
               v.VENUE_NAME, v.CITY, v.STATE,
               d.DAY_NAME, d.MONTH_NAME,
               d.YEAR::INT as YEAR,
               d.QUARTER::INT as QUARTER,
               CASE WHEN d.IS_WEEKEND THEN 'Weekend' ELSE 'Weekday' END as IS_WEEKEND
        FROM RAW_MARTS.FACT_EVENTS f
        LEFT JOIN RAW_MARTS.DIM_ARTISTS a ON f.ARTIST_KEY = a.ARTIST_KEY
        LEFT JOIN RAW_MARTS.DIM_VENUES v ON f.VENUE_KEY = v.VENUE_KEY
        LEFT JOIN RAW_MARTS.DIM_DATES d ON f.DATE_KEY = d.DATE_KEY
    """)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Add geocoding
coords = df.apply(lambda r: geocode(r["CITY"], r["STATE"]), axis=1)
df["lat"] = coords.apply(lambda x: x[0] if x else None)
df["lon"] = coords.apply(lambda x: x[1] if x else None)

# ── Title ────────────────────────────────────────────────────────────────────

st.title("Live Music Analytics")
st.caption("Combining Ticketmaster events with Spotify streaming data for entertainment BI insights")

# ── Tabs ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", "Pricing Analytics", "Artist Insights", "Venues & Geography", "Time Trends"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
    st.header("At a Glance")

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", f"{df['EVENT_ID'].nunique():,}")
    col2.metric("Unique Artists", f"{df['ARTIST_NAME'].nunique():,}")
    col3.metric("Unique Venues", f"{df['VENUE_NAME'].nunique():,}")
    priced = df[df["PRICE_AVG"].notna() & (df["PRICE_AVG"] > 0)]
    avg_p = priced["PRICE_AVG"].mean() if not priced.empty else None
    col4.metric("Avg Ticket Price", f"${avg_p:,.0f}" if avg_p else "N/A")

    st.divider()

    # Top 10s
    col_left, col_mid, col_right = st.columns(3)

    with col_left:
        st.subheader("Top 10 Genres")
        top_genres = df.groupby("GENRE").size().reset_index(name="Events").sort_values("Events", ascending=False).head(10)
        st.dataframe(top_genres, use_container_width=True, hide_index=True)

    with col_mid:
        st.subheader("Top 10 Artists")
        top_artists = df.groupby("ARTIST_NAME").agg(
            Events=("EVENT_ID", "count"),
            Listeners=("MONTHLY_LISTENERS", "first")
        ).reset_index().sort_values("Events", ascending=False).head(10)
        top_artists["Listeners"] = top_artists["Listeners"].apply(
            lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—"
        )
        st.dataframe(top_artists, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("Top 10 Venues")
        top_venues = df.groupby("VENUE_NAME").agg(
            Events=("EVENT_ID", "count"),
            City=("CITY", "first"),
            State=("STATE", "first")
        ).reset_index().sort_values("Events", ascending=False).head(10)
        st.dataframe(top_venues, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: PRICING ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.header("Pricing Analytics")

    priced_df = df[df["PRICE_AVG"].notna() & (df["PRICE_AVG"] > 0)].copy()

    if priced_df.empty:
        st.info("No pricing data available.")
    else:
        # Price by genre
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Average Ticket Price by Genre")
            price_genre = (
                priced_df.groupby("GENRE")["PRICE_AVG"]
                .mean()
                .reset_index()
                .sort_values("PRICE_AVG", ascending=True)
            )
            st.bar_chart(price_genre, x="GENRE", y="PRICE_AVG", horizontal=True)

        with col2:
            st.subheader("Price Distribution")
            st.bar_chart(
                priced_df["PRICE_AVG"]
                .apply(lambda x: f"${int(x // 25 * 25)}-${int(x // 25 * 25 + 25)}")
                .value_counts()
                .sort_index()
                .reset_index()
                .rename(columns={"index": "Range", "PRICE_AVG": "Range", "count": "Events"}),
                x="Range", y="Events"
            )

        st.divider()

        # Streaming vs ticket pricing
        st.subheader("Streaming Popularity vs Ticket Pricing")
        st.caption("Do artists with more Spotify listeners command higher ticket prices?")

        artist_pricing = (
            priced_df.groupby("ARTIST_NAME")
            .agg(
                avg_price=("PRICE_AVG", "mean"),
                monthly_listeners=("MONTHLY_LISTENERS", "first"),
                events=("EVENT_ID", "count"),
            )
            .reset_index()
        )
        artist_pricing = artist_pricing[
            artist_pricing["monthly_listeners"].notna() & (artist_pricing["monthly_listeners"] > 0)
        ]

        if not artist_pricing.empty:
            st.scatter_chart(artist_pricing, x="monthly_listeners", y="avg_price")
            st.caption("X = Spotify monthly listeners, Y = average ticket price")

        st.divider()

        # Revenue opportunity combos
        st.subheader("Top Revenue Opportunities")
        st.caption("Artist + venue + market combos ranked by estimated revenue potential (avg price x event count x streaming signal)")

        combos = (
            priced_df.groupby(["ARTIST_NAME", "VENUE_NAME", "CITY", "STATE"])
            .agg(
                events=("EVENT_ID", "count"),
                avg_price=("PRICE_AVG", "mean"),
                listeners=("MONTHLY_LISTENERS", "first"),
            )
            .reset_index()
        )
        combos["est_revenue"] = combos["avg_price"] * combos["events"]
        combos["listeners"] = combos["listeners"].apply(
            lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—"
        )
        combos["avg_price"] = combos["avg_price"].apply(lambda x: f"${x:,.0f}")
        combos = combos.sort_values("est_revenue", ascending=False).head(15)
        combos["est_revenue"] = combos["est_revenue"].apply(lambda x: f"${x:,.0f}")
        combos.columns = ["Artist", "Venue", "City", "State", "Events", "Avg Price", "Listeners", "Est Revenue"]
        st.dataframe(combos, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ARTIST INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.header("Artist Insights")

    # Artist search
    artists_list = sorted(df["ARTIST_NAME"].dropna().unique().tolist())
    selected_artist = st.selectbox("Search for an artist", ["All Artists"] + artists_list)

    if selected_artist != "All Artists":
        adf = df[df["ARTIST_NAME"] == selected_artist]

        # Artist card
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Artist", selected_artist)
        genre = adf["GENRE"].mode().iloc[0] if not adf["GENRE"].mode().empty else "Unknown"
        col2.metric("Genre", genre)
        listeners = adf["MONTHLY_LISTENERS"].iloc[0] if not adf.empty else 0
        col3.metric("Spotify Listeners", f"{listeners:,.0f}" if pd.notna(listeners) and listeners > 0 else "N/A")
        col4.metric("Live Events", f"{adf['EVENT_ID'].nunique()}")

        st.divider()

        st.subheader(f"Events for {selected_artist}")
        event_table = adf[["EVENT_NAME", "VENUE_NAME", "CITY", "STATE", "EVENT_DATE", "PRICE_AVG"]].copy()
        event_table["PRICE_AVG"] = event_table["PRICE_AVG"].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "—"
        )
        event_table.columns = ["Event", "Venue", "City", "State", "Date", "Avg Price"]
        st.dataframe(event_table, use_container_width=True, hide_index=True)

    else:
        # Scatter: listeners vs event count
        st.subheader("Streaming Popularity vs Live Event Count")
        st.caption("**Diagnostic:** Do streaming-popular artists have more live events?")

        artist_stats = (
            df.groupby("ARTIST_NAME")
            .agg(
                event_count=("EVENT_ID", "count"),
                monthly_listeners=("MONTHLY_LISTENERS", "first"),
                genre=("GENRE", "first"),
            )
            .reset_index()
        )
        artist_stats = artist_stats[
            artist_stats["monthly_listeners"].notna() & (artist_stats["monthly_listeners"] > 0)
        ]

        if not artist_stats.empty:
            st.scatter_chart(artist_stats, x="monthly_listeners", y="event_count", color="genre")
            st.caption("Each dot is an artist colored by genre. X = Spotify listeners, Y = number of live events.")

        st.divider()

        # Untapped opportunities
        st.subheader("Untapped Opportunities")
        st.caption("Artists with high streaming popularity but few live events — potential booking targets")

        all_artists = (
            df.groupby("ARTIST_NAME")
            .agg(
                events=("EVENT_ID", "count"),
                listeners=("MONTHLY_LISTENERS", "first"),
                genre=("GENRE", "first"),
            )
            .reset_index()
        )
        all_artists = all_artists[
            all_artists["listeners"].notna() & (all_artists["listeners"] > 0)
        ].copy()

        if not all_artists.empty:
            median_events = all_artists["events"].median()
            median_listeners = all_artists["listeners"].median()
            untapped = all_artists[
                (all_artists["listeners"] > median_listeners) & (all_artists["events"] <= median_events)
            ].sort_values("listeners", ascending=False).head(10)
            untapped["listeners"] = untapped["listeners"].apply(lambda x: f"{x:,.0f}")
            untapped.columns = ["Artist", "Events", "Spotify Listeners", "Genre"]
            st.dataframe(untapped, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: VENUES & GEOGRAPHY
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.header("Venues & Geography")

    # Map
    st.subheader("Event Hotspot Map")
    map_data = (
        df[df["lat"].notna()]
        .groupby(["CITY", "STATE", "lat", "lon"])
        .agg(events=("EVENT_ID", "count"))
        .reset_index()
    )

    if not map_data.empty:
        # Scale dot sizes
        map_data["size"] = map_data["events"] * 50
        st.map(map_data, latitude="lat", longitude="lon", size="size")
    else:
        st.info("No geocoded event locations available.")

    st.divider()

    # State/city search
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Events by State")
        state_counts = df.groupby("STATE").size().reset_index(name="Events").sort_values("Events", ascending=False)
        st.bar_chart(state_counts, x="STATE", y="Events")

    with col2:
        st.subheader("Top Venues")
        venue_stats = (
            df.groupby(["VENUE_NAME", "CITY", "STATE"])
            .agg(Events=("EVENT_ID", "count"), Avg_Price=("PRICE_AVG", "mean"))
            .reset_index()
            .sort_values("Events", ascending=False)
            .head(15)
        )
        venue_stats["Avg_Price"] = venue_stats["Avg_Price"].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "—"
        )
        venue_stats.columns = ["Venue", "City", "State", "Events", "Avg Price"]
        st.dataframe(venue_stats, use_container_width=True, hide_index=True)

    st.divider()

    # Market profiles
    st.subheader("Market Profiles")
    st.caption("Select a state to see its market profile — genre mix, avg pricing, and top artists")

    states_list = sorted(df["STATE"].dropna().unique().tolist())
    selected_state = st.selectbox("Select a state", states_list)

    if selected_state:
        state_df = df[df["STATE"] == selected_state]

        col1, col2, col3 = st.columns(3)
        col1.metric("Events in Market", f"{state_df['EVENT_ID'].nunique():,}")
        col2.metric("Venues", f"{state_df['VENUE_NAME'].nunique():,}")
        state_priced = state_df[state_df["PRICE_AVG"].notna() & (state_df["PRICE_AVG"] > 0)]
        state_avg = state_priced["PRICE_AVG"].mean() if not state_priced.empty else None
        col3.metric("Avg Ticket Price", f"${state_avg:,.0f}" if state_avg else "N/A")

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("**Genre Mix**")
            genre_mix = state_df.groupby("GENRE").size().reset_index(name="Events").sort_values("Events", ascending=False)
            st.bar_chart(genre_mix, x="GENRE", y="Events")

        with col_right:
            st.markdown("**Top Artists in Market**")
            market_artists = (
                state_df.groupby("ARTIST_NAME")
                .agg(Events=("EVENT_ID", "count"), Listeners=("MONTHLY_LISTENERS", "first"))
                .reset_index()
                .sort_values("Events", ascending=False)
                .head(10)
            )
            market_artists["Listeners"] = market_artists["Listeners"].apply(
                lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—"
            )
            st.dataframe(market_artists, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: TIME TRENDS
# ═══════════════════════════════════════════════════════════════════════════════

with tab5:
    st.header("Time Trends")

    col1, col2 = st.columns(2)

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    with col1:
        st.subheader("Events by Day of Week")
        dow = df.groupby("DAY_NAME").size().reset_index(name="Events")
        dow["DAY_NAME"] = pd.Categorical(dow["DAY_NAME"], categories=day_order, ordered=True)
        dow = dow.sort_values("DAY_NAME").reset_index(drop=True)
        st.bar_chart(dow, x="DAY_NAME", y="Events")

    with col2:
        st.subheader("Weekend vs Weekday")
        we = df.groupby("IS_WEEKEND").size().reset_index(name="Events")
        st.bar_chart(we, x="IS_WEEKEND", y="Events")

    st.divider()

    # Day of week by genre
    st.subheader("When Do Different Genres Perform?")
    genre_dow = df.groupby(["GENRE", "DAY_NAME"]).size().reset_index(name="Events")
    genre_dow["DAY_NAME"] = pd.Categorical(genre_dow["DAY_NAME"], categories=day_order, ordered=True)
    genre_dow = genre_dow.sort_values("DAY_NAME")

    genre_select = st.selectbox("Select a genre", sorted(df["GENRE"].dropna().unique().tolist()))
    if genre_select:
        gdata = genre_dow[genre_dow["GENRE"] == genre_select]
        st.bar_chart(gdata, x="DAY_NAME", y="Events")
