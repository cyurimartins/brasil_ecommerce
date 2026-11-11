"""Assets de ingestão: Kaggle → arquivos CSV → schema ``raw`` do DuckDB."""

import dagster as dg

from brasil_ecommerce.config import get_settings
from brasil_ecommerce.ingestion import SOURCES, extract, load_raw

GROUP = "ingestao"
SOURCE_NAME = "olist"  # mesmo nome do source no dbt: as chaves se conectam no lineage

ARQUIVOS_BRUTOS = dg.AssetKey("arquivos_brutos_olist")


@dg.asset(
    key=ARQUIVOS_BRUTOS,
    group_name=GROUP,
    kinds={"python", "kaggle"},
    description="CSVs do dataset público da Olist, baixados do Kaggle para data/raw.",
)
def arquivos_brutos_olist() -> dg.MaterializeResult:
    settings = get_settings()
    raw_dir = extract(settings.kaggle_dataset, settings.raw_dir)
    return dg.MaterializeResult(
        metadata={
            "diretorio": dg.MetadataValue.path(str(raw_dir)),
            "arquivos": len(SOURCES),
        }
    )


@dg.multi_asset(
    specs=[
        dg.AssetSpec(
            key=dg.AssetKey([SOURCE_NAME, spec.table]),
            deps=[ARQUIVOS_BRUTOS],
            group_name=GROUP,
            kinds={"python", "duckdb"},
            description=f"raw.{spec.table} — {spec.filename} carregado como VARCHAR.",
        )
        for spec in SOURCES
    ],
)
def tabelas_raw_olist() -> dg.Output:  # type: ignore[return]
    """Carga atômica das 9 tabelas: ou todas são atualizadas, ou nenhuma."""
    settings = get_settings()
    results = load_raw(settings.raw_dir, settings.warehouse_path)
    for result in results:
        table = result.table.removeprefix("raw.")
        yield dg.MaterializeResult(
            asset_key=dg.AssetKey([SOURCE_NAME, table]),
            metadata={
                "linhas": dg.MetadataValue.int(result.rows),
                "colunas": dg.MetadataValue.int(result.columns),
                "tabela": result.table,
            },
        )
