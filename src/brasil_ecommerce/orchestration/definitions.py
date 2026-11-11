"""Ponto de entrada do Dagster: ``dagster dev -m brasil_ecommerce.orchestration.definitions``."""

import dagster as dg

from brasil_ecommerce.orchestration.dbt import dbt_resource, modelos_dbt
from brasil_ecommerce.orchestration.ingestion import arquivos_brutos_olist, tabelas_raw_olist
from brasil_ecommerce.orchestration.publication import banco_consulta, exportacao_tableau

pipeline_completo = dg.define_asset_job(
    name="pipeline_completo",
    selection=dg.AssetSelection.all(),
    description="Ingestão → dbt build (modelos + testes) → publicação → exportação.",
)

execucao_diaria = dg.ScheduleDefinition(
    name="execucao_diaria",
    job=pipeline_completo,
    cron_schedule="0 6 * * *",
    execution_timezone="America/Sao_Paulo",
    # Desligado por padrão: o dataset é estático. Ative pela interface quando quiser.
    default_status=dg.DefaultScheduleStatus.STOPPED,
)

defs = dg.Definitions(
    assets=[
        arquivos_brutos_olist,
        tabelas_raw_olist,
        modelos_dbt,
        banco_consulta,
        exportacao_tableau,
    ],
    jobs=[pipeline_completo],
    schedules=[execucao_diaria],
    resources={"dbt": dbt_resource},
)
