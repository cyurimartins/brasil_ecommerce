-- Granularidade: 1 linha por cliente real (customer_unique_id).
-- A Olist gera um customer_id novo a cada pedido; agrupar pelo customer_unique_id
-- é o que permite medir recompra. O endereço é o do pedido mais recente.

with

customers as (

    select * from {{ ref('stg_olist__customers') }}

),

orders as (

    select * from {{ ref('stg_olist__orders') }}

),

geolocation as (

    select * from {{ ref('int_geolocation__by_zip_prefix') }}

),

customer_orders as (

    select
        customers.customer_unique_id,
        customers.customer_zip_code_prefix,
        customers.customer_city,
        customers.customer_state,
        orders.purchased_at

    from customers
    inner join orders on customers.customer_id = orders.customer_id

),

aggregated as (

    select
        customer_unique_id,
        arg_max(customer_zip_code_prefix, purchased_at) as zip_code_prefix,
        arg_max(customer_city, purchased_at) as city,
        arg_max(customer_state, purchased_at) as state,
        min(purchased_at) as first_purchase_at,
        max(purchased_at) as last_purchase_at,
        count(*) as order_count

    from customer_orders
    group by customer_unique_id

),

final as (

    select
        aggregated.customer_unique_id,
        aggregated.zip_code_prefix,
        aggregated.city,
        aggregated.state,
        geolocation.latitude,
        geolocation.longitude,
        aggregated.first_purchase_at,
        aggregated.last_purchase_at,
        aggregated.order_count,
        aggregated.order_count > 1 as is_repeat_customer

    from aggregated
    left join geolocation on aggregated.zip_code_prefix = geolocation.zip_code_prefix

)

select * from final
