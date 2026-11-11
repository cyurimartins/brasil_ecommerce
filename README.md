# Brasil E-commerce: pipeline de dados analítico

Pipeline de dados de ponta a ponta sobre o [dataset público de e-commerce brasileiro da Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(~100 mil pedidos, 2016–2018), construído só com ferramentas **open source**, seguindo práticas
de mercado de *analytics engineering*.

> 🚧 **Em construção.** O roadmap abaixo mostra o andamento.

## Arquitetura (alvo)

```
Kaggle (CSV) ──► Ingestão (Python) ──► DuckDB [raw]
                                          │
                                   dbt ───┼──► staging      limpeza e tipagem
                                          ├──► intermediate regras e agregações
                                          └──► marts        modelo estrela (Kimball)
                                                   │
                                                   ▼
                                             Dashboard (Evidence)

Orquestração: Dagster  ·  Qualidade: testes dbt  ·  CI: GitHub Actions
```

## Stack

| Camada          | Ferramenta                        |
|-----------------|-----------------------------------|
| Linguagem       | Python 3.12, SQL                  |
| Ambiente        | uv (dependências com lockfile)    |
| Armazenamento   | DuckDB                            |
| Transformação   | dbt-core + dbt-duckdb             |
| Orquestração    | Dagster                           |
| Visualização    | Evidence.dev                      |
| Qualidade       | ruff, pre-commit, pytest, testes dbt |
| CI              | GitHub Actions                    |

## Como rodar

Pré-requisitos: [uv](https://docs.astral.sh/uv/getting-started/installation/) e `make`.

```bash
git clone <url-do-repositorio>
cd brasil_ecommerce
make setup      # cria .venv, instala dependências e ganchos do pre-commit
make check      # lint + testes
make run        # pipeline completo: ingestão + transformação (dbt build)
make docs       # documentação do dbt com lineage em http://localhost:8080
```

O download do Kaggle não exige credenciais (dataset público). O warehouse fica em
`data/warehouse.duckdb`.

Comandos disponíveis: `make help`.

## Decisões técnicas

**Ingestão (camada raw)**

- **Todas as colunas como `VARCHAR`.** A camada raw é fiel à fonte e a tipagem é feita de forma
  explícita no staging (dbt). Isso evita, por exemplo, que prefixos de CEP como `01310` virem o
  número `1310`.
- **Carga atômica.** As 9 tabelas são recriadas em uma única transação: se qualquer arquivo violar
  o contrato (colunas obrigatórias ou arquivo vazio), há rollback e o warehouse permanece intacto.
- **Idempotente.** Rodar a ingestão N vezes produz o mesmo estado. O download só acontece se
  faltar algum arquivo (ou com `--force-download`).
- **Auditoria.** Toda tabela raw tem `_source_file` e `_loaded_at`.

**Transformação (dbt)**

| Camada | Materialização | Papel |
|---|---|---|
| `staging` | view | 1:1 com a fonte: renomeia, tipa e limpa. Sem joins. |
| `intermediate` | view | Regras de negócio e mudança de granularidade (ex.: pagamentos → pedido). |
| `marts` | table | Modelo estrela consumido pelo BI. |

Modelo estrela (`marts`):

- **Fatos:** `fct_orders` (1 linha por pedido) e `fct_order_items` (1 linha por item)
- **Dimensões:** `dim_customers`, `dim_products`, `dim_sellers`, `dim_dates`

Armadilhas do dataset tratadas na modelagem (identificadas por perfilamento dos dados):

- **Pagamentos múltiplos:** ~3 mil pedidos têm mais de um pagamento. São agregados por pedido
  *antes* do join, para não duplicar a receita.
- **Avaliações:** `review_id` não é único e ~550 pedidos têm mais de uma avaliação. Fica a mais
  recente, com desempate determinístico.
- **Cliente real:** a Olist gera um `customer_id` por pedido. A dimensão usa o
  `customer_unique_id`, sem o qual a taxa de recompra seria sempre 0%.
- **Geolocalização:** vários pontos por CEP, grafias divergentes e pontos fora do Brasil.
  Consolidado pela mediana das coordenadas dentro do território nacional.
- **Atraso de entrega:** comparado no nível de dia, porque a data prometida não tem hora.

Qualidade: mais de 100 testes dbt (unicidade, não nulo, integridade referencial, domínios) rodam
a cada `make transform`. Reconciliação validada: o valor total dos itens bate nas três camadas.

## Estrutura

```
├── src/brasil_ecommerce/   # pacote Python (configuração, ingestão, orquestração)
├── transform/              # projeto dbt (fase 3)
├── tests/                  # testes automatizados
├── notebooks/              # análise exploratória
├── data/                   # dados locais, fora do git (raw/ + warehouse.duckdb)
├── pyproject.toml          # dependências e configuração das ferramentas
└── Makefile                # interface de comandos
```

## Roadmap

- [x] **Fase 1: fundação** (git, uv, ruff, pre-commit, configuração centralizada, testes)
- [x] **Fase 2: ingestão** (Kaggle → DuckDB, camada raw com validação)
- [x] **Fase 3: transformação** (dbt: staging → intermediate → marts)
- [ ] **Fase 4: qualidade** (testes de dados e regras de negócio)
- [ ] **Fase 5: orquestração** (Dagster)
- [ ] **Fase 6: visualização** (Evidence.dev)
- [ ] **Fase 7: CI/CD e documentação**

## Licença

MIT
