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

joined as (
    select
        t.tm_artist_id,
        t.artist_name,
        t.genre,
        s.spotify_artist_id,
        s.spotify_url,
        s.monthly_listeners
    from deduped_artists t
    left join spotify_artists s
        on lower(t.artist_name) = lower(s.artist_name)
)

select
    {{ dbt_utils.generate_surrogate_key(['tm_artist_id']) }} as artist_key,
    tm_artist_id,
    artist_name,
    genre,
    spotify_artist_id,
    spotify_url,
    monthly_listeners
from joined
