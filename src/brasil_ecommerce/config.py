"""Configuração centralizada do projeto.

Valores vêm de variáveis de ambiente (ou do arquivo ``.env``), com padrões
seguros para desenvolvimento local. Nenhum caminho absoluto fica fixo no código.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configurações do pipeline, lidas de variáveis de ambiente com prefixo ``BRECOM_``."""

    model_config = SettingsConfigDict(
        env_prefix="BRECOM_",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = PROJECT_ROOT / "data"
    kaggle_dataset: str = "olistbr/brazilian-ecommerce"
    log_level: str = "INFO"

    @property
    def raw_dir(self) -> Path:
        """Diretório dos arquivos brutos, exatamente como baixados da fonte."""
        return self.data_dir / "raw"

    @property
    def warehouse_path(self) -> Path:
        """Arquivo DuckDB que funciona como data warehouse local."""
        return self.data_dir / "warehouse.duckdb"

    @property
    def consulta_path(self) -> Path:
        """Cópia publicada do warehouse, para leitura (DBeaver, dashboard).

        Só é atualizada quando o pipeline termina com todos os testes aprovados.
        """
        return self.data_dir / "consulta.duckdb"

    @property
    def tableau_dir(self) -> Path:
        """CSVs dos marts para o Tableau Public, que não se conecta ao DuckDB."""
        return self.data_dir / "exports" / "tableau"


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância única (cacheada) das configurações."""
    return Settings()
