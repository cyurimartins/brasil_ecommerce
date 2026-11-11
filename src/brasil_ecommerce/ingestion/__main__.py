"""CLI da ingestão: ``uv run brecom-ingest`` ou ``python -m brasil_ecommerce.ingestion``."""

import argparse
import logging
import sys

from brasil_ecommerce.config import get_settings
from brasil_ecommerce.ingestion.extract import extract
from brasil_ecommerce.ingestion.load import load_raw
from brasil_ecommerce.logging_config import setup_logging

log = logging.getLogger("brasil_ecommerce.ingestion")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="brecom-ingest",
        description="Baixa o dataset da Olist e carrega na camada raw do DuckDB.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--force-download", action="store_true", help="baixa de novo mesmo se os arquivos existem"
    )
    group.add_argument(
        "--skip-download", action="store_true", help="usa apenas os arquivos já presentes"
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    setup_logging(settings.log_level)

    try:
        if not args.skip_download:
            extract(settings.kaggle_dataset, settings.raw_dir, force=args.force_download)
        load_raw(settings.raw_dir, settings.warehouse_path)
    except Exception:
        log.exception("Falha na ingestão")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
