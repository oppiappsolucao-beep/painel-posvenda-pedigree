import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import plotly.express as px
import re

# ===============================
# LOGIN
# ===============================
APP_USER = "operacao"
APP_PASS = "100316"

def ensure_login() -> bool:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    user = st.text_input("usuario")
    pwd = st.text_input("senha", type="password")

    if st.button("Entrar"):
        if user.strip() == APP_USER and pwd.strip() == APP_PASS:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

    return False


st.set_page_config(page_title="Painel Pós-Venda", layout="wide")

if not ensure_login():
    st.stop()

# ===============================
# CONFIG
# ===============================
SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1Q0mLvOBxEGCojUITBLxCXRtpXVMAHE3ngvGsa2Cgf9Q"
    "/gviz/tq?tqx=out:csv"
)

# ===============================
# LOAD DATA
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

COL_VALOR = "Valor Filhote"

for c in ["c1", "c2", "c3"]:
    if COL[c] in df.columns:
        df[COL[c]] = pd.to_datetime(df[COL[c]], errors="coerce", dayfirst=True)

hoje = pd.to_datetime(datetime.date.today())

# ===============================
# FUNÇÕES AUXILIARES
# ===============================
def norm(x):
    return str(x).strip().lower() if pd.notna(x) else ""

def is_done(status):
    return norm(status) in ["feito","concluido","concluído","ok","realizado","finalizado"]

def is_error(status):
    s = norm(status)
    return "erro" in s or "atras" in s or "pendenc" in s

def brl_to_float(v):
    if pd.isna(v):
        return 0.0

    s = str(v)
    s = s.replace("\u00a0", "")
    s = s.replace("R$", "").strip()
    s = re.sub(r"[^\d,.\-]", "", s)

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

# ===============================
# FILTROS
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

# filtro mensal normal (para vendas e faturamento)
f = df[df[COL["mes"]].astype(str) == mes].copy()
if unidade != "Todas":
    f = f[f[COL["unidade"]] == unidade]

# ===============================
# KPIs CONTATOS HOJE (IGNORA MÊS)
# ===============================
df_global = df.copy()
if unidade != "Todas":
    df_global = df_global[df_global[COL["unidade"]] == unidade]

def count_today(dataframe, date_col, status_col):
    if date_col not in dataframe.columns:
        return 0
    sub = dataframe[dataframe[date_col].dt.date == hoje.date()]
    if status_col in sub.columns:
        sub = sub[~sub[status_col].apply(is_done)]
    return len(sub)

if setor == "Pós-Venda":
    c1 = count_today(df_global, COL["c1"], COL["s1"])
    c2 = count_today(df_global, COL["c2"], COL["s2"])
    c3 = count_today(df_global, COL["c3"], COL["s3"])

    erro_hoje = 0
    for _, r in df_global.iterrows():
        for dc, sc in [(COL["c1"], COL["s1"]),
                       (COL["c2"], COL["s2"]),
                       (COL["c3"], COL["s3"])]:
            if pd.notna(r.get(dc)) and pd.to_datetime(r.get(dc)).date() == hoje.date():
                if is_error(r.get(sc)):
                    erro_hoje += 1
else:
    c1 = c2 = c3 = erro_hoje = 0

# ===============================
# FATURAMENTO (MÊS FILTRADO)
# ===============================
vendas_mes = len(f)
faturamento = f[COL_VALOR].apply(brl_to_float).sum()

# ===============================
# KPIs
# ===============================
st.markdown("---")
k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("1º contato hoje", c1)
k2.metric("2º contato hoje", c2)
k3.metric("3º contato hoje", c3)
k4.metric("Status com erro", erro_hoje)
k5.metric("Vendas no mês", vendas_mes)
k6.metric("Faturamento", money_br(faturamento))
