import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import plotly.express as px
import urllib.request
import urllib.error
import io

# ===============================
# CONFIG
# ===============================
SPREADSHEET_ID = "1Q0mLvOBxEGCojUITBLxCXRtpXVMAHE3ngvGsa2Cgf9Q"
GID = "1396326144"  # sua aba

SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export"
    f"?format=csv&gid={GID}"
)

st.set_page_config(page_title="Painel Pós-Venda", layout="wide")

# ===============================
# CSS
# ===============================
st.markdown(
    """
    <style>
        .stApp { background-color: #F3F4F6; }
        .block-container {
            padding-top: 2.4rem !important;
            padding-bottom: 1.6rem !important;
        }
        h1, h2, h3, h4 { margin-top: 0 !important; padding-top: 0 !important; }
        div[data-baseweb="select"] { margin-top: 10px; }

        .panel-card{
            background:#ffffff;
            border-radius:18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
            border: 1px solid rgba(15,23,42,0.06);
            overflow: hidden;
        }
        .panel-head{
            padding: 14px 16px 0px 16px;
            background:#ffffff;
        }
        .panel-title{
            font-weight: 900;
            color:#0f172a;
            font-size: 18px;
            display:flex;
            align-items:center;
            gap:8px;
        }
        .panel-body{
            padding: 8px 10px 12px 10px;
            background:#ffffff;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ===============================
# PALETA
# ===============================
NAVY = "#1B1D6D"
WINE = "#9B0033"
NAVY_2 = "#2E3192"
WINE_2 = "#C00040"
GRAY = "#64748b"
BAR_SEQ = [NAVY, WINE, NAVY_2, WINE_2, "#334155", "#94a3b8"]

# ===============================
# HELPERS
# ===============================
def pick_first_existing(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def norm(x):
    return str(x).strip().lower() if pd.notna(x) else ""

def is_done(status):
    return norm(status) in [
        "feito", "concluido", "concluído", "ok",
        "realizado", "finalizado", "concluida", "concluída"
    ]

def is_error(status):
    s = norm(status)
    return ("erro" in s) or ("atras" in s) or ("pendenc" in s)

def is_sent(status):
    s = norm(status)
    return ("enviado" in s) or ("enviada" in s)

def status_bucket_today(status):
    if is_error(status):
        return "Erro"
    if is_sent(status):
        return "Enviado"
    return "Aguardando"

def brl_to_float(v):
    if pd.isna(v):
        return 0.0
    s = str(v).replace("R$", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return 0.0

def money_br(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def kpi_card(title, value, subtitle, accent, value_color="#0f172a", value_size=38):
    html = f"""
    <div style="
        background:#ffffff;
        border-radius:16px;
        padding:16px;
        border-left:8px solid {accent};
        box-shadow:0 8px 20px rgba(15,23,42,.06);
        height:120px;
        font-family:Inter,Arial,sans-serif;
    ">
        <div style="font-size:14px;font-weight:900;color:#334155;">{title}</div>
        <div style="font-size:{value_size}px;font-weight:900;color:{value_color};
                    line-height:1.05;margin-top:6px;">
            {value}
        </div>
        <div style="font-size:12px;color:{GRAY};margin-top:6px;">{subtitle}</div>
    </div>
    """
    components.html(html, height=130)

def tune_plotly(fig, height=360):
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(t=6, b=6, l=6, r=6),
        font=dict(color="#0f172a"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(15,23,42,0.06)", zeroline=False)
    return fig

# ===============================
# LOAD DATA (com timeout)
# ===============================
@st.cache_data(ttl=60)
def load_sheet(url: str) -> pd.DataFrame:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()

        df = pd.read_csv(io.BytesIO(content))
        # limpa nomes de colunas
        df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]
        return df

    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTPError {e.code} ao acessar a planilha. Verifique se está pública.")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URLError ao acessar a planilha: {e}")
    except Exception as e:
        raise RuntimeError(f"Erro ao ler CSV da planilha: {e}")

# ===============================
# CARREGA PLANILHA
# ===============================
with st.spinner("Carregando dados da planilha..."):
    try:
        df = load_sheet(SHEET_CSV_URL)
    except Exception as e:
        st.error("❌ Não consegui carregar a planilha.")
        st.caption("Teste este link em aba anônima (sem login). Se pedir login, não está pública:")
        st.code(SHEET_CSV_URL)
        st.exception(e)
        st.stop()

# ===============================
# DETECÇÃO DE COLUNAS (robusta)
# ===============================
COL_MES = pick_first_existing(df, ["Mês", "Mes", "MÊS", "MES"])
COL_UNIDADE = pick_first_existing(df, ["Unidade", "Loja", "Unidade/Loja", "UNIDADE"])
COL_RACA = pick_first_existing(df, ["Raça", "Raca", "RAÇA", "RACA"])

COL_C1 = pick_first_existing(df, ["1º contato", "1 contato", "1º Contato", "Primeiro contato", "1o contato"])
COL_S1 = pick_first_existing(df, ["Status 1º contato", "Status 1 contato", "Status 1", "Status Primeiro contato"])

COL_C2 = pick_first_existing(df, ["2º contato", "2 contato", "2º Contato", "Segundo contato", "2o contato"])
COL_S2 = pick_first_existing(df, ["Status 2º contato", "Status 2 contato", "Status 2", "Status Segundo contato"])

COL_C3 = pick_first_existing(df, ["3º contato", "3 contato", "3º Contato", "Terceiro contato", "3o contato"])
COL_S3 = pick_first_existing(df, ["Status 3º contato", "Status 3 contato", "Status 3", "Status Terceiro contato"])

COL_VALOR = pick_first_existing(df, ["Valor do filhote", "Valor de filhote", "Valor Filhote", "Valor", "Valor do Filhote"])
COL_VENDEDOR = pick_first_existing(df, ["Vendedor", "Vendedora", "Atendente", "Consultor", "Responsável"])

missing_essenciais = [c for c in [COL_MES, COL_UNIDADE, COL_RACA] if c is None]
if missing_essenciais:
    st.error("❌ Faltam colunas essenciais (Mês/Unidade/Raça) ou estão com nome diferente.")
    st.write("Colunas encontradas na planilha:")
    st.write(df.columns.tolist())
    st.stop()

# ===============================
# CONVERSÕES
# ===============================
for col in [COL_C1, COL_C2, COL_C3]:
    if col and col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

hoje = pd.to_datetime(datetime.date.today())

# ===============================
# HEADER
# ===============================
st.markdown("## 📊 Painel de Pós-Venda")
st.caption(f"Total de registros: **{len(df)}**")

# ===============================
# FILTROS
# ===============================
f1, f2, f3 = st.columns(3)
with f1:
    setor = st.selectbox("Setor", ["Pós-Venda", "Pedigree"])
with f2:
    meses = sorted(df[COL_MES].dropna().astype(str).unique())
    if not meses:
        st.error("❌ A coluna de Mês está vazia.")
        st.stop()
    mes = st.selectbox("Mês", meses, index=len(meses) - 1)
with f3:
    unidades = ["Todas"] + sorted(df[COL_UNIDADE].dropna().astype(str).unique().tolist())
    unidade = st.selectbox("Unidade", unidades)

f = df[df[COL_MES].astype(str) == str(mes)].copy()
if unidade != "Todas":
    f = f[f[COL_UNIDADE].astype(str) == str(unidade)]

# ===============================
# CONTATOS HOJE
# ===============================
def count_today(date_col, status_col):
    if not date_col or date_col not in f.columns:
        return 0
    sub = f[f[date_col].dt.date == hoje.date()]
    if status_col and status_col in sub.columns:
        sub = sub[~sub[status_col].apply(is_done)]
    return int(len(sub))

records_today = []
if setor == "Pós-Venda":
    c1 = count_today(COL_C1, COL_S1)
    c2 = count_today(COL_C2, COL_S2)
    c3 = count_today(COL_C3, COL_S3)

    for _, r in f.iterrows():
        for dc, sc in [(COL_C1, COL_S1), (COL_C2, COL_S2), (COL_C3, COL_S3)]:
            if dc and pd.notna(r.get(dc)) and pd.to_datetime(r.get(dc)).date() == hoje.date():
                records_today.append(status_bucket_today(r.get(sc) if sc else ""))
else:
    c1 = c2 = c3 = 0

erro_hoje = records_today.count("Erro")
vendas_mes = len(f)
faturamento = f[COL_VALOR].apply(brl_to_float).sum() if (COL_VALOR and COL_VALOR in f.columns) else 0

# ===============================
# KPIs
# ===============================
st.markdown("---")
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: kpi_card("💬 1º contato hoje", c1, "pendentes", NAVY)
with k2: kpi_card("💬 2º contato hoje", c2, "pendentes", NAVY_2)
with k3: kpi_card("💬 3º contato hoje", c3, "pendentes", WINE_2)
with k4: kpi_card("⚠️ Status com erro", erro_hoje, "atenção", WINE, value_color="#ef4444" if erro_hoje else "#0f172a")
with k5: kpi_card("🛍️ Vendas no mês", vendas_mes, str(mes), "#F59E0B")
with k6: kpi_card("💰 Faturamento", money_br(faturamento), "valor do filhote", NAVY, value_size=28)

# ===============================
# GRÁFICOS
# ===============================
st.markdown("---")
g1, g2 = st.columns(2)
g3, g4 = st.columns(2)

# 1) Contatos por Status (hoje)
with g1:
    st.markdown(
        '<div class="panel-card"><div class="panel-head"><div class="panel-title">📌 Contatos por Status (hoje)</div></div><div class="panel-body">',
        unsafe_allow_html=True
    )
    counts = {"Aguardando": 0, "Enviado": 0, "Erro": 0}
    for r in records_today:
        counts[r] = counts.get(r, 0) + 1
    df_status = pd.DataFrame({"Status": list(counts.keys()), "Total": list(counts.values())})
    fig = px.pie(
        df_status,
        names="Status",
        values="Total",
        hole=0.55,
        color="Status",
        color_discrete_map={"Aguardando": NAVY, "Enviado": WINE, "Erro": "#ef4444"},
    )
    fig.update_traces(textinfo="label+value", textposition="inside")
    st.plotly_chart(tune_plotly(fig, height=360), use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

# 2) Vendas por loja (Unidade)
with g2:
    st.markdown(
        '<div class="panel-card"><div class="panel-head"><div class="panel-title">🏬 Vendas por loja (Unidade)</div></div><div class="panel-body">',
        unsafe_allow_html=True
    )
    vp = f.groupby(COL_UNIDADE).size().reset_index(name="Total")
    fig = px.bar(
        vp, x=COL_UNIDADE, y="Total", text="Total",
        color=COL_UNIDADE, color_discrete_sequence=BAR_SEQ
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False)
    st.plotly_chart(tune_plotly(fig, height=360), use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

# 3) Raças mais vendidas (mês)
with g3:
    st.markdown(
        '<div class="panel-card"><div class="panel-head"><div class="panel-title">🐶 Raças mais vendidas (mês)</div></div><div class="panel-body">',
        unsafe_allow_html=True
    )
    vr = (f.groupby(COL_RACA).size().reset_index(name="Total")
          .sort_values("Total", ascending=False).head(10))
    fig = px.bar(
        vr, x=COL_RACA, y="Total", text="Total",
        color=COL_RACA, color_discrete_sequence=BAR_SEQ
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False)
    st.plotly_chart(tune_plotly(fig, height=360), use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

# 4) Vendas por vendedora (mês)
with g4:
    st.markdown(
        '<div class="panel-card"><div class="panel-head"><div class="panel-title">🏆 Vendas por vendedora (mês)</div></div><div class="panel-body">',
        unsafe_allow_html=True
    )
    if COL_VENDEDOR and (COL_VENDEDOR in f.columns):
        vv = (f.groupby(COL_VENDEDOR).size().reset_index(name="Total")
              .sort_values("Total", ascending=False))
        fig = px.bar(
            vv, x=COL_VENDEDOR, y="Total", text="Total",
            color=COL_VENDEDOR, color_discrete_sequence=BAR_SEQ
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(showlegend=False)
        st.plotly_chart(tune_plotly(fig, height=360), use_container_width=True)
    else:
        st.info("Coluna de vendedor(a) não encontrada.")
    st.markdown("</div></div>", unsafe_allow_html=True)

