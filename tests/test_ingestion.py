from pathlib import Path

import duckdb
import kagglehub
import pytest

from brasil_ecommerce.ingestion.extract import extract, missing_files
from brasil_ecommerce.ingestion.load import load_raw
from brasil_ecommerce.ingestion.sources import SOURCES, SchemaValidationError, SourceSpec

CUSTOMERS = SourceSpec(
    table="customers",
    filename="customers.csv",
    required_columns=("customer_id", "customer_zip_code_prefix"),
)
SELLERS = SourceSpec(
    table="sellers",
    filename="sellers.csv",
    required_columns=("seller_id",),
)


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "raw"
    directory.mkdir()
    (directory / "customers.csv").write_text(
        "customer_id,customer_zip_code_prefix\nc1,01310\nc2,22070\n", encoding="utf-8"
    )
    (directory / "sellers.csv").write_text("seller_id\ns1\n", encoding="utf-8")
    return directory


@pytest.fixture
def warehouse(tmp_path: Path) -> Path:
    return tmp_path / "warehouse.duckdb"


def _query(warehouse: Path, sql: str) -> list[tuple]:
    with duckdb.connect(str(warehouse), read_only=True) as con:
        return con.execute(sql).fetchall()


# --- catálogo -----------------------------------------------------------------


def test_catalogo_nao_tem_tabelas_ou_arquivos_duplicados() -> None:
    assert len({s.table for s in SOURCES}) == len(SOURCES)
    assert len({s.filename for s in SOURCES}) == len(SOURCES)


# --- carga ----------------------------------------------------------------------


def test_carga_cria_tabelas_no_schema_raw_com_contagem_correta(
    raw_dir: Path, warehouse: Path
) -> None:
    results = load_raw(raw_dir, warehouse, sources=[CUSTOMERS, SELLERS])

    assert [(r.table, r.rows) for r in results] == [("raw.customers", 2), ("raw.sellers", 1)]
    assert _query(warehouse, "SELECT count(*) FROM raw.customers") == [(2,)]


def test_carga_preserva_zeros_a_esquerda_do_cep(raw_dir: Path, warehouse: Path) -> None:
    load_raw(raw_dir, warehouse, sources=[CUSTOMERS])

    rows = _query(warehouse, "SELECT customer_zip_code_prefix FROM raw.customers ORDER BY 1")
    assert rows == [("01310",), ("22070",)]


def test_carga_adiciona_colunas_de_auditoria(raw_dir: Path, warehouse: Path) -> None:
    load_raw(raw_dir, warehouse, sources=[CUSTOMERS])

    rows = _query(
        warehouse, "SELECT DISTINCT _source_file, _loaded_at IS NOT NULL FROM raw.customers"
    )
    assert rows == [("customers.csv", True)]


def test_carga_e_idempotente(raw_dir: Path, warehouse: Path) -> None:
    load_raw(raw_dir, warehouse, sources=[CUSTOMERS])
    load_raw(raw_dir, warehouse, sources=[CUSTOMERS])

    assert _query(warehouse, "SELECT count(*) FROM raw.customers") == [(2,)]


def test_carga_remove_bom_do_cabecalho(raw_dir: Path, warehouse: Path) -> None:
    (raw_dir / "sellers.csv").write_text("﻿seller_id\ns1\n", encoding="utf-8")

    results = load_raw(raw_dir, warehouse, sources=[SELLERS])

    assert results[0].rows == 1


def test_coluna_obrigatoria_ausente_falha_e_nao_altera_o_warehouse(
    raw_dir: Path, warehouse: Path
) -> None:
    load_raw(raw_dir, warehouse, sources=[CUSTOMERS, SELLERS])
    (raw_dir / "customers.csv").write_text("customer_id,c_novo\nc9,x\n", encoding="utf-8")
    (raw_dir / "sellers.csv").write_text("seller_id\ns1\ns2\ns3\n", encoding="utf-8")

    with pytest.raises(SchemaValidationError, match="customer_zip_code_prefix"):
        load_raw(raw_dir, warehouse, sources=[SELLERS, CUSTOMERS])

    # Rollback: nem sellers (carregada antes da falha) nem customers foram alterados.
    assert _query(warehouse, "SELECT count(*) FROM raw.sellers") == [(1,)]
    assert _query(warehouse, "SELECT count(*) FROM raw.customers") == [(2,)]


def test_arquivo_sem_linhas_falha(raw_dir: Path, warehouse: Path) -> None:
    (raw_dir / "sellers.csv").write_text("seller_id\n", encoding="utf-8")

    with pytest.raises(SchemaValidationError, match="sem linhas"):
        load_raw(raw_dir, warehouse, sources=[SELLERS])


def test_arquivo_inexistente_falha(tmp_path: Path, warehouse: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_raw(tmp_path, warehouse, sources=[CUSTOMERS])


# --- extração -------------------------------------------------------------------


def test_extracao_nao_baixa_se_arquivos_existem(
    raw_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _nao_deveria_baixar(*_args: object, **_kwargs: object) -> str:
        raise AssertionError("download não deveria ser chamado")

    monkeypatch.setattr(kagglehub, "dataset_download", _nao_deveria_baixar)

    assert extract("qualquer/dataset", raw_dir, sources=[CUSTOMERS, SELLERS]) == raw_dir


def test_extracao_baixa_quando_faltam_arquivos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_dir = tmp_path / "raw"
    chamadas: list[str] = []

    def _download_falso(handle: str, *, output_dir: str, force_download: bool) -> str:
        chamadas.append(handle)
        (Path(output_dir) / "sellers.csv").write_text("seller_id\ns1\n", encoding="utf-8")
        return output_dir

    monkeypatch.setattr(kagglehub, "dataset_download", _download_falso)

    extract("olistbr/brazilian-ecommerce", raw_dir, sources=[SELLERS])

    assert chamadas == ["olistbr/brazilian-ecommerce"]
    assert missing_files(raw_dir, [SELLERS]) == []


def test_extracao_falha_se_download_nao_traz_todos_os_arquivos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(kagglehub, "dataset_download", lambda *_a, **_k: str(tmp_path))

    with pytest.raises(FileNotFoundError, match=r"sellers\.csv"):
        extract("x/y", tmp_path / "raw", sources=[SELLERS])
