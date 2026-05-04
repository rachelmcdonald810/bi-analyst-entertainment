with source as (
    select *,
        row_number() over (partition by performer_name order by loaded_at desc) as _rn
    from {{ source('raw', 'raw_seatgeek_performers') }}
),

deduped as (
    select * from source where _rn = 1
)

select
    cast(performer_id as varchar) as performer_id,
    trim(initcap(performer_name)) as performer_name,
    trim(short_name) as short_name,
    trim(seatgeek_url) as seatgeek_url,
    cast(sg_score as float) as sg_score,
    cast(sg_popularity as float) as sg_popularity,
    cast(upcoming_events as integer) as upcoming_events,
    trim(genres) as genres,
    trim(performer_type) as performer_type,
    cast(loaded_at as timestamp_tz) as loaded_at
from deduped
where sg_score > 0.5
