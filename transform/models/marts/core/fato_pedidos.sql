-- Granularidade: 1 linha por pedido.
-- Fato central: valores, pagamento, avaliação e indicadores de entrega (SLA).

with

orders as (

    select * from {{ ref('stg_olist__orders') }}

),

customers as (

    select * from {{ ref('stg_olist__customers') }}

),

items as (

    select * from {{ ref('int_order_items__aggregated_to_orders') }}

),

payments as (

    select * from {{ ref('int_order_payments__aggregated_to_orders') }}

),

reviews as (

    select * from {{ ref('int_order_reviews__latest_per_order') }}

),

joined as (

    select
        orders.order_id,
        customers.customer_unique_id,
        orders.customer_id,
        customers.customer_state,
        orders.order_status,
        cast(orders.purchased_at as date) as purchase_date,

        orders.purchased_at,
        orders.approved_at,
        orders.delivered_to_carrier_at,
        orders.delivered_to_customer_at,
        orders.estimated_delivery_at,

        coalesce(items.item_count, 0) as item_count,
        coalesce(items.distinct_seller_count, 0) as distinct_seller_count,
        coalesce(items.items_value, 0) as items_value,
        coalesce(items.freight_value, 0) as freight_value,
        coalesce(items.items_value, 0) + coalesce(items.freight_value, 0) as order_value,

        payments.total_paid,
        payments.payment_count,
        payments.primary_payment_type,
        payments.max_installments,
        coalesce(payments.has_voucher, false) as has_voucher,

        reviews.review_score,
        coalesce(reviews.review_count, 0) as review_count

    from orders
    inner join customers on orders.customer_id = customers.customer_id
    left join items on orders.order_id = items.order_id
    left join payments on orders.order_id = payments.order_id
    left join reviews on orders.order_id = reviews.order_id

),

delivery_metrics as (

    select
        *,

        order_status = 'delivered' and delivered_to_customer_at is not null as is_delivered,

        date_diff('hour', purchased_at, approved_at) as approval_hours,
        date_diff('day', purchase_date, cast(delivered_to_customer_at as date)) as delivery_days,
        date_diff(
            'day', purchase_date, cast(estimated_delivery_at as date)
        ) as promised_delivery_days,

        -- Positivo = atraso; negativo = entregue antes do prometido. Comparação no
        -- nível de dia, pois a data prometida não tem hora (00:00).
        date_diff(
            'day', cast(estimated_delivery_at as date), cast(delivered_to_customer_at as date)
        ) as delivery_delay_days

    from joined

),

final as (

    select
        order_id as id_pedido,
        customer_unique_id as id_cliente,
        customer_id as id_cliente_pedido,
        customer_state as uf_cliente,
        order_status as status_pedido,
        purchase_date as data_compra,

        purchased_at as data_hora_compra,
        approved_at as data_hora_aprovacao,
        delivered_to_carrier_at as data_hora_envio_transportadora,
        delivered_to_customer_at as data_hora_entrega,
        cast(estimated_delivery_at as date) as data_entrega_prometida,

        cast(item_count as integer) as quantidade_itens,
        cast(distinct_seller_count as integer) as quantidade_vendedores,
        cast(items_value as decimal(14, 2)) as valor_itens,
        cast(freight_value as decimal(14, 2)) as valor_frete,
        cast(order_value as decimal(14, 2)) as valor_pedido,

        cast(total_paid as decimal(14, 2)) as valor_pago,
        cast(payment_count as integer) as quantidade_pagamentos,
        primary_payment_type as forma_pagamento_principal,
        max_installments as quantidade_parcelas,
        has_voucher as usou_voucher,

        review_score as nota_avaliacao,
        cast(review_count as integer) as quantidade_avaliacoes,

        is_delivered as entregue,
        cast(approval_hours as integer) as horas_ate_aprovacao,
        cast(delivery_days as integer) as dias_ate_entrega,
        cast(promised_delivery_days as integer) as dias_prometidos_entrega,
        cast(delivery_delay_days as integer) as dias_atraso_entrega,
        case
            when is_delivered then delivery_delay_days > 0
        end as atrasado

    from delivery_metrics

)

select * from final
