# Guia: dashboard no Tableau Public

O Tableau Public não se conecta ao DuckDB. Por isso o pipeline exporta os marts em CSV
(*asset* `exportacao_tableau`), sempre a partir do banco de consulta, ou seja, só com dados
aprovados nos testes.

## 1. Gerar os arquivos

```bash
make run
```

Os CSVs ficam em `data/exports/tableau/`:

| Arquivo | Linhas | Granularidade |
|---|---|---|
| `fato_pedidos.csv` | 99.441 | 1 linha por pedido |
| `fato_itens_pedido.csv` | 112.650 | 1 linha por item de pedido |
| `dim_clientes.csv` | 96.096 | 1 linha por cliente real |
| `dim_produtos.csv` | 32.951 | 1 linha por produto |
| `dim_vendedores.csv` | 3.095 | 1 linha por vendedor |
| `dim_datas.csv` | 1.096 | 1 linha por dia (2016–2018) |

Formato: UTF-8, separador vírgula, ponto decimal, datas `AAAA-MM-DD`.

## 2. Modelo de dados (relacionamentos)

No Tableau Public Desktop: **Conectar → Arquivo de texto → `fato_pedidos.csv`**. Depois
arraste os demais arquivos para a tela de fonte de dados e crie **relacionamentos** (a
"linha macarrão"), não *joins*. Assim cada tabela mantém a própria granularidade e o Tableau
não duplica valores.

| De | Para | Campos |
|---|---|---|
| `fato_pedidos` | `dim_clientes` | `id_cliente` = `id_cliente` |
| `fato_pedidos` | `dim_datas` | `data_compra` = `data_calendario` |
| `fato_pedidos` | `fato_itens_pedido` | `id_pedido` = `id_pedido` |
| `fato_itens_pedido` | `dim_produtos` | `id_produto` = `id_produto` |
| `fato_itens_pedido` | `dim_vendedores` | `id_vendedor` = `id_vendedor` |

⚠️ **Confira os tipos** depois de conectar: `prefixo_cep` deve ser **texto** (senão o Tableau
remove os zeros à esquerda), e os campos `data_*` devem ser **data** ou **data e hora**.

## 3. Mesmas definições do dashboard Streamlit

Para os números dos dois dashboards baterem, use as mesmas regras:

| Métrica | Campo calculado no Tableau |
|---|---|
| Pedido válido | `NOT [status_pedido] IN ('canceled', 'unavailable')` |
| Faturamento | `SUM(IF [Pedido válido] THEN [valor_pedido] END)` |
| Pedidos | `COUNTD(IF [Pedido válido] THEN [id_pedido] END)` |
| Ticket médio | `[Faturamento] / [Pedidos]` |
| % atraso | `AVG(IF [entregue] THEN INT([atrasado]) END)` |
| Prazo médio (dias) | `AVG(IF [entregue] THEN [dias_ate_entrega] END)` |
| Nota média | `AVG([nota_avaliacao])` |

Período padrão: **jan/2017 a ago/2018**. As bordas do dataset têm poucos pedidos e distorcem
as séries.

Valores de referência no período padrão, com todas as UFs: faturamento **R$ 15,68 mi**,
**97.910** pedidos, ticket médio **R$ 160,18**, **6,8%** de atraso, nota média **4,09**.

## 4. Sugestão de layout

O Streamlit cobre a visão analítica completa. No Tableau, a sugestão é **um painel executivo
focado em logística**, o tema mais ligado à experiência em cabotagem:

```
┌───────────────────────────────────────────────────────────────┐
│ Filtros: período · UF do cliente                              │
├──────────┬──────────┬──────────┬──────────┬──────────────────┤
│Faturam.  │ Pedidos  │ % atraso │ Prazo    │ Nota: no prazo × │
│          │          │          │ médio    │ atrasado         │
├──────────┴──────────┴──────────┼──────────┴──────────────────┤
│ Mapa do Brasil: % de atraso    │ Prazo prometido × realizado │
│ por UF (cor sequencial,        │ (linhas mensais)            │
│ uma única cor)                 │                             │
├────────────────────────────────┼─────────────────────────────┤
│ Nota média por faixa de atraso │ Frete como % do preço por   │
│ (barras)                       │ faixa de distância          │
└────────────────────────────────┴─────────────────────────────┘
```

O **mapa por UF** é o diferencial em relação ao Streamlit: o Tableau reconhece siglas de UF
como papel geográfico ("Estado/Província", país Brasil).

## 5. Publicar

**Arquivo → Salvar no Tableau Public**. Depois de publicar, adicione o link no README do
projeto e no seu perfil do LinkedIn.
