"""Carga: CSVs brutos → schema ``raw`` do DuckDB.

Decisões de projeto:

* **Todas as colunas como VARCHAR.** A camada raw é fiel à fonte; tipagem é
  responsabilidade explícita do staging (dbt). Evita, por exemplo, que prefixos
  de CEP como ``01310`` virem o número ``1310``.
* **Colunas de auditoria** ``_source_file`` e ``_loaded_at`` em todas as tabelas.
* **Tudo ou nada.** As tabelas são recriadas dentro de uma única transação; se
  qualquer fonte violar o contrato, nada é alterado no warehouse.
* **Idempotente.** ``CREATE OR REPLACE``: rodar duas vezes gera o mesmo estado.
"""

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from brasil_ecommerce.ingestion.sources import SOURCES, SchemaValidationError, SourceSpec

log = logging.getLogger(__name__)

RAW_SCHEMA = "raw"
_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class LoadResult:
    """Resumo da carga de uma tabela."""

    table: str
    rows: int
    columns: int


def _validate_identifier(name: str) -> str:
    # Nomes de tabela não podem ser parametrizados em SQL; validamos para evitar injeção.
    if not _IDENTIFIER.match(name):
        raise ValueError(f"Identificador SQL inválido: {name!r}")
    return name


def _load_table(
    con: duckdb.DuckDBPyConnection, spec: SourceSpec, raw_dir: Path, loaded_at: datetime
) -> LoadResult:
    table = f"{RAW_SCHEMA}.{_validate_identifier(spec.table)}"
    path = raw_dir / spec.filename
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de origem não encontrado: {path}")

    con.execute(
        f"""
        CREATE OR REPLACE TABLE {table} AS
        SELECT
            *,
            $source_file::VARCHAR   AS _source_file,
            $loaded_at::TIMESTAMPTZ AS _loaded_at
        FROM read_csv($path, header = true, all_varchar = true)
        """,
        {"path": str(path), "source_file": spec.filename, "loaded_at": loaded_at},
    )

    columns = [row[0] for row in con.execute(f"DESCRIBE {table}").fetchall()]
    missing = [c for c in spec.required_columns if c not in columns]
    if missing:
        raise SchemaValidationError(
            f"{spec.filename}: colunas obrigatórias ausentes {missing}; encontradas {columns}"
        )

    (rows,) = con.execute(f"SELECT count(*) FROM {table}").fetchone()  # type: ignore[misc]
    if rows == 0:
        raise SchemaValidationError(f"{spec.filename}: arquivo sem linhas de dados")

    data_columns = len(columns) - 2  # desconta as colunas de auditoria
    log.info("%-30s %9d linhas  %2d colunas", table, rows, data_columns)
    return LoadResult(table=table, rows=rows, columns=data_columns)


def load_raw(
    raw_dir: Path,
    warehouse_path: Path,
    sources: Iterable[SourceSpec] = SOURCES,
) -> list[LoadResult]:
    """Carrega todas as fontes no schema ``raw`` do warehouse DuckDB, de forma atômica."""
    warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    loaded_at = datetime.now(UTC)

    with duckdb.connect(str(warehouse_path)) as con:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")
        con.begin()
        try:
            results = [_load_table(con, spec, raw_dir, loaded_at) for spec in sources]
        except Exception:
            con.rollback()
            log.error("Carga abortada — nenhuma tabela foi alterada (rollback)")
            raise
        con.commit()

    log.info("Carga concluída — %d tabelas em %s", len(results), warehouse_path)
    return results
