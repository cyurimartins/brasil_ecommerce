import streamlit as st
from comum import barras, consultar, filtros, inteiro, linha, mostrar, percentual

st.title("Clientes")
st.caption("Cliente = pessoa real (customer_unique_id), não o identificador gerado a cada pedido.")
f = filtros()

r = consultar("resumo", f).iloc[0]
c1, c2 = st.columns(2)
c1.metric("Clientes no período", inteiro(r.clientes))
c2.metric(
    "Clientes que recompraram",
    percentual(r.pct_recompra),
    help="Clientes com mais de um pedido válido dentro do período filtrado.",
)

st.subheader("Clientes novos por mês")
novos = consultar("clientes_novos_mensal", f)
mostrar(linha(novos, "mes", "clientes_novos", "Clientes novos", inteiro), novos, "clientes novos")

st.subheader("Top 10 UFs por número de clientes")
uf = consultar("clientes_por_uf", f).head(10)
mostrar(barras(uf, "uf", "clientes", "Clientes", inteiro, horizontal=True), uf, "clientes por UF")
