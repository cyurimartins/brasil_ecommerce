"""Exportação dos marts em CSV, para ferramentas que não leem DuckDB (ex.: Tableau Public).

Formato: UTF-8, separador vírgula, ponto como separador decimal, datas ISO (AAAA-MM-DD)
e cabeçalho com os nomes das colunas dos marts. Cada arquivo é escrito em um
temporário e renomeado ao final, para nunca expor um CSV pela metade.
"""

import logging
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)


def export_csv(source_db: Path, out_dir: Path, schema: str = "marts") -> dict[str, int]:
    """Exporta todas as tabelas de ``schema`` para ``out_dir/<tabela>.csv``.

    Returns:
        Quantidade de linhas exportadas por tabela.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    with duckdb.connect(str(source_db), read_only=True) as con:
        tables = [
            row[0]
            for row in con.execute(
                "select table_name from information_schema.tables "
                "where table_schema = ? and table_type = 'BASE TABLE' order by 1",
                [schema],
            ).fetchall()
        ]
        if not tables:
            raise RuntimeError(f"Nenhuma tabela no schema '{schema}' de {source_db}")
        for table in tables:
            final = out_dir / f"{table}.csv"
            tmp = out_dir / f".{table}.csv.tmp"
            con.execute(
                f'copy (select * from "{schema}"."{table}") to \'{tmp}\' '
                "(header, delimiter ',', dateformat '%Y-%m-%d', "
                "timestampformat '%Y-%m-%d %H:%M:%S')"
            )
            tmp.replace(final)
            counts[table] = con.execute(f'select count(*) from "{schema}"."{table}"').fetchall()[0][
                0
            ]
            log.info("Exportado %-22s %9d linhas → %s", table, counts[table], final)
    return counts
