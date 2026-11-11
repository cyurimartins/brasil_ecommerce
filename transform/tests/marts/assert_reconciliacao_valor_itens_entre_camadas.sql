-- Reconciliação: o valor total dos itens deve ser idêntico na origem tipada
-- (staging) e nas duas tabelas fato. Detecta joins que duplicam ou perdem linhas.

with

staging as (

    select sum(item_price) as valor from {{ ref('stg_olist__order_items') }}

),

fato_pedidos as (

    select sum(valor_itens) as valor from {{ ref('fato_pedidos') }}

),

fato_itens as (

    select sum(valor_item) as valor from {{ ref('fato_itens_pedido') }}

)

select
    staging.valor as valor_staging,
    fato_pedidos.valor as valor_fato_pedidos,
    fato_itens.valor as valor_fato_itens

from staging
cross join fato_pedidos
cross join fato_itens
where
    staging.valor <> fato_pedidos.valor
    or staging.valor <> fato_itens.valor
