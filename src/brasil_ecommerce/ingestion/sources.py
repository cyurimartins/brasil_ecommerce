"""Catálogo das fontes da Olist: arquivo de origem, tabela de destino e contrato mínimo."""

from dataclasses import dataclass


class SchemaValidationError(Exception):
    """A fonte não cumpre o contrato mínimo esperado (colunas ou volume)."""


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """Contrato de uma fonte de dados bruta.

    Attributes:
        table: nome da tabela no schema ``raw`` do DuckDB.
        filename: nome do arquivo CSV como publicado no Kaggle.
        required_columns: colunas que precisam existir para o pipeline funcionar.
    """

    table: str
    filename: str
    required_columns: tuple[str, ...]


SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec(
        table="orders",
        filename="olist_orders_dataset.csv",
        required_columns=(
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ),
    ),
    SourceSpec(
        table="order_items",
        filename="olist_order_items_dataset.csv",
        required_columns=(
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "price",
            "freight_value",
        ),
    ),
    SourceSpec(
        table="order_payments",
        filename="olist_order_payments_dataset.csv",
        required_columns=("order_id", "payment_sequential", "payment_type", "payment_value"),
    ),
    SourceSpec(
        table="order_reviews",
        filename="olist_order_reviews_dataset.csv",
        required_columns=("review_id", "order_id", "review_score", "review_creation_date"),
    ),
    SourceSpec(
        table="customers",
        filename="olist_customers_dataset.csv",
        required_columns=(
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_state",
        ),
    ),
    SourceSpec(
        table="products",
        filename="olist_products_dataset.csv",
        required_columns=("product_id", "product_category_name", "product_weight_g"),
    ),
    SourceSpec(
        table="sellers",
        filename="olist_sellers_dataset.csv",
        required_columns=("seller_id", "seller_zip_code_prefix", "seller_state"),
    ),
    SourceSpec(
        table="geolocation",
        filename="olist_geolocation_dataset.csv",
        required_columns=(
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ),
    ),
    SourceSpec(
        table="product_category_translation",
        filename="product_category_name_translation.csv",
        required_columns=("product_category_name", "product_category_name_english"),
    ),
)
