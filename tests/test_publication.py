from pathlib import Path

import duckdb
import pytest

from brasil_ecommerce.publication import publish


@pytest.fixture
def warehouse(tmp_path: Path) -> Path:
    path = tmp_path / "warehouse.duckdb"
    with duckdb.connect(str(path)) as con:
        con.execute("create schema marts")
        con.execute("create table marts.fato as select * from range(3) t(id)")
        con.execute("create schema staging")
        con.execute("create view staging.v as select * from marts.fato")
    return path


def test_publica_copia_com_tabelas_e_views(warehouse: Path, tmp_path: Path) -> None:
    target = tmp_path / "publicado" / "consulta.duckdb"

    result = publish(warehouse, target)

    assert result.table_counts == {"fato": 3}
    with duckdb.connect(str(target), read_only=True) as con:
        assert con.execute("select count(*) from staging.v").fetchall() == [(3,)]


def test_republicar_substitui_a_versao_anterior(warehouse: Path, tmp_path: Path) -> None:
    target = tmp_path / "consulta.duckdb"
    publish(warehouse, target)
    with duckdb.connect(str(warehouse)) as con:
        con.execute("insert into marts.fato values (99)")

    result = publish(warehouse, target)

    assert result.table_counts == {"fato": 4}
    assert not list(tmp_path.glob(".*.tmp"))


def test_publicar_com_leitor_conectado_nao_falha(warehouse: Path, tmp_path: Path) -> None:
    """O cenário do DBeaver: um leitor conectado na cópia não bloqueia a publicação."""
    target = tmp_path / "consulta.duckdb"
    publish(warehouse, target)

    with duckdb.connect(str(target), read_only=True) as leitor:
        with duckdb.connect(str(warehouse)) as con:
            con.execute("insert into marts.fato values (99)")
        publish(warehouse, target)
        # O leitor conectado continua vendo a versão anterior, sem erro.
        assert leitor.execute("select count(*) from marts.fato").fetchall() == [(3,)]

    with duckdb.connect(str(target), read_only=True) as novo_leitor:
        assert novo_leitor.execute("select count(*) from marts.fato").fetchall() == [(4,)]


def test_nao_publica_se_nao_houver_tabelas_de_consumo(tmp_path: Path) -> None:
    vazio = tmp_path / "vazio.duckdb"
    duckdb.connect(str(vazio)).close()
    target = tmp_path / "consulta.duckdb"

    with pytest.raises(RuntimeError, match="sem tabelas"):
        publish(vazio, target)

    assert not target.exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_warehouse_inexistente_falha(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        publish(tmp_path / "nao_existe.duckdb", tmp_path / "consulta.duckdb")
