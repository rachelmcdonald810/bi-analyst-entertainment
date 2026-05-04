with source as (
    select * from {{ source('raw', 'raw_tour_revenue') }}
)

select
    trim(initcap(artist_name)) as artist_name,
    trim(tour_name) as tour_name,
    cast(gross_revenue as number) as gross_revenue,
    cast(tickets_sold as number) as tickets_sold,
    cast(avg_ticket_price as number) as avg_ticket_price,
    cast(shows as number) as shows,
    trim(tour_year) as tour_year,
    trim(source) as source,
    cast(loaded_at as timestamp_tz) as loaded_at
from source
