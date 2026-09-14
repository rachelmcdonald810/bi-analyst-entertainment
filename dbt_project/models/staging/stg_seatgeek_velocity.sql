-- Day-over-day changes in SeatGeek listing_count and event_score per event.
-- listing_velocity > 0 = demand building (more listings appearing).
-- score_velocity > 0 = event gaining traction on SeatGeek.
-- price_gap_ratio = resale avg / TM avg ticket (computed in dashboard, not here).
with snapshots as (
    select
        cast(event_id as varchar)           as event_id,
        trim(initcap(performer_name))       as performer_name,
        cast(listing_count as integer)      as listing_count,
        cast(event_score as float)          as event_score,
        cast(average_price as float)        as average_price,
        cast(loaded_at as timestamp_tz)     as loaded_at,
        cast(loaded_at as date)             as snapshot_date
    from {{ source('raw', 'raw_seatgeek_events') }}
    where event_id is not null
),

with_velocity as (
    select
        *,
        listing_count - lag(listing_count) over (
            partition by event_id order by loaded_at
        ) as listing_velocity,
        event_score - lag(event_score) over (
            partition by event_id order by loaded_at
        ) as score_velocity
    from snapshots
)

select * from with_velocity
