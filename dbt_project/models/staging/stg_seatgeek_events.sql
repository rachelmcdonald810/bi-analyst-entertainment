with source as (
    select *,
        row_number() over (partition by event_id order by loaded_at desc) as _rn
    from {{ source('raw', 'raw_seatgeek_events') }}
),

deduped as (
    select * from source where _rn = 1
)

select
    cast(event_id as varchar) as event_id,
    trim(event_title) as event_title,
    trim(event_url) as event_url,
    cast(event_date as date) as event_date,
    cast(event_time as varchar) as event_time,
    trim(event_type) as event_type,
    trim(initcap(performer_name)) as performer_name,
    cast(performer_id as varchar) as performer_id,
    trim(initcap(venue_name)) as venue_name,
    cast(venue_id as varchar) as venue_id,
    trim(initcap(city)) as city,
    trim(upper(state)) as state,
    cast(lowest_price as float) as lowest_price,
    cast(average_price as float) as average_price,
    cast(highest_price as float) as highest_price,
    cast(listing_count as integer) as listing_count,
    cast(event_popularity as float) as event_popularity,
    cast(event_score as float) as event_score,
    cast(loaded_at as timestamp_tz) as loaded_at
from deduped
