with venues as (
    select distinct
        venue_id,
        venue_name,
        city,
        state
    from {{ ref('stg_ticketmaster_events') }}
    where venue_id is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['venue_id']) }} as venue_key,
    venue_id,
    venue_name,
    city,
    state
from venues
