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
        order_status as status_pedido,
        purchase_date as data_compra,

        purchased_at as data_hora_compra,
        approved_at as data_hora_aprovacao,
        delivered_to_carrier_at as data_hora_envio_transportadora,
        delivered_to_customer_at as data_hora_entrega,
        cast(estimated_delivery_at as date) as data_entrega_prometida,

        item_count as quantidade_itens,
        distinct_seller_count as quantidade_vendedores,
        items_value as valor_itens,
        freight_value as valor_frete,
        order_value as valor_pedido,

        total_paid as valor_pago,
        payment_count as quantidade_pagamentos,
        primary_payment_type as forma_pagamento_principal,
        max_installments as quantidade_parcelas,
        has_voucher as usou_voucher,

        review_score as nota_avaliacao,
        review_count as quantidade_avaliacoes,

        is_delivered as entregue,
        approval_hours as horas_ate_aprovacao,
        delivery_days as dias_ate_entrega,
        promised_delivery_days as dias_prometidos_entrega,
        delivery_delay_days as dias_atraso_entrega,
        case
            when is_delivered then delivery_delay_days > 0
        end as atrasado

    from delivery_metrics

)

select * from final
