-- Announced tour dates from Bandsintown.
-- Labeled as proxy data — does not include unannounced/private bookings.
with source as (
    select *
    from {{ source('raw', 'raw_tour_calendar') }}
    where artist_name is not null
      and event_date is not null
)

select
    trim(initcap(artist_name))          as artist_name,
    cast(event_date as date)            as event_date,
    trim(initcap(venue_name))           as venue_name,
    trim(initcap(city))                 as city,
    trim(upper(state))                  as state,
    trim(ticket_url)                    as ticket_url,
    trim(lower(source))                 as source,
    cast(loaded_at as timestamp_tz)     as loaded_at
from source
where event_date >= current_date()  -- only future events
