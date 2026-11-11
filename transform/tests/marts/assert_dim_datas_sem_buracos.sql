-- O calendário precisa ser contínuo: um dia faltando faria pedidos "sumirem"
-- em análises por data. Retorna linha (= falha) se houver buraco.

with

limites as (

    select
        count(*) as dias_existentes,
        date_diff('day', min(data_calendario), max(data_calendario)) + 1 as dias_esperados

    from {{ ref('dim_datas') }}

)

select *
from limites
where dias_existentes <> dias_esperados
