-- Completude: todo pedido e todo item da origem precisam chegar às tabelas fato.
-- Um inner join mal colocado poderia descartar registros silenciosamente.

with

contagens as (

    select 'pedidos' as entidade,
        (select count(*) from {{ source('olist', 'orders') }}) as origem,
        (select count(*) from {{ ref('fato_pedidos') }}) as fato

    union all

    select 'itens' as entidade,
        (select count(*) from {{ source('olist', 'order_items') }}) as origem,
        (select count(*) from {{ ref('fato_itens_pedido') }}) as fato

)

select *
from contagens
where origem <> fato
