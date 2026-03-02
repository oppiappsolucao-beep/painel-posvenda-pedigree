import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Painel Pós-Venda", layout="wide")

# =====================================================
# LOGIN CONFIG
# =====================================================
APP_USER = "operacao"
APP_PASS = "100316"

def ensure_login():

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    # ================= CSS LOGIN =================
    st.markdown("""
    <style>

    .stApp{
        background:#F3F4F6;
    }

    .login-box{
        max-width:520px;
        margin:10vh auto;
        background:white;
        border-radius:20px;
        padding:30px;
        box-shadow:0 20px 40px rgba(0,0,0,.08);
        font-family:Inter;
    }

    .login-title{
        font-size:24px;
        font-weight:900;
        color:#0f172a;
    }

    .login-sub{
        font-size:13px;
        color:#64748b;
        margin-bottom:20px;
    }

    div.stButton > button{
        background:#000000 !important;
        color:white !important;
        border:none !important;
        border-radius:12px !important;
        height:48px !important;
        font-weight:900 !important;
        font-size:15px !important;
        box-shadow:none !important;
    }

    div.stButton > button:hover{
        background:#111111 !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # ================= LOGIN UI =================
    st.markdown('<div class="login-box">', unsafe_allow_html=True)

    st.markdown('<div class="login-title">🔒 Acesso ao Painel</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">Digite usuário e senha</div>', unsafe_allow_html=True)

    user = st.text_input("usuario")
    pwd = st.text_input("senha", type="password")

    entrar = st.button("Entrar", use_container_width=True)

    if entrar:
        if user == APP_USER and pwd == APP_PASS:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

    st.markdown("</div>", unsafe_allow_html=True)

    return False


# BLOQUEIA DASHBOARD
if not ensure_login():
    st.stop()

# =====================================================
# GOOGLE SHEETS
# =====================================================
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1Q0mLvOBxEGCojUITBLxCXRtpXVMAHE3ngvGsa2Cgf9Q"
    "/gviz/tq?tqx=out:csv"
)

@st.cache_data
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = [c.strip() for c in df.columns]
    return df

df = load_data()

# =====================================================
# CORES
# =====================================================
NAVY="#1B1D6D"
WINE="#9B0033"
BAR_SEQ=[NAVY,WINE,"#2E3192","#C00040","#334155","#94a3b8"]

# =====================================================
# HEADER
# =====================================================
col1,col2=st.columns([6,1])

with col1:
    st.title("📊 Painel Pós-Venda")
    st.caption(f"{len(df)} registros")

with col2:
    if st.button("Sair",use_container_width=True):
        st.session_state.logged_in=False
        st.rerun()

# =====================================================
# FILTROS
# =====================================================
mes_col="Mês"
unidade_col="Unidade"
raca_col="Raça"

f1,f2=st.columns(2)

with f1:
    meses=sorted(df[mes_col].dropna().astype(str).unique())
    mes=st.selectbox("Mês",meses,index=len(meses)-1)

with f2:
    unidades=["Todas"]+sorted(df[unidade_col].dropna().unique())
    unidade=st.selectbox("Unidade",unidades)

f=df[df[mes_col].astype(str)==mes]

if unidade!="Todas":
    f=f[f[unidade_col]==unidade]

# =====================================================
# KPI CARDS
# =====================================================
def kpi(title,value,color):
    html=f"""
    <div style="
    background:white;
    border-radius:16px;
    padding:18px;
    box-shadow:0 8px 20px rgba(0,0,0,.06);
    border-left:8px solid {color}">
        <div style="font-size:14px;font-weight:900">{title}</div>
        <div style="font-size:36px;font-weight:900">{value}</div>
    </div>
    """
    components.html(html,height=120)

st.markdown("---")

k1,k2,k3=st.columns(3)

with k1:
    kpi("Vendas no mês",len(f),NAVY)

with k2:
    kpi("Raças diferentes",f[raca_col].nunique(),WINE)

with k3:
    kpi("Lojas ativas",f[unidade_col].nunique(),NAVY)

# =====================================================
# GRÁFICOS
# =====================================================
st.markdown("---")

g1,g2=st.columns(2)

with g1:
    vendas_loja=f.groupby(unidade_col).size().reset_index(name="Total")

    fig=px.bar(
        vendas_loja,
        x=unidade_col,
        y="Total",
        text="Total",
        color=unidade_col,
        color_discrete_sequence=BAR_SEQ
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig,use_container_width=True)

with g2:
    racas=f.groupby(raca_col).size().reset_index(name="Total")\
        .sort_values("Total",ascending=False).head(10)

    fig=px.bar(
        racas,
        x=raca_col,
        y="Total",
        text="Total",
        color=raca_col,
        color_discrete_sequence=BAR_SEQ
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig,use_container_width=True)
