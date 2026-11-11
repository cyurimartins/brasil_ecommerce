# Interface única de comandos do projeto. Rode `make` ou `make help` para ver as opções.
.DEFAULT_GOAL := help
.PHONY: help setup lint format test check clean

UV ?= uv

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Cria o ambiente (.venv), instala dependências e ganchos do pre-commit
	$(UV) sync
	$(UV) run pre-commit install
	@test -f .env || cp .env.example .env

lint: ## Verifica estilo e erros (sem alterar arquivos)
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format: ## Formata o código automaticamente
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

test: ## Roda os testes automatizados
	$(UV) run pytest

check: lint test ## Lint + testes (o mesmo que roda no CI)

clean: ## Remove caches e artefatos gerados (preserva data/raw)
	rm -rf .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -not -path './.venv/*' -not -path './venv/*' -exec rm -rf {} +
