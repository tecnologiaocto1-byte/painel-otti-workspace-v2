import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import json
import time
import os
from datetime import datetime

# ==============================================================================
# 1. SETUP
# ==============================================================================
st.set_page_config(page_title="Otti Workspace", layout="wide", page_icon="🐙")

# --- CORES FIXAS (MODO CLARO ORIGINAL) ---
# Extraídas exatamente do dicionário 'light' do seu código
C_BG_LIGHT      = "#F0F2F5"
C_SIDEBAR_LIGHT = "#031A89" # Azul escuro
C_TEXT_LIGHT    = "#101828" # Texto escuro
C_CARD_LIGHT    = "#FFFFFF"
C_INPUT_BG      = "#FFFFFF"
C_INPUT_TEXT    = "#000000"
C_ACCENT        = "#3F00FF"
C_BTN_TEXT      = "#000000"

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
# 3. CSS (ORIGINAL RESTAURADO)
# ==============================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;800&family=Inter:wght@300;400;600&display=swap');

    .stApp {{ background-color: {C_BG_LIGHT}; color: {C_TEXT_LIGHT}; font-family: 'Inter', sans-serif; }}
    
    /* --- SIDEBAR (AZUL ESCURO) --- */
    section[data-testid="stSidebar"] {{ 
        background-color: {C_SIDEBAR_LIGHT}; 
        border-right: 1px solid rgba(255,255,255,0.1); 
    }}
    
    /* Regra Geral: Texto Branco na Sidebar (pois o fundo é AZUL ESCURO) */
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label {{ color: #FFFFFF !important; }}

    h1, h2, h3, h4 {{ font-family: 'Sora', sans-serif; color: {C_TEXT_LIGHT} !important; font-weight: 700; }}
    p, label {{ color: {C_TEXT_LIGHT} !important; }}

    /* --- INPUTS & SELECTBOX (BRANCO) --- */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
        background-color: {C_INPUT_BG} !important;
        color: {C_INPUT_TEXT} !important;
        border: 1px solid {C_ACCENT};
        border-radius: 8px;
    }}
    
    /* CRÍTICO: Container do Selectbox */
    div[data-baseweb="select"] > div {{
        background-color: {C_INPUT_BG} !important;
        border-color: {C_ACCENT} !important;
    }}
    
    /* CRÍTICO: Texto dentro do Selectbox (PRETO) */
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {{ 
        color: {C_INPUT_TEXT} !important; 
    }}
    
    /* Menu Dropdown */
    div[data-baseweb="popover"] {{ background-color: {C_INPUT_BG} !important; }}
    div[data-baseweb="option"] {{ color: {C_INPUT_TEXT} !important; }}

    /* --- BOTÃO PRIMARY (LOGIN/SALVAR) --- */
    button[kind="primary"] {{
        background: linear-gradient(90deg, #3F00FF 0%, #031A89 100%) !important;
        color: #FFFFFF !important; border: none !important; padding: 0.6rem 1.2rem; border-radius: 6px;
    }}

    /* --- BOTÃO SECUNDÁRIO --- */
    div[data-testid="stAppViewContainer"] .main .stButton > button {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid {C_ACCENT} !important;
    }}
    div[data-testid="stAppViewContainer"] .main .stButton > button:hover {{
        border-color: {C_ACCENT} !important;
        color: {C_ACCENT} !important;
    }}

    /* --- BOTÃO SIDEBAR (SAIR) --- */
    section[data-testid="stSidebar"] button {{
        background-color: transparent !important; border: 1px solid rgba(255,255,255,0.5) !important;
    }}
    section[data-testid="stSidebar"] button p {{ color: #FFFFFF !important; }}

    /* Cards */
    div[data-testid="stMetric"] {{ background-color: {C_CARD_LIGHT}; border: 1px solid {C_ACCENT}; border-radius: 8px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    div[data-testid="stMetricValue"] {{ color: {C_ACCENT} !important; font-family: 'Sora', sans-serif; }}
    label[data-testid="stMetricLabel"] {{ color: {C_TEXT_LIGHT} !important; opacity: 0.8; }}

    .login-wrapper {{ margin-top: 10vh; max-width: 400px; margin-left: auto; margin-right: auto; text-align: center; }}
    .login-wrapper div[data-testid="stImage"] {{ margin: 0 auto; display: block; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    .block-container {{padding-top: 2rem;}}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LOGIN
# ==============================================================================
def render_logo(width=100):
    if os.path.exists("logo.png"): st.image("logo.png", width=width)
    else: st.markdown(f"<h1 style='color:#3F00FF; margin:0; font-family:Sora; text-align:center;'>OCTO</h1>", unsafe_allow_html=True)

if 'usuario_logado' not in st.session_state: st.session_state['usuario_logado'] = None

def render_login_screen():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
        render_logo(width=120)
        st.markdown(f"<h3 style='margin-bottom:30px; color:{C_TEXT_LIGHT}; text-align:center;'>Otti Workspace</h3>", unsafe_allow_html=True)
        
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
perfil = user['perfil']

# SIDEBAR (Sem toggle de tema)
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    render_logo(width=130)
    st.markdown("---")
    st.write(f"Olá, **{user['nome_usuario']}**")
    
    st.markdown("---")
    if st.button("SAIR"):
        st.session_state['usuario_logado'] = None
        st.rerun()

if not supabase: st.stop()
try: df_kpis = pd.DataFrame(supabase.table('view_dashboard_kpis').select("*").execute().data)
except:
    st.error("Erro ao carregar dados.")
    st.stop()

if perfil == 'admin':
    lista = df_kpis['nome_empresa'].unique()
    if 'last_cli' not in st.session_state: st.session_state['last_cli'] = lista[0]
    if st.session_state['last_cli'] not in lista: st.session_state['last_cli'] = lista[0]
    idx = list(lista).index(st.session_state['last_cli'])
    sel = st.sidebar.selectbox("Cliente:", lista, index=idx, key="cli_selector")
    st.session_state['last_cli'] = sel
    c_data = df_kpis[df_kpis['nome_empresa'] == sel].iloc[0]
else:
    filtro = df_kpis[df_kpis['cliente_id'] == user['cliente_id']]
    if filtro.empty: st.stop()
    c_data = filtro.iloc[0]

c_id = int(c_data['cliente_id'])
active = not bool(c_data['bot_pausado'])

c1, c2 = st.columns([3, 1])
with c1:
    st.title(c_data['nome_empresa'])
    st.caption(f"ID: {c_id}")
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    lbl = "⏸️ PAUSAR" if active else "▶️ ATIVAR"
    if st.button(lbl, use_container_width=True):
        supabase.table('clientes').update({'bot_pausado': active}).eq('id', c_id).execute()
        st.rerun()

st.divider()

tot = c_data['total_mensagens']
sav = round((tot * 1.5) / 60, 1)
rev = float(c_data['receita_total'] or 0)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita", f"R$ {rev:,.2f}")
k2.metric("Tempo", f"{sav}h")
k3.metric("Atendimentos", c_data['total_atendimentos'])
k4.metric("Status", "Online" if active else "Offline")
st.markdown("<br>", unsafe_allow_html=True)

tabs = st.tabs(["Analytics", "Espião", "Produtos", "Agenda", "Cérebro"])

# --- CORREÇÃO DO ERRO DE DATA (Analytics) ---
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
            
            # --- Lógica de segurança para o date_input ---
            min_date = df['dt'].min()
            max_date = df['dt'].max()
            if pd.isnull(min_date): min_date = datetime.now().date()
            if pd.isnull(max_date): max_date = datetime.now().date()
            
            # Valor padrão seguro (dentro do range)
            default_val = datetime.now().date()
            if default_val < min_date: default_val = min_date
            if default_val > max_date: default_val = max_date
            
            # Date input seguro
            d_select = st.date_input("Filtrar Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)

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
                    fig = px.line(df_g, x='dt', y='v', template='plotly_white', markers=True)
                    fig.update_traces(line_color="#3F00FF", line_width=3)
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_LIGHT})
                    st.plotly_chart(fig, use_container_width=True)
            with c_g2:
                st.markdown("##### Produtos Mais Vendidos")
                df_top = df_filt['p'].value_counts().reset_index().head(5)
                if not df_top.empty:
                    fig2 = px.bar(df_top, x='count', y='p', orientation='h', template='plotly_white')
                    fig2.update_traces(marker_color="#5396FF")
                    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_LIGHT})
                    st.plotly_chart(fig2, use_container_width=True)
        else: st.info("Sem dados.")
    except Exception as e: st.error(f"Erro Visual: {e}")

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
                sel = st.radio("Conversas:", list(opts.keys()))
                sid = opts[sel]
                if st.button("Atualizar"): st.rerun()
            else: sid = None
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

with tabs[2]:
    c1, c2 = st.columns([2,1])
    with c1:
        rp = supabase.table('produtos').select('nome, categoria, ativo').eq('cliente_id', c_id).order('nome').execute()
        if rp.data: st.dataframe(pd.DataFrame(rp.data), use_container_width=True, hide_index=True)
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

# --- CÉREBRO (COM BOTÃO SALVAR) ---
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
                    nova_temp = st.slider("Criatividade da Resposta:", min_value=0.0, max_value=1.0, value=temp_atual, step=0.1)
                    st.caption("🤖 0.0 = Mais Robótico | 🎨 1.0 = Mais Criativo")
                    
                    with st.expander("🗣️ Guia de Vozes"):
                        st.markdown("""
                        - **Alloy:** Neutra/Padrão
                        - **Echo:** Masculina/Suave
                        - **Onyx:** Masculina/Grave
                        - **Nova:** Feminina/Alegre
                        - **Shimmer:** Feminina/Sofisticada
                        """)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- BOTÃO SALVAR QUE FALTAVA ---
                if st.button("SALVAR CONFIGURAÇÕES", type="primary"):
                    curr_c['openai_voice'] = nova_voz
                    curr_c['temperature'] = nova_temp
                    
                    supabase.table('clientes').update({
                        'prompt_full': new_p,
                        'config_fluxo': json.dumps(curr_c)
                    }).eq('id', c_id).execute()
                    
                    st.success("Configurações salvas com sucesso!")
                    time.sleep(1)
                    st.rerun()

        except Exception as e: st.error(f"Erro: {e}")
