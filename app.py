import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import json
import time
import os
import base64
from datetime import datetime, timedelta, time as dt_time

# ==============================================================================
# 1. SETUP
# ==============================================================================

st.set_page_config(
    page_title="Otti Workspace", 
    layout="wide", 
    page_icon="🐙", 
    initial_sidebar_state="expanded" 
)

# --- CORES OFICIAIS OCTO ---
C_BG_OCTO_LIGHT = "#E2E8F0"
C_SIDEBAR_NAVY  = "#031A89"
C_ACCENT_NEON   = "#3F00FF"
C_TEXT_DARK     = "#101828"
C_CARD_WHITE    = "#FFFFFF"
C_BTN_DARK      = "#031A89"

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
# 3. CSS (VISUAL)
# ==============================================================================

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;800&family=Inter:wght@300;400;600&display=swap');

    .stApp {{ background-color: {C_BG_OCTO_LIGHT}; color: {C_TEXT_DARK}; font-family: 'Inter', sans-serif; }}
    
    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {{ background-color: {C_SIDEBAR_NAVY}; border-right: 1px solid rgba(255,255,255,0.1); }}
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {{ color: #FFFFFF !important; }}

    h1 {{ font-family: 'Sora', sans-serif; color: {C_SIDEBAR_NAVY} !important; font-weight: 800; }}
    h2, h3, h4 {{ font-family: 'Sora', sans-serif; color: {C_TEXT_DARK} !important; font-weight: 700; }}
    p, label {{ color: {C_TEXT_DARK} !important; }}

    /* --- ABAS --- */
    button[data-baseweb="tab"] {{
        color: {C_TEXT_DARK} !important;
        font-family: 'Sora', sans-serif !important;
        font-weight: 600 !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {C_ACCENT_NEON} !important;
        border-color: {C_ACCENT_NEON} !important;
    }}

    /* --- INPUTS --- */
    .stTextInput > div > div > input {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
    }}
    .stTextInput > div > div > button {{
        background-color: transparent !important;
        color: #64748B !important;
        border: none !important;
    }}

    div[data-baseweb="select"] > div {{ background-color: #FFFFFF !important; border-color: #CBD5E1 !important; }}
    div[data-baseweb="select"] span {{ color: #000000 !important; }}
    div[data-baseweb="popover"] {{ background-color: #FFFFFF !important; }}
    div[data-baseweb="option"] {{ color: #000000 !important; }}

    /* --- BOTÕES GERAIS --- */
    button[kind="primary"] {{
        background-color: #FFFFFF !important;
        color: {C_ACCENT_NEON} !important;
        border: 2px solid {C_ACCENT_NEON} !important;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        font-weight: 700;
        transition: all 0.2s ease;
    }}
    button[kind="primary"]:hover {{
        background-color: {C_ACCENT_NEON} !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(63, 0, 255, 0.2);
        transform: translateY(-1px);
    }}

    /* --- BOTÕES DA SIDEBAR (Correção do botão branco) --- */
    section[data-testid="stSidebar"] button[kind="secondary"] {{
        background-color: transparent !important;
        border: 1px solid rgba(255,255,255,0.6) !important;
        color: #FFFFFF !important;
    }}
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background-color: #FFFFFF !important;
        color: {C_SIDEBAR_NAVY} !important;
        border-color: #FFFFFF !important;
    }}
    
    /* O Botão "Novo Cliente" agora será AZUL NEON com texto BRANCO */
    section[data-testid="stSidebar"] button[kind="primary"] {{
        background-color: {C_ACCENT_NEON} !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 800 !important;
    }}
    section[data-testid="stSidebar"] button[kind="primary"]:hover {{
        background-color: #FFFFFF !important;
        color: {C_ACCENT_NEON} !important;
        transform: scale(1.02);
    }}
    
    /* --- LOGIN & MOBILE --- */
    .login-container {{
        max-width: 400px; margin: 8vh auto 0 auto; background: white;
        border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); overflow: hidden; 
    }}
    .login-header {{
        background-color: {C_SIDEBAR_NAVY}; padding: 30px 0; text-align: center;
        border-bottom: 4px solid {C_ACCENT_NEON}; display: flex; justify-content: center; align-items: center;
    }}
    .login-body {{ padding: 40px; padding-top: 20px; }}
    div[data-testid="stForm"] {{ border: none; padding: 0; }}

    @media (max-width: 600px) {{
        .login-container {{ margin-top: 2vh; width: 95%; margin-left: auto; margin-right: auto; }}
    }}

    /* --- HEADER E CONTAINER --- */
    #MainMenu, footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    .block-container {{padding-top: 0rem !important; padding-bottom: 2rem;}}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LOGIN
# ==============================================================================

def get_image_as_base64(path):
    try:
        with open(path, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None

if 'usuario_logado' not in st.session_state: st.session_state['usuario_logado'] = None

def render_login_screen():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        logo_b64 = get_image_as_base64("logo.png")
        if logo_b64:
            img_html = f'<img src="data:image/png;base64,{logo_b64}" width="120" style="filter: brightness(0) invert(1); display: block; margin: 0 auto;">'
        else:
            img_html = '<h1 style="color:white !important; margin:0; font-family:Sora;">OCTO</h1>'

        st.markdown(f"""
        <div class="login-container">
            <div class="login-header">
                {img_html}
            </div>
            <div class="login-body">
                <h4 style="text-align:center; color:#101828; margin-bottom:20px; font-family:Sora;">Acessar Workspace</h4>
        """, unsafe_allow_html=True)

        with st.form("login_master"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")            

            st.markdown("<br>", unsafe_allow_html=True)          
            submitted = st.form_submit_button("ENTRAR", type="primary", use_container_width=True)          

            if submitted:
                if not email or not senha: 
                    st.warning("Preencha todos os campos.")
                else:
                    if not supabase: 
                        st.error("Erro de configuração interna.")
                    else:
                        try:
                            res = supabase.table('acesso_painel').select('*').eq('email', email).eq('senha', senha).execute()
                            if res.data:
                                st.session_state['usuario_logado'] = res.data[0]
                                st.rerun()
                            else: 
                                st.error("Dados incorretos.")
                        except Exception as e:
                            st.error(f"Erro técnico: {e}")

        st.markdown('</div></div>', unsafe_allow_html=True)

if not st.session_state['usuario_logado']:
    render_login_screen()
    st.stop()

# ==============================================================================
# 5. CARREGAMENTO DE DADOS (CRUCIAL: ANTES DA SIDEBAR)
# ==============================================================================

user = st.session_state['usuario_logado']
perfil = user.get('perfil', 'user')

# --- CONFIGURAÇÃO DE NAVEGAÇÃO ---
if 'modo_view' not in st.session_state: 
    st.session_state['modo_view'] = 'dashboard'

if perfil != 'admin':
    st.session_state['modo_view'] = 'dashboard'

# --- CARREGA DADOS DO BANCO (CORREÇÃO DO ERRO) ---
# Carregamos isso AQUI para a variável df_kpis existir quando a sidebar for montada.
if not supabase: st.stop()
try: 
    df_kpis = pd.DataFrame(supabase.table('view_dashboard_kpis').select("*").execute().data)
except: 
    df_kpis = pd.DataFrame()

# Inicializa c_data como None para segurança
c_data = None

# ==============================================================================
# 6. SIDEBAR
# ==============================================================================

def render_sidebar_logo():
    if os.path.exists("logo.png"): st.image("logo.png", width=120)
    else: st.markdown(f"<h1 style='color:white; margin:0;'>OCTO</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    render_sidebar_logo()
    st.markdown("---")
    st.write(f"Olá, **{user.get('nome_usuario', 'User')}**")
    st.markdown("---")

    if st.button("SAIR", type="secondary"): 
        st.session_state['usuario_logado'] = None
        st.rerun()

    # --- MENU DE ADMIN ---
    if perfil == 'admin':
        st.success("🔒 PAINEL ADMIN")
        
        # MODO DASHBOARD: Mostra seletor e botão de novo
        if st.session_state['modo_view'] == 'dashboard':
            if not df_kpis.empty:
                lista = df_kpis['nome_empresa'].unique()
                if 'last_cli' not in st.session_state: st.session_state['last_cli'] = lista[0]
                if st.session_state['last_cli'] not in lista: st.session_state['last_cli'] = lista[0]
                
                idx = list(lista).index(st.session_state['last_cli'])
                sel = st.selectbox("Cliente:", lista, index=idx, key="cli_selector")
                st.session_state['last_cli'] = sel
                
                # Define o cliente selecionado
                c_data = df_kpis[df_kpis['nome_empresa'] == sel].iloc[0]
            else:
                st.warning("Sem dados de KPI.")
                c_data = None
            
            st.markdown("---")
            # BOTÃO DE CADASTRO (Agora com CSS corrigido para Azul)
            if st.button("➕ NOVO CLIENTE", type="primary", use_container_width=True):
                st.session_state['modo_view'] = 'cadastro'
                st.rerun()
        
        # MODO CADASTRO: Mostra botão de voltar
        else:
            st.info("Modo de Cadastro")
            st.markdown("---")
            if st.button("⬅️ VOLTAR AO PAINEL", type="secondary", use_container_width=True):
                st.session_state['modo_view'] = 'dashboard'
                st.rerun()

    # --- MENU DE USUÁRIO COMUM ---
    else:
        filtro = df_kpis[df_kpis['cliente_id'] == user['cliente_id']]
        if filtro.empty: 
            st.error("Cliente não encontrado.")
            st.stop()
        c_data = filtro.iloc[0]

# ==============================================================================
# 7. ROTEADOR DE TELAS (MAIN CONTENT)
# ==============================================================================

# --- TELA 1: CADASTRO DE CLIENTE (Exclusivo Admin) ---
if perfil == 'admin' and st.session_state['modo_view'] == 'cadastro':
    st.title("🏢 Cadastro de Novo Cliente")
    st.markdown("Crie uma nova empresa e o login do administrador dela.")
    st.divider()

    with st.container(border=True):
        with st.form("form_novo_cliente_full"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Dados da Empresa")
                empresa_nome = st.text_input("Nome da Empresa")
                whats_id = st.text_input("WhatsApp ID (Ex: 551199999999)")
            
            with col_b:
                st.subheader("Login do Admin")
                email_login = st.text_input("E-mail de Acesso")
                senha_login = st.text_input("Senha Inicial", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.form_submit_button("✅ CADASTRAR SISTEMA", type="primary", use_container_width=True):
                if not empresa_nome or not email_login or not senha_login:
                    st.warning("Preencha todos os campos.")
                else:
                    try:
                        with st.spinner("Criando infraestrutura..."):
                            # Config Padrão
                            cfg_padrao = {
                                "horario_inicio": "09:00", "horario_fim": "18:00", 
                                "sinal_minimo_reais": 100.0, "temperature": 0.5,
                                "responde_em_audio": False, "openai_voice": "alloy"
                            }
                            # 1. Cria Cliente
                            res = supabase.table('clientes').insert({
                                "nome_empresa": empresa_nome, "whatsapp_id": whats_id,
                                "ativo": True, "bot_pausado": False, "config_fluxo": cfg_padrao
                            }).execute()
                            
                            if res.data:
                                new_id = res.data[0]['id']
                                # 2. Cria Login
                                supabase.table('acesso_painel').insert({
                                    "cliente_id": new_id, "email": email_login, "senha": senha_login,
                                    "nome_usuario": f"Admin {empresa_nome}", "perfil": "user"
                                }).execute()
                                
                                st.success("Cliente criado com sucesso!")
                                time.sleep(1.5)
                                st.session_state['modo_view'] = 'dashboard'
                                st.rerun()
                            else:
                                st.error("Erro ao gerar ID da empresa.")
                    except Exception as e:
                        st.error(f"Erro técnico: {e}")

# --- TELA 2: DASHBOARD (Se não for cadastro, cai aqui) ---
else:
    # Verificação de segurança (caso c_data não tenha sido preenchido na sidebar)
    if c_data is None:
        st.info("Nenhum cliente selecionado ou base de dados vazia.")
        st.stop()

    # >>>>> INÍCIO DO PAINEL <<<<<
    
    c_id = int(c_data['cliente_id'])
    active = not bool(c_data.get('bot_pausado', False))

    c1, c2 = st.columns([3, 1])
    with c1:
        st.title(c_data['nome_empresa'])
        st.caption(f"ID: {c_id}")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        lbl = "⏸️ PAUSAR SISTEMA" if active else "▶️ ATIVAR SISTEMA"
        if st.button(lbl, use_container_width=True):
            supabase.table('clientes').update({'bot_pausado': active}).eq('id', c_id).execute()
            st.rerun()

    st.divider()

    # --- CÁLCULO DE KPIS ---
    SALARIO_MINIMO = 1518.00
    HORAS_MENSAIS = 22 * 8
    CUSTO_HORA = SALARIO_MINIMO / HORAS_MENSAIS

    tot_msgs = c_data.get('total_mensagens', 0)
    horas_economizadas = round((tot_msgs * 1.5) / 60, 1)
    valor_economia = horas_economizadas * CUSTO_HORA
    receita_direta = float(c_data.get('receita_total', 0) or 0)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Receita Direta", f"R$ {receita_direta:,.2f}")
    k2.metric("Economia Estimada", f"R$ {valor_economia:,.2f}")
    k3.metric("Atendimentos", c_data.get('total_atendimentos', 0))
    k4.metric("Status Atual", "Online 🟢" if active else "Offline 🔴")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- ABAS (TABS) ---
    tabs = st.tabs(["📊 Analytics", "📦 Produtos", "📅 Agenda", "🧠 Cérebro"])

    # --------------------------------------------------------------------------
    # TAB 1: ANALYTICS
    # --------------------------------------------------------------------------
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
                df['dt_full'] = pd.to_datetime(df['dt'], format='mixed')
                df['dt'] = df['dt_full'].dt.date
                df = df[df['st'] != 'Cancelado']
                
                min_date = df['dt'].min()
                max_date = df['dt'].max()
                if pd.isnull(min_date): min_date = datetime.now().date()
                if pd.isnull(max_date): max_date = datetime.now().date()
                
                with st.container(border=True):
                    cf1, cf2 = st.columns(2)
                    with cf1:
                        d_select = st.date_input("📅 Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)
                    with cf2:
                        prods_un = df['p'].unique()
                        prod_sel = st.multiselect("📦 Filtrar Produtos", prods_un, default=prods_un)

                df_filt = df.copy()
                if isinstance(d_select, tuple) and len(d_select) == 2:
                    start_d, end_d = d_select
                    df_filt = df_filt[(df_filt['dt'] >= start_d) & (df_filt['dt'] <= end_d)]
                if prod_sel:
                    df_filt = df_filt[df_filt['p'].isin(prod_sel)]

                st.markdown("<br>", unsafe_allow_html=True)

                # Gráficos
                c_g1, c_g2 = st.columns(2)
                with c_g1:
                    st.markdown("##### 📈 Receita Diária")
                    df_g = df_filt.groupby('dt')['v'].sum().reset_index()
                    if not df_g.empty:
                        fig = px.line(df_g, x='dt', y='v', text='v')
                        fig.update_traces(line_shape='spline', line_color=C_ACCENT_NEON, line_width=4, textposition="top center", texttemplate='R$%{text:.0f}', mode='lines+text')
                        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_DARK}, xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=False, showticklabels=False, title=None), margin=dict(l=0, r=0, t=20, b=20))
                        st.plotly_chart(fig, use_container_width=True)
                    else: st.info("Sem dados.")

                with c_g2:
                    st.markdown("##### 📊 Volume")
                    df_vol = df_filt.groupby('dt').size().reset_index(name='qtd')
                    if not df_vol.empty:
                        fig_vol = px.bar(df_vol, x='dt', y='qtd', text='qtd')
                        fig_vol.update_traces(marker_color=C_SIDEBAR_NAVY, textposition='outside')
                        fig_vol.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_DARK}, xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=False, showticklabels=False, title=None), margin=dict(l=0, r=0, t=20, b=20))
                        st.plotly_chart(fig_vol, use_container_width=True)
                    else: st.info("Sem dados.")

            else: st.info("Sem dados para exibir.")
        except Exception as e: st.error(f"Erro Visual: {e}")

    # --------------------------------------------------------------------------
    # TAB 2: PRODUTOS
    # --------------------------------------------------------------------------
    with tabs[1]:
        rp = supabase.table('produtos').select('id, nome, categoria, regras_preco').eq('cliente_id', c_id).order('nome').execute()
        lista_produtos = []
        if rp.data:
            for item in rp.data:
                regras = item.get('regras_preco', {})
                if isinstance(regras, str):
                    try: regras = json.loads(regras)
                    except: regras = {}
                if not isinstance(regras, dict): regras = {}
                lista_produtos.append({
                    'id': item['id'], 'Nome': item['nome'], 'Categoria': item['categoria'],
                    'Preço (R$)': float(regras.get('preco_padrao', 0)),
                    'Sinal (R$)': float(regras.get('valor_sinal', 0)), 'raw_regras': regras
                })
            df_prod = pd.DataFrame(lista_produtos)
        else: df_prod = pd.DataFrame()

        col_table, col_actions = st.columns([2, 1])
        with col_table:
            if not df_prod.empty:
                st.dataframe(df_prod[['Nome', 'Categoria', 'Preço (R$)', 'Sinal (R$)']], use_container_width=True, hide_index=True)
            else: st.info("Nenhum produto cadastrado.")

        with col_actions:
            tab_new, tab_edit = st.tabs(["➕ Novo", "✏️ Editar"])
            with tab_new:
                with st.form("form_add_prod"):
                    n_new = st.text_input("Nome")
                    c_new = st.selectbox("Categoria", ["Serviço", "Produto", "Serviço Salão"], key="c_n")
                    cv1, cv2 = st.columns(2)
                    with cv1: p_new = st.number_input("Preço", min_value=0.0, step=10.0, key="pn")
                    with cv2: s_new = st.number_input("Sinal", min_value=0.0, step=10.0, key="sn")
                    if st.form_submit_button("Salvar", type="primary"):
                        if n_new:
                            js = {"preco_padrao": p_new, "valor_sinal": s_new, "duracao_minutos": 60}
                            supabase.table('produtos').insert({"cliente_id": c_id, "nome": n_new, "categoria": c_new, "ativo": True, "regras_preco": js}).execute()
                            st.success("Criado!"); time.sleep(1); st.rerun()

            with tab_edit:
                if not df_prod.empty:
                    map_ids = {row['Nome']: row['id'] for i, row in df_prod.iterrows()}
                    sel_name = st.selectbox("Editar:", list(map_ids.keys()))
                    sel_id = map_ids[sel_name]
                    item_atual = df_prod[df_prod['id'] == sel_id].iloc[0]
                    with st.form("form_edit_prod"):
                        n_ed = st.text_input("Nome", value=item_atual['Nome'])
                        try: idx_c = ["Serviço", "Produto", "Serviço Salão"].index(item_atual['Categoria'])
                        except: idx_c = 0
                        c_ed = st.selectbox("Categoria", ["Serviço", "Produto", "Serviço Salão"], index=idx_c)
                        ce1, ce2 = st.columns(2)
                        with ce1: p_ed = st.number_input("Preço", value=float(item_atual['Preço (R$)']), step=10.0)
                        with ce2: s_ed = st.number_input("Sinal", value=float(item_atual['Sinal (R$)']), step=10.0)
                        
                        cb1, cb2 = st.columns(2)
                        with cb1:
                            if st.form_submit_button("💾 Salvar"):
                                js = item_atual['raw_regras']
                                if not isinstance(js, dict): js = {}
                                js['preco_padrao'] = p_ed; js['valor_sinal'] = s_ed
                                supabase.table('produtos').update({"nome": n_ed, "categoria": c_ed, "regras_preco": js}).eq('id', sel_id).execute()
                                st.success("Ok!"); time.sleep(1); st.rerun()
                        with cb2:
                            del_chk = st.checkbox("Excluir?")
                            if st.form_submit_button("🗑️"):
                                if del_chk:
                                    supabase.table('produtos').delete().eq('id', sel_id).execute()
                                    st.success("Tchau!"); time.sleep(1); st.rerun()

    # --------------------------------------------------------------------------
    # TAB 3: AGENDA
    # --------------------------------------------------------------------------
    with tabs[2]:
        try:
            res_prod = supabase.table('produtos').select('id, nome').eq('cliente_id', c_id).execute()
            map_prod = {p['id']: p['nome'] for p in res_prod.data} if res_prod.data else {}
            map_prod_inv = {v: k for k, v in map_prod.items()}
        except: map_prod, map_prod_inv = {}, {}

        cl, cr = st.columns([2, 1])
        with cl:
            st.subheader("Agenda")
            lista_agenda, delete_map = [], {}
            try:
                rv = supabase.table('agendamentos').select('*').eq('cliente_id', c_id).order('created_at', desc=True).limit(15).execute()
                for i in (rv.data or []):
                    nm = map_prod.get(i.get('servico_id'), 'Serviço')
                    dt = pd.to_datetime(i.get('data_hora_inicio')).strftime('%d/%m %H:%M')
                    lista_agenda.append({'Data': dt, 'Cliente': i.get('cliente_final_waid'), 'Item': nm})
                    delete_map[f"[S] {dt} {nm}"] = {'id': i['id'], 't': 'agendamentos'}
            except: pass
            
            try:
                re = supabase.table('agendamentos_salao').select('*').eq('cliente_id', c_id).order('created_at', desc=True).limit(15).execute()
                for i in (re.data or []):
                    nm = map_prod.get(i.get('produto_salao_id'), 'Salão')
                    dt = i.get('data_reserva')
                    lista_agenda.append({'Data': dt, 'Cliente': i.get('cliente_final_waid'), 'Item': nm})
                    delete_map[f"[E] {dt} {nm}"] = {'id': i['id'], 't': 'agendamentos_salao'}
            except: pass

            if lista_agenda: st.dataframe(pd.DataFrame(lista_agenda), use_container_width=True, hide_index=True)
            else: st.info("Vazia.")
            
            if delete_map:
                s_del = st.selectbox("Apagar:", list(delete_map.keys()))
                if st.button("Confirmar Apagar"):
                    tabela = delete_map[s_del]['t']
                    supabase.table(tabela).delete().eq('id', delete_map[s_del]['id']).execute()
                    st.rerun()

        with cr:
            st.write("**Novo Agendamento**")
            with st.form("new_agd"):
                cli = st.text_input("Cliente")
                dt_d = st.date_input("Data")
                dt_h = st.time_input("Hora")
                item = st.selectbox("Item", list(map_prod_inv.keys())) if map_prod_inv else None
                val = st.number_input("Valor", 0.0)
                if st.form_submit_button("Agendar", type="primary"):
                    try:
                        dt_iso = datetime.combine(dt_d, dt_h).isoformat()
                        supabase.table('agendamentos').insert({
                            "cliente_id": c_id, "data_hora_inicio": dt_iso, 
                            "cliente_final_waid": cli, "servico_id": map_prod_inv.get(item), 
                            "valor_total_registrado": val, "status": "Confirmado"
                        }).execute()
                        st.success("Feito!"); time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

    # --------------------------------------------------------------------------
    # TAB 4: CÉREBRO (CORRIGIDO)
    # --------------------------------------------------------------------------
    with tabs[3]:
        st.subheader("Configuração da IA")
        try:
            res = supabase.table('clientes').select('config_fluxo, prompt_full').eq('id', c_id).execute()
            if res.data:
                d = res.data[0]
                
                # Leitura segura do JSON
                curr_c = d.get('config_fluxo')
                if isinstance(curr_c, str): 
                    try: curr_c = json.loads(curr_c)
                    except: curr_c = {}
                if not isinstance(curr_c, dict): curr_c = {}
                
                prompt_atual = d.get('prompt_full') or ""
                
                c_p1, c_p2 = st.columns([2, 1])
                
                # Coluna da Esquerda: Prompt
                with c_p1:
                    new_p = st.text_area("Instruções do Sistema", value=prompt_atual, height=550)
                
                # Coluna da Direita: Ajustes Finos
                with c_p2:
                    st.header("Configurações")
                    st.subheader("🔊 Personalidade e Voz")
                    
                    # Leitura segura dos valores para os widgets
                    val_audio = bool(curr_c.get('responde_em_audio', False))
                    val_temp = float(curr_c.get('temperature', 0.5))
                    val_voz = curr_c.get('openai_voice', 'alloy')

                    aud = st.toggle("Respostas em Áudio", value=val_audio)
                    
                    vozes = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
                    try: idx_voz = vozes.index(val_voz)
                    except: idx_voz = 0
                    voz = st.selectbox("Voz do Assistente", vozes, index=idx_voz)
                    
                    temp = st.slider("Tom de Voz", 0.0, 1.0, val_temp)
                    if temp < 0.5: st.info("🤖 Modo Robótico")
                    else: st.success("✨ Modo Humano")

                    st.divider()
                    st.subheader("🕒 Horário")
                    
                    lista_h = [f"{i:02d}:00" for i in range(24)]
                    try: idx_h_i = lista_h.index(curr_c.get('horario_inicio', '09:00'))
                    except: idx_h_i = 9
                    try: idx_h_f = lista_h.index(curr_c.get('horario_fim', '18:00'))
                    except: idx_h_f = 18

                    h_ini = st.selectbox("Início", lista_h, index=idx_h_i)
                    h_fim = st.selectbox("Fim", lista_h, index=idx_h_f)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.button("💾 SALVAR TUDO", type="primary", use_container_width=True):
                        # Atualiza o dicionário local curr_c com os novos valores
                        curr_c['responde_em_audio'] = aud
                        curr_c['openai_voice'] = voz
                        curr_c['temperature'] = temp
                        curr_c['horario_inicio'] = h_ini
                        curr_c['horario_fim'] = h_fim
                        
                        # Salva no banco
                        supabase.table('clientes').update({
                            'prompt_full': new_p, 
                            'config_fluxo': curr_c
                        }).eq('id', c_id).execute()
                        
                        st.success("Configurações Salvas!")
                        time.sleep(1)
                        st.rerun()

        except Exception as e: st.error(f"Erro Cérebro: {e}")
