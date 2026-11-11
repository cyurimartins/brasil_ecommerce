"""Ingestão: extrai o dataset da Olist do Kaggle e carrega na camada raw do DuckDB."""

from brasil_ecommerce.ingestion.extract import extract
from brasil_ecommerce.ingestion.load import LoadResult, load_raw
from brasil_ecommerce.ingestion.sources import SOURCES, SourceSpec

__all__ = ["SOURCES", "LoadResult", "SourceSpec", "extract", "load_raw"]
