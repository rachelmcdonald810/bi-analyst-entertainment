with source as (
    select * from {{ source('raw', 'raw_ticketmaster_events') }}
)

select
    event_id,
    event_name,
    event_url,
    event_date,
    event_time,
    sale_status,
    artist_name,
    artist_id,
    venue_name,
    venue_id,
    city,
    state,
    price_min,
    price_max,
    currency,
    genre,
    loaded_at
from source
