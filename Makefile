# Interface única de comandos do projeto. Rode `make` ou `make help` para ver as opções.
.DEFAULT_GOAL := help
.PHONY: help setup lint format test check ingest transform run docs clean

UV ?= uv
DBT_ARGS := --project-dir transform --profiles-dir transform
DBT := $(UV) run dbt

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Cria o ambiente (.venv), instala dependências, pacotes dbt e ganchos do pre-commit
	$(UV) sync
	$(DBT) deps $(DBT_ARGS)
	$(UV) run pre-commit install
	@test -f .env || cp .env.example .env

lint: ## Verifica estilo e erros em Python e SQL (sem alterar arquivos)
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run sqlfluff lint transform/models

format: ## Formata Python e SQL automaticamente
	$(UV) run ruff check --fix .
	$(UV) run ruff format .
	$(UV) run sqlfluff fix transform/models

test: ## Roda os testes Python
	$(UV) run pytest

check: lint test ## Lint + testes Python (o mesmo que roda no CI)

ingest: ## Baixa o dataset (se necessário) e carrega a camada raw no DuckDB
	$(UV) run brecom-ingest

transform: ## Executa e testa os modelos dbt (staging → intermediate → marts)
	$(DBT) build $(DBT_ARGS)

run: ingest transform ## Pipeline completo: ingestão + transformação

docs: ## Gera e abre a documentação do dbt (catálogo + lineage) em http://localhost:8080
	$(DBT) docs generate $(DBT_ARGS)
	$(DBT) docs serve $(DBT_ARGS) --port 8080

clean: ## Remove caches e artefatos gerados (preserva data/raw)
	rm -rf .ruff_cache .pytest_cache transform/target transform/logs
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
