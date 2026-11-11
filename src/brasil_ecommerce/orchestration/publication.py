"""Asset de publicação: só roda se toda a transformação e os testes passarem."""

import dagster as dg

from brasil_ecommerce.config import get_settings
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
