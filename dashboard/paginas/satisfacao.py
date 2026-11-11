import streamlit as st
from comum import barras, consultar, decimal, filtros, mostrar, percentual

st.title("Satisfação")
f = filtros()

nota = consultar("nota_no_prazo_x_atrasado", f).iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Nota média: entregue no prazo", f"{decimal(nota.nota_no_prazo, 2)} / 5")
c2.metric("Nota média: entregue com atraso", f"{decimal(nota.nota_atrasado, 2)} / 5")
c3.metric(
    "Diferença",
    f"{decimal(nota.nota_no_prazo - nota.nota_atrasado, 2)} ponto(s)",
    help="Quanto a nota média cai quando o pedido atrasa.",
)

st.subheader("Nota média por faixa de atraso")
st.caption("Até a data prometida a nota fica acima de 4; a partir de 4 dias de atraso, despenca.")
faixa = consultar("nota_por_atraso", f)
mostrar(
    barras(faixa, "faixa", "nota_media", "Nota média (1 a 5)", lambda v: decimal(v, 2)),
    faixa,
    "nota por atraso",
)

st.subheader("Distribuição das notas")
dist = consultar("distribuicao_notas", f)
dist["nota"] = dist["nota"].map(lambda n: f"{n} ★")
mostrar(barras(dist, "nota", "participacao", "% das avaliações", percentual), dist, "notas")
