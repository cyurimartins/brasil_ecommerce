"""Testes estruturais do grafo do Dagster (não executam o pipeline).

Exigem o manifest do dbt: `make test` roda `dbt parse` antes do pytest.
"""

from typing import Any

import dagster as dg
import pytest

from brasil_ecommerce.ingestion import SOURCES
from brasil_ecommerce.orchestration.definitions import defs


@pytest.fixture(scope="module")
def graph() -> Any:  # AssetGraph não é exportado pela API pública do Dagster
    return defs.resolve_asset_graph()


def test_definitions_carregam_sem_erro() -> None:
    dg.Definitions.validate_loadable(defs)


def test_tabelas_raw_alimentam_os_sources_do_dbt(graph: Any) -> None:
    """A chave da ingestão precisa ser a mesma do source dbt, senão o lineage quebra."""
    for spec in SOURCES:
        raw = dg.AssetKey(["olist", spec.table])
        assert raw in graph.get_all_asset_keys()
        assert graph.get(raw).child_keys, f"{raw} não alimenta nenhum modelo dbt"


def test_publicacao_depende_de_todos_os_marts(graph: Any) -> None:
    marts = {k for k in graph.get_all_asset_keys() if k.path[0] == "marts"}
    publicacao = graph.get(dg.AssetKey("banco_consulta"))

    assert len(marts) == 6
    assert set(publicacao.parent_keys) == marts


def test_testes_do_dbt_viram_asset_checks(graph: Any) -> None:
    assert len(list(graph.asset_check_keys)) > 50


def test_agendamento_diario_em_horario_de_brasilia() -> None:
    schedule = defs.resolve_schedule_def("execucao_diaria")

    assert schedule.cron_schedule == "0 6 * * *"
    assert schedule.execution_timezone == "America/Sao_Paulo"
    assert schedule.default_status == dg.DefaultScheduleStatus.STOPPED
