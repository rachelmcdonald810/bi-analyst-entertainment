with ticketmaster_artists as (
    select
        artist_id as tm_artist_id,
        artist_name,
        genre,
        row_number() over (partition by artist_id order by artist_name) as rn
    from {{ ref('stg_ticketmaster_events') }}
    where artist_name is not null
      and artist_id is not null
),

deduped_artists as (
    select
        tm_artist_id,
        artist_name,
        genre
    from ticketmaster_artists
    where rn = 1
),

spotify_artists as (
    select
        artist_id as spotify_artist_id,
        artist_name,
        spotify_url,
        monthly_listeners
    from {{ ref('stg_spotify_artists') }}
),

seatgeek_performers as (
    select
        performer_id as sg_performer_id,
        performer_name,
        seatgeek_url,
        sg_score,
        sg_popularity,
        upcoming_events as sg_upcoming_events,
        genres as sg_genres
    from {{ ref('stg_seatgeek_performers') }}
),

joined as (
    select
        t.tm_artist_id,
        t.artist_name,
        t.genre,
        s.spotify_artist_id,
        s.spotify_url,
        s.monthly_listeners,
        sg.sg_performer_id,
        sg.seatgeek_url,
        sg.sg_score,
        sg.sg_popularity,
        sg.sg_upcoming_events,
        sg.sg_genres
    from deduped_artists t
    left join spotify_artists s
        on lower(t.artist_name) = lower(s.artist_name)
    left join seatgeek_performers sg
        on lower(t.artist_name) = lower(sg.performer_name)
)

select
    {{ dbt_utils.generate_surrogate_key(['tm_artist_id']) }} as artist_key,
    tm_artist_id,
    artist_name,
    genre,
    spotify_artist_id,
    spotify_url,
    monthly_listeners,
    sg_performer_id,
    seatgeek_url,
    sg_score,
    sg_popularity,
    sg_upcoming_events,
    sg_genres
from joined
