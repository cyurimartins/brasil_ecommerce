"""Testes das consultas do dashboard e da aplicação Streamlit, com um banco fictício."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import duckdb
import pytest
from streamlit.testing.v1 import AppTest

from brasil_ecommerce.config import PROJECT_ROOT, get_settings
from brasil_ecommerce.dashboard import queries as q
from brasil_ecommerce.dashboard.queries import Filtros

# id, cliente, uf, status, data, valor, entregue, atrasado, dias_atraso, nota
PEDIDOS = [
    ("p1", "c1", "SP", "delivered", "2018-01-10", 100.0, True, False, -5, 5),
    ("p2", "c1", "SP", "delivered", "2018-02-10", 200.0, True, True, 2, 3),
    ("p3", "c2", "RJ", "delivered", "2018-01-15", 300.0, True, True, 10, 1),
    ("p4", "c3", "RJ", "canceled", "2018-01-20", 999.0, False, None, None, None),
    ("p5", "c4", "MG", "delivered", "2016-10-01", 50.0, True, False, 0, 4),  # fora do período
]


@pytest.fixture
def banco(tmp_path: Path) -> Path:
    caminho = tmp_path / "consulta.duckdb"
    with duckdb.connect(str(caminho)) as con:
        con.execute("create schema marts")
        con.execute("""
            create table marts.fato_pedidos (
                id_pedido varchar, id_cliente varchar, uf_cliente varchar, status_pedido varchar,
                data_compra date, valor_pedido decimal(14, 2), entregue boolean, atrasado boolean,
                dias_atraso_entrega integer, nota_avaliacao integer,
                dias_ate_entrega integer, dias_prometidos_entrega integer,
                forma_pagamento_principal varchar
            )
        """)
        for p in PEDIDOS:
            con.execute(
                "insert into marts.fato_pedidos values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 10, 20,"
                " 'credit_card')",
                list(p),
            )
        con.execute("""
            create table marts.fato_itens_pedido as
            select id_pedido, 1 as numero_item, 'prod1' as id_produto, uf_cliente, status_pedido,
                   data_compra, valor_pedido as valor_item, 10.0 as valor_frete,
                   150.0 as distancia_vendedor_cliente_km
            from marts.fato_pedidos
        """)
        con.execute(
            "create table marts.dim_produtos as "
            "select 'prod1' as id_produto, 'cama_mesa' as categoria"
        )
    return caminho


@pytest.fixture
def con(banco: Path) -> Iterator[duckdb.DuckDBPyConnection]:
    with duckdb.connect(str(banco), read_only=True) as conexao:
        yield conexao


PERIODO_2018 = Filtros(inicio=date(2018, 1, 1), fim=date(2018, 3, 1))


def test_resumo_aplica_as_definicoes_de_negocio(con: duckdb.DuckDBPyConnection) -> None:
    r = q.resumo(con, PERIODO_2018).iloc[0]

    assert r.pedidos == 3  # p4 cancelado não conta; p5 fora do período
    assert r.faturamento == 600
    assert r.ticket_medio == 200
    assert r.pct_atraso == pytest.approx(2 / 3)  # p2 e p3 atrasados, entre 3 entregues
    assert r.clientes == 2
    assert r.pct_recompra == pytest.approx(0.5)  # c1 comprou 2 vezes, c2 uma vez


def test_filtro_por_uf(con: duckdb.DuckDBPyConnection) -> None:
    r = q.resumo(con, Filtros(inicio=date(2018, 1, 1), fim=date(2018, 3, 1), ufs=("RJ",))).iloc[0]

    assert r.pedidos == 1
    assert r.faturamento == 300


def test_nota_por_faixa_de_atraso(con: duckdb.DuckDBPyConnection) -> None:
    df = q.nota_por_atraso(con, PERIODO_2018)

    assert dict(zip(df.faixa, df.nota_media, strict=True)) == {
        "Antecipado 1-7 dias": 5,
        "Atraso 1-3 dias": 3,
        "Atraso 8+ dias": 1,
    }


def test_faturamento_mensal_respeita_periodo(con: duckdb.DuckDBPyConnection) -> None:
    df = q.faturamento_mensal(con, PERIODO_2018)

    assert df.faturamento.tolist() == [400, 200]  # jan: p1+p3; fev: p2


def test_logistica_por_distancia_usa_faixas_ordenadas(con: duckdb.DuckDBPyConnection) -> None:
    df = q.logistica_por_distancia(con, PERIODO_2018)

    assert df.faixa.tolist() == ["100-300"]
    assert df.itens.iloc[0] == 3


@pytest.mark.parametrize("pagina", ["visao_geral", "vendas", "logistica", "satisfacao", "clientes"])
def test_paginas_do_dashboard_renderizam_sem_erro(
    banco: Path, monkeypatch: pytest.MonkeyPatch, pagina: str
) -> None:
    monkeypatch.setenv("BRECOM_DATA_DIR", str(banco.parent))
    get_settings.cache_clear()
    try:
        app = AppTest.from_file(str(PROJECT_ROOT / "dashboard" / "app.py"), default_timeout=60)
        app.run()
        app.switch_page(f"paginas/{pagina}.py").run()

        assert not app.exception, [e.value for e in app.exception]
    finally:
        get_settings.cache_clear()
