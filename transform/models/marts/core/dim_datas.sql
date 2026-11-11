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
        cast(date_day as date) as data_calendario,
        cast(year(date_day) as integer) as ano,
        cast(quarter(date_day) as integer) as trimestre,
        cast(month(date_day) as integer) as mes,
        strftime(date_day, '%Y-%m') as ano_mes,
        case month(date_day)
            when 1 then 'janeiro' when 2 then 'fevereiro' when 3 then 'março'
            when 4 then 'abril' when 5 then 'maio' when 6 then 'junho'
            when 7 then 'julho' when 8 then 'agosto' when 9 then 'setembro'
            when 10 then 'outubro' when 11 then 'novembro' when 12 then 'dezembro'
        end as nome_mes,
        cast(isodow(date_day) as integer) as dia_semana,
        case isodow(date_day)
            when 1 then 'segunda' when 2 then 'terça' when 3 then 'quarta'
            when 4 then 'quinta' when 5 then 'sexta' when 6 then 'sábado'
            when 7 then 'domingo'
        end as nome_dia_semana,
        isodow(date_day) in (6, 7) as fim_de_semana

    from date_spine

)

select * from final
