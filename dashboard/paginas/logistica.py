import streamlit as st
from comum import barras, consultar, decimal, filtros, linha, moeda, mostrar, percentual

st.title("Logística")
st.caption("Prazos em dias corridos, da compra à entrega. Distância em linha reta entre os CEPs.")
f = filtros()

r = consultar("resumo", f).iloc[0]
c1, c2 = st.columns(2)
c1.metric("Prazo médio de entrega", f"{decimal(r.dias_entrega)} dias")
c2.metric("Pedidos com atraso", percentual(r.pct_atraso))

st.subheader("Prazo prometido × prazo realizado")
st.caption(
    "A promessa é muito maior que o prazo real: margem de segurança alta e pouco competitiva."
)
prazo = consultar("prazo_mensal", f)
mostrar(
    linha(prazo, "mes", "dias", "Dias", lambda v: f"{decimal(v)} dias", serie="serie"),
    prazo,
    "prazos mensais",
)

st.subheader("% de pedidos atrasados por UF do cliente")
uf = consultar("atraso_por_uf", f)
grafico_uf = barras(uf, "uf", "pct_atraso", "% atrasados", percentual, rotular=False)
mostrar(grafico_uf, uf, "atraso por UF")

dist = consultar("logistica_por_distancia", f)
st.subheader("Efeito da distância vendedor → cliente")
st.caption("Faixas de distância em km, em linha reta entre os CEPs do vendedor e do cliente.")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Frete médio por item**")
    mostrar(barras(dist, "faixa", "frete_medio", "R$", moeda, horizontal=True), dist, "frete")
with col2:
    st.markdown("**Frete como % do preço**")
    mostrar(
        barras(dist, "faixa", "frete_sobre_preco", "% do preço", percentual, horizontal=True),
        dist,
        "frete/preço",
    )
with col3:
    st.markdown("**Prazo médio de entrega**")
    mostrar(
        barras(dist, "faixa", "dias_entrega", "Dias", lambda v: f"{decimal(v)} d", horizontal=True),
        dist,
        "prazo por distância",
    )
