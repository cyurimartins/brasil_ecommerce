"""Asset de publicação: só roda se toda a transformação e os testes passarem."""

import dagster as dg

from brasil_ecommerce.config import get_settings
from brasil_ecommerce.export import export_csv
from brasil_ecommerce.orchestration.dbt import modelos_dbt
from brasil_ecommerce.publication import publish

MARTS = [key for key in modelos_dbt.keys if key.path[-1].startswith(("fato_", "dim_"))]


@dg.asset(
    key="banco_consulta",
    deps=MARTS,
    group_name="publicacao",
    kinds={"duckdb"},
    description=(
        "Cópia do warehouse para leitura (DBeaver, dashboard): data/consulta.duckdb. "
        "Atualizada só quando o dbt build termina sem falhas (write-audit-publish)."
    ),
)
def banco_consulta() -> dg.MaterializeResult:
    settings = get_settings()
    result = publish(settings.warehouse_path, settings.consulta_path)
    return dg.MaterializeResult(
        metadata={
            "arquivo": dg.MetadataValue.path(str(result.path)),
            "tamanho_mb": dg.MetadataValue.float(result.size_mb),
            **{f"linhas_{t}": dg.MetadataValue.int(n) for t, n in result.table_counts.items()},
        }
    )


@dg.asset(
    key="exportacao_tableau",
    deps=[banco_consulta],
    group_name="publicacao",
    kinds={"csv", "tableau"},
    description=(
        "Marts em CSV (data/exports/tableau/) para o Tableau Public, que não se conecta ao "
        "DuckDB. Gerado a partir do banco de consulta, ou seja, só com dados aprovados nos testes."
    ),
)
def exportacao_tableau() -> dg.MaterializeResult:
    settings = get_settings()
    counts = export_csv(settings.consulta_path, settings.tableau_dir)
    return dg.MaterializeResult(
        metadata={
            "diretorio": dg.MetadataValue.path(str(settings.tableau_dir)),
            **{f"linhas_{t}": dg.MetadataValue.int(n) for t, n in counts.items()},
        }
    )
