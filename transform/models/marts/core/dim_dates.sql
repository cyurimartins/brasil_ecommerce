-- Granularidade: 1 linha por dia, cobrindo todo o período do dataset.

with

date_spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2016-01-01' as date)",
        end_date="cast('2019-01-01' as date)"
    ) }}

),

final as (

    select
        cast(date_day as date) as date_day,
        year(date_day) as calendar_year,
        quarter(date_day) as calendar_quarter,
        month(date_day) as calendar_month,
        strftime(date_day, '%Y-%m') as calendar_year_month,
        case month(date_day)
            when 1 then 'janeiro' when 2 then 'fevereiro' when 3 then 'março'
            when 4 then 'abril' when 5 then 'maio' when 6 then 'junho'
            when 7 then 'julho' when 8 then 'agosto' when 9 then 'setembro'
            when 10 then 'outubro' when 11 then 'novembro' when 12 then 'dezembro'
        end as month_name,
        isodow(date_day) as day_of_week,
        case isodow(date_day)
            when 1 then 'segunda' when 2 then 'terça' when 3 then 'quarta'
            when 4 then 'quinta' when 5 then 'sexta' when 6 then 'sábado'
            when 7 then 'domingo'
        end as day_name,
        isodow(date_day) in (6, 7) as is_weekend

    from date_spine

)

select * from final
