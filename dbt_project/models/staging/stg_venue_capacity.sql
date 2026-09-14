-- One row per venue with capacity and tier bucketing.
with source as (
    select *,
        row_number() over (
            partition by venue_name, city, state order by loaded_at desc
        ) as _rn
    from {{ source('raw', 'raw_venue_capacity') }}
),

deduped as (
    select * from source where _rn = 1
)

select
    trim(initcap(venue_name))           as venue_name,
    trim(initcap(city))                 as city,
    trim(upper(state))                  as state,
    cast(capacity as integer)           as capacity,
    trim(lower(venue_tier))             as venue_tier,
    trim(sg_venue_id)                   as sg_venue_id,
    cast(loaded_at as timestamp_tz)     as loaded_at
from deduped
where capacity is not null and capacity > 0
