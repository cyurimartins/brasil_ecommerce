"""Configuração de logging compartilhada pelos pontos de entrada do projeto."""

import logging


def setup_logging(level: str = "INFO") -> None:
    """Configura o logger raiz com um formato único para todo o projeto."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
