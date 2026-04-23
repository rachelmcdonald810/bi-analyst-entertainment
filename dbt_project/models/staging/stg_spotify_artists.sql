with source as (
    select * from {{ source('raw', 'raw_spotify_artists') }}
)

select
    artist_id,
    artist_name,
    spotify_url,
    monthly_listeners,
    page_title,
    page_description,
    loaded_at
from source
