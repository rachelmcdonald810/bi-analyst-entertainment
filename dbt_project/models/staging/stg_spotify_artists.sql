with source as (
    select *,
        row_number() over (partition by artist_name order by loaded_at desc) as _rn
    from {{ source('raw', 'raw_spotify_artists') }}
),

deduped as (
    select * from source where _rn = 1
)

select
    -- identifiers
    cast(artist_id as varchar) as artist_id,

    -- artist details (cleaned)
    trim(initcap(artist_name)) as artist_name,
    trim(spotify_url) as spotify_url,

    -- metrics (type cast)
    cast(monthly_listeners as integer) as monthly_listeners,

    -- page metadata (cleaned)
    trim(page_title) as page_title,
    trim(page_description) as page_description,

    -- metadata
    cast(loaded_at as timestamp_tz) as loaded_at
from deduped
