-- Granularidade: 1 linha por prefixo de CEP.
-- A origem tem vários pontos por prefixo, grafias diferentes da mesma cidade
-- ("sao paulo" / "são paulo") e alguns pontos fora do território brasileiro.
-- Usamos a mediana (robusta a outliers) das coordenadas válidas.

with

geolocation as (

    select * from {{ ref('stg_olist__geolocation') }}

),

inside_brazil as (

    -- Bounding box do território brasileiro (extremos N/S/L/O, com folga).
    select *
    from geolocation
    where
        latitude between -33.8 and 5.3
        and longitude between -74.0 and -34.7

),

aggregated as (

    select
        zip_code_prefix,
        median(latitude) as latitude,
        median(longitude) as longitude,
        mode(state) as state,
        count(*) as source_point_count

    from inside_brazil
    group by zip_code_prefix

)

select * from aggregated
