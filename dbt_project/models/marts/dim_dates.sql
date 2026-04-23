with event_dates as (
    select distinct
        event_date
    from {{ ref('stg_ticketmaster_events') }}
    where event_date is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['event_date']) }} as date_key,
    event_date,
    dayofweek(event_date::date) as day_of_week,
    case dayofweek(event_date::date)
        when 0 then 'Sunday'
        when 1 then 'Monday'
        when 2 then 'Tuesday'
        when 3 then 'Wednesday'
        when 4 then 'Thursday'
        when 5 then 'Friday'
        when 6 then 'Saturday'
    end as day_name,
    month(event_date::date) as month_num,
    monthname(event_date::date) as month_name,
    year(event_date::date) as year,
    quarter(event_date::date) as quarter,
    case when dayofweek(event_date::date) in (0, 6) then true else false end as is_weekend
from event_dates
