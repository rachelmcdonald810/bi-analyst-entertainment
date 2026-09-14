-- Full time series of Spotify listener counts — one row per artist per day.
-- Used for listener growth rate calculations and Career Arc charts.
-- Unlike stg_spotify_artists, this model does NOT deduplicate.
select
    trim(initcap(artist_name))          as artist_name,
    cast(monthly_listeners as integer)  as monthly_listeners,
    cast(loaded_at as timestamp_tz)     as loaded_at,
    cast(loaded_at as date)             as snapshot_date
from {{ source('raw', 'raw_spotify_artists') }}
where monthly_listeners is not null
  and artist_name is not null
