"""
Live Music Analytics Dashboard
Multi-page dashboard connecting to Snowflake mart tables.
"""

import streamlit as st
import snowflake.connector
import pandas as pd

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

# Industry benchmark: ~1-2% of monthly Spotify listeners in a region convert to ticket buyers
LISTENER_TO_BUYER_RATE = 0.01

# ── Snowflake Connection ─────────────────────────────────────────────────────

@st.cache_resource
def get_connection():
    if "snowflake" in st.secrets:
        sf = st.secrets["snowflake"]
    else:
        sf = st.secrets
    return snowflake.connector.connect(
        account=sf["account"], user=sf["user"], password=sf["password"],
        warehouse=sf["warehouse"], database=sf["database"],
        schema=sf["schema"], role=sf["role"],
    )


@st.cache_data(ttl=600)
def run_query(query):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=columns)


def geocode(city, state):
    if pd.isna(city) or pd.isna(state):
        return None, None
    key = (str(city).strip(), str(state).strip())
    coords = CITY_COORDS.get(key)
    if coords:
        return coords
    for (c, s), (lat, lon) in CITY_COORDS.items():
        if s == key[1] and key[0].lower() in c.lower():
            return lat, lon
    return None, None


# ── Load Data ────────────────────────────────────────────────────────────────

try:
    events = run_query("""
        SELECT f.EVENT_ID, f.EVENT_NAME,
               f.EVENT_DATE::VARCHAR as EVENT_DATE,
               f.EVENT_TIME, f.SALE_STATUS,
               f.PRICE_MIN::FLOAT as PRICE_MIN,
               f.PRICE_MAX::FLOAT as PRICE_MAX,
               f.PRICE_AVG::FLOAT as PRICE_AVG,
               f.CURRENCY,
               a.ARTIST_NAME, a.GENRE,
               a.MONTHLY_LISTENERS::FLOAT as MONTHLY_LISTENERS,
               a.SG_SCORE::FLOAT as SG_SCORE,
               a.SG_POPULARITY::FLOAT as SG_POPULARITY,
               v.VENUE_NAME, v.CITY, v.STATE,
               d.DAY_NAME,
               d.MONTH_NAME,
               d.MONTH_NUM::INT as MONTH_NUM,
               d.YEAR::INT as YEAR,
               d.QUARTER::INT as QUARTER,
               CASE WHEN d.IS_WEEKEND THEN 'Weekend' ELSE 'Weekday' END as IS_WEEKEND
        FROM RAW_MARTS.FACT_EVENTS f
        LEFT JOIN RAW_MARTS.DIM_ARTISTS a ON f.ARTIST_KEY = a.ARTIST_KEY
        LEFT JOIN RAW_MARTS.DIM_VENUES v ON f.VENUE_KEY = v.VENUE_KEY
        LEFT JOIN RAW_MARTS.DIM_DATES d ON f.DATE_KEY = d.DATE_KEY
    """)

    # Load Spotify data separately (not dependent on event join)
    spotify = run_query("""
        SELECT ARTIST_NAME, MONTHLY_LISTENERS::FLOAT as MONTHLY_LISTENERS
        FROM RAW_STAGING.STG_SPOTIFY_ARTISTS
        WHERE MONTHLY_LISTENERS IS NOT NULL
    """)

    # Load SeatGeek performer data separately
    seatgeek = run_query("""
        SELECT PERFORMER_NAME as ARTIST_NAME,
               SG_SCORE::FLOAT as SG_SCORE,
               SG_POPULARITY::FLOAT as SG_POPULARITY,
               UPCOMING_EVENTS::INT as SG_UPCOMING_EVENTS,
               GENRES as SG_GENRES
        FROM RAW_STAGING.STG_SEATGEEK_PERFORMERS
    """)

    # Load verified tour revenue data
    tour_rev = run_query("""
        SELECT ARTIST_NAME, TOUR_NAME, GROSS_REVENUE::FLOAT as GROSS_REVENUE,
               TICKETS_SOLD::FLOAT as TICKETS_SOLD,
               AVG_TICKET_PRICE::FLOAT as AVG_TICKET_PRICE,
               SHOWS::INT as SHOWS, TOUR_YEAR, SOURCE
        FROM RAW_STAGING.STG_TOUR_REVENUE
    """)

except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Geocode events
coords = events.apply(lambda r: geocode(r["CITY"], r["STATE"]), axis=1)
events["lat"] = coords.apply(lambda x: x[0] if x else None)
events["lon"] = coords.apply(lambda x: x[1] if x else None)

# ── Title ────────────────────────────────────────────────────────────────────

st.title("Live Music Analytics")
st.caption("Ticketmaster events + Spotify streaming + SeatGeek demand signals | Entertainment BI insights")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", "Pricing Analytics", "Artist Insights", "Venues & Geography", "Time Trends"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
    st.header("At a Glance")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Events", f"{events['EVENT_ID'].nunique():,}")
    col2.metric("Unique Artists", f"{events['ARTIST_NAME'].nunique():,}")
    col3.metric("Unique Venues", f"{events['VENUE_NAME'].nunique():,}")
    priced = events[events["PRICE_AVG"].notna() & (events["PRICE_AVG"] > 0)]
    avg_p = priced["PRICE_AVG"].mean() if not priced.empty else None
    col4.metric("Avg Ticket Price", f"${avg_p:,.0f}" if avg_p else "N/A")
    col5.metric("Spotify Artists Tracked", f"{len(spotify)}")

    st.divider()

    col_left, col_mid, col_right = st.columns(3)

    with col_left:
        st.subheader("Top 10 Genres")
        top_genres = events.groupby("GENRE").size().reset_index(name="Events").sort_values("Events", ascending=False).head(10)
        st.dataframe(top_genres, use_container_width=True, hide_index=True)

    with col_mid:
        st.subheader("Top 10 Artists")
        top_artists = events.groupby("ARTIST_NAME").agg(
            Events=("EVENT_ID", "count")
        ).reset_index().sort_values("Events", ascending=False).head(10)
        # Merge Spotify listeners
        top_artists = top_artists.merge(spotify, on="ARTIST_NAME", how="left")
        top_artists["MONTHLY_LISTENERS"] = top_artists["MONTHLY_LISTENERS"].apply(
            lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—"
        )
        top_artists.columns = ["Artist", "Events", "Spotify Listeners"]
        st.dataframe(top_artists, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("Top 10 Venues")
        top_venues = events.groupby("VENUE_NAME").agg(
            Events=("EVENT_ID", "count"), City=("CITY", "first"), State=("STATE", "first")
        ).reset_index().sort_values("Events", ascending=False).head(10)
        st.dataframe(top_venues, use_container_width=True, hide_index=True)

    st.divider()

    # Three-signal demand leaderboard
    st.subheader("Artist Demand Signals — Three Sources")
    st.caption("Combining Spotify (streaming), SeatGeek (ticketing demand), and Ticketmaster (live events)")
    st.markdown("""
    **How to read these metrics:**
    - **Spotify Listeners** — Monthly listener count from Spotify. Higher = more streaming demand.
    - **SeatGeek Score** — A 0–1 composite rating based on ticket sales velocity, listing volume, and price trends. Closer to 1.0 = near-peak demand (e.g., almost every listed event sells aggressively).
    - **SeatGeek Popularity** — A ranking based on how often people search for an artist on SeatGeek and how many tickets are being bought/sold. Higher = more people actively looking for tickets. This is a volume signal — how much attention, not how fast tickets move.
    - **TM Events** — Number of events currently listed on Ticketmaster.
    """)

    event_counts = events.groupby("ARTIST_NAME").agg(tm_events=("EVENT_ID", "count")).reset_index()
    demand = spotify.merge(seatgeek, on="ARTIST_NAME", how="outer").merge(event_counts, on="ARTIST_NAME", how="outer")
    demand["tm_events"] = demand["tm_events"].fillna(0).astype(int)
    demand = demand.sort_values("MONTHLY_LISTENERS", ascending=False, na_position="last").head(25)

    display_demand = demand.copy()
    display_demand["MONTHLY_LISTENERS"] = display_demand["MONTHLY_LISTENERS"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "—")
    display_demand["SG_SCORE"] = display_demand["SG_SCORE"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    display_demand["SG_POPULARITY"] = display_demand["SG_POPULARITY"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—")
    display_demand = display_demand[["ARTIST_NAME", "MONTHLY_LISTENERS", "SG_SCORE", "SG_POPULARITY", "tm_events"]]
    display_demand.columns = ["Artist", "Spotify Listeners", "SeatGeek Score", "SeatGeek Popularity", "TM Events"]
    st.dataframe(display_demand, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: PRICING ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.header("Pricing Analytics")

    priced_df = events[events["PRICE_AVG"].notna() & (events["PRICE_AVG"] > 0)].copy()

    if priced_df.empty:
        st.info("No pricing data available.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Average Ticket Price by Genre")
            price_genre = (
                priced_df.groupby("GENRE")["PRICE_AVG"]
                .mean().reset_index()
                .sort_values("PRICE_AVG", ascending=True)
            )
            st.bar_chart(price_genre, x="GENRE", y="PRICE_AVG", horizontal=True)

        with col2:
            st.subheader("Price Distribution")
            bins = [0, 25, 50, 75, 100, 150, 200, 300, 500]
            labels = ["$0-25", "$25-50", "$50-75", "$75-100", "$100-150", "$150-200", "$200-300", "$300+"]
            priced_df["price_bucket"] = pd.cut(priced_df["PRICE_AVG"], bins=bins, labels=labels, right=True)
            hist = priced_df["price_bucket"].value_counts().sort_index().reset_index()
            hist.columns = ["Price Range", "Events"]
            st.bar_chart(hist, x="Price Range", y="Events")

        st.divider()

        # REAL tour revenue vs streaming revenue
        st.subheader("Streaming Revenue vs Tour Revenue — Verified Data")
        st.caption("Real tour gross from Pollstar/Billboard vs estimated Spotify streaming revenue ($0.004/stream × ~50 streams/listener/month)")

        rev_compare = tour_rev.merge(spotify, on="ARTIST_NAME", how="inner")
        if not rev_compare.empty:
            rev_compare["est_annual_streaming"] = rev_compare["MONTHLY_LISTENERS"] * 50 * 12 * 0.004
            rev_compare["tour_vs_streaming"] = rev_compare["GROSS_REVENUE"] / rev_compare["est_annual_streaming"].clip(lower=1)
            rev_compare = rev_compare.sort_values("GROSS_REVENUE", ascending=False)

            display_rev = rev_compare[["ARTIST_NAME", "TOUR_NAME", "GROSS_REVENUE", "TICKETS_SOLD", "AVG_TICKET_PRICE", "MONTHLY_LISTENERS", "est_annual_streaming", "tour_vs_streaming"]].copy()
            display_rev["GROSS_REVENUE"] = display_rev["GROSS_REVENUE"].apply(lambda x: f"${x:,.0f}")
            display_rev["TICKETS_SOLD"] = display_rev["TICKETS_SOLD"].apply(lambda x: f"{x:,.0f}")
            display_rev["AVG_TICKET_PRICE"] = display_rev["AVG_TICKET_PRICE"].apply(lambda x: f"${x:,.0f}")
            display_rev["MONTHLY_LISTENERS"] = display_rev["MONTHLY_LISTENERS"].apply(lambda x: f"{x:,.0f}")
            display_rev["est_annual_streaming"] = display_rev["est_annual_streaming"].apply(lambda x: f"${x:,.0f}")
            display_rev["tour_vs_streaming"] = display_rev["tour_vs_streaming"].apply(lambda x: f"{x:,.0f}x")
            display_rev.columns = ["Artist", "Tour", "Tour Gross", "Tickets Sold", "Avg Ticket", "Spotify Listeners", "Est. Annual Streaming Rev", "Tour / Streaming"]
            st.dataframe(display_rev, use_container_width=True, hide_index=True)
            st.caption("Sources: Pollstar, Billboard Boxscore, Touring Data. Streaming estimate: ~50 streams/listener/month × $0.004/stream × 12 months.")

        st.divider()

        # Full tour revenue table
        st.subheader("Verified Tour Revenue — All 20 Artists")
        st.caption("Real gross revenue, tickets sold, and avg ticket price from industry sources")

        tour_display = tour_rev.sort_values("GROSS_REVENUE", ascending=False).copy()
        tour_display["GROSS_REVENUE"] = tour_display["GROSS_REVENUE"].apply(lambda x: f"${x:,.0f}")
        tour_display["TICKETS_SOLD"] = tour_display["TICKETS_SOLD"].apply(lambda x: f"{x:,.0f}")
        tour_display["AVG_TICKET_PRICE"] = tour_display["AVG_TICKET_PRICE"].apply(lambda x: f"${x:,.0f}")
        tour_display.columns = ["Artist", "Tour", "Gross Revenue", "Tickets Sold", "Avg Ticket", "Shows", "Year", "Source"]
        st.dataframe(tour_display, use_container_width=True, hide_index=True)

        st.divider()

        # Smaller acts with TM pricing
        st.subheader("Ticketmaster Pricing — Smaller Acts")
        st.caption("Events where Ticketmaster exposes pricing through the public API (24% of events)")

        combos = (
            priced_df.groupby(["ARTIST_NAME", "VENUE_NAME", "CITY", "STATE"])
            .agg(events=("EVENT_ID", "count"), avg_price=("PRICE_AVG", "mean"))
            .reset_index()
        )
        combos["est_revenue"] = combos["avg_price"] * combos["events"] * 2000
        combos = combos.sort_values("est_revenue", ascending=False).head(15)

        display_combos = combos[["ARTIST_NAME", "VENUE_NAME", "CITY", "STATE", "events", "avg_price", "est_revenue"]].copy()
        display_combos["avg_price"] = display_combos["avg_price"].apply(lambda x: f"${x:,.0f}")
        display_combos["est_revenue"] = display_combos["est_revenue"].apply(lambda x: f"${x:,.0f}")
        display_combos.columns = ["Artist", "Venue", "City", "State", "Events", "Avg Price", "Est. Revenue"]
        st.dataframe(display_combos, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ARTIST INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.header("Artist Insights")

    # Combine all known artists
    event_artists = events[["ARTIST_NAME"]].dropna().drop_duplicates()
    all_known = pd.concat([event_artists, spotify[["ARTIST_NAME"]]]).drop_duplicates().sort_values("ARTIST_NAME")
    artists_list = all_known["ARTIST_NAME"].tolist()

    selected_artist = st.selectbox("Search for an artist", ["All Artists"] + artists_list)

    if selected_artist != "All Artists":
        adf = events[events["ARTIST_NAME"] == selected_artist]
        sp_row = spotify[spotify["ARTIST_NAME"].str.lower() == selected_artist.lower()]
        sg_row = seatgeek[seatgeek["ARTIST_NAME"].str.lower() == selected_artist.lower()]

        listeners = sp_row["MONTHLY_LISTENERS"].iloc[0] if not sp_row.empty else None
        sg_score = sg_row["SG_SCORE"].iloc[0] if not sg_row.empty and pd.notna(sg_row["SG_SCORE"].iloc[0]) else None
        sg_pop = sg_row["SG_POPULARITY"].iloc[0] if not sg_row.empty and pd.notna(sg_row["SG_POPULARITY"].iloc[0]) else None
        num_events = adf["EVENT_ID"].nunique()
        genre = adf["GENRE"].mode().iloc[0] if not adf.empty and not adf["GENRE"].mode().empty else "—"
        if genre == "—" and not sg_row.empty:
            sg_genres = sg_row["SG_GENRES"].iloc[0]
            genre = sg_genres if pd.notna(sg_genres) else "—"
        avg_ticket = adf[adf["PRICE_AVG"] > 0]["PRICE_AVG"].mean() if not adf.empty else None

        # Artist card — 3 signal metrics
        st.caption("**SeatGeek Score:** 0–1 rating based on ticket sales velocity and price trends (closer to 1 = near-peak demand) | **SeatGeek Popularity:** ranking by search volume and ticket activity (higher = more attention)")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Genre", genre)
        col2.metric("Spotify Listeners", f"{listeners:,.0f}" if listeners else "N/A")
        col3.metric("SeatGeek Score", f"{sg_score:.2f}" if sg_score else "N/A")
        col4.metric("Live Events", f"{num_events}")
        col5.metric("Avg Ticket Price", f"${avg_ticket:,.0f}" if avg_ticket else "Dynamic Pricing")
        est_buyers = listeners * LISTENER_TO_BUYER_RATE if listeners else None
        col6.metric("Est. Ticket Buyers (1%)", f"{est_buyers:,.0f}" if est_buyers else "N/A")

        # Show verified tour revenue if available
        artist_tour = tour_rev[tour_rev["ARTIST_NAME"].str.lower() == selected_artist.lower()]
        if not artist_tour.empty:
            st.divider()
            st.subheader("Verified Tour Revenue")
            t = artist_tour.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Tour Gross", f"${t['GROSS_REVENUE']:,.0f}")
            col2.metric("Tickets Sold", f"{t['TICKETS_SOLD']:,.0f}")
            col3.metric("Avg Ticket Price", f"${t['AVG_TICKET_PRICE']:,.0f}")
            col4.metric("Shows", f"{t['SHOWS']}")
            st.caption(f"**{t['TOUR_NAME']}** ({t['TOUR_YEAR']}) — Source: {t['SOURCE']}")

            if listeners:
                st.divider()
                st.subheader("Streaming vs Live Revenue")
                est_annual_streaming = listeners * 50 * 12 * 0.004
                col1, col2, col3 = st.columns(3)
                col1.metric("Tour Gross Revenue", f"${t['GROSS_REVENUE']:,.0f}")
                col2.metric("Est. Annual Streaming Rev", f"${est_annual_streaming:,.0f}", help="~50 streams/listener/month × $0.004 × 12 months")
                ratio = t['GROSS_REVENUE'] / max(est_annual_streaming, 1)
                col3.metric("Tour / Streaming Ratio", f"{ratio:,.0f}x", help="How many years of streaming revenue = one tour")

        elif listeners and avg_ticket:
            st.divider()
            st.subheader("Estimated Revenue Potential")
            est_event_rev = avg_ticket * 5000
            est_streaming_monthly = listeners * 50 * 0.004
            col1, col2, col3 = st.columns(3)
            col1.metric("Est. Revenue per Event", f"${est_event_rev:,.0f}", help="Assumes ~5,000 tickets sold")
            col2.metric("Est. Monthly Streaming Rev", f"${est_streaming_monthly:,.0f}", help="~50 streams/listener x $0.004")
            col3.metric("Streaming-to-Live Multiplier", f"{est_event_rev / max(est_streaming_monthly, 1):,.1f}x")

        if num_events > 0:
            st.divider()
            st.subheader(f"Events for {selected_artist}")
            event_table = adf[["EVENT_NAME", "VENUE_NAME", "CITY", "STATE", "EVENT_DATE", "PRICE_AVG"]].copy()
            event_table["PRICE_AVG"] = event_table["PRICE_AVG"].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "—"
            )
            event_table.columns = ["Event", "Venue", "City", "State", "Date", "Avg Price"]
            st.dataframe(event_table, use_container_width=True, hide_index=True)
        elif listeners:
            st.info(f"{selected_artist} has {listeners:,.0f} monthly listeners but no live events in our data — potential booking opportunity.")

    else:
        # Scatter: all Spotify artists with event counts
        st.subheader("Streaming Popularity vs Live Event Count")
        st.caption("**Diagnostic:** Do streaming-popular artists have more live events? Artists with high listeners but few events are untapped opportunities.")

        event_counts = events.groupby("ARTIST_NAME").agg(event_count=("EVENT_ID", "count")).reset_index()
        event_counts["_merge_key"] = event_counts["ARTIST_NAME"].str.strip().str.lower()
        spotify_copy = spotify.copy()
        spotify_copy["_merge_key"] = spotify_copy["ARTIST_NAME"].str.strip().str.lower()
        scatter_data = spotify_copy.merge(event_counts.drop(columns=["ARTIST_NAME"]), on="_merge_key", how="left").drop(columns=["_merge_key"]).fillna({"event_count": 0})

        # Debug: show match rates
        matched = scatter_data[scatter_data["event_count"] > 0]
        unmatched = scatter_data[scatter_data["event_count"] == 0]
        st.caption(f"Matched: {len(matched)} artists | Unmatched: {len(unmatched)} artists")
        if not unmatched.empty:
            with st.expander("Unmatched Spotify artists (click to debug)"):
                st.write(unmatched[["ARTIST_NAME"]].values.tolist())
                st.write("Ticketmaster artist sample:", event_counts["ARTIST_NAME"].head(20).tolist())

        if not scatter_data.empty:
            st.scatter_chart(scatter_data, x="MONTHLY_LISTENERS", y="event_count")
            st.caption("X-axis: Monthly Spotify Listeners | Y-axis: Number of Live Events in Dataset. Each dot is one artist. Artists near Y=0 with high X values represent untapped booking opportunities.")

        st.divider()

        # Untapped opportunities
        st.subheader("Untapped Booking Opportunities")
        st.caption("Spotify artists with high streaming but no/few live events in our data")

        if not scatter_data.empty:
            untapped = scatter_data[scatter_data["event_count"] <= 1].sort_values("MONTHLY_LISTENERS", ascending=False)
            untapped["est_buyers"] = (untapped["MONTHLY_LISTENERS"] * LISTENER_TO_BUYER_RATE).apply(lambda x: f"{x:,.0f}")
            untapped["MONTHLY_LISTENERS"] = untapped["MONTHLY_LISTENERS"].apply(lambda x: f"{x:,.0f}")
            untapped.columns = ["Artist", "Monthly Listeners", "Live Events", "Est. Ticket Buyers (1%)"]
            st.dataframe(untapped, use_container_width=True, hide_index=True)

        st.divider()

        # Full artist comparison table
        st.subheader("Full Artist Comparison")
        all_compare = events.groupby("ARTIST_NAME").agg(
            events=("EVENT_ID", "count"),
            avg_price=("PRICE_AVG", "mean"),
            genres=("GENRE", "first"),
            states=("STATE", lambda x: ", ".join(sorted(x.dropna().unique())))
        ).reset_index().merge(spotify, on="ARTIST_NAME", how="outer")

        all_compare["MONTHLY_LISTENERS"] = all_compare["MONTHLY_LISTENERS"].apply(
            lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—"
        )
        all_compare["avg_price"] = all_compare["avg_price"].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "—"
        )
        all_compare["events"] = all_compare["events"].fillna(0).astype(int)
        all_compare = all_compare.sort_values("events", ascending=False).head(30)
        all_compare.columns = ["Artist", "Events", "Avg Price", "Genre", "Markets", "Spotify Listeners"]
        st.dataframe(all_compare, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: VENUES & GEOGRAPHY
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.header("Venues & Geography")

    # Map
    st.subheader("Event Hotspot Map")
    map_data = (
        events[events["lat"].notna()]
        .groupby(["CITY", "STATE", "lat", "lon"])
        .agg(events=("EVENT_ID", "count"))
        .reset_index()
    )

    if not map_data.empty:
        import pydeck as pdk

        max_events = map_data["events"].max()
        # Color gradient: light (few events) → red (many events)
        map_data["color"] = map_data["events"].apply(lambda x: [
            int(x / max_events * 220 + 35),
            int((1 - x / max_events) * 120),
            int((1 - x / max_events) * 80),
            200
        ])
        map_data["size"] = map_data["events"] * 300 + 500

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data,
            get_position=["lon", "lat"],
            get_radius="size",
            get_fill_color="color",
            pickable=True,
            radius_min_pixels=5,
            radius_max_pixels=50,
        )

        view = pdk.ViewState(latitude=39.5, longitude=-98.35, zoom=3.3, pitch=0)

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view,
            map_style="mapbox://styles/mapbox/dark-v10",
            tooltip={"text": "{CITY}, {STATE}\n{events} events"},
        ))
        st.caption("Dot size and color intensity = number of events. Red = high concentration, light = few events.")
    else:
        st.info("No geocoded locations available.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Events by State")
        state_counts = events.groupby("STATE").size().reset_index(name="Events").sort_values("Events", ascending=False)
        st.bar_chart(state_counts, x="STATE", y="Events")

    with col2:
        st.subheader("Top Venues")
        venue_stats = (
            events.groupby(["VENUE_NAME", "CITY", "STATE"])
            .agg(Events=("EVENT_ID", "count"), Avg_Price=("PRICE_AVG", "mean"))
            .reset_index().sort_values("Events", ascending=False).head(15)
        )
        venue_stats["Avg_Price"] = venue_stats["Avg_Price"].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "—"
        )
        venue_stats.columns = ["Venue", "City", "State", "Events", "Avg Price"]
        st.dataframe(venue_stats, use_container_width=True, hide_index=True)

    st.divider()

    # Market profiles
    st.subheader("Market Profiles")
    st.caption("Select a state to see its audience profile — genre preferences, pricing, and top artists")

    states_list = sorted(events["STATE"].dropna().unique().tolist())
    selected_state = st.selectbox("Select a state", states_list)

    if selected_state:
        state_df = events[events["STATE"] == selected_state]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Events", f"{state_df['EVENT_ID'].nunique():,}")
        col2.metric("Venues", f"{state_df['VENUE_NAME'].nunique():,}")
        col3.metric("Artists", f"{state_df['ARTIST_NAME'].nunique():,}")
        state_priced = state_df[state_df["PRICE_AVG"].notna() & (state_df["PRICE_AVG"] > 0)]
        state_avg = state_priced["PRICE_AVG"].mean() if not state_priced.empty else None
        col4.metric("Avg Ticket Price", f"${state_avg:,.0f}" if state_avg else "N/A")

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("**Genre Preferences**")
            genre_mix = state_df.groupby("GENRE").size().reset_index(name="Events").sort_values("Events", ascending=False)
            st.bar_chart(genre_mix, x="GENRE", y="Events")

        with col_right:
            st.markdown("**Top Artists in This Market**")
            market_artists = (
                state_df.groupby("ARTIST_NAME").agg(Events=("EVENT_ID", "count"))
                .reset_index().sort_values("Events", ascending=False).head(10)
                .merge(spotify, on="ARTIST_NAME", how="left")
            )
            market_artists["MONTHLY_LISTENERS"] = market_artists["MONTHLY_LISTENERS"].apply(
                lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—"
            )
            market_artists.columns = ["Artist", "Events", "Spotify Listeners"]
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
        dow = events.groupby("DAY_NAME").size().reset_index(name="Events")
        dow["DAY_NAME"] = pd.Categorical(dow["DAY_NAME"], categories=day_order, ordered=True)
        dow = dow.sort_values("DAY_NAME").reset_index(drop=True)
        st.bar_chart(dow, x="DAY_NAME", y="Events")

    with col2:
        st.subheader("Weekend vs Weekday")
        we = events.groupby("IS_WEEKEND").size().reset_index(name="Events")
        st.bar_chart(we, x="IS_WEEKEND", y="Events")

    st.divider()

    # Monthly trends
    st.subheader("Events by Month")
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly = events.groupby("MONTH_NAME").size().reset_index(name="Events")
    monthly["MONTH_NAME"] = pd.Categorical(monthly["MONTH_NAME"], categories=month_order, ordered=True)
    monthly = monthly.sort_values("MONTH_NAME").reset_index(drop=True)
    st.bar_chart(monthly, x="MONTH_NAME", y="Events")

    st.divider()

    # Genre by day of week — show all days
    st.subheader("When Do Different Genres Perform?")
    genre_select = st.selectbox("Select a genre", sorted(events["GENRE"].dropna().unique().tolist()))
    if genre_select:
        gdata = events[events["GENRE"] == genre_select].groupby("DAY_NAME").size().reset_index(name="Events")
        # Ensure all days show up
        all_days = pd.DataFrame({"DAY_NAME": day_order})
        gdata = all_days.merge(gdata, on="DAY_NAME", how="left").fillna(0)
        gdata["DAY_NAME"] = pd.Categorical(gdata["DAY_NAME"], categories=day_order, ordered=True)
        gdata = gdata.sort_values("DAY_NAME").reset_index(drop=True)
        gdata["Events"] = gdata["Events"].astype(int)
        st.bar_chart(gdata, x="DAY_NAME", y="Events")
