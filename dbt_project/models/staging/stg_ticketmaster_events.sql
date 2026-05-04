with source as (
    select *,
        row_number() over (partition by event_id order by loaded_at desc) as _rn
    from {{ source('raw', 'raw_ticketmaster_events') }}
),

deduped as (
    select * from source where _rn = 1
)

select
    -- identifiers
    cast(event_id as varchar) as event_id,
    cast(artist_id as varchar) as artist_id,
    cast(venue_id as varchar) as venue_id,

    -- event details (cleaned)
    trim(event_name) as event_name,
    trim(event_url) as event_url,
    trim(upper(sale_status)) as sale_status,
    trim(genre) as genre,

    -- artist and venue (standardized casing)
    trim(initcap(artist_name)) as artist_name,
    trim(initcap(venue_name)) as venue_name,
    trim(initcap(city)) as city,
    trim(upper(state)) as state,

    -- dates and times (type cast)
    cast(event_date as date) as event_date,
    cast(event_time as varchar) as event_time,

    -- pricing (cast to numeric)
    cast(price_min as number(10,2)) as price_min,
    cast(price_max as number(10,2)) as price_max,
    trim(upper(currency)) as currency,

    -- metadata
    cast(loaded_at as timestamp_tz) as loaded_at
from deduped
