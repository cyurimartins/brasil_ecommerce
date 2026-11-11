"""Dashboard do e-commerce brasileiro (Olist).

Execução: ``make dashboard`` (ou ``uv run streamlit run dashboard/app.py``).
Lê o banco de consulta publicado pelo pipeline (data/consulta.duckdb).
"""

import streamlit as st

st.set_page_config(page_title="Brasil E-commerce", page_icon="📦", layout="wide")

paginas = [
    st.Page("paginas/visao_geral.py", title="Visão geral", icon="📊", default=True),
    st.Page("paginas/vendas.py", title="Vendas", icon="🛒"),
    st.Page("paginas/logistica.py", title="Logística", icon="🚚"),
    st.Page("paginas/satisfacao.py", title="Satisfação", icon="⭐"),
    st.Page("paginas/clientes.py", title="Clientes", icon="👥"),
]
st.navigation(paginas).run()
