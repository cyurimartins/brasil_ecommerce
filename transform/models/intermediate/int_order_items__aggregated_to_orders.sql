-- Granularidade: 1 linha por pedido.

with

items as (

    select * from {{ ref('stg_olist__order_items') }}

),

aggregated as (

    select
        order_id,
        count(*) as item_count,
        count(distinct product_id) as distinct_product_count,
        count(distinct seller_id) as distinct_seller_count,
        sum(item_price) as items_value,
        sum(freight_value) as freight_value

    from items
    group by order_id

)

select * from aggregated
