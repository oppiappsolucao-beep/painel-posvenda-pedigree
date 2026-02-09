import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request
import urllib.error
import io
from zoneinfo import ZoneInfo

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
def normalize_colname(name: str) -> str:
    """Normaliza nomes de colunas vindos do Google Sheets/CSV:
    - remove BOM e NBSP
    - troca ° por º
    - colapsa espaços
    - lowercase
    """
    s = str(name).replace("\ufeff", "").replace("\u00a0", " ")
    s = s.replace("°", "º")
    s = " ".join(s.split())
    return s.strip().lower()

def pick_first_existing(df, candidates):
    """Escolhe a primeira coluna existente comparando por nome normalizado."""
    col_map = {normalize_colname(c): c for c in df.columns}  # normalizado -> real
    for cand in candidates:
        key = normalize_colname(cand)
        if key in col_map:
            return col_map[key]
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

def is_aguardando(status):
    return norm(status) == "aguardando"

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

# ✅ IMPORTANTE: NÃO usar components.html (causa removeChild em produção)
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
    st.markdown(html, unsafe_allow_html=True)

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

        # ✅ limpa/normaliza nomes (remove NBSP, troca ° -> º, strip)
        df.columns = [
            str(c)
            .replace("\ufeff", "")
            .replace("\u00a0", " ")
            .replace("°", "º")
            .strip()
            for c in df.columns
        ]
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
# DETECÇÃO DE COLUNAS (ROBUSTA)
# ===============================
COL_MES = pick_first_existing(df, ["Mês", "Mes", "MÊS", "MES"])
COL_UNIDADE = pick_first_existing(df, ["Unidade", "Loja", "Unidade/Loja", "UNIDADE"])
COL_RACA = pick_first_existing(df, ["Raça", "Raca", "RAÇA", "RACA"])

COL_C1 = pick_first_existing(df, ["1º contato", "1 contato", "1º Contato", "Primeiro contato", "1o contato"])
COL_S1 = pick_first_existing(df, ["Status 1º contato", "Status 1 contato", "Status 1", "Status Primeiro contato"])

COL_C2 = pick_first_existing(df, [
    "2º contato", "2 contato", "2º Contato", "Segundo contato", "2o contato",
    "2° contato", "2° Contato", "2ºcontato", "2°contato", "Contato 2", "Contato2"
])
COL_S2 = pick_first_existing(df, [
    "Status 2º contato", "Status 2 contato", "Status 2", "Status Segundo contato",
    "Status 2° contato", "Status 2° Contato", "Status 2ºcontato", "Status contato 2", "Status Contato 2"
])

COL_C3 = pick_first_existing(df, [
    "3º contato", "3 contato", "3º Contato", "Terceiro contato", "3o contato",
    "3° contato", "3° Contato", "3ºcontato", "3°contato", "Contato 3", "Contato3"
])
COL_S3 = pick_first_existing(df, [
    "Status 3º contato", "Status 3 contato", "Status 3", "Status Terceiro contato",
    "Status 3° contato", "Status 3° Contato", "Status 3ºcontato", "Status contato 3", "Status Contato 3"
])

COL_VALOR = pick_first_existing(df, ["Valor do filhote", "Valor de filhote", "Valor Filhote", "Valor", "Valor do Filhote"])
COL_VENDEDOR = pick_first_existing(df, ["Vendedor", "Vendedora", "Atendente", "Consultor", "Responsável"])

missing_essenciais = [c for c in [COL_MES, COL_UNIDADE, COL_RACA] if c is None]
if missing_essenciais:
    st.error("❌ Faltam colunas essenciais (Mês/Unidade/Raça) ou estão com nome diferente.")
    st.write("Colunas encontradas na planilha:")
    st.write(df.columns.tolist())
    st.stop()

# ===============================
# DEBUG (opcional)
# ===============================
with st.expander("🔎 DEBUG — Detecção de colunas (clique para abrir)"):
    st.write({
        "COL_MES": COL_MES,
        "COL_UNIDADE": COL_UNIDADE,
        "COL_RACA": COL_RACA,
        "COL_C1": COL_C1, "COL_S1": COL_S1,
        "COL_C2": COL_C2, "COL_S2": COL_S2,
        "COL_C3": COL_C3, "COL_S3": COL_S3,
        "COL_VALOR": COL_VALOR,
        "COL_VENDEDOR": COL_VENDEDOR,
    })

# ===============================
# CONVERSÕES (datas)
# ===============================
for col in [COL_C1, COL_C2, COL_C3]:
    if col and col in df.columns:
        s = df[col].astype(str).str.replace("\u00a0", " ", regex=False).str.strip()
        s = s.str.extract(r"(\d{1,2}/\d{1,2}/\d{4})", expand=False)
        df[col] = pd.to_datetime(s, errors="coerce", dayfirst=True)

# ✅ hoje no fuso do Brasil
hoje = pd.Timestamp.now(tz=ZoneInfo("America/Sao_Paulo")).date()

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

# ✅ f_mes: usado para VENDAS/FATURAMENTO/GRÁFICOS (depende do Mês)
f_mes = df[df[COL_MES].astype(str) == str(mes)].copy()
if unidade != "Todas":
    f_mes = f_mes[f_mes[COL_UNIDADE].astype(str) == str(unidade)]

# ✅ f_hoje: usado para CONTATOS HOJE (IGNORA coluna Mês, usa só a data do contato)
f_hoje = df.copy()
if unidade != "Todas":
    f_hoje = f_hoje[f_hoje[COL_UNIDADE].astype(str) == str(unidade)]

with st.expander("🧪 DEBUG — Contagens na data de hoje (contatos ignoram Mês)"):
    st.write("Hoje (Brasil):", str(hoje))
    for label, dc in [("1º contato", COL_C1), ("2º contato", COL_C2), ("3º contato", COL_C3)]:
        if dc and dc in f_hoje.columns:
            st.write(
                label,
                "coluna:", dc,
                "=> matches hoje:", int((f_hoje[dc].dt.date == hoje).sum()),
                "não-nulos:", int(f_hoje[dc].notna().sum())
            )
        else:
            st.write(label, "=> coluna NÃO encontrada")

# ===============================
# CONTATOS HOJE (AGORA USA f_hoje)
# ===============================
def count_today(date_col):
    if not date_col or date_col not in f_hoje.columns:
        return 0
    sub = f_hoje[f_hoje[date_col].dt.date == hoje]
    return int(len(sub))

def count_today_by_status(date_col, status_col, kind: str) -> int:
    """Conta registros na data de hoje, separados por status (enviado/aguardando/erro)."""
    if not date_col or date_col not in f_hoje.columns:
        return 0

    sub = f_hoje[f_hoje[date_col].dt.date == hoje]
    if not status_col or status_col not in sub.columns:
        return 0

    kind = (kind or "").strip().lower()
    if kind == "enviado":
        sub = sub[sub[status_col].apply(is_sent)]
    elif kind == "aguardando":
        sub = sub[sub[status_col].apply(is_aguardando)]
    elif kind == "erro":
        sub = sub[sub[status_col].apply(is_error)]
    else:
        return 0

    return int(len(sub))

records_today = []
if setor == "Pós-Venda":
    c1 = count_today(COL_C1)
    c2 = count_today(COL_C2)
    c3 = count_today(COL_C3)

    c1_enviado = count_today_by_status(COL_C1, COL_S1, "enviado")
    c1_aguardando = count_today_by_status(COL_C1, COL_S1, "aguardando")

    c2_enviado = count_today_by_status(COL_C2, COL_S2, "enviado")
    c2_aguardando = count_today_by_status(COL_C2, COL_S2, "aguardando")

    c3_enviado = count_today_by_status(COL_C3, COL_S3, "enviado")
    c3_aguardando = count_today_by_status(COL_C3, COL_S3, "aguardando")

    # registros do dia para pizza (usa f_hoje, não f_mes)
    for _, r in f_hoje.iterrows():
        for dc, sc in [(COL_C1, COL_S1), (COL_C2, COL_S2), (COL_C3, COL_S3)]:
            if dc and pd.notna(r.get(dc)) and pd.to_datetime(r.get(dc)).date() == hoje:
                records_today.append(status_bucket_today(r.get(sc) if sc else ""))
else:
    c1 = c2 = c3 = 0
    c1_enviado = c1_aguardando = 0
    c2_enviado = c2_aguardando = 0
    c3_enviado = c3_aguardando = 0

erro_hoje = records_today.count("Erro")

# ✅ Vendas/Faturamento continuam por mês
vendas_mes = len(f_mes)
faturamento = f_mes[COL_VALOR].apply(brl_to_float).sum() if (COL_VALOR and COL_VALOR in f_mes.columns) else 0

# ===============================
# KPIs
# ===============================
st.markdown("---")
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: kpi_card("💬 1º contato hoje", c1, f"{c1_enviado} enviados • {c1_aguardando} aguardando", NAVY)
with k2: kpi_card("💬 2º contato hoje", c2, f"{c2_enviado} enviados • {c2_aguardando} aguardando", NAVY_2)
with k3: kpi_card("💬 3º contato hoje", c3, f"{c3_enviado} enviados • {c3_aguardando} aguardando", WINE_2)
with k4: kpi_card("⚠️ Status com erro", erro_hoje, "atenção", WINE, value_color="#ef4444" if erro_hoje else "#0f172a")
with k5: kpi_card("🛍️ Vendas no mês", vendas_mes, str(mes), "#F59E0B")
with k6: kpi_card("💰 Faturamento", money_br(faturamento), "valor do filhote", NAVY, value_size=28)

# ===============================
# GRÁFICOS (USAM f_mes)
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
    vp = f_mes.groupby(COL_UNIDADE).size().reset_index(name="Total")
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
    vr = (f_mes.groupby(COL_RACA).size().reset_index(name="Total")
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
    if COL_VENDEDOR and (COL_VENDEDOR in f_mes.columns):
        vv = (f_mes.groupby(COL_VENDEDOR).size().reset_index(name="Total")
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
