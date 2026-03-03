import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import plotly.express as px

# ===============================
# LOGIN (ADICIONADO - NÃO MUDA O DASHBOARD)
# ===============================
APP_USER = "operacao"
APP_PASS = "100316"

def ensure_login() -> bool:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    # Tela de login (só aparece antes de liberar o dashboard)
    st.markdown(
        """
        <style>
            .stApp { background-color: #F3F4F6; }

            .login-wrap{
                max-width: 560px;
                margin: 9vh auto 0 auto;
                padding: 0 14px;
                font-family: Inter, system-ui, -apple-system, Segoe UI, Arial, sans-serif;
            }

            .login-card{
                background:#ffffff;
                border-radius:18px;
                border: 1px solid rgba(15,23,42,0.06);
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
                padding: 22px 22px 18px 22px;
            }

            .login-title{
                font-weight: 900;
                color:#0f172a;
                font-size: 22px;
                display:flex;
                align-items:center;
                gap:10px;
                margin-bottom: 2px;
            }

            .login-sub{
                color:#64748b;
                font-size: 13px;
                margin-bottom: 14px;
            }

            .login-divider{
                height: 1px;
                background: rgba(15,23,42,0.06);
                margin: 10px 0 14px 0;
            }

            /* labels minúsculos */
            section[data-testid="stTextInput"] label p{
                text-transform: lowercase;
                font-weight: 800;
                color:#334155;
            }

            /* botão preto (sem faixa branca/halo) */
            div.stButton > button{
                background:#000000 !important;
                color:#ffffff !important;
                border:none !important;
                border-radius: 14px !important;
                height: 48px !important;
                font-weight: 900 !important;
                box-shadow: none !important;
            }
            div.stButton > button:hover{
                background:#111111 !important;
            }
            div.stButton > button:focus,
            div.stButton > button:active{
                outline:none !important;
                box-shadow:none !important;
            }

            .hint{
                margin-top: 10px;
                font-size: 12px;
                color:#94a3b8;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="login-wrap"><div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🔒 Acesso ao Painel</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">Digite usuário e senha</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-divider"></div>', unsafe_allow_html=True)

    user = st.text_input("usuario")
    pwd = st.text_input("senha", type="password")

    entrar = st.button("Entrar", use_container_width=True)

    if entrar:
        u = (user or "").strip()
        p = (pwd or "").strip()

        if u == APP_USER and p == APP_PASS:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

    st.markdown('<div class="hint">Acesso restrito • Operação interna</div>', unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    return False


# ===============================
# CONFIG (IGUAL AO SEU)
# ===============================
SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1Q0mLvOBxEGCojUITBLxCXRtpXVMAHE3ngvGsa2Cgf9Q"
    "/gviz/tq?tqx=out:csv"
)

st.set_page_config(page_title="Painel Pós-Venda", layout="wide")

# trava aqui: se não logar, não roda mais nada do dashboard
if not ensure_login():
    st.stop()

# ===============================
# CSS (IGUAL AO SEU - NÃO MUDEI)
# ===============================
st.markdown(
    """
    <style>
        .stApp { background-color: #F3F4F6; }

        /* resolve título “comendo” no topo */
        .block-container {
            padding-top: 2.4rem !important;
            padding-bottom: 1.6rem !important;
        }

        h1, h2, h3, h4 { margin-top: 0 !important; padding-top: 0 !important; }

        /* filtros com respiro */
        div[data-baseweb="select"] { margin-top: 10px; }

        /* CARD – tudo branco dentro */
        .panel-card{
            background:#ffffff;
            border-radius:18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
            border: 1px solid rgba(15,23,42,0.06);
            overflow: hidden; /* corta o gráfico nas bordas arredondadas */
        }

        /* título do card (sem “faixa branca separada”) */
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
# PALETA (IGUAL AO SEU)
# ===============================
NAVY = "#1B1D6D"
WINE = "#9B0033"
NAVY_2 = "#2E3192"
WINE_2 = "#C00040"
GRAY = "#64748b"
BAR_SEQ = [NAVY, WINE, NAVY_2, WINE_2, "#334155", "#94a3b8"]

# ===============================
# HELPERS (IGUAL AO SEU)
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
        "feito","concluido","concluído","ok",
        "realizado","finalizado","concluida","concluída"
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
        <div style="font-size:{value_size}px;font-weight:900;color:{value_color};line-height:1.05;margin-top:6px;">
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
# LOAD DATA (IGUAL AO SEU)
# ===============================
@st.cache_data
def load_sheet():
    d = pd.read_csv(SHEET_CSV_URL)
    d.columns = [c.strip() for c in d.columns]
    return d

df = load_sheet()

COL = {
    "mes": "Mês",
    "raca": "Raça",
    "unidade": "Unidade",
    "c1": "1º contato",
    "s1": "Status 1º contato",
    "c2": "2º contato",
    "s2": "Status 2º contato",
    "c3": "3º contato",
    "s3": "Status 3º contato",
}

# >>> IMPORTANTE: inclui "Valor Filhote" (como você disse)
COL_VALOR = pick_first_existing(df, ["Valor Filhote", "Valor de filhote", "Valor Filhote ", "Valor Filhote", "Valor"])
COL_VENDEDOR = pick_first_existing(df, ["Vendedor", "Vendedora", "Atendente"])

for c in ["c1", "c2", "c3"]:
    if COL[c] in df.columns:
        df[COL[c]] = pd.to_datetime(df[COL[c]], errors="coerce", dayfirst=True)

hoje = pd.to_datetime(datetime.date.today())

# ===============================
# HEADER + SAIR (ADICIONE O SAIR SEM MUDAR O LAYOUT)
# ===============================
top_l, top_r = st.columns([6, 1])
with top_l:
    st.markdown("## 📊 Painel de Pós-Venda")
    st.caption(f"Total de registros: **{len(df)}**")
with top_r:
    if st.button("Sair", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ===============================
# FILTROS (IGUAL AO SEU)
# ===============================
f1, f2, f3 = st.columns(3)
with f1:
    setor = st.selectbox("Setor", ["Pós-Venda", "Pedigree"])
with f2:
    meses = sorted(df[COL["mes"]].dropna().astype(str).unique())
    mes = st.selectbox("Mês", meses, index=len(meses)-1)
with f3:
    unidades = ["Todas"] + sorted(df[COL["unidade"]].dropna().unique().tolist())
    unidade = st.selectbox("Unidade", unidades)

# filtro NORMAL (continua igual) -> usado para vendas no mês, faturamento, gráficos do mês
f = df[df[COL["mes"]].astype(str) == mes].copy()
if unidade != "Todas":
    f = f[f[COL["unidade"]] == unidade]

# ===============================
# CONTATOS HOJE (ÚNICA MUDANÇA AQUI)
# - 1º/2º/3º contato hoje + Status com erro
# - IGNORA o filtro de MÊS (pega TODOS os meses)
# - Mantém filtro de UNIDADE (se escolher uma loja)
# ===============================
df_base = df.copy()
if unidade != "Todas":
    df_base = df_base[df_base[COL["unidade"]] == unidade]

def count_today(date_col, status_col):
    if date_col not in df_base.columns:
        return 0
    sub = df_base[df_base[date_col].dt.date == hoje.date()]
    if status_col in sub.columns:
        sub = sub[~sub[status_col].apply(is_done)]
    return int(len(sub))

records_today = []
if setor == "Pós-Venda":
    c1 = count_today(COL["c1"], COL["s1"])
    c2 = count_today(COL["c2"], COL["s2"])
    c3 = count_today(COL["c3"], COL["s3"])

    for _, r in df_base.iterrows():
        for dc, sc in [(COL["c1"], COL["s1"]), (COL["c2"], COL["s2"]), (COL["c3"], COL["s3"])]:
            if pd.notna(r.get(dc)) and pd.to_datetime(r.get(dc)).date() == hoje.date():
                records_today.append(status_bucket_today(r.get(sc)))
else:
    c1 = c2 = c3 = 0

erro_hoje = records_today.count("Erro")

# ===============================
# KPIs DO MÊS (IGUAL AO SEU - NÃO MEXI)
# ===============================
vendas_mes = len(f)

# faturamento continua baseado no MÊS selecionado (igual ao seu),
# mas agora encontra a coluna "Valor Filhote" corretamente
faturamento = f[COL_VALOR].apply(brl_to_float).sum() if COL_VALOR and (COL_VALOR in f.columns) else 0

# ===============================
# KPIs (IGUAL AO SEU)
# ===============================
st.markdown("---")
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: kpi_card("💬 1º contato hoje", c1, "pendentes", NAVY)
with k2: kpi_card("💬 2º contato hoje", c2, "pendentes", NAVY_2)
with k3: kpi_card("💬 3º contato hoje", c3, "pendentes", WINE_2)
with k4: kpi_card("⚠️ Status com erro", erro_hoje, "atenção", WINE, value_color="#ef4444" if erro_hoje else "#0f172a")
with k5: kpi_card("🛍️ Vendas no mês", vendas_mes, mes, "#F59E0B")
with k6: kpi_card("💰 Faturamento", money_br(faturamento), "valor do filhote", NAVY, value_size=28)

# ===============================
# GRÁFICOS (IGUAL AO SEU)
# ===============================
st.markdown("---")
g1, g2 = st.columns(2)
g3, g4 = st.columns(2)

with g1:
    st.markdown('<div class="panel-card"><div class="panel-head"><div class="panel-title">📌 Contatos por Status (hoje)</div></div><div class="panel-body">', unsafe_allow_html=True)
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

with g2:
    st.markdown('<div class="panel-card"><div class="panel-head"><div class="panel-title">🏬 Vendas por loja (Unidade)</div></div><div class="panel-body">', unsafe_allow_html=True)
    vp = f.groupby(COL["unidade"]).size().reset_index(name="Total")
    fig = px.bar(vp, x=COL["unidade"], y="Total", text="Total",
                 color=COL["unidade"], color_discrete_sequence=BAR_SEQ)
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False)
    st.plotly_chart(tune_plotly(fig, height=360), use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

with g3:
    st.markdown('<div class="panel-card"><div class="panel-head"><div class="panel-title">🐶 Raças mais vendidas (mês)</div></div><div class="panel-body">', unsafe_allow_html=True)
    vr = (f.groupby(COL["raca"]).size().reset_index(name="Total")
          .sort_values("Total", ascending=False).head(10))
    fig = px.bar(vr, x=COL["raca"], y="Total", text="Total",
                 color=COL["raca"], color_discrete_sequence=BAR_SEQ)
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False)
    st.plotly_chart(tune_plotly(fig, height=360), use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

with g4:
    st.markdown('<div class="panel-card"><div class="panel-head"><div class="panel-title">🏆 Vendas por vendedora (mês)</div></div><div class="panel-body">', unsafe_allow_html=True)
    if COL_VENDEDOR:
        vv = (f.groupby(COL_VENDEDOR).size().reset_index(name="Total")
              .sort_values("Total", ascending=False))
        fig = px.bar(vv, x=COL_VENDEDOR, y="Total", text="Total",
                     color=COL_VENDEDOR, color_discrete_sequence=BAR_SEQ)
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(showlegend=False)
        st.plotly_chart(tune_plotly(fig, height=360), use_container_width=True)
    else:
        st.info("Coluna de vendedor não encontrada")
    st.markdown("</div></div>", unsafe_allow_html=True)
