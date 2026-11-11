"""Componentes compartilhados: acesso a dados, filtros, formatação e gráficos.

Diretrizes visuais: uma cor por série (paleta validada para daltonismo, com passos
próprios para o modo escuro), um único eixo Y por gráfico, marcas finas, grade
discreta, tooltip em todos os gráficos e uma tabela com os dados de cada gráfico.
"""

from collections.abc import Callable
from datetime import date

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from brasil_ecommerce.config import get_settings
from brasil_ecommerce.dashboard import queries
from brasil_ecommerce.dashboard.queries import Filtros

# Paleta categórica validada (slots 1 e 2), com passos próprios para o modo escuro.
_PALETA = {
    "light": {"serie_1": "#2a78d6", "serie_2": "#eb6834", "grade": "#e7e6e2"},
    "dark": {"serie_1": "#3987e5", "serie_2": "#d95926", "grade": "#383835"},
}

MESES = [
    "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez",
]  # fmt: skip


# --------------------------------------------------------------------------- dados


def _tema() -> str:
    tipo = getattr(st.context.theme, "type", None)
    return "dark" if tipo == "dark" else "light"


def cor(nome: str) -> str:
    return _PALETA[_tema()][nome]


@st.cache_data(show_spinner=False)
def _executar(nome: str, filtros: Filtros, versao: int) -> pd.DataFrame:
    # `versao` (data de modificação do arquivo) invalida o cache a cada publicação.
    with duckdb.connect(str(get_settings().consulta_path), read_only=True) as con:
        return getattr(queries, nome)(con, filtros)


@st.cache_data(show_spinner=False)
def _ufs(versao: int) -> list[str]:
    with duckdb.connect(str(get_settings().consulta_path), read_only=True) as con:
        return queries.ufs_disponiveis(con)


def _versao() -> int:
    caminho = get_settings().consulta_path
    if not caminho.is_file():
        st.error(
            f"Banco de consulta não encontrado em `{caminho}`. "
            "Rode `make run` para executar o pipeline e publicá-lo."
        )
        st.stop()
    return caminho.stat().st_mtime_ns


def consultar(nome: str, filtros: Filtros) -> pd.DataFrame:
    return _executar(nome, filtros, _versao())


# --------------------------------------------------------------------------- filtros


def _meses_disponiveis() -> list[date]:
    return list(pd.date_range("2016-09-01", "2018-10-01", freq="MS").date)


def _rotulo_mes(d: date) -> str:
    return f"{MESES[d.month - 1]}/{d.year}"


def filtros() -> Filtros:
    """Linha única de filtros no topo da página; o estado é mantido entre páginas."""
    meses = _meses_disponiveis()
    padrao = (date(2017, 1, 1), date(2018, 8, 1))
    col_periodo, col_uf = st.columns([3, 2])
    with col_periodo:
        inicio, fim = st.select_slider(
            "Período (mês da compra)",
            options=meses,
            value=st.session_state.get("periodo", padrao),
            format_func=_rotulo_mes,
            key="periodo",
            help="O padrão exclui as bordas do dataset (meses com poucos pedidos).",
        )
    with col_uf:
        ufs = st.multiselect(
            "UF do cliente",
            options=_ufs(_versao()),
            default=st.session_state.get("ufs", []),
            key="ufs",
            placeholder="Todas as UFs",
        )
    fim_exclusivo = (pd.Timestamp(fim) + pd.offsets.MonthBegin(1)).date()
    return Filtros(inicio=inicio, fim=fim_exclusivo, ufs=tuple(sorted(ufs)))


# --------------------------------------------------------------------------- formatação


def _br(valor: float, casas: int = 0) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def moeda(valor: float) -> str:
    if valor >= 1_000_000:
        return f"R$ {_br(valor / 1_000_000, 2)} mi"
    if valor >= 1_000:
        return f"R$ {_br(valor / 1_000, 1)} mil"
    return f"R$ {_br(valor, 2)}"


def inteiro(valor: float) -> str:
    return _br(valor, 0)


def decimal(valor: float, casas: int = 1) -> str:
    return _br(valor, casas)


def percentual(valor: float, casas: int = 1) -> str:
    return f"{_br(valor * 100, casas)}%"


# --------------------------------------------------------------------------- gráficos


def _layout(fig: go.Figure, titulo_y: str, altura: int = 340, eixo_pct: bool = False) -> go.Figure:
    fig.update_layout(
        height=altura,
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        separators=",.",
        showlegend=False,
        hoverlabel={"namelength": -1},
        barcornerradius=4,
        bargap=0.35,
    )
    fig.update_yaxes(
        title_text=titulo_y, gridcolor=cor("grade"), gridwidth=1, zeroline=False, rangemode="tozero"
    )
    fig.update_xaxes(showgrid=False, title_text=None)
    fig.update_yaxes(tickformat=".0%" if eixo_pct else ",~r", exponentformat="none")
    return fig


def mostrar(fig: go.Figure, dados: pd.DataFrame, nome_tabela: str) -> None:
    """Exibe o gráfico com a tabela de dados equivalente (acessibilidade)."""
    st.plotly_chart(fig, width="stretch", theme="streamlit", config={"displayModeBar": False})
    with st.expander(f"Ver dados: {nome_tabela}"):
        st.dataframe(dados, width="stretch", hide_index=True)


def linha(
    df: pd.DataFrame,
    x: str,
    y: str,
    titulo_y: str,
    formato: Callable[[float], str],
    serie: str | None = None,
) -> go.Figure:
    """Linha temporal; com `serie`, até 2 séries no mesmo eixo, com rótulo direto no fim."""
    fig = go.Figure()
    df = df.assign(**{x: [_rotulo_mes(d) for d in pd.to_datetime(df[x]).dt.date]})
    grupos = [(None, df)] if serie is None else list(df.groupby(serie, sort=False))
    for i, (nome, dados) in enumerate(grupos):
        c = cor(f"serie_{i + 1}")
        fig.add_scatter(
            x=dados[x],
            y=dados[y],
            name=nome or titulo_y,
            mode="lines+markers",
            line={"width": 2, "color": c},
            marker={"size": 8, "color": c, "line": {"width": 2, "color": "rgba(0,0,0,0)"}},
            customdata=[formato(v) for v in dados[y]],
            hovertemplate="%{customdata}<extra>%{fullData.name}</extra>",
        )
        if serie is not None:
            fim = dados.iloc[-1]
            fig.add_annotation(
                x=fim[x], y=fim[y], text=f"<b>{nome}</b>", showarrow=False,
                xanchor="left", xshift=10, font={"size": 12},
            )  # fmt: skip
    fig = _layout(fig, titulo_y)
    fig.update_layout(hovermode="x unified")
    rotulos = list(dict.fromkeys(df[x]))
    fig.update_xaxes(type="category", tickvals=rotulos[::3], categoryarray=rotulos)
    if serie is not None:
        fig.update_layout(showlegend=True, legend={"orientation": "h", "y": 1.08, "x": 0})
        fig.update_layout(margin={"r": 120})
    return fig


def barras(
    df: pd.DataFrame,
    categoria: str,
    valor: str,
    titulo_valor: str,
    formato: Callable[[float], str],
    horizontal: bool = False,
    rotular: bool = True,
) -> go.Figure:
    """Barras de uma única série (uma cor); a ordem das categorias é a do DataFrame."""
    textos = [formato(v) for v in df[valor]]
    fig = go.Figure()
    fig.add_bar(
        x=df[valor] if horizontal else df[categoria],
        y=df[categoria] if horizontal else df[valor],
        orientation="h" if horizontal else "v",
        marker={"color": cor("serie_1"), "line": {"width": 0}},
        customdata=textos,
        text=textos if rotular else None,
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{" + ("y" if horizontal else "x") + "}: %{customdata}<extra></extra>",
    )
    altura = max(260, 34 * len(df) + 40) if horizontal else 340
    eixo_pct = formato is percentual
    fig = _layout(
        fig, "" if horizontal else titulo_valor, altura, eixo_pct=eixo_pct and not horizontal
    )
    fig.update_traces(textfont={"size": 12})
    if horizontal:
        fig.update_yaxes(autorange="reversed", title_text=None, showgrid=False)
        fig.update_xaxes(title_text=titulo_valor, showgrid=True, gridcolor=cor("grade"))
        fig.update_xaxes(tickformat=".0%" if eixo_pct else ",~r", exponentformat="none")
        if rotular and len(df):
            fig.update_xaxes(range=[0, float(df[valor].max()) * 1.3])
    else:
        fig.update_xaxes(tickangle=0)
        if rotular and len(df):
            fig.update_yaxes(range=[0, float(df[valor].max()) * 1.15])
        fig.update_layout(margin={"r": 70})
    return fig
