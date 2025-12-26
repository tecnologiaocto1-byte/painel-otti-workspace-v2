import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import json
from datetime import datetime, timedelta

# ==============================================================================
# 1. SETUP & CONEXÃO
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

# ==============================================================================
# 2. ESTILO LIGHT MODE PREMIUM (VISUAL LIMPO)
# ==============================================================================
def apply_light_style():
    # PALETA LIGHT
    C_BG          = "#F3F4F6"  # Cinza bem claro (Fundo do Site)
    C_SIDEBAR     = "#FFFFFF"  # Branco (Sidebar)
    C_CARD        = "#FFFFFF"  # Branco (Cards)
    C_TEXT_MAIN   = "#111827"  # Preto Suave
    C_TEXT_SEC    = "#6B7280"  # Cinza Texto
    C_ACCENT      = "#3F00FF"  # Azul Elétrico (Sua Marca)
    C_BORDER      = "#E5E7EB"  # Borda Sutil

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700&display=swap');

        /* GERAL */
        .stApp {{ background-color: {C_BG}; color: {C_TEXT_MAIN}; font-family: 'Inter', sans-serif; }}
        
        /* SIDEBAR */
        section[data-testid="stSidebar"] {{ 
            background-color: {C_SIDEBAR}; 
            border-right: 1px solid {C_BORDER};
            box-shadow: 4px 0 15px rgba(0,0,0,0.02);
        }}
        section[data-testid="stSidebar"] h1 {{ color: {C_ACCENT} !important; font-family: 'Sora', sans-serif; }}
        section[data-testid="stSidebar"] p, label, span {{ color: {C_TEXT_MAIN} !important; }}

        /* METRICS / CARDS */
        div[data-testid="stMetric"] {{
            background-color: {C_CARD};
            border: 1px solid {C_BORDER};
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        div[data-testid="stMetricValue"] {{ color: {C_ACCENT} !important; font-family: 'Sora', sans-serif; font-weight: 700; }}
        div[data-testid="stMetricLabel"] {{ color: {C_TEXT_SEC} !important; }}

        /* BOTÕES */
        button[kind="primary"] {{
            background-color: {C_ACCENT} !important;
            color: white !important;
            border-radius: 8px;
            border: none;
            font-weight: 600;
        }}
        div[data-testid="stAppViewContainer"] .main .stButton > button {{
            background-color: white !important;
            color: {C_TEXT_MAIN} !important;
            border: 1px solid {C_BORDER} !important;
            border-radius: 8px;
        }}
        div[data-testid="stAppViewContainer"] .main .stButton > button:hover {{
            border-color: {C_ACCENT} !important;
            color: {C_ACCENT} !important;
        }}

        /* INPUTS & FILTROS */
        .stDateInput > div > div > input {{ color: {C_TEXT_MAIN}; }}
        .stSelectbox > div > div {{ color: {C_TEXT_MAIN}; }}
        
        /* TABS */
        .stTabs [data-baseweb="tab-list"] {{ gap: 24px; border-bottom: 1px solid {C_BORDER}; }}
        .stTabs [data-baseweb="tab"] {{ color: {C_TEXT_SEC}; font-weight: 500; }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{ color: {C_ACCENT}; border-top: 2px solid {C_ACCENT}; border-bottom: none; font-weight: 700; }}
    </style>
    """, unsafe_allow_html=True)

apply_light_style()

# ==============================================================================
# 3. FUNÇÕES ROBUSTAS (Backend)
# ==============================================================================
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
    # Trazendo a lógica de formatação do seu código original
    try:
        rs = supabase.table('agendamentos_salao').select('data_reserva, valor_total_registrado, cliente_final_waid').eq('cliente_id', c_id).order('created_at', desc=True).limit(50).execute()
        if rs.data: 
            d = pd.DataFrame(rs.data)
            # Formatação Bonita de Data
            d['Data'] = pd.to_datetime(d['data_reserva']).dt.strftime('%d/%m/%Y')
            df_final = d[['Data', 'valor_total_registrado', 'cliente_final_waid']]
            df_final.columns = ['Data', 'Valor (R$)', 'Cliente']
            return df_final
        
        rv = supabase.table('agendamentos').select('data_hora_inicio, valor_total_registrado').eq('cliente_id', c_id).order('created_at', desc=True).limit(50).execute()
        if rv.data: 
            d = pd.DataFrame(rv.data)
            # Formatação Bonita de Data/Hora
            d['Data/Hora'] = pd.to_datetime(d['data_hora_inicio']).dt.strftime('%d/%m/%Y %H:%M')
            df_final = d[['Data/Hora', 'valor_total_registrado']]
            df_final.columns = ['Data/Hora', 'Valor (R$)']
            return df_final
        return pd.DataFrame()
    except: return pd.DataFrame()

def toggle_bot(c_id, current_status):
    supabase.table('clientes').update({'bot_pausado': not current_status}).eq('id', c_id).execute()
    st.cache_data.clear()

def create_product(c_id, nome, categoria, preco):
    try:
        regras_json = {"preco_padrao": float(preco), "duracao_minutos": 60}
        supabase.table('produtos').insert({"cliente_id": c_id, "nome": nome, "categoria": categoria, "ativo": True, "regras_preco": json.dumps(regras_json)}).execute()
        return True
    except: return False

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
    except: return False

# ==============================================================================
# 4. APP PRINCIPAL
# ==============================================================================

# --- LOGIN ---
if 'usuario_logado' not in st.session_state: st.session_state['usuario_logado'] = None
if not st.session_state['usuario_logado']:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><h1 style='text-align:center; color:#3F00FF; font-family:Sora;'>OCTO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666;'>Acesse seu painel administrativo</p>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR SISTEMA", type="primary", use_container_width=True):
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

# --- DASHBOARD ---
user = st.session_state['usuario_logado']
perfil = user['perfil']

with st.sidebar:
    st.markdown("## 🐙 Otti")
    st.write(f"Olá, **{user['nome_usuario']}**")
    st.caption("Workspace v2.0")
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
with c1: 
    st.title(c_data['nome_empresa'])
    st.caption(f"Status Atual: {'🟢 Online' if active else '🔴 Pausado'}")
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    lbl = "⏸️ PAUSAR" if active else "▶️ ATIVAR"
    if st.button(lbl, use_container_width=True):
        toggle_bot(c_id, bool(c_data['bot_pausado']))
        st.rerun()

# METRICAS
k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita Total", f"R$ {float(c_data['receita_total'] or 0):,.2f}")
k2.metric("Tempo Economizado", f"{round((c_data['total_mensagens']*1.5)/60, 1)}h")
k3.metric("Atendimentos", c_data['total_atendimentos'])
k4.metric("Status do Bot", "Ativo" if active else "Pausado")
st.divider()

# ABAS
tabs = st.tabs(["Analytics", "Espião", "Produtos", "Agenda", "Cérebro"])

# 1. ANALYTICS (COM FILTRO DE DATA!)
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
        
        # --- FILTRO DE DATA NOVO ---
        st.markdown("##### 📅 Filtrar Período")
        c_filter1, c_filter2, c_vazio = st.columns([1, 1, 2])
        with c_filter1:
            # Pega o primeiro e o ultimo dia dos dados, ou padrão de 30 dias
            min_date = df['dt'].min()
            max_date = df['dt'].max()
            d_inicio = st.date_input("Início", value=(datetime.now().date() - timedelta(days=30)), min_value=min_date, max_value=max_date)
        with c_filter2:
            d_fim = st.date_input("Fim", value=datetime.now().date(), min_value=min_date, max_value=max_date)
            
        # Aplica Filtro
        mask = (df['dt'] >= d_inicio) & (df['dt'] <= d_fim)
        df_filtered = df.loc[mask]
        
        st.divider()

        c_g1, c_g2 = st.columns(2)
        with c_g1:
            st.markdown("##### Receita no Período")
            if not df_filtered.empty:
                df_g = df_filtered.groupby('dt')['v'].sum().reset_index()
                # USANDO TEMPLATE LIGHT (plotly_white)
                fig = px.area(df_g, x='dt', y='v', template='plotly_white', markers=True)
                fig.update_traces(line_color="#3F00FF", fillcolor="rgba(63, 0, 255, 0.1)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados neste período.")
                
        with c_g2:
            st.markdown("##### Produtos Mais Vendidos")
            if not df_filtered.empty:
                df_top = df_filtered['p'].value_counts().reset_index().head(5)
                fig2 = px.bar(df_top, x='count', y='p', orientation='h', template='plotly_white')
                fig2.update_traces(marker_color="#3F00FF")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Sem dados neste período.")
    else: st.info("Sem histórico financeiro.")

# 2. ESPIÃO
with tabs[1]:
    cl, cr = st.columns([1, 2])
    with cl:
        rc = get_messages(c_id)
        if rc.data:
            opts = {f"{c.get('metadata',{}).get('push_name','Cliente')}": c['id'] for c in rc.data}
            sel_chat = st.radio("Conversas Recentes:", list(opts.keys()))
            sid = opts[sel_chat]
        else: sid = None
    with cr:
        if sid:
            rm = get_chat_history(sid)
            msgs = rm.data[::-1] if rm.data else []
            with st.container(height=500, border=True):
                for m in msgs:
                    av = "👤" if m['role']=='user' else "🐙"
                    with st.chat_message(m['role'], avatar=av): st.write(m['content'])

# 3. PRODUTOS
with tabs[2]:
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown("##### Catálogo Atual")
        rp = get_products(c_id)
        if rp.data: st.dataframe(pd.DataFrame(rp.data), use_container_width=True, hide_index=True)
    with c2:
        with st.form("add_prod"):
            st.markdown("##### Adicionar Novo")
            n = st.text_input("Nome")
            c = st.text_input("Categoria")
            p = st.number_input("Preço (R$)", min_value=0.0)
            if st.form_submit_button("Salvar Item", type="primary"):
                if create_product(c_id, n, c, p):
                    st.success("Produto criado!")
                    st.rerun()

# 4. AGENDA (FORMATADA E BONITA)
with tabs[3]:
    st.subheader("Próximos Agendamentos")
    df_ag = get_agenda(c_id)
    if not df_ag.empty: 
        # Mostra a tabela limpa com datas formatadas
        st.dataframe(df_ag, use_container_width=True, hide_index=True)
    else: st.info("Nenhum agendamento encontrado.")

# 5. CÉREBRO
with tabs[4]:
    if perfil == 'admin':
        st.subheader("Personalidade e Inteligência")
        prompt_atual, config_atual = get_client_config(c_id)
        
        c_p1, c_p2 = st.columns([2, 1])
        with c_p1:
            new_prompt = st.text_area("Instruções Principais (Prompt)", value=prompt_atual or '', height=400)
        with c_p2:
            st.markdown("##### Voz e Criatividade")
            vozes = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            v_atual = config_atual.get('openai_voice', 'alloy')
            if v_atual not in vozes: v_atual = 'alloy'
            
            raw_temp = config_atual.get('temperature', 0.5)
            try: temp_val = float(str(raw_temp).replace(',', '.'))
            except: temp_val = 0.5
            
            new_voice = st.selectbox("Voz da IA:", vozes, index=vozes.index(v_atual))
            new_temp = st.slider("Criatividade:", 0.0, 1.0, value=temp_val, step=0.1)
            
            if st.button("💾 Salvar Configurações", type="primary", use_container_width=True):
                if update_brain(c_id, new_prompt, new_voice, new_temp, config_atual):
                    st.success("IA Atualizada com Sucesso!")
                    st.rerun()
    else: st.warning("Acesso restrito.")
