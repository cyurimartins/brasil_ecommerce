"""Publicação: copia o warehouse para o banco de consulta (padrão write-audit-publish).

O DuckDB não permite que um processo escreva enquanto outro lê o mesmo arquivo.
Por isso o pipeline escreve em ``warehouse.duckdb`` e, só depois que todos os
testes passam, publica uma cópia em ``consulta.duckdb`` — o arquivo que o DBeaver
e o dashboard leem. Consequências:

* Leitores podem ficar conectados o tempo todo, sem bloquear o pipeline.
* O consumo nunca vê dados de uma execução que falhou nos testes.
* A troca é atômica (``Path.replace``): quem estiver conectado continua lendo a
  versão anterior até reconectar.
"""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Resumo da publicação."""

    path: Path
    size_mb: float
    table_counts: dict[str, int]


def _count_tables(path: Path, schema: str) -> dict[str, int]:
    with duckdb.connect(str(path), read_only=True) as con:
        tables = [
            row[0]
            for row in con.execute(
                "select table_name from information_schema.tables "
                "where table_schema = ? and table_type = 'BASE TABLE' order by 1",
                [schema],
            ).fetchall()
        ]
        return {
            t: con.execute(f'select count(*) from "{schema}"."{t}"').fetchall()[0][0]
            for t in tables
        }


def publish(warehouse_path: Path, target_path: Path, schema: str = "marts") -> PublishResult:
    """Publica uma cópia consistente do warehouse em ``target_path``.

    Raises:
        FileNotFoundError: se o warehouse não existir.
        RuntimeError: se a cópia não tiver nenhuma tabela no ``schema`` esperado.
    """
    if not warehouse_path.is_file():
        raise FileNotFoundError(f"Warehouse não encontrado: {warehouse_path}")

    # CHECKPOINT grava no arquivo principal tudo o que estiver no WAL, garantindo
    # que a cópia byte a byte seja um banco completo e consistente.
    with duckdb.connect(str(warehouse_path)) as con:
        con.execute("CHECKPOINT")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_name(f".{target_path.name}.tmp")
    shutil.copyfile(warehouse_path, tmp_path)

    # Audita a cópia antes de expô-la: precisa abrir e conter as tabelas de consumo.
    try:
        counts = _count_tables(tmp_path, schema)
        if not counts:
            raise RuntimeError(f"Cópia sem tabelas no schema '{schema}'")
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    tmp_path.replace(target_path)  # rename atômico no mesmo sistema de arquivos
    size_mb = round(target_path.stat().st_size / 1024**2, 1)
    log.info("Publicado %s (%.1f MB, %d tabelas em %s)", target_path, size_mb, len(counts), schema)
    return PublishResult(path=target_path, size_mb=size_mb, table_counts=counts)
