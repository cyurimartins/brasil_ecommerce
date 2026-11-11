"""
ingest.py — Camada de ingestão de dados do Olist
=================================================
Responsabilidade única: carregar os CSVs brutos, validar integridade básica
e disponibilizar os DataFrames prontos para o transform.py.

Uso:
    python ingest.py                   # roda validação e imprime relatório
    from ingest import load_all        # importa no transform.py
"""

import os
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Caminhos (ajuste se necessário)
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]   # raiz do projeto
DATA_DIR = ROOT_DIR / "data" / "ods"

# Mapeamento: chave lógica → nome do arquivo CSV
CSV_FILES: dict[str, str] = {
    "orders":        "olist_orders_dataset.csv",
    "order_items":   "olist_order_items_dataset.csv",
    "order_payments":"olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers":     "olist_customers_dataset.csv",
    "products":      "olist_products_dataset.csv",
    "sellers":       "olist_sellers_dataset.csv",
    "geolocation":   "olist_geolocation_dataset.csv",
    "category_names":"product_category_name_translation.csv",
}

# Colunas que devem ser convertidas para datetime automaticamente
DATETIME_COLS: dict[str, list[str]] = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_reviews": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}

# Colunas-chave esperadas por tabela (validação mínima)
REQUIRED_COLS: dict[str, list[str]] = {
    "orders":         ["order_id", "customer_id", "order_status"],
    "order_items":    ["order_id", "product_id", "seller_id", "price"],
    "order_payments": ["order_id", "payment_type", "payment_value"],
    "order_reviews":  ["order_id", "review_score"],
    "customers":      ["customer_id", "customer_state"],
    "products":       ["product_id", "product_category_name"],
    "sellers":        ["seller_id", "seller_state"],
    "geolocation":    ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng"],
    "category_names": ["product_category_name", "product_category_name_english"],
}


# ---------------------------------------------------------------------------
# Funções de carregamento
# ---------------------------------------------------------------------------

def load_csv(name: str, data_dir: Path = DATA_DIR) -> Optional[pd.DataFrame]:
    """
    Carrega um único CSV pelo nome lógico (ex: 'orders').
    Aplica conversão de datas e valida colunas obrigatórias.
    Retorna None se o arquivo não existir.
    """
    filename = CSV_FILES.get(name)
    if filename is None:
        raise ValueError(f"Nome desconhecido: '{name}'. Opções: {list(CSV_FILES)}")

    filepath = data_dir / filename
    if not filepath.exists():
        log.warning("Arquivo não encontrado: %s", filepath)
        return None

    log.info("Carregando %-20s → %s", name, filename)

    # Colunas de data para parsear diretamente na leitura
    parse_dates = DATETIME_COLS.get(name, [])

    df = pd.read_csv(
        filepath,
        parse_dates=parse_dates if parse_dates else False,
        low_memory=False,   # evita DtypeWarning em colunas mistas
    )

    # Validação de colunas obrigatórias
    required = REQUIRED_COLS.get(name, [])
    missing = [c for c in required if c not in df.columns]
    if missing:
        log.error("%-20s faltando colunas: %s", name, missing)
    else:
        log.info("%-20s OK — %d linhas, %d colunas", name, len(df), df.shape[1])

    return df


def load_all(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    """
    Carrega todos os CSVs definidos em CSV_FILES.
    Retorna um dict {nome_lógico: DataFrame}.
    Tabelas não encontradas são omitidas do resultado com aviso.
    """
    log.info("=" * 55)
    log.info("Iniciando ingestão — diretório: %s", data_dir)
    log.info("=" * 55)

    datasets: dict[str, pd.DataFrame] = {}

    for name in CSV_FILES:
        df = load_csv(name, data_dir)
        if df is not None:
            datasets[name] = df

    log.info("-" * 55)
    log.info(
        "Ingestão concluída — %d/%d tabelas carregadas",
        len(datasets), len(CSV_FILES),
    )
    return datasets


# ---------------------------------------------------------------------------
# Relatório de qualidade rápido
# ---------------------------------------------------------------------------

def quality_report(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Gera um DataFrame resumo com linhas, colunas, % de nulos e duplicatas
    de cada tabela carregada. Útil para inspecionar antes de transformar.
    """
    rows = []
    for name, df in datasets.items():
        null_pct = (df.isnull().sum().sum() / df.size * 100) if df.size else 0
        rows.append({
            "tabela":        name,
            "linhas":        len(df),
            "colunas":       df.shape[1],
            "nulos_%":       round(null_pct, 2),
            "duplicatas":    df.duplicated().sum(),
        })

    report = pd.DataFrame(rows).sort_values("nulos_%", ascending=False)
    return report


def show_report(datasets: dict[str, pd.DataFrame]) -> None:
    """Imprime o relatório de qualidade formatado no terminal."""
    report = quality_report(datasets)
    print("\n" + "=" * 60)
    print("  RELATÓRIO DE QUALIDADE — DADOS BRUTOS")
    print("=" * 60)
    print(report.to_string(index=False))
    print("=" * 60 + "\n")

    # Aviso se alguma tabela tem muitos nulos
    problema = report[report["nulos_%"] > 30]
    if not problema.empty:
        log.warning(
            "Tabelas com >30%% de nulos: %s",
            problema["tabela"].tolist(),
        )


# ---------------------------------------------------------------------------
# Execução direta (python ingest.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    datasets = load_all()

    if not datasets:
        log.error("Nenhum dado carregado. Verifique se DATA_DIR está correto: %s", DATA_DIR)
    else:
        show_report(datasets)

        # Mostra amostra de cada tabela
        for name, df in datasets.items():
            print(f"\n--- {name} (primeiras 3 linhas) ---")
            print(df.head(3).to_string())
