import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import json
from datetime import datetime

# ==============================================================================
# 1. SETUP & SERVICES (MOTOR ROBUSTO)
# ==============================================================================
st.set_page_config(page_title="Otti Workspace", layout="wide", page_icon="🐙")

# --- CONEXÃO ---
@st.cache_resource
def init_connection():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url: return None
    return create_client(url, key)

supabase = init_connection()

# --- ESTILO (VISUAL DARK NEON ORIGINAL) ---
def apply_original_style():
    C_BG_DARK       = "#001024" 
    C_SIDEBAR_DARK  = "#020A14"
    C_TEXT_DARK     = "#F8FAFC"
    C_CARD          = "rgba(3, 26, 137, 0.2)"
    C_INPUT_BG      = "#0B1221"
    C_METRIC_VAL    = "#E7F9A9" # Verde Neon
    C_ACCENT        = "#3F00FF" # Azul Elétrico

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;800&family=Inter:wght@300;400;600&display=swap');

        .stApp {{ background-color: {C_BG_DARK}; color: {C_TEXT_DARK}; font-family: 'Inter', sans-serif; }}
        
        /* SIDEBAR */
        section[data-testid="stSidebar"] {{ background-color: {C_SIDEBAR_DARK}; border-right: 1px solid rgba(255,255,255,0.1); }}
        section[data-testid="stSidebar"] p, label, span {{ color: #FFFFFF !important; }}

        /* TÍTULOS */
        h1, h2, h3, h4 {{ font-family: 'Sora', sans-serif; color: {C_TEXT_DARK} !important; }}
        p, label {{ color: {C_TEXT_DARK} !important; }}
        
        /* INPUTS */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div {{
            background-color: {C_INPUT_BG} !important;
            color: #FFFFFF !important;
            border: 1px solid {C_ACCENT};
            border-radius: 8px;
        }}
        /* Correção específica para Selectbox no Streamlit */
        div[data-baseweb="select"] > div {{ background-color: {C_INPUT_BG} !important; }}
        div[data-baseweb="popover"] {{ background-color: {C_INPUT_BG} !important; }}
        div[data-baseweb="option"] {{ color: #FFFFFF !important; }}

        /* BOTÕES */
        button[kind="primary"] {{
            background: linear-gradient(90deg, {C_ACCENT} 0%, #031A89 100%) !important;
            color: #FFFFFF !important; border: none !important;
        }}
        /* Botão Secundário (Pausar/Ativar) */
        div[data-testid="stAppViewContainer"] .main .stButton > button {{
            background-color: {C_INPUT_BG} !important;
            color: #FFFFFF !important;
            border: 1px solid {C_ACCENT} !important;
        }}

        /* CARDS/METRICS */
        div[data-testid="stMetric"] {{ 
            background-color: {C_CARD}; 
            border: 1px solid {C_ACCENT}; 
            border-radius: 8px; 
            padding: 15px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.2); 
        }}
        div[data-testid="stMetricValue"] {{ color: {C_METRIC_VAL} !important; font-family: 'Sora', sans-serif; }}
        label[data-testid="stMetricLabel"] {{ color: {C_TEXT_DARK} !important; opacity: 0.8; }}
        
        /* TABS */
        .stTabs [data-baseweb="tab-list"] {{ gap: 20px; }}
        .stTabs [data-baseweb="tab"] {{ color: #FFFFFF; background-color: transparent; }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{ color: {C_METRIC_VAL}; border-color: {C_METRIC_VAL}; }}
    </style>
    """, unsafe_allow_html=True)

apply_original_style()

# --- FUNÇÕES DO SISTEMA (DATA LAYER) ---
@st.cache_data(ttl=60)
def get_kpis():
    if not supabase: return pd.DataFrame()
    return pd.DataFrame(supabase.table('view_dashboard_kpis').select("*").execute().data)

@st.cache_data(ttl=60)
def get_financial_data(c_id):
    try:
        r_s = supabase.table('agendamentos_salao').select('created_at, valor_sinal_registrado, status, produto_salao_id, produtos:produto_salao_id(nome)').eq('cliente_id', c_id).execute().data
        r_p = supabase.table('agendamentos').select('created_at, valor_sinal_registrado, status, servico_id').eq('cliente_id', c_id).execute().data
        return r_s, r_p
    except: return [], []

def get_messages(c_id):
    return supabase.table('conversas').select('id, cliente_wa_id, updated_at, metadata').eq('cliente_id', c_id).order('updated_at', desc=True).limit(20).execute()

def get_chat_history(conversa_id):
    return supabase.table('historico_mensagens').select('*').eq('conversa_id', conversa_id).order('created_at', desc=True).limit(40).execute()

def get_products(c_id):
    return supabase.table('produtos').select('nome, categoria, ativo').eq('cliente_id', c_id).order('nome').execute()

def get_agenda(c_id):
    try:
        rs = supabase.table('agendamentos_salao').select('data_reserva, valor_total_registrado, cliente_final_waid').eq('cliente_id', c_id).order('created_at', desc=True).limit(50).execute()
        if rs.data: 
            df = pd.DataFrame(rs.data)
            df.columns = ['Data', 'Valor', 'Cliente']
            return df
        
        rv = supabase.table('agendamentos').select('data_hora_inicio, valor_total_registrado').eq('cliente_id', c_id).order('created_at', desc=True).limit(50).execute()
        if rv.data: 
            df = pd.DataFrame(rv.data)
            df.columns = ['Data/Hora', 'Valor']
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# Funções de Escrita (Sem Cache)
def toggle_bot(c_id, current_status):
    supabase.table('clientes').update({'bot_pausado': not current_status}).eq('id', c_id).execute()
    st.cache_data.clear()

def create_product(c_id, nome, categoria, preco):
    try:
        regras_json = {"preco_padrao": float(preco), "duracao_minutos": 60}
        supabase.table('produtos').insert({"cliente_id": c_id, "nome": nome, "categoria": categoria, "ativo": True, "regras_preco": json.dumps(regras_json)}).execute()
        return True
    except Exception as e:
        st.error(f"Erro: {e}")
        return False

def get_client_config(c_id):
    try:
        res = supabase.table('clientes').select('config_fluxo, prompt_full').eq('id', c_id).execute()
        if res.data:
            data = res.data[0]
            config = data.get('config_fluxo') or {}
            if isinstance(config, str): config = json.loads(config)
            return data.get('prompt_full'), config
        return "", {}
    except: return "", {}

def update_brain(c_id, prompt_text, new_voice, new_temp, current_config):
    try:
        current_config['openai_voice'] = new_voice
        current_config['temperature'] = new_temp
        supabase.table('clientes').update({'prompt_full': prompt_text, 'config_fluxo': json.dumps(current_config)}).eq('id', c_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro: {e}")
        return False

# ==============================================================================
# 2. APLICAÇÃO PRINCIPAL (FRONTEND)
# ==============================================================================

# LOGIN
if 'usuario_logado' not in st.session_state: st.session_state['usuario_logado'] = None
if not st.session_state['usuario_logado']:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><h1 style='text-align:center; color:#3F00FF'>OCTO</h1>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR", type="primary", use_container_width=True):
                if not supabase: st.error("Erro de conexão com banco.")
                else:
                    try:
                        res = supabase.table('acesso_painel').select('*').eq('email', email).eq('senha', senha).execute()
                        if res.data:
                            st.session_state['usuario_logado'] = res.data[0]
                            st.rerun()
                        else: st.error("Login inválido")
                    except: st.error("Erro interno.")
    st.stop()

# DASHBOARD
user = st.session_state['usuario_logado']
perfil = user['perfil']

with st.sidebar:
    st.title("🐙 Otti")
    st.write(f"Olá, **{user['nome_usuario']}**")
    st.markdown("---")
    if st.button("SAIR"):
        st.session_state['usuario_logado'] = None
        st.rerun()

df_kpis = get_kpis()
if df_kpis.empty:
    st.error("Sem dados de KPIs disponíveis.")
    st.stop()

if perfil == 'admin':
    lista = df_kpis['nome_empresa'].unique()
    sel = st.sidebar.selectbox("Cliente:", lista)
    c_data = df_kpis[df_kpis['nome_empresa'] == sel].iloc[0]
else:
    filtro = df_kpis[df_kpis['cliente_id'] == user['cliente_id']]
    if filtro.empty: st.stop()
    c_data = filtro.iloc[0]

c_id = int(c_data['cliente_id'])
active = not bool(c_data['bot_pausado'])

# HEADER
c1, c2 = st.columns([3, 1])
with c1: st.title(c_data['nome_empresa'])
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    lbl = "⏸️ PAUSAR" if active else "▶️ ATIVAR"
    if st.button(lbl, use_container_width=True):
        toggle_bot(c_id, bool(c_data['bot_pausado']))
        st.rerun()

# METRICAS
k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita", f"R$ {float(c_data['receita_total'] or 0):,.2f}")
k2.metric("Tempo", f"{round((c_data['total_mensagens']*1.5)/60, 1)}h")
k3.metric("Atendimentos", c_data['total_atendimentos'])
k4.metric("Status", "Online" if active else "Offline")
st.divider()

# ABAS
tabs = st.tabs(["Analytics", "Espião", "Produtos", "Agenda", "Cérebro"])

# 1. Analytics
with tabs[0]:
    r_s, r_p = get_financial_data(c_id)
    lista = []
    for i in r_s:
         p_nome = i.get('produtos', {}).get('nome', 'Salão') if i.get('produtos') else 'Salão'
         lista.append({'dt': i['created_at'], 'v': i.get('valor_sinal_registrado',0), 'p': p_nome})
    for i in r_p:
         lista.append({'dt': i['created_at'], 'v': i.get('valor_sinal_registrado',0), 'p': 'Serviço'})
    
    if lista:
        df = pd.DataFrame(lista)
        df['dt'] = pd.to_datetime(df['dt']).dt.date
        c_g1, c_g2 = st.columns(2)
        with c_g1:
            st.markdown("##### Receita Diária")
            df_g = df.groupby('dt')['v'].sum().reset_index()
            fig = px.line(df_g, x='dt', y='v', template='plotly_dark', markers=True)
            fig.update_traces(line_color="#3F00FF", line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        with c_g2:
            st.markdown("##### Produtos Mais Vendidos")
            df_top = df['p'].value_counts().reset_index().head(5)
            fig2 = px.bar(df_top, x='count', y='p', orientation='h', template='plotly_dark')
            fig2.update_traces(marker_color="#5396FF")
            st.plotly_chart(fig2, use_container_width=True)
    else: st.info("Sem dados financeiros.")

# 2. Espião
with tabs[1]:
    cl, cr = st.columns([1, 2])
    with cl:
        rc = get_messages(c_id)
        if rc.data:
            opts = {f"{c.get('metadata',{}).get('push_name','Cliente')}": c['id'] for c in rc.data}
            sel_chat = st.radio("Conversas:", list(opts.keys()))
            sid = opts[sel_chat]
        else: sid = None
    with cr:
        if sid:
            rm = get_chat_history(sid)
            msgs = rm.data[::-1] if rm.data else []
            with st.container(height=500):
                for m in msgs:
                    av = "👤" if m['role']=='user' else "🐙"
                    with st.chat_message(m['role'], avatar=av): st.write(m['content'])

# 3. Produtos
with tabs[2]:
    c1, c2 = st.columns([2,1])
    with c1:
        rp = get_products(c_id)
        if rp.data: st.dataframe(pd.DataFrame(rp.data), use_container_width=True, hide_index=True)
    with c2:
        with st.form("add_prod"):
            st.write("Novo Produto")
            n = st.text_input("Nome")
            c = st.text_input("Categoria")
            p = st.number_input("Preço (R$)", min_value=0.0)
            if st.form_submit_button("Salvar", type="primary"):
                if create_product(c_id, n, c, p):
                    st.success("Produto criado!")
                    st.rerun()

# 4. Agenda
with tabs[3]:
    st.subheader("Próximos Agendamentos")
    df_ag = get_agenda(c_id)
    if not df_ag.empty: st.dataframe(df_ag, use_container_width=True)
    else: st.info("Agenda vazia.")

# 5. Cérebro
with tabs[4]:
    if perfil == 'admin':
        st.subheader("Configuração da Inteligência")
        prompt_atual, config_atual = get_client_config(c_id)
        
        c_p1, c_p2 = st.columns([2, 1])
        with c_p1:
            new_prompt = st.text_area("Prompt (Personalidade)", value=prompt_atual or '', height=400)
        with c_p2:
            st.markdown("##### Configurações")
            vozes = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            v_atual = config_atual.get('openai_voice', 'alloy')
            if v_atual not in vozes: v_atual = 'alloy'
            
            # Tratamento da temperatura
            raw_temp = config_atual.get('temperature', 0.5)
            try: temp_val = float(str(raw_temp).replace(',', '.'))
            except: temp_val = 0.5
            
            new_voice = st.selectbox("Voz:", vozes, index=vozes.index(v_atual))
            new_temp = st.slider("Criatividade:", 0.0, 1.0, value=temp_val, step=0.1)
            
            if st.button("💾 Atualizar Cérebro", type="primary"):
                if update_brain(c_id, new_prompt, new_voice, new_temp, config_atual):
                    st.success("IA Atualizada!")
                    st.rerun()
    else: st.warning("Acesso restrito.")
