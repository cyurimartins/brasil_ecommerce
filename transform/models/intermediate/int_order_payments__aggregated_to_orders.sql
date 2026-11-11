-- Granularidade: 1 linha por pedido.
-- Pedidos podem ter vários pagamentos (ex.: cartão + voucher); agregar aqui evita
-- duplicar valores ao juntar pagamentos com pedidos ou itens.

with

payments as (

    select * from {{ ref('stg_olist__order_payments') }}

),

aggregated as (

    select
        order_id,
        count(*) as payment_count,
        sum(payment_value) as total_paid,
        max(payment_installments) as max_installments,
        -- Meio de pagamento de maior valor; desempate pelo primeiro pagamento.
        arg_max(payment_type, (payment_value, -payment_sequential)) as primary_payment_type,
        bool_or(payment_type = 'voucher') as has_voucher

    from payments
    group by order_id

)

select * from aggregated
