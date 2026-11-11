"""Extração: baixa o dataset público da Olist do Kaggle para ``data/raw``."""

import logging
from collections.abc import Iterable
from pathlib import Path

import kagglehub

from brasil_ecommerce.ingestion.sources import SOURCES, SourceSpec

log = logging.getLogger(__name__)


def missing_files(raw_dir: Path, sources: Iterable[SourceSpec] = SOURCES) -> list[str]:
    """Lista os arquivos esperados que ainda não existem em ``raw_dir``."""
    return [s.filename for s in sources if not (raw_dir / s.filename).is_file()]


def extract(
    dataset: str,
    raw_dir: Path,
    *,
    force: bool = False,
    sources: Iterable[SourceSpec] = SOURCES,
) -> Path:
    """Garante que todos os CSVs de origem estejam em ``raw_dir``.

    Idempotente: se os arquivos já existem, não baixa de novo (a menos que ``force``).

    Raises:
        FileNotFoundError: se, após o download, algum arquivo esperado continuar faltando.
    """
    sources = tuple(sources)
    pending = missing_files(raw_dir, sources)

    if not pending and not force:
        log.info("Arquivos brutos já presentes em %s — download ignorado", raw_dir)
        return raw_dir

    log.info("Baixando dataset '%s' do Kaggle para %s", dataset, raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    kagglehub.dataset_download(dataset, output_dir=str(raw_dir), force_download=force)

    still_missing = missing_files(raw_dir, sources)
    if still_missing:
        raise FileNotFoundError(f"Arquivos ausentes após o download: {still_missing}")

    log.info("Download concluído — %d arquivos disponíveis", len(sources))
    return raw_dir
