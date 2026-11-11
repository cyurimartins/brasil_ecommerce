from pathlib import Path

import pytest

from brasil_ecommerce.config import PROJECT_ROOT, Settings


def test_caminhos_padrao_ficam_dentro_do_projeto() -> None:
    settings = Settings(_env_file=None)

    assert settings.data_dir == PROJECT_ROOT / "data"
    assert settings.raw_dir == PROJECT_ROOT / "data" / "raw"
    assert settings.warehouse_path.suffix == ".duckdb"


def test_variavel_de_ambiente_sobrescreve_padrao(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("BRECOM_DATA_DIR", str(tmp_path))

    settings = Settings(_env_file=None)

    assert settings.raw_dir == tmp_path / "raw"
