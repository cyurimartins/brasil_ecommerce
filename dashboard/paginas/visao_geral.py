import streamlit as st
from comum import consultar, decimal, filtros, inteiro, linha, moeda, mostrar, percentual

st.title("Visão geral")
st.caption(
    "Marketplace Olist, 2016–2018. **Faturamento** = mercadoria + frete dos pedidos válidos "
    "(exceto cancelados e indisponíveis). Prazos e atrasos consideram só pedidos entregues."
)

f = filtros()
r = consultar("resumo", f).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Faturamento", moeda(r.faturamento))
c2.metric("Pedidos", inteiro(r.pedidos))
c3.metric("Ticket médio", moeda(r.ticket_medio))
c4.metric("Clientes", inteiro(r.clientes))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pedidos com atraso", percentual(r.pct_atraso))
c2.metric("Prazo médio de entrega", f"{decimal(r.dias_entrega)} dias")
c3.metric("Nota média", f"{decimal(r.nota_media, 2)} / 5")
c4.metric("Clientes que recompraram", percentual(r.pct_recompra))

st.subheader("Faturamento mensal")
mensal = consultar("faturamento_mensal", f)
fig = linha(mensal, "mes", "faturamento", "Faturamento (R$)", moeda)
if not mensal.empty:
    pico = mensal.loc[mensal["faturamento"].idxmax()]
    fig.add_annotation(
        x=pico["mes"], y=pico["faturamento"], text="Pico: Black Friday" if pico["mes"].month == 11
        else "Pico do período", showarrow=True, arrowhead=0, ay=-30,
    )  # fmt: skip
mostrar(fig, mensal, "faturamento mensal")

nota = consultar("nota_no_prazo_x_atrasado", f).iloc[0]
st.info(
    f"**Principal achado:** pedidos entregues **no prazo** têm nota média "
    f"**{decimal(nota.nota_no_prazo, 2)}**; pedidos **atrasados**, "
    f"**{decimal(nota.nota_atrasado, 2)}**. O atraso é o maior detrator da satisfação "
    "(detalhes nas páginas Logística e Satisfação).",
    icon="💡",
)
