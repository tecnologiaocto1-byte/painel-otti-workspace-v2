import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import json
import time
import os
from datetime import datetime, timedelta

# ==============================================================================
# 1. SETUP
# ==============================================================================
st.set_page_config(page_title="Otti Workspace", layout="wide", page_icon="🐙")

# --- DEFINIÇÃO DE TEMAS ---
if 'theme' not in st.session_state: 
    st.session_state['theme'] = 'dark'

# Definição de Cores Baseadas no Tema
if st.session_state['theme'] == 'dark':
    P = {
        'bg': "#001024",
        'sidebar': "#020A14",
        'text': "#F8FAFC",
        'card': "rgba(3, 26, 137, 0.2)",
        'input_bg': "#0B1221",
        'input_text': "#FFFFFF",
        'input_border': "#3F00FF", # Borda Neon no Dark
        'metric_val': "#E7F9A9",
        'btn_bg': "#0B1221",
        'btn_text': "#FFFFFF",
        'chart_template': 'plotly_dark',
        'sidebar_text': "#FFFFFF" # Texto forçado branco na sidebar escura
    }
else:
    # LIGHT MODE "CLEAN" (Estilo Antigo/Padrão)
    P = {
        'bg': "#F0F2F5",
        'sidebar': "#FFFFFF", # Sidebar Branca
        'text': "#101828",
        'card': "#FFFFFF",
        'input_bg': "#FFFFFF",
        'input_text': "#000000",
        'input_border': "#E0E0E0", # Borda suave no Light
        'metric_val': "#3F00FF",
        'btn_bg': "#FFFFFF",
        'btn_text': "#000000",
        'chart_template': 'plotly_white',
        'sidebar_text': "#101828" # Texto escuro na sidebar clara
    }

# ==============================================================================
# 2. CONEXÃO
# ==============================================================================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_connection():
    if not SUPABASE_URL: return None
    try: return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

supabase = init_connection()

# ==============================================================================
# 3. CSS INTELIGENTE (CORRIGIDO)
# ==============================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;800&family=Inter:wght@300;400;600&display=swap');

    .stApp {{ background-color: {P['bg']}; color: {P['text']}; font-family: 'Inter', sans-serif; }}
    
    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {{ 
        background-color: {P['sidebar']}; 
        border-right: 1px solid rgba(0,0,0,0.05); 
    }}
    
    /* Cor do texto da Sidebar dinâmica */
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label {{ color: {P['sidebar_text']} !important; }}

    h1, h2, h3, h4 {{ font-family: 'Sora', sans-serif; color: {P['text']} !important; font-weight: 700; }}
    p, label {{ color: {P['text']} !important; }}

    /* --- INPUTS & SELECTBOX --- */
    /* Removemos o !important agressivo das cores para o Light Mode fluir melhor */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
        background-color: {P['input_bg']} !important;
        color: {P['input_text']} !important;
        border: 1px solid {P['input_border']};
        border-radius: 8px;
    }}
    
    /* Selectbox Container */
    div[data-baseweb="select"] > div {{
        background-color: {P['input_bg']} !important;
        border-color: {P['input_border']} !important;
        color: {P['input_text']} !important;
    }}
    
    /* Texto do Selectbox e Dropdown */
    div[data-baseweb="select"] span, div[data-baseweb="popover"] {{ 
        color: {P['input_text']} !important; 
    }}
    
    /* Opções do Menu Dropdown */
    div[data-baseweb="option"] {{
        background-color: {P['input_bg']} !important;
        color: {P['input_text']} !important;
    }}

    /* --- BOTÃO PRIMARY --- */
    button[kind="primary"] {{
        background: linear-gradient(90deg, #3F00FF 0%, #031A89 100%) !important;
        color: #FFFFFF !important; border: none !important; padding: 0.6rem 1.2rem; border-radius: 6px;
    }}

    /* --- BOTÃO SECUNDÁRIO --- */
    div[data-testid="stAppViewContainer"] .main .stButton > button {{
        background-color: {P['btn_bg']} !important;
        color: {P['btn_text']} !important;
        border: 1px solid {P['input_border']} !important;
    }}

    /* Cards/Metrics */
    div[data-testid="stMetric"] {{ 
        background-color: {P['card']}; 
        border: 1px solid {P['input_border']}; 
        border-radius: 8px; 
        padding: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
    }}
    div[data-testid="stMetricValue"] {{ color: {P['metric_val']} !important; font-family: 'Sora', sans-serif; }}
    
    .login-wrapper {{ margin-top: 10vh; max-width: 400px; margin-left: auto; margin-right: auto; text-align: center; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    .block-container {{padding-top: 2rem;}}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LOGIN
# ==============================================================================
def render_logo(width=100):
    # Fallback visual se não tiver imagem
    st.markdown(f"<h1 style='color:#3F00FF; margin:0; font-family:Sora; text-align:center; font-size: 2rem;'>OCTO</h1>", unsafe_allow_html=True)

if 'usuario_logado' not in st.session_state: st.session_state['usuario_logado'] = None

def render_login_screen():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
        render_logo(width=120)
        st.markdown(f"<h3 style='margin-bottom:30px; color:{P['text']}; text-align:center;'>Otti Workspace</h3>", unsafe_allow_html=True)
        
        with st.form("login_master"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("ACESSAR SISTEMA", use_container_width=True, type="primary")
            
            if submitted:
                if not email or not senha: st.warning("Preencha todos os campos.")
                else:
                    if not supabase: st.error("Erro interno.")
                    else:
                        try:
                            # Tabela simplificada para o exemplo
                            res = supabase.table('acesso_painel').select('*').eq('email', email).eq('senha', senha).execute()
                            if res.data:
                                st.session_state['usuario_logado'] = res.data[0]
                                st.rerun()
                            else: st.error("Credenciais inválidas.")
                        except: st.error("Erro de conexão.")
        st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state['usuario_logado']:
    render_login_screen()
    st.stop()

# ==============================================================================
# 5. DASHBOARD
# ==============================================================================
user = st.session_state['usuario_logado']
perfil = user.get('perfil', 'user')

# SIDEBAR
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    render_logo(width=130)
    st.markdown("---")
    st.write(f"Olá, **{user.get('nome_usuario', 'User')}**")
    
    dark_on = (st.session_state['theme'] == 'dark')
    if st.toggle("🌙 Modo Escuro", value=dark_on):
        if st.session_state['theme'] != 'dark':
            st.session_state['theme'] = 'dark'
            st.rerun()
    else:
        if st.session_state['theme'] != 'light':
            st.session_state['theme'] = 'light'
            st.rerun()

    st.markdown("---")
    if st.button("SAIR"):
        st.session_state['usuario_logado'] = None
        st.rerun()

if not supabase: st.stop()

# Carregamento de dados
try: 
    # Tenta carregar KPI, se falhar cria DF vazio
    kpis_data = supabase.table('view_dashboard_kpis').select("*").execute().data
    df_kpis = pd.DataFrame(kpis_data) if kpis_data else pd.DataFrame()
except:
    df_kpis = pd.DataFrame()

if df_kpis.empty:
    st.warning("Nenhum dado de KPI encontrado.")
    st.stop()

if perfil == 'admin':
    lista = df_kpis['nome_empresa'].unique()
    if 'last_cli' not in st.session_state: st.session_state['last_cli'] = lista[0]
    # Proteção caso a lista mude
    if st.session_state['last_cli'] not in lista: st.session_state['last_cli'] = lista[0]
    
    idx = list(lista).index(st.session_state['last_cli'])
    sel = st.sidebar.selectbox("Cliente:", lista, index=idx, key="cli_selector")
    st.session_state['last_cli'] = sel
    c_data = df_kpis[df_kpis['nome_empresa'] == sel].iloc[0]
else:
    filtro = df_kpis[df_kpis['cliente_id'] == user['cliente_id']]
    if filtro.empty: 
        st.error("Cliente não encontrado nos KPIs.")
        st.stop()
    c_data = filtro.iloc[0]

c_id = int(c_data['cliente_id'])
active = not bool(c_data.get('bot_pausado', False))

c1, c2 = st.columns([3, 1])
with c1:
    st.title(c_data.get('nome_empresa', 'Empresa'))
    st.caption(f"ID: {c_id}")
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    lbl = "⏸️ PAUSAR" if active else "▶️ ATIVAR"
    if st.button(lbl, use_container_width=True):
        supabase.table('clientes').update({'bot_pausado': active}).eq('id', c_id).execute()
        st.rerun()

st.divider()

tot = c_data.get('total_mensagens', 0)
sav = round((tot * 1.5) / 60, 1)
rev = float(c_data.get('receita_total', 0) or 0)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita", f"R$ {rev:,.2f}")
k2.metric("Tempo", f"{sav}h")
k3.metric("Atendimentos", c_data.get('total_atendimentos', 0))
k4.metric("Status", "Online" if active else "Offline")
st.markdown("<br>", unsafe_allow_html=True)

tabs = st.tabs(["Analytics", "Espião", "Produtos", "Agenda", "Cérebro"])

# ==============================================================================
# TAB 1: ANALYTICS (CORREÇÃO DO DATE_INPUT)
# ==============================================================================
with tabs[0]:
    try:
        r_s = supabase.table('agendamentos_salao').select('created_at, valor_sinal_registrado, status, produto_salao_id').eq('cliente_id', c_id).execute().data
        r_p = supabase.table('agendamentos').select('created_at, valor_sinal_registrado, status, servico_id').eq('cliente_id', c_id).execute().data
        r_pr = supabase.table('produtos').select('id, nome').eq('cliente_id', c_id).execute().data
        map_pr = {p['id']: p['nome'] for p in r_pr} if r_pr else {}
        
        lista = []
        if r_s:
            for i in r_s: lista.append({'dt': i['created_at'], 'v': i.get('valor_sinal_registrado',0), 'st': i['status'], 'p': map_pr.get(i.get('produto_salao_id'), 'Salão')})
        if r_p:
            for i in r_p: lista.append({'dt': i['created_at'], 'v': i.get('valor_sinal_registrado',0), 'st': i['status'], 'p': map_pr.get(i.get('servico_id'), 'Serviço')})
        
        if lista:
            df = pd.DataFrame(lista)
            df['dt'] = pd.to_datetime(df['dt'], format='mixed').dt.date
            df = df[df['st'] != 'Cancelado']
            
            # --- CORREÇÃO DO DATE INPUT ---
            # O erro acontecia aqui. Vamos calcular min e max seguros.
            min_date = df['dt'].min()
            max_date = df['dt'].max()
            
            # Se por acaso os dados estiverem vazios ou null, fallback para hoje
            if pd.isnull(min_date): min_date = datetime.now().date()
            if pd.isnull(max_date): max_date = datetime.now().date()
            
            # O value padrão (hoje) deve estar DENTRO dos limites
            default_val = datetime.now().date()
            if default_val < min_date: default_val = min_date
            if default_val > max_date: default_val = max_date
            
            # Filtro de Data
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                # Agora usamos variáveis seguras
                d_select = st.date_input(
                    "Filtrar Período", 
                    value=(min_date, max_date), # Padrão: Todo o período
                    min_value=min_date, 
                    max_value=max_date
                )
            
            # Aplica filtro se for um range (tupla de 2)
            if isinstance(d_select, tuple) and len(d_select) == 2:
                start_d, end_d = d_select
                mask = (df['dt'] >= start_d) & (df['dt'] <= end_d)
                df_filt = df.loc[mask]
            else:
                df_filt = df

            c_g1, c_g2 = st.columns(2)
            with c_g1:
                st.markdown("##### Receita Diária")
                df_g = df_filt.groupby('dt')['v'].sum().reset_index()
                if not df_g.empty:
                    fig = px.line(df_g, x='dt', y='v', template=P['chart_template'], markers=True)
                    fig.update_traces(line_color="#3F00FF", line_width=3)
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': P['text']})
                    st.plotly_chart(fig, use_container_width=True)
                else: st.info("Sem dados no período.")
                
            with c_g2:
                st.markdown("##### Produtos Mais Vendidos")
                df_top = df_filt['p'].value_counts().reset_index().head(5)
                if not df_top.empty:
                    fig2 = px.bar(df_top, x='count', y='p', orientation='h', template=P['chart_template'])
                    fig2.update_traces(marker_color="#5396FF")
                    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': P['text']})
                    st.plotly_chart(fig2, use_container_width=True)
                else: st.info("Sem dados.")
        else:
            st.info("Sem dados de transações.")
    except Exception as e:
        st.error(f"Erro Visual: {e}")

# ==============================================================================
# TAB 2: ESPIÃO
# ==============================================================================
with tabs[1]:
    cl, cr = st.columns([1, 2])
    with cl:
        try:
            rc = supabase.table('conversas').select('id, cliente_wa_id, updated_at, metadata').eq('cliente_id', c_id).order('updated_at', desc=True).limit(15).execute()
            if rc.data:
                opts = {}
                for c in rc.data:
                    dt = pd.to_datetime(c['updated_at']).strftime('%d/%m %H:%M') if c['updated_at'] else ""
                    m = c.get('metadata') or {}
                    nm = m.get('push_name') or c['cliente_wa_id']
                    opts[f"{nm} ({dt})"] = c['id']
                
                sel = st.radio("Conversas Recentes:", list(opts.keys()))
                sid = opts[sel]
                if st.button("🔄 Atualizar Conversas"): st.rerun()
            else: 
                sid = None
                st.info("Nenhuma conversa recente.")
        except: sid = None
    with cr:
        if sid:
            try:
                rm = supabase.table('historico_mensagens').select('*').eq('conversa_id', sid).order('created_at', desc=True).limit(40).execute()
                msgs = rm.data[::-1] if rm.data else []
                cont = st.container(height=500)
                with cont:
                    for m in msgs:
                        role = m['role']
                        av = "👤" if role=='user' else "🐙"
                        with st.chat_message(role, avatar=av): st.write(m['content'])
            except: pass

# ==============================================================================
# TAB 3: PRODUTOS
# ==============================================================================
with tabs[2]:
    c1, c2 = st.columns([2,1])
    with c1:
        rp = supabase.table('produtos').select('nome, categoria, ativo').eq('cliente_id', c_id).order('nome').execute()
        if rp.data: st.dataframe(pd.DataFrame(rp.data), use_container_width=True, hide_index=True)
        else: st.info("Nenhum produto cadastrado.")
    with c2:
        with st.form("add"):
            st.write("Novo Item")
            n = st.text_input("Nome")
            c = st.text_input("Categoria")
            p = st.number_input("Preço", min_value=0.0)
            if st.form_submit_button("Salvar", type="primary"):
                js = {"preco_padrao": p, "duracao_minutos": 60}
                supabase.table('produtos').insert({"cliente_id": c_id, "nome": n, "categoria": c, "ativo": True, "regras_preco": json.dumps(js)}).execute()
                st.rerun()

# ==============================================================================
# TAB 4: AGENDA
# ==============================================================================
with tabs[3]:
    st.subheader("Próximos Agendamentos")
    try:
        df_final = pd.DataFrame()
        rs = supabase.table('agendamentos_salao').select('data_reserva, valor_total_registrado, cliente_final_waid').eq('cliente_id', c_id).order('created_at', desc=True).limit(50).execute()
        rv = supabase.table('agendamentos').select('data_hora_inicio, valor_total_registrado').eq('cliente_id', c_id).order('created_at', desc=True).limit(50).execute()
        
        if rs.data:
            d = pd.DataFrame(rs.data)
            d['Data'] = pd.to_datetime(d['data_reserva']).dt.strftime('%d/%m/%Y')
            df_final = d[['Data', 'valor_total_registrado', 'cliente_final_waid']]
            df_final.columns = ['Data', 'Valor (R$)', 'Cliente']
        elif rv.data:
            d = pd.DataFrame(rv.data)
            d['Data/Hora'] = pd.to_datetime(d['data_hora_inicio']).dt.strftime('%d/%m/%Y %H:%M')
            df_final = d[['Data/Hora', 'valor_total_registrado']]
            df_final.columns = ['Data/Hora', 'Valor (R$)']
            
        if not df_final.empty: st.dataframe(df_final, use_container_width=True, hide_index=True)
        else: st.info("Agenda vazia.")
    except Exception as e: st.error(f"Erro agenda: {e}")

# ==============================================================================
# TAB 5: CÉREBRO
# ==============================================================================
if perfil == 'admin' and len(tabs) > 4:
    with tabs[4]:
        st.subheader("Configuração da IA")
        try:
            res = supabase.table('clientes').select('config_fluxo, prompt_full').eq('id', c_id).execute()
            if res.data:
                d = res.data[0]
                curr_c = d.get('config_fluxo') or {}
                if isinstance(curr_c, str): curr_c = json.loads(curr_c)
                
                raw_temp = curr_c.get('temperature', 0.5)
                if isinstance(raw_temp, str):
                    try:
                        raw_temp = raw_temp.replace(',', '.')
                        curr_c['temperature'] = float(raw_temp)
                    except: curr_c['temperature'] = 0.5

                c_p1, c_p2 = st.columns([2, 1])
                with c_p1:
                    st.markdown("##### 1. Personalidade (Prompt)")
                    new_p = st.text_area("", value=d.get('prompt_full','') or '', height=350)

                with c_p2:
                    st.markdown("##### 2. Áudio e Voz")
                    vozes = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
                    v_atual = curr_c.get('openai_voice', 'alloy')
                    if v_atual not in vozes: v_atual = 'alloy'
                    
                    nova_voz = st.selectbox("Voz da IA:", vozes, index=vozes.index(v_atual))
                    
                    temp_atual = float(curr_c.get('temperature', 0.5))
                    nova_temp = st.slider("Criatividade:", min_value=0.0, max_value=1.0, value=temp_atual, step=0.1)
                    
                    with st.expander("🗣️ Guia de Vozes"):
                        st.markdown("""
                        - **Alloy:** Neutra
                        - **Echo:** Masc. Suave
                        - **Onyx:** Masc. Grave
                        - **Nova:** Fem. Alegre
                        - **Shimmer:** Fem. Chique
                        """)
        except Exception as e: st.error(f"Erro: {e}")
