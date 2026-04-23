with events as (
    select
        *,
        row_number() over (partition by event_id order by loaded_at desc) as rn
    from {{ ref('stg_ticketmaster_events') }}
),

deduped_events as (
    select * from events where rn = 1
),

dim_artists as (
    select * from {{ ref('dim_artists') }}
),

dim_venues as (
    select * from {{ ref('dim_venues') }}
),

dim_dates as (
    select * from {{ ref('dim_dates') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['e.event_id']) }} as event_key,
    e.event_id,
    e.event_name,
    e.event_url,
    da.artist_key,
    dv.venue_key,
    dd.date_key,
    e.event_date,
    e.event_time,
    e.sale_status,
    e.price_min,
    e.price_max,
    case
        when e.price_min is not null and e.price_max is not null
        then (e.price_min + e.price_max) / 2
    end as price_avg,
    e.currency,
    e.loaded_at
from deduped_events e
left join dim_artists da
    on e.artist_id = da.tm_artist_id
left join dim_venues dv
    on e.venue_id = dv.venue_id
left join dim_dates dd
    on e.event_date = dd.event_date
