import streamlit as st
from comum import barras, consultar, filtros, inteiro, linha, moeda, mostrar, percentual

st.title("Vendas")
f = filtros()

st.subheader("Faturamento mensal")
mensal = consultar("faturamento_mensal", f)
mostrar(linha(mensal, "mes", "faturamento", "Faturamento (R$)", moeda), mensal, "faturamento")

st.subheader("Pedidos por mês")
mostrar(linha(mensal, "mes", "pedidos", "Pedidos", inteiro), mensal, "pedidos")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top 10 categorias por faturamento")
    cat = consultar("top_categorias", f)
    mostrar(
        barras(cat, "categoria", "faturamento", "Faturamento (R$)", moeda, horizontal=True),
        cat,
        "categorias",
    )
with col2:
    st.subheader("Forma de pagamento principal")
    pag = consultar("formas_pagamento", f)
    mostrar(
        barras(
            pag, "forma_pagamento", "participacao", "% dos pedidos", percentual, horizontal=True
        ),
        pag,
        "formas de pagamento",
    )
