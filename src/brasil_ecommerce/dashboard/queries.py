"""Consultas do dashboard, isoladas da interface para serem testáveis.

Todas leem o schema ``marts`` do banco de consulta e aplicam os mesmos filtros
(período e UF do cliente no momento da compra).

Definições de negócio usadas em todo o dashboard:

* **Pedido válido:** status diferente de ``canceled`` e ``unavailable``.
* **Faturamento:** soma de ``valor_pedido`` (mercadoria + frete) dos pedidos válidos.
* **Ticket médio:** faturamento / pedidos válidos.
* **% de atraso e prazos:** calculados só sobre pedidos entregues.
"""

from dataclasses import dataclass, field
from datetime import date

import duckdb
import pandas as pd

PEDIDO_VALIDO = "status_pedido not in ('canceled', 'unavailable')"

# Faixas ordenadas, usadas como categorias nos gráficos.
FAIXAS_ATRASO = [
    "Antecipado 8+ dias",
    "Antecipado 1-7 dias",
    "No dia prometido",
    "Atraso 1-3 dias",
    "Atraso 4-7 dias",
    "Atraso 8+ dias",
]
FAIXAS_DISTANCIA = ["até 100", "100-300", "300-700", "700-1.500", "1.500+"]  # km


@dataclass(frozen=True)
class Filtros:
    """Recorte aplicado a todas as consultas. ``fim`` é exclusivo."""

    inicio: date = date(2017, 1, 1)
    fim: date = date(2018, 9, 1)
    ufs: tuple[str, ...] = field(default_factory=tuple)

    def params(self) -> dict[str, object]:
        return {"inicio": self.inicio, "fim": self.fim, "ufs": list(self.ufs)}


# Recorte comum: período + UF do cliente na compra (lista vazia = todas as UFs).
_RECORTE = """
    data_compra >= $inicio and data_compra < $fim
    and (len($ufs) = 0 or list_contains($ufs, uf_cliente))
"""


def _df(con: duckdb.DuckDBPyConnection, sql: str, filtros: Filtros) -> pd.DataFrame:
    return con.execute(sql, filtros.params()).df()


def resumo(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    """KPIs gerais em uma linha."""
    sql = f"""
        with pedidos as (
            select * from marts.fato_pedidos where {_RECORTE}
        ),
        validos as (
            select * from pedidos where {PEDIDO_VALIDO}
        ),
        compras_por_cliente as (
            select id_cliente, count(*) as n from validos group by id_cliente
        )
        select
            (select count(*) from validos) as pedidos,
            (select sum(valor_pedido) from validos) as faturamento,
            (select sum(valor_pedido) / nullif(count(*), 0) from validos) as ticket_medio,
            (select avg(atrasado::int) from pedidos where entregue) as pct_atraso,
            (select avg(dias_ate_entrega) from pedidos where entregue) as dias_entrega,
            (select avg(nota_avaliacao) from pedidos) as nota_media,
            (select count(*) from compras_por_cliente) as clientes,
            (select avg((n > 1)::int) from compras_por_cliente) as pct_recompra
    """
    return _df(con, sql, filtros)


def faturamento_mensal(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    sql = f"""
        select
            date_trunc('month', data_compra)::date as mes,
            sum(valor_pedido) as faturamento,
            count(*) as pedidos
        from marts.fato_pedidos
        where {_RECORTE} and {PEDIDO_VALIDO}
        group by 1
        order by 1
    """
    return _df(con, sql, filtros)


def top_categorias(
    con: duckdb.DuckDBPyConnection, filtros: Filtros, limite: int = 10
) -> pd.DataFrame:
    sql = f"""
        select
            replace(produtos.categoria, '_', ' ') as categoria,
            sum(itens.valor_item) as faturamento,
            count(*) as itens
        from marts.fato_itens_pedido as itens
        inner join marts.dim_produtos as produtos using (id_produto)
        where {_RECORTE} and {PEDIDO_VALIDO}
        group by 1
        order by faturamento desc
        limit {int(limite)}
    """
    return _df(con, sql, filtros)


def formas_pagamento(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    sql = f"""
        select
            case forma_pagamento_principal
                when 'credit_card' then 'Cartão de crédito'
                when 'boleto' then 'Boleto'
                when 'voucher' then 'Voucher'
                when 'debit_card' then 'Cartão de débito'
                else 'Não informado'
            end as forma_pagamento,
            count(*) as pedidos,
            count(*) / sum(count(*)) over () as participacao
        from marts.fato_pedidos
        where {_RECORTE} and {PEDIDO_VALIDO}
        group by 1
        order by pedidos desc
    """
    return _df(con, sql, filtros)


def prazo_mensal(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    """Prazo prometido x realizado (dias), em formato longo para o gráfico de linhas."""
    sql = f"""
        with mensal as (
            select
                date_trunc('month', data_compra)::date as mes,
                avg(dias_prometidos_entrega) as prometido,
                avg(dias_ate_entrega) as realizado
            from marts.fato_pedidos
            where {_RECORTE} and entregue
            group by 1
        )
        unpivot mensal on prometido, realizado into name serie value dias
        order by mes, serie
    """
    df = _df(con, sql, filtros)
    df["serie"] = df["serie"].map({"prometido": "Prazo prometido", "realizado": "Prazo realizado"})
    return df


def atraso_por_uf(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    sql = f"""
        select
            uf_cliente as uf,
            count(*) as pedidos_entregues,
            avg(atrasado::int) as pct_atraso,
            avg(dias_ate_entrega) as dias_entrega
        from marts.fato_pedidos
        where {_RECORTE} and entregue
        group by 1
        order by pct_atraso desc
    """
    return _df(con, sql, filtros)


def logistica_por_distancia(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    sql = """
        with itens as (
            select
                itens.*,
                pedidos.dias_ate_entrega,
                case
                    when itens.distancia_vendedor_cliente_km < 100 then 1
                    when itens.distancia_vendedor_cliente_km < 300 then 2
                    when itens.distancia_vendedor_cliente_km < 700 then 3
                    when itens.distancia_vendedor_cliente_km < 1500 then 4
                    else 5
                end as ordem
            from marts.fato_itens_pedido as itens
            inner join marts.fato_pedidos as pedidos using (id_pedido)
            where
                itens.data_compra >= $inicio and itens.data_compra < $fim
                and (len($ufs) = 0 or list_contains($ufs, itens.uf_cliente))
                and pedidos.entregue
                and itens.distancia_vendedor_cliente_km is not null
        )
        select
            ordem,
            count(*) as itens,
            avg(valor_frete) as frete_medio,
            avg(valor_frete / nullif(valor_item, 0)) as frete_sobre_preco,
            avg(dias_ate_entrega) as dias_entrega
        from itens
        group by ordem
        order by ordem
    """
    df = _df(con, sql, filtros)
    df.insert(0, "faixa", df.pop("ordem").map(lambda o: FAIXAS_DISTANCIA[o - 1]))
    return df


def nota_por_atraso(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    sql = f"""
        select
            case
                when dias_atraso_entrega <= -8 then 1
                when dias_atraso_entrega <= -1 then 2
                when dias_atraso_entrega = 0 then 3
                when dias_atraso_entrega <= 3 then 4
                when dias_atraso_entrega <= 7 then 5
                else 6
            end as ordem,
            count(*) as pedidos,
            avg(nota_avaliacao) as nota_media
        from marts.fato_pedidos
        where {_RECORTE} and entregue and nota_avaliacao is not null
        group by ordem
        order by ordem
    """
    df = _df(con, sql, filtros)
    df.insert(0, "faixa", df.pop("ordem").map(lambda o: FAIXAS_ATRASO[o - 1]))
    return df


def nota_no_prazo_x_atrasado(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    sql = f"""
        select
            avg(nota_avaliacao) filter (where not atrasado) as nota_no_prazo,
            avg(nota_avaliacao) filter (where atrasado) as nota_atrasado
        from marts.fato_pedidos
        where {_RECORTE} and entregue
    """
    return _df(con, sql, filtros)


def distribuicao_notas(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    sql = f"""
        select
            nota_avaliacao as nota,
            count(*) as pedidos,
            count(*) / sum(count(*)) over () as participacao
        from marts.fato_pedidos
        where {_RECORTE} and nota_avaliacao is not null
        group by 1
        order by 1
    """
    return _df(con, sql, filtros)


def clientes_novos_mensal(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    """Clientes cuja primeira compra (no recorte de UF) caiu em cada mês."""
    sql = f"""
        with primeira as (
            select id_cliente, min(data_compra) as primeira_compra
            from marts.fato_pedidos
            where (len($ufs) = 0 or list_contains($ufs, uf_cliente)) and {PEDIDO_VALIDO}
            group by id_cliente
        )
        select
            date_trunc('month', primeira_compra)::date as mes,
            count(*) as clientes_novos
        from primeira
        where primeira_compra >= $inicio and primeira_compra < $fim
        group by 1
        order by 1
    """
    return _df(con, sql, filtros)


def clientes_por_uf(con: duckdb.DuckDBPyConnection, filtros: Filtros) -> pd.DataFrame:
    sql = f"""
        select
            uf_cliente as uf,
            count(distinct id_cliente) as clientes,
            sum(valor_pedido) as faturamento
        from marts.fato_pedidos
        where {_RECORTE} and {PEDIDO_VALIDO}
        group by 1
        order by clientes desc
    """
    return _df(con, sql, filtros)


def ufs_disponiveis(con: duckdb.DuckDBPyConnection) -> list[str]:
    return [
        r[0]
        for r in con.execute(
            "select distinct uf_cliente from marts.fato_pedidos order by 1"
        ).fetchall()
    ]
