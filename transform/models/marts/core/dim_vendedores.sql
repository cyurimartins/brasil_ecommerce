-- Granularidade: 1 linha por vendedor.

with

sellers as (

    select * from {{ ref('stg_olist__sellers') }}

),

geolocation as (

    select * from {{ ref('int_geolocation__by_zip_prefix') }}

),

final as (

    select
        sellers.seller_id as id_vendedor,
        sellers.seller_zip_code_prefix as prefixo_cep,
        sellers.seller_city as cidade,
        sellers.seller_state as uf,
        geolocation.latitude,
        geolocation.longitude

    from sellers
    left join geolocation on sellers.seller_zip_code_prefix = geolocation.zip_code_prefix

)

select * from final
