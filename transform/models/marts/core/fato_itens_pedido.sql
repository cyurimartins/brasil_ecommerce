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
            as chave_item_pedido,
        items.order_id as id_pedido,
        items.order_item_id as numero_item,
        items.product_id as id_produto,
        items.seller_id as id_vendedor,
        customers.customer_unique_id as id_cliente,
        orders.order_status as status_pedido,
        cast(orders.purchased_at as date) as data_compra,
        items.shipping_limit_at as data_hora_limite_envio,

        items.item_price as valor_item,
        items.freight_value as valor_frete,
        cast(items.item_price + items.freight_value as decimal(12, 2)) as valor_total_item,

        customers.customer_state as uf_cliente,
        sellers.seller_state as uf_vendedor,
        customers.customer_state = sellers.seller_state as mesma_uf,
        round(
            {{ haversine_km(
                'seller_geo.latitude', 'seller_geo.longitude',
                'customer_geo.latitude', 'customer_geo.longitude'
            ) }},
            1
        ) as distancia_vendedor_cliente_km

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
