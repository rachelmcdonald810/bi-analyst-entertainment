"""
Live Music Analytics Dashboard
Multi-page dashboard connecting to Snowflake mart tables.
Three data sources: Ticketmaster, Spotify, SeatGeek + verified tour revenue.
"""

import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Live Music Analytics", layout="wide", page_icon="🎵")

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0E1117 0%, #1B3A5C 100%);
        border: 1px solid #D4A843;
        border-radius: 10px;
        padding: 15px 20px;
    }
    div[data-testid="stMetric"] label {
        color: #D4A843 !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #FAFAFA !important;
    }
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
    }
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── Color Palette ────────────────────────────────────────────────────────────

COLORS = {
    "coral": "#E8735A",
    "gold": "#D4A843",
    "blue": "#1B3A5C",
    "coral_light": "#F09A88",
    "gold_light": "#E8C97A",
    "blue_light": "#2E5C8A",
    "ombre": ["#1B3A5C", "#2E5C8A", "#D4A843", "#E8735A"],
    "ombre_warm": ["#D4A843", "#E8735A"],
    "ombre_cool": ["#1B3A5C", "#2E5C8A"],
    "categorical": ["#E8735A", "#D4A843", "#2E5C8A", "#F09A88", "#E8C97A",
                     "#1B3A5C", "#C45B3E", "#B8922F", "#4A7FB5", "#D4765A"],
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#FAFAFA"),
    margin=dict(l=20, r=20, t=40, b=20),
)

# ── US City Geocoding ────────────────────────────────────────────────────────

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
    ("Fresno", "CA"): (36.7378, -119.7871), ("Sacramento", "CA"): (38.5816, -121.4944),
    ("Atlanta", "GA"): (33.7490, -84.3880), ("Kansas City", "MO"): (39.0997, -94.5786),
    ("Omaha", "NE"): (41.2565, -95.9345), ("Raleigh", "NC"): (35.7796, -78.6382),
    ("Miami", "FL"): (25.7617, -80.1918), ("Cleveland", "OH"): (41.4993, -81.6944),
    ("Tulsa", "OK"): (36.1540, -95.9928), ("Minneapolis", "MN"): (44.9778, -93.2650),
    ("Tampa", "FL"): (27.9506, -82.4572), ("New Orleans", "LA"): (29.9511, -90.0715),
    ("Anaheim", "CA"): (33.8366, -117.9143), ("Pittsburgh", "PA"): (40.4406, -79.9959),
    ("Orlando", "FL"): (28.5383, -81.3792), ("Detroit", "MI"): (42.3314, -83.0458),
    ("Salt Lake City", "UT"): (40.7608, -111.8910), ("Boise", "ID"): (43.6150, -116.2023),
    ("Richmond", "VA"): (37.5407, -77.4360), ("Knoxville", "TN"): (35.9606, -83.9207),
    ("Inglewood", "CA"): (33.9617, -118.3531), ("Noblesville", "IN"): (40.0456, -86.0086),
    ("Bristow", "VA"): (38.7232, -77.5389), ("Tinley Park", "IL"): (41.5731, -87.7845),
    ("Maryland Heights", "MO"): (38.7131, -90.4263), ("West Palm Beach", "FL"): (26.7153, -80.0534),
    ("Burgettstown", "PA"): (40.3823, -80.3923), ("Clarkston", "MI"): (42.7356, -83.4188),
    ("Morrison", "CO"): (39.6536, -105.1911), ("Rosemont", "IL"): (41.9953, -87.8706),
    ("Wantagh", "NY"): (40.6834, -73.5101), ("Camden", "NJ"): (39.9259, -75.1196),
    ("Virginia Beach", "VA"): (36.8529, -75.9780), ("Saratoga Springs", "NY"): (43.0831, -73.7846),
    ("George", "WA"): (47.0790, -119.8522), ("Mansfield", "MA"): (42.0334, -71.2190),
}

LISTENER_TO_BUYER_RATE = 0.01

# ── Snowflake Connection ─────────────────────────────────────────────────────

@st.cache_resource
def get_connection():
    sf = st.secrets["snowflake"] if "snowflake" in st.secrets else st.secrets
    return snowflake.connector.connect(
        account=sf["account"], user=sf["user"], password=sf["password"],
        warehouse=sf["warehouse"], database=sf["database"],
        schema=sf["schema"], role=sf["role"],
    )

@st.cache_data(ttl=600)
def run_query(query):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)
    except Exception:
        # Clear cached connection and retry on auth expiry
        get_connection.clear()
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
        SELECT f.EVENT_ID, f.EVENT_NAME, f.EVENT_DATE::VARCHAR as EVENT_DATE,
               f.EVENT_TIME, f.SALE_STATUS,
               f.PRICE_MIN::FLOAT as PRICE_MIN, f.PRICE_MAX::FLOAT as PRICE_MAX,
               f.PRICE_AVG::FLOAT as PRICE_AVG, f.CURRENCY,
               a.ARTIST_NAME, a.GENRE,
               a.MONTHLY_LISTENERS::FLOAT as MONTHLY_LISTENERS,
               a.SG_SCORE::FLOAT as SG_SCORE, a.SG_POPULARITY::FLOAT as SG_POPULARITY,
               v.VENUE_NAME, v.CITY, v.STATE,
               d.DAY_NAME, d.MONTH_NAME, d.MONTH_NUM::INT as MONTH_NUM,
               d.YEAR::INT as YEAR, d.QUARTER::INT as QUARTER,
               CASE WHEN d.IS_WEEKEND THEN 'Weekend' ELSE 'Weekday' END as IS_WEEKEND
        FROM RAW_MARTS.FACT_EVENTS f
        LEFT JOIN RAW_MARTS.DIM_ARTISTS a ON f.ARTIST_KEY = a.ARTIST_KEY
        LEFT JOIN RAW_MARTS.DIM_VENUES v ON f.VENUE_KEY = v.VENUE_KEY
        LEFT JOIN RAW_MARTS.DIM_DATES d ON f.DATE_KEY = d.DATE_KEY
    """)
    spotify = run_query("""
        SELECT ARTIST_NAME, MONTHLY_LISTENERS::FLOAT as MONTHLY_LISTENERS
        FROM RAW_STAGING.STG_SPOTIFY_ARTISTS WHERE MONTHLY_LISTENERS IS NOT NULL
    """)
    seatgeek = run_query("""
        SELECT PERFORMER_NAME as ARTIST_NAME, SG_SCORE::FLOAT as SG_SCORE,
               SG_POPULARITY::FLOAT as SG_POPULARITY,
               UPCOMING_EVENTS::INT as SG_UPCOMING_EVENTS, GENRES as SG_GENRES
        FROM RAW_STAGING.STG_SEATGEEK_PERFORMERS
    """)
    tour_rev = run_query("""
        SELECT ARTIST_NAME, TOUR_NAME, GROSS_REVENUE::FLOAT as GROSS_REVENUE,
               TICKETS_SOLD::FLOAT as TICKETS_SOLD, AVG_TICKET_PRICE::FLOAT as AVG_TICKET_PRICE,
               SHOWS::INT as SHOWS, TOUR_YEAR, SOURCE
        FROM RAW_STAGING.STG_TOUR_REVENUE
    """)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

coords = events.apply(lambda r: geocode(r["CITY"], r["STATE"]), axis=1)
events["lat"] = coords.apply(lambda x: x[0] if x else None)
events["lon"] = coords.apply(lambda x: x[1] if x else None)

# ── Title ────────────────────────────────────────────────────────────────────

st.markdown("# 🎵 Live Music Analytics")
st.caption("Ticketmaster events + Spotify streaming + SeatGeek demand + verified tour revenue")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", "💰 Pricing & Revenue", "🎤 Artist Insights", "📍 Venues & Geography", "📅 Time Trends"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Events", f"{events['EVENT_ID'].nunique():,}")
    col2.metric("Unique Artists", f"{events['ARTIST_NAME'].nunique():,}")
    col3.metric("Unique Venues", f"{events['VENUE_NAME'].nunique():,}")
    priced = events[events["PRICE_AVG"].notna() & (events["PRICE_AVG"] > 0)]
    avg_p = priced["PRICE_AVG"].mean() if not priced.empty else None
    col4.metric("Avg Ticket Price", f"${avg_p:,.0f}" if avg_p else "N/A")
    col5.metric("Data Sources", "4")

    st.divider()

    # Top 10s as horizontal bar charts instead of tables
    col_left, col_mid, col_right = st.columns(3)

    with col_left:
        st.subheader("Top 10 Genres")
        top_genres = events.groupby("GENRE").size().reset_index(name="Events").sort_values("Events", ascending=True).tail(10)
        fig = px.bar(top_genres, x="Events", y="GENRE", orientation="h", color="Events",
                     color_continuous_scale=COLORS["ombre_cool"])
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False, height=350)
        fig.update_traces(texttemplate="%{x}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_mid:
        st.subheader("Top 10 Artists")
        top_artists = events.groupby("ARTIST_NAME").size().reset_index(name="Events").sort_values("Events", ascending=True).tail(10)
        fig = px.bar(top_artists, x="Events", y="ARTIST_NAME", orientation="h", color="Events",
                     color_continuous_scale=COLORS["ombre_warm"])
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False, height=350)
        fig.update_traces(texttemplate="%{x}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Top 10 Venues")
        top_venues = events.groupby("VENUE_NAME").size().reset_index(name="Events").sort_values("Events", ascending=True).tail(10)
        fig = px.bar(top_venues, x="Events", y="VENUE_NAME", orientation="h", color="Events",
                     color_continuous_scale=["#1B3A5C", "#D4A843"])
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False, height=350)
        fig.update_traces(texttemplate="%{x}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Demand leaderboard
    st.subheader("Artist Demand Signals — Three Sources")
    with st.expander("What do these metrics mean?"):
        st.markdown("""
- **Spotify Listeners** — Monthly listener count from Spotify. Measures passive demand — how many people are streaming an artist's music.
- **SeatGeek Score (0–1)** — A composite rating based on ticket sales velocity, listing volume, and price trends. Closer to 1.0 = near-peak demand. This measures how aggressively tickets are selling.
- **SeatGeek Popularity** — A raw ranking based on search volume and ticket-buying activity on SeatGeek. Higher number = more people actively looking for tickets. This is a volume signal — how much attention an artist gets on the ticketing side.
- **TM Events** — Number of events currently listed on Ticketmaster. Represents live event supply.

**How to read the table:** When Spotify listeners AND SeatGeek score are both high but TM Events is low, that's the strongest signal of untapped booking demand.
""")
    event_counts = events.groupby("ARTIST_NAME").agg(tm_events=("EVENT_ID", "count")).reset_index()
    demand = spotify.merge(seatgeek, on="ARTIST_NAME", how="outer").merge(event_counts, on="ARTIST_NAME", how="outer")
    demand["tm_events"] = demand["tm_events"].fillna(0).astype(int)
    demand = demand.sort_values("MONTHLY_LISTENERS", ascending=False, na_position="last").head(20)

    display_demand = demand.copy()
    display_demand["MONTHLY_LISTENERS"] = display_demand["MONTHLY_LISTENERS"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "—")
    display_demand["SG_SCORE"] = display_demand["SG_SCORE"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    display_demand["SG_POPULARITY"] = display_demand["SG_POPULARITY"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—")
    display_demand = display_demand[["ARTIST_NAME", "MONTHLY_LISTENERS", "SG_SCORE", "SG_POPULARITY", "tm_events"]]
    display_demand.columns = ["Artist", "Spotify Listeners", "SeatGeek Score", "SeatGeek Popularity", "TM Events"]
    st.dataframe(display_demand, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: PRICING & REVENUE
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    # Tour revenue hero chart
    st.subheader("Tour Revenue — Verified from Pollstar & Billboard")
    tour_sorted = tour_rev.sort_values("GROSS_REVENUE", ascending=True)
    fig = px.bar(tour_sorted, x="GROSS_REVENUE", y="ARTIST_NAME", orientation="h",
                 color="AVG_TICKET_PRICE", color_continuous_scale=COLORS["ombre"],
                 hover_data=["TOUR_NAME", "TICKETS_SOLD", "SHOWS", "TOUR_YEAR"],
                 labels={"GROSS_REVENUE": "Tour Gross ($)", "AVG_TICKET_PRICE": "Avg Ticket ($)"})
    fig.update_layout(**PLOTLY_LAYOUT, height=600, coloraxis_colorbar=dict(title="Avg Ticket $"))
    fig.update_traces(texttemplate="$%{x:,.0f}", textposition="outside", textfont_size=10)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bar color = average ticket price. Hover for tour details. Sources: Pollstar, Billboard Boxscore, Touring Data.")

    st.divider()

    # The Conversion Case: streaming listeners → ticket buyers
    st.subheader("The Ticketing Platform's Case: Where the Money Actually Is")
    st.markdown("""
    Streaming builds the audience. **Live events capture the revenue.** This chart is the pitch
    a ticketing platform makes to artists, managers, and promoters: *your streaming listeners are
    worth far more as ticket buyers than as streamers — and we're the platform that converts them.*
    """)

    rev_compare = tour_rev.merge(spotify, on="ARTIST_NAME", how="inner")
    if not rev_compare.empty:
        rev_compare["est_annual_streaming"] = rev_compare["MONTHLY_LISTENERS"] * 50 * 12 * 0.004
        rev_compare["revenue_multiplier"] = (rev_compare["GROSS_REVENUE"] / rev_compare["est_annual_streaming"].clip(lower=1)).round(0).astype(int)
        rev_compare["conversion_rate"] = ((rev_compare["TICKETS_SOLD"] / rev_compare["MONTHLY_LISTENERS"]) * 100).round(1)
        rev_compare = rev_compare.sort_values("GROSS_REVENUE", ascending=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Tour Gross (verified)", y=rev_compare["ARTIST_NAME"],
            x=rev_compare["GROSS_REVENUE"], orientation="h",
            marker_color=COLORS["coral"],
            text=rev_compare["GROSS_REVENUE"].apply(lambda x: f"${x/1e6:,.0f}M"),
            textposition="outside", textfont_size=14))
        fig.add_trace(go.Bar(
            name="Est. Annual Streaming Rev", y=rev_compare["ARTIST_NAME"],
            x=rev_compare["est_annual_streaming"], orientation="h",
            marker_color=COLORS["gold"],
            text=rev_compare["est_annual_streaming"].apply(lambda x: f"${x/1e6:,.0f}M"),
            textposition="outside", textfont_size=14))
        fig.update_layout(**PLOTLY_LAYOUT, barmode="group",
                          height=max(500, len(rev_compare) * 60),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=14)),
                          xaxis_title="Revenue ($)", xaxis=dict(tickfont=dict(size=13)),
                          yaxis=dict(tickfont=dict(size=13)))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Coral = verified tour gross (Pollstar/Billboard). Gold = estimated annual Spotify revenue (~50 streams/listener/month × $0.004 × 12 months).")

        st.divider()

        # Conversion metrics — the bargaining table
        st.subheader("Listener-to-Buyer Conversion & Revenue Multiplier")
        st.markdown("*How effectively does each artist convert streaming listeners into ticket buyers — and how much more is a ticket buyer worth than a streamer?*")

        conv = rev_compare[["ARTIST_NAME", "MONTHLY_LISTENERS", "TICKETS_SOLD", "conversion_rate", "GROSS_REVENUE", "est_annual_streaming", "revenue_multiplier"]].copy()
        conv = conv.sort_values("revenue_multiplier", ascending=False)

        # KPI callouts for the top artist
        top = conv.iloc[0]
        col1, col2, col3 = st.columns(3)
        col1.metric("Highest Multiplier", f"{top['ARTIST_NAME']}", f"{top['revenue_multiplier']}x tour vs streaming")
        avg_conv = conv["conversion_rate"].mean()
        col2.metric("Avg Conversion Rate", f"{avg_conv:.1f}%", "listeners → ticket buyers")
        total_tour = rev_compare["GROSS_REVENUE"].sum()
        total_stream = rev_compare["est_annual_streaming"].sum()
        col3.metric("Total Gap", f"${(total_tour - total_stream)/1e9:,.1f}B", "revenue left on table if artists only streamed")

        # Conversion table
        display_conv = conv.copy()
        display_conv["MONTHLY_LISTENERS"] = display_conv["MONTHLY_LISTENERS"].apply(lambda x: f"{x:,.0f}")
        display_conv["TICKETS_SOLD"] = display_conv["TICKETS_SOLD"].apply(lambda x: f"{x:,.0f}")
        display_conv["conversion_rate"] = display_conv["conversion_rate"].apply(lambda x: f"{x:.1f}%")
        display_conv["GROSS_REVENUE"] = display_conv["GROSS_REVENUE"].apply(lambda x: f"${x/1e6:,.0f}M")
        display_conv["est_annual_streaming"] = display_conv["est_annual_streaming"].apply(lambda x: f"${x/1e6:,.0f}M")
        display_conv["revenue_multiplier"] = display_conv["revenue_multiplier"].apply(lambda x: f"{x}x")
        display_conv.columns = ["Artist", "Monthly Listeners", "Tickets Sold", "Conversion Rate", "Tour Gross", "Est. Streaming Rev", "Revenue Multiplier"]
        st.dataframe(display_conv, use_container_width=True, hide_index=True)
        st.caption("**Conversion Rate** = tickets sold ÷ monthly listeners. **Revenue Multiplier** = tour gross ÷ est. annual streaming rev. Higher multiplier = stronger case for live.")

    st.divider()

    # Pricing from TM API
    priced_df = events[events["PRICE_AVG"].notna() & (events["PRICE_AVG"] > 0)].copy()
    if not priced_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Ticket Prices by Genre")
            price_genre = priced_df.groupby("GENRE")["PRICE_AVG"].mean().reset_index().sort_values("PRICE_AVG", ascending=True)
            fig = px.bar(price_genre, x="PRICE_AVG", y="GENRE", orientation="h",
                         color="PRICE_AVG", color_continuous_scale=COLORS["ombre_warm"])
            fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False, height=400)
            fig.update_traces(texttemplate="$%{x:,.0f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Price Distribution")
            fig = px.histogram(priced_df, x="PRICE_AVG", nbins=20, color_discrete_sequence=[COLORS["coral"]])
            fig.update_layout(**PLOTLY_LAYOUT, xaxis_title="Avg Ticket Price ($)", yaxis_title="Events", height=400)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("From Ticketmaster API — 24% of events have public pricing (mostly smaller acts)")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ARTIST INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    event_artists = events[["ARTIST_NAME"]].dropna().drop_duplicates()
    all_known = pd.concat([event_artists, spotify[["ARTIST_NAME"]]]).drop_duplicates().sort_values("ARTIST_NAME")
    selected_artist = st.selectbox("Search for an artist", ["All Artists"] + all_known["ARTIST_NAME"].tolist())

    if selected_artist != "All Artists":
        adf = events[events["ARTIST_NAME"] == selected_artist]
        sp_row = spotify[spotify["ARTIST_NAME"].str.lower() == selected_artist.lower()]
        sg_row = seatgeek[seatgeek["ARTIST_NAME"].str.lower() == selected_artist.lower()]

        listeners = sp_row["MONTHLY_LISTENERS"].iloc[0] if not sp_row.empty else None
        sg_score = sg_row["SG_SCORE"].iloc[0] if not sg_row.empty and pd.notna(sg_row["SG_SCORE"].iloc[0]) else None
        num_events = adf["EVENT_ID"].nunique()
        genre = adf["GENRE"].mode().iloc[0] if not adf.empty and not adf["GENRE"].mode().empty else "—"
        if genre == "—" and not sg_row.empty:
            sg_genres = sg_row["SG_GENRES"].iloc[0]
            genre = sg_genres if pd.notna(sg_genres) else "—"
        avg_ticket = adf[adf["PRICE_AVG"] > 0]["PRICE_AVG"].mean() if not adf.empty else None

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Genre", genre)
        col2.metric("Spotify Listeners", f"{listeners:,.0f}" if listeners else "N/A")
        col3.metric("SeatGeek Score", f"{sg_score:.2f}" if sg_score else "N/A")
        col4.metric("Live Events", f"{num_events}")
        col5.metric("Avg Ticket Price", f"${avg_ticket:,.0f}" if avg_ticket else "Dynamic Pricing")

        # Tour revenue
        artist_tour = tour_rev[tour_rev["ARTIST_NAME"].str.lower() == selected_artist.lower()]
        if not artist_tour.empty:
            st.divider()
            t = artist_tour.iloc[0]
            st.subheader(f"🏟️ {t['TOUR_NAME']} ({t['TOUR_YEAR']})")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Tour Gross", f"${t['GROSS_REVENUE']:,.0f}")
            col2.metric("Tickets Sold", f"{t['TICKETS_SOLD']:,.0f}")
            col3.metric("Avg Ticket Price", f"${t['AVG_TICKET_PRICE']:,.0f}")
            col4.metric("Shows", f"{t['SHOWS']}")

            if listeners:
                est_annual_streaming = listeners * 50 * 12 * 0.004
                ratio = t['GROSS_REVENUE'] / max(est_annual_streaming, 1)

                fig = go.Figure()
                fig.add_trace(go.Bar(x=["Tour Gross", "Est. Annual Streaming"],
                                     y=[t['GROSS_REVENUE'], est_annual_streaming],
                                     marker_color=[COLORS["coral"], COLORS["gold"]],
                                     text=[f"${t['GROSS_REVENUE']/1e6:,.0f}M", f"${est_annual_streaming/1e6:,.0f}M"],
                                     textposition="outside"))
                fig.update_layout(**PLOTLY_LAYOUT, height=300,
                                  title=f"One tour = {ratio:,.0f}x annual streaming revenue",
                                  yaxis_title="Revenue ($)")
                st.plotly_chart(fig, use_container_width=True)

        if num_events > 0:
            st.divider()
            st.subheader("Upcoming & Recent Events")
            event_table = adf[["EVENT_NAME", "VENUE_NAME", "CITY", "STATE", "EVENT_DATE", "PRICE_AVG"]].copy()
            event_table["PRICE_AVG"] = event_table["PRICE_AVG"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "Dynamic")
            event_table.columns = ["Event", "Venue", "City", "State", "Date", "Avg Price"]
            st.dataframe(event_table, use_container_width=True, hide_index=True)
        elif listeners:
            st.info(f"{selected_artist} has {listeners:,.0f} monthly listeners but no live events — potential booking opportunity.")

    else:
        # Scatter plot with plotly
        st.subheader("Streaming Popularity vs Live Event Count")
        st.caption("Do streaming-popular artists have more live events?")

        event_counts = events.groupby("ARTIST_NAME").agg(event_count=("EVENT_ID", "count")).reset_index()
        event_counts["_key"] = event_counts["ARTIST_NAME"].str.strip().str.lower()
        sp_copy = spotify.copy()
        sp_copy["_key"] = sp_copy["ARTIST_NAME"].str.strip().str.lower()
        scatter = sp_copy.merge(event_counts.drop(columns=["ARTIST_NAME"]), on="_key", how="left").drop(columns=["_key"]).fillna({"event_count": 0})

        if not scatter.empty:
            fig = px.scatter(scatter, x="MONTHLY_LISTENERS", y="event_count",
                             text="ARTIST_NAME", size="MONTHLY_LISTENERS",
                             color="event_count", color_continuous_scale=COLORS["ombre"],
                             labels={"MONTHLY_LISTENERS": "Spotify Monthly Listeners", "event_count": "Live Events"})
            fig.update_traces(textposition="top center", textfont_size=9)
            fig.update_layout(**PLOTLY_LAYOUT, height=500, coloraxis_colorbar=dict(title="Events"))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Artists at bottom-right = high streaming, few events = untapped booking opportunities")

        st.divider()

        st.subheader("Untapped Booking Opportunities")
        if not scatter.empty:
            untapped = scatter[scatter["event_count"] <= 1].sort_values("MONTHLY_LISTENERS", ascending=False)
            if not untapped.empty:
                fig = px.bar(untapped, x="MONTHLY_LISTENERS", y="ARTIST_NAME", orientation="h",
                             color="MONTHLY_LISTENERS", color_continuous_scale=COLORS["ombre_warm"])
                fig.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False, coloraxis_showscale=False,
                                  xaxis_title="Monthly Spotify Listeners")
                fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", textfont_size=10)
                st.plotly_chart(fig, use_container_width=True)
                st.caption("These artists have massive streaming audiences but 0-1 live events in our data")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: VENUES & GEOGRAPHY
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.subheader("Event Hotspot Map")
    map_data = (
        events[events["lat"].notna()]
        .groupby(["CITY", "STATE", "lat", "lon"])
        .agg(events=("EVENT_ID", "count"))
        .reset_index()
    )

    if not map_data.empty:
        fig = px.scatter_geo(
            map_data,
            lat="lat", lon="lon",
            size="events", color="events",
            hover_name="CITY",
            hover_data={"STATE": True, "events": True, "lat": False, "lon": False},
            color_continuous_scale=["#3a2a18", "#c4884d", "#ff4444"],
            size_max=40,
            scope="usa",
        )
        fig.update_layout(
            geo=dict(
                bgcolor="rgba(0,0,0,0)",
                landcolor="#2a2a45",
                countrycolor="#888888",
                subunitcolor="#555577",
                showsubunits=True,
                showcountries=True,
                showlakes=False,
                lakecolor="rgba(0,0,0,0)",
                showcoastlines=True,
                coastlinecolor="#888888",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_colorbar=dict(title="Events"),
            margin=dict(l=0, r=0, t=0, b=0),
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Dot size and color intensity = event concentration. Red = high, tan = low.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Events by State")
        state_counts = events.groupby("STATE").size().reset_index(name="Events").sort_values("Events", ascending=True).tail(15)
        fig = px.bar(state_counts, x="Events", y="STATE", orientation="h",
                     color="Events", color_continuous_scale=COLORS["ombre_cool"])
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False, height=450)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top Venues")
        venue_stats = (
            events.groupby(["VENUE_NAME", "CITY", "STATE"])
            .agg(Events=("EVENT_ID", "count")).reset_index()
            .sort_values("Events", ascending=False).head(15)
        )
        venue_stats["Label"] = venue_stats["VENUE_NAME"] + " (" + venue_stats["STATE"] + ")"
        fig = px.bar(venue_stats.sort_values("Events"), x="Events", y="Label", orientation="h",
                     color="Events", color_continuous_scale=["#1B3A5C", "#D4A843"])
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False, height=450)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Market profiles
    st.subheader("Market Profiles")
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
            genre_mix = state_df.groupby("GENRE").size().reset_index(name="Events").sort_values("Events", ascending=False).head(8)
            fig = px.pie(genre_mix, values="Events", names="GENRE", color_discrete_sequence=COLORS["categorical"],
                         title="Genre Mix")
            fig.update_layout(**PLOTLY_LAYOUT, height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            market_artists = (
                state_df.groupby("ARTIST_NAME").agg(Events=("EVENT_ID", "count"))
                .reset_index().sort_values("Events", ascending=False).head(10)
                .merge(spotify, on="ARTIST_NAME", how="left")
            )
            market_artists["MONTHLY_LISTENERS"] = market_artists["MONTHLY_LISTENERS"].apply(
                lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—"
            )
            market_artists.columns = ["Artist", "Events", "Spotify Listeners"]
            st.markdown("**Top Artists in Market**")
            st.dataframe(market_artists, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: TIME TRENDS
# ═══════════════════════════════════════════════════════════════════════════════

with tab5:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Events by Day of Week")
        dow = events.groupby("DAY_NAME").size().reset_index(name="Events")
        dow["DAY_NAME"] = pd.Categorical(dow["DAY_NAME"], categories=day_order, ordered=True)
        dow = dow.sort_values("DAY_NAME").reset_index(drop=True)
        dow["color"] = dow["DAY_NAME"].isin(["Friday", "Saturday", "Sunday"]).map({True: "Weekend", False: "Weekday"})
        fig = px.bar(dow, x="DAY_NAME", y="Events", color="color",
                     color_discrete_map={"Weekend": COLORS["coral"], "Weekday": COLORS["gold"]})
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=True, height=400, xaxis_title="", legend_title="")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Events by Month")
        month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly = events.groupby("MONTH_NAME").size().reset_index(name="Events")
        monthly["MONTH_NAME"] = pd.Categorical(monthly["MONTH_NAME"], categories=month_order, ordered=True)
        monthly = monthly.sort_values("MONTH_NAME").reset_index(drop=True)
        fig = px.bar(monthly, x="MONTH_NAME", y="Events", color="Events",
                     color_continuous_scale=["#023E8A", "#00B4D8", "#2EC4B6"])
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False, height=400, xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("When Do Different Genres Perform?")
    genre_select = st.selectbox("Select a genre", sorted(events["GENRE"].dropna().unique().tolist()))
    if genre_select:
        gdata = events[events["GENRE"] == genre_select].groupby("DAY_NAME").size().reset_index(name="Events")
        all_days = pd.DataFrame({"DAY_NAME": day_order})
        gdata = all_days.merge(gdata, on="DAY_NAME", how="left").fillna(0)
        gdata["DAY_NAME"] = pd.Categorical(gdata["DAY_NAME"], categories=day_order, ordered=True)
        gdata = gdata.sort_values("DAY_NAME").reset_index(drop=True)
        gdata["Events"] = gdata["Events"].astype(int)
        fig = px.bar(gdata, x="DAY_NAME", y="Events", color="Events",
                     color_continuous_scale=COLORS["ombre_warm"])
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, coloraxis_showscale=False, height=350, xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
