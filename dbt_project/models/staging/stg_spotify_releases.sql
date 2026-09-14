-- One row per artist: their latest known release.
-- Release date is approximated as Jan 1 of the release year
-- (Spotify pages expose year only, not exact date).
with source as (
    select *,
        row_number() over (partition by artist_name order by loaded_at desc) as _rn
    from {{ source('raw', 'raw_spotify_releases') }}
),

deduped as (
    select * from source where _rn = 1
)

select
    trim(initcap(artist_name))          as artist_name,
    trim(artist_spotify_url)            as artist_spotify_url,
    trim(latest_release_title)          as latest_release_title,
    trim(initcap(release_type))         as release_type,
    cast(release_date as date)          as release_date,
    datediff('day', release_date, current_date()) as days_since_release,
    case
        when datediff('day', release_date, current_date()) <= 90 then true
        else false
    end                                 as is_recent_release,
    cast(loaded_at as timestamp_tz)     as loaded_at
from deduped
where release_date is not null
