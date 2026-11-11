"""Assets dbt: cada modelo vira um asset e cada teste vira um asset check."""

import os
from collections.abc import Iterator, Mapping
from typing import Any

import dagster as dg
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

from brasil_ecommerce.config import PROJECT_ROOT, get_settings

DBT_PROJECT_DIR = PROJECT_ROOT / "transform"

# O dbt roda como subprocesso a partir de transform/; o profiles.yml lê o diretório
# de dados desta variável. Garantimos um caminho absoluto, igual ao do pacote Python.
os.environ.setdefault("BRECOM_DATA_DIR", str(get_settings().data_dir))

dbt_project = DbtProject(project_dir=DBT_PROJECT_DIR, profiles_dir=DBT_PROJECT_DIR)
dbt_project.prepare_if_dev()  # gera o manifest.json ao rodar `dagster dev`

dbt_resource = DbtCliResource(project_dir=dbt_project)


class BrasilEcommerceTranslator(DagsterDbtTranslator):
    """Agrupa os assets pela camada do dbt (staging, intermediate, marts)."""

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> str | None:
        fqn = dbt_resource_props.get("fqn", [])
        if dbt_resource_props.get("resource_type") == "model" and len(fqn) > 1:
            return fqn[1]
        return super().get_group_name(dbt_resource_props)


@dbt_assets(
    manifest=dbt_project.manifest_path,
    project=dbt_project,
    dagster_dbt_translator=BrasilEcommerceTranslator(),
)
def modelos_dbt(context: dg.AssetExecutionContext, dbt: DbtCliResource) -> Iterator[Any]:
    """Executa `dbt build`: modelos, testes de dados e testes unitários."""
    yield from dbt.cli(["build"], context=context).stream()
