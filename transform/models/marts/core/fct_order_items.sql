-- Granularidade: 1 linha por item de pedido.
-- Inclui a distância vendedor → cliente (linha reta), base para análises logísticas.

with

items as (

    select * from {{ ref('stg_olist__order_items') }}

),

orders as (

    select * from {{ ref('stg_olist__orders') }}

),

customers as (

    select * from {{ ref('stg_olist__customers') }}

),

sellers as (

    select * from {{ ref('stg_olist__sellers') }}

),

geolocation as (

    select * from {{ ref('int_geolocation__by_zip_prefix') }}

),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['items.order_id', 'items.order_item_id']) }}
            as order_item_key,
        items.order_id,
        items.order_item_id,
        items.product_id,
        items.seller_id,
        customers.customer_unique_id,
        orders.order_status,
        cast(orders.purchased_at as date) as purchase_date,
        items.shipping_limit_at,

        items.item_price,
        items.freight_value,
        items.item_price + items.freight_value as item_total_value,

        customers.customer_state,
        sellers.seller_state,
        customers.customer_state = sellers.seller_state as is_same_state,
        round(
            {{ haversine_km(
                'seller_geo.latitude', 'seller_geo.longitude',
                'customer_geo.latitude', 'customer_geo.longitude'
            ) }},
            1
        ) as seller_customer_distance_km

    from items
    inner join orders on items.order_id = orders.order_id
    inner join customers on orders.customer_id = customers.customer_id
    inner join sellers on items.seller_id = sellers.seller_id
    left join geolocation as seller_geo
        on sellers.seller_zip_code_prefix = seller_geo.zip_code_prefix
    left join geolocation as customer_geo
        on customers.customer_zip_code_prefix = customer_geo.zip_code_prefix

)

select * from final
