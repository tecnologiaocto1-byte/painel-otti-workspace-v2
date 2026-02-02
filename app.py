import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import json
import time
import os
import base64
import requests
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

    /* --- BOTÕES DA SIDEBAR --- */
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
    
    /* Botão "Novo Cliente" - Azul Neon */
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

# --- CARREGA DADOS DO BANCO ---
if not supabase: st.stop()
try: 
    df_kpis = pd.DataFrame(supabase.table('view_dashboard_kpis').select("*").execute().data)
except: 
    df_kpis = pd.DataFrame()

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
                
                c_data = df_kpis[df_kpis['nome_empresa'] == sel].iloc[0]
            else:
                st.warning("Sem dados de KPI.")
                c_data = None
            
            st.markdown("---")
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

# --- TELA 1: CADASTRO DE CLIENTE (COMPLETO) ---
if perfil == 'admin' and st.session_state['modo_view'] == 'cadastro':
    st.title("🏢 Cadastro de Novo Cliente")
    st.markdown("Configure a infraestrutura completa do novo inquilino.")
    
    with st.container(border=True):
        with st.form("form_novo_cliente_full"):
            
            # --- 1. DADOS CADASTRAIS ---
            st.markdown("### 1. 🏢 Dados da Empresa e Acesso")
            c1, c2 = st.columns(2)
            with c1:
                empresa_nome = st.text_input("Nome da Empresa")
                whats_id = st.text_input("WhatsApp ID (Ex: 551199999999)")
                plano_sel = st.selectbox("Plano", ["full", "basic", "trial"], index=0)
            with c2:
                email_login = st.text_input("E-mail de Login")
                senha_login = st.text_input("Senha Inicial", type="password")
                humano_ativo = st.toggle("Atendimento Humano Ativo?", value=True)

            st.divider()

            # --- 2. FINANCEIRO (PIX E ADQUIRENTES) ---
            st.markdown("### 2. 💰 Financeiro & Pagamentos")
            cf1, cf2, cf3 = st.columns(3)
            with cf1:
                sinal_val = st.number_input("Sinal Mínimo (R$)", value=100.0, step=10.0)
                checkout_auto = st.toggle("Checkout Automático?", value=False)
            with cf2:
                pix_key = st.text_input("Chave PIX")
                gateway_sel = st.selectbox("Adquirente (Cartão)", ["Nenhum", "Mercado Pago", "InfinitePay", "Getnet"])
            with cf3:
                # Campo genérico para token, dependendo do gateway escolhido
                gateway_token = st.text_input("Token/API Key do Adquirente", type="password", help="Cole a credencial de produção aqui")

            st.divider()

            # --- 3. INTELIGÊNCIA E COMPORTAMENTO ---
            with st.expander("🧠 Configurações do Cérebro (IA)", expanded=False):
                ci1, ci2 = st.columns(2)
                with ci1:
                    voz_ia = st.selectbox("Voz da OpenAI", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"], index=0)
                    temp_ia = st.slider("Criatividade (Temperatura)", 0.0, 1.0, 0.8)
                with ci2:
                    aceita_audio = st.toggle("Entende Áudio do Cliente?", value=True)
                    responde_audio = st.toggle("Responde em Áudio?", value=False)
                
                st.markdown("**Instruções de Visão (Análise de Foto):**")
                visao_txt = st.text_area("Prompt para fotos", value="FOTO DE REFERÊNCIA/INSPIRAÇÃO: Analise a decoração da foto (cores, tema, balões) e diga se conseguimos fazer algo parecido baseando-se no nosso catálogo.", height=80)
                
                btn_txt = st.text_input("Texto do Botão de Pedido", value="📝 Fazer Pedido")

            # --- 4. FOLLOW-UP AUTOMÁTICO (COBRANÇA) ---
            with st.expander("⏰ Follow-up Automático (Recuperação)", expanded=False):
                f_ativo = st.checkbox("Ativar Follow-up Automático?", value=True)
                cf_h1, cf_h2 = st.columns(2)
                with cf_h1:
                    fu_ini = st.time_input("Início dos Disparos", value=dt_time(9,0))
                with cf_h2:
                    fu_fim = st.time_input("Fim dos Disparos", value=dt_time(21,0))
                
                st.caption("As etapas padrão (30min, 60min, 24h) serão carregadas automaticamente. Edite no JSON se precisar mudar a lógica.")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- SUBMIT ---
            if st.form_submit_button("✅ CADASTRAR", type="primary", use_container_width=True):
                if not empresa_nome or not email_login or not senha_login:
                    st.warning("Preencha Nome, Login e Senha pelo menos.")
                else:
                    try:
                        with st.spinner("Subindo configuração completa..."):
                            
                            # 1. MONTAGEM DO JSON DE FOLLOW-UP (Padrão Rico)
                            followup_structure = {
                                "ativo": f_ativo,
                                "horario_inicio": fu_ini.strftime("%H:%M"),
                                "horario_fim": fu_fim.strftime("%H:%M"),
                                "ignorar_horario_silencio": False,
                                "system_prompt_template": "Você é o assistente de cobrança da {nome_empresa}. O cliente parou de responder.\nSua última msg foi: '{ultima_msg_bot}'.\n\nAgora, siga estritamente esta ordem: '{instrucao}'.\n\nREGRAS:\n- MÁXIMO 15 PALAVRAS.\n- NÃO mande links.\n- Se o cliente já fechou/desistiu, responda: CANCELAR_FLUXO",
                                "etapas": [
                                    {"nivel": 1, "minutos_apos_ultimo_input": 30, "instrucao_ia": "Seja gentil. O cliente parou de responder. Pergunte se ficou alguma dúvida."},
                                    {"nivel": 2, "minutos_apos_ultimo_input": 60, "instrucao_ia": "Gere leve urgência. A data solicitada é muito procurada."},
                                    {"nivel": 3, "minutos_apos_ultimo_input": 1440, "acao_sistema": "cancelar", "instrucao_ia": "Despedida profissional. Avise que o sistema liberou a data."}
                                ]
                            }

                            # 2. MONTAGEM DO JSON CONFIG_FLUXO (O Cérebro Completo)
                            config_completa = {
                                "plano": plano_sel,
                                # Horários Gerais (Padrão Loja)
                                "horario_inicio": "09:00", 
                                "horario_fim": "18:00",
                                
                                # Financeiro
                                "sinal_minimo_reais": sinal_val,
                                "chave_pix": pix_key,
                                "checkout_automatico": checkout_auto,
                                "adquirente_ativo": gateway_sel,
                                "adquirente_token": gateway_token, # Cuidado com segurança em prod
                                
                                # IA & Voz
                                "temperature": temp_ia,
                                "openai_voice": voz_ia,
                                "aceita_audio": aceita_audio,
                                "responde_em_audio": responde_audio,
                                "atendimento_humano_ativo": humano_ativo,
                                "instrucoes_visao_especificas": visao_txt,
                                "btn_texto_pedido_kit": btn_txt,
                                
                                # Módulo Follow-up
                                "followup_automatico": followup_structure
                            }

                            # 3. INSERT NO BANCO
                            res = supabase.table('clientes').insert({
                                "nome_empresa": empresa_nome,
                                "whatsapp_id": whats_id,
                                "ativo": True,
                                "bot_pausado": False,
                                "config_fluxo": config_completa # Payload Gigante aqui
                            }).execute()
                            
                            if res.data:
                                new_id = res.data[0]['id']
                                # Cria Login
                                supabase.table('acesso_painel').insert({
                                    "cliente_id": new_id,
                                    "email": email_login,
                                    "senha": senha_login,
                                    "nome_usuario": f"Admin {empresa_nome}",
                                    "perfil": "user"
                                }).execute()
                                
                                st.toast(f"Cliente {empresa_nome} cadastrado com sucesso!", icon="🚀")
                                time.sleep(2)
                                st.session_state['modo_view'] = 'dashboard'
                                st.rerun()
                            else:
                                st.error("Erro ao obter ID do novo cliente.")
                                
                    except Exception as e:
                        st.error(f"Erro técnico no upload: {e}")

# --- TELA 2: DASHBOARD ---
else:
    if c_data is None:
        st.info("Nenhum cliente selecionado ou base de dados vazia.")
        st.stop()

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

    # --- KPIS ---
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

    # --- ABAS ---
    tabs = st.tabs(["💰 Funil", "💬 Inbox", "📊 Analytics", "📦 Produtos", "📅 Agenda", "🧠 Cérebro"])

    # --------------------------------------------------------------------------
    # TAB 0: FUNIL DE VENDAS (KANBAN DETALHADO + LINK ZAP)
    # --------------------------------------------------------------------------
    with tabs[0]:
        st.subheader("Funil de Vendas")
        
        # 1. PREPARAÇÃO: Mapear Nomes dos Produtos
        try:
            res_prod = supabase.table('produtos').select('id, nome').eq('cliente_id', c_id).execute()
            map_produtos = {p['id']: p['nome'] for p in res_prod.data} if res_prod.data else {}
        except: map_produtos = {}

        # 2. BUSCA DADOS
        leads_list = []
        try:
            # A. Serviços
            rv = supabase.table('agendamentos').select('id, cliente_final_waid, status, valor_total_registrado, servico_id, data_hora_inicio').eq('cliente_id', c_id).execute()
            for i in (rv.data or []):
                # TRUQUE: Se o nome do produto falhar, mostramos o ID pra você saber o que é
                p_nome = map_produtos.get(i.get('servico_id'), f"Serviço ID {i.get('servico_id')}")
                # TRUQUE 2: Garante que o telefone apareça
                telefone = i.get('cliente_final_waid')
                if not telefone: telefone = "Sem Número"
                
                leads_list.append({
                    'id': i['id'], 'tipo': 'servico', 
                    'cliente': telefone, # Agora força mostrar o telefone
                    'produto': p_nome,
                    'status': i.get('status', 'Pendente'), 
                    'valor': float(i.get('valor_total_registrado', 0) or 0),
                    'data': pd.to_datetime(i.get('data_hora_inicio')).strftime('%d/%m %H:%M')
                })

            # B. Eventos (Salão)
            re = supabase.table('agendamentos_salao').select('id, cliente_final_waid, status, valor_total_registrado, produto_salao_id, data_reserva').eq('cliente_id', c_id).execute()
            for i in (re.data or []):
                p_nome = map_produtos.get(i.get('produto_salao_id'), f"Salão ID {i.get('produto_salao_id')}")
                telefone = i.get('cliente_final_waid')
                if not telefone: telefone = "Sem Número"

                leads_list.append({
                    'id': i['id'], 'tipo': 'salao', 
                    'cliente': telefone,
                    'produto': p_nome,
                    'status': i.get('status', 'Pendente'), 
                    'valor': float(i.get('valor_total_registrado', 0) or 0),
                    'data': i.get('data_reserva')
                })
        except Exception as e: st.error(f"Erro funil: {e}")

        # 3. RENDERIZAÇÃO
        if leads_list:
            cols = st.columns(3)
            # Mapeamento exato dos status do seu banco para as colunas
            status_map = {
                "🟡 Pendentes (A cobrar)": ["Pendente", "Novo", "Aguardando", None, ""],
                "🟢 Confirmados (Pagos)": ["Confirmado", "Pago", "Agendado"],
                "🔴 Cancelados": ["Cancelado", "Desistiu"]
            }
            colors = ["#FFD700", "#00C851", "#FF4444"] 
            
            for idx, (col_name, status_keys) in enumerate(status_map.items()):
                with cols[idx]:
                    st.markdown(f"<div style='border-top: 4px solid {colors[idx]}; background: #F8F9FA; padding: 5px; border-radius: 5px; text-align:center;'><b>{col_name}</b></div>", unsafe_allow_html=True)
                    st.write("") # Espaçamento
                    
                    cards = [l for l in leads_list if l['status'] in status_keys]
                    
                    for card in cards:
                        with st.container(border=True):
                            # Título do Produto
                            st.markdown(f"**📦 {card['produto']}**")
                            
                            # Telefone com Link para WhatsApp
                            fone_limpo = str(card['cliente']).replace("+", "").replace(" ", "").replace("-", "")
                            link_wa = f"https://wa.me/{fone_limpo}"
                            st.markdown(f"👤 [{card['cliente']}]({link_wa})")
                            
                            # Data e Valor
                            c_info1, c_info2 = st.columns(2)
                            with c_info1: st.caption(f"📅 {card['data']}")
                            with c_info2: 
                                if card['valor'] > 0: st.markdown(f"**R$ {card['valor']:.2f}**")
                                else: st.caption("R$ --")

                            # Botões Lógicos (Só aparecem se não estiver cancelado)
                            if "Cancelado" not in col_name:
                                st.divider()
                                b1, b2 = st.columns(2)
                                with b1:
                                    # Botão Aprovar vira dinheiro
                                    if "Confirmado" not in col_name:
                                        if st.button("💰 Pagar", key=f"pay_{card['id']}_{card['tipo']}", use_container_width=True, help="Muda status para Confirmado"):
                                            table = 'agendamentos' if card['tipo'] == 'servico' else 'agendamentos_salao'
                                            supabase.table(table).update({'status': 'Confirmado'}).eq('id', card['id']).execute()
                                            st.toast("Confirmado! $$", icon="🤑")
                                            time.sleep(1); st.rerun()
                                    else:
                                        st.success("Pago ✅")
                                with b2:
                                    if st.button("❌", key=f"del_{card['id']}_{card['tipo']}", use_container_width=True, help="Cancelar pedido"):
                                        table = 'agendamentos' if card['tipo'] == 'servico' else 'agendamentos_salao'
                                        supabase.table(table).update({'status': 'Cancelado'}).eq('id', card['id']).execute()
                                        st.toast("Cancelado", icon="🗑️")
                                        time.sleep(1); st.rerun()
        else:
            st.info("Funil vazio. Aguardando novos leads do Otti.")

   # --------------------------------------------------------------------------
    # TAB 1: INBOX + CRM 360º (COM FICHA CAPIVARA E TAGS)
    # --------------------------------------------------------------------------
    with tabs[1]:
        # Layout expandido para caber as 3 colunas
        st.subheader("💬 Atendimento & CRM")
        
        # 1. INICIALIZAÇÃO SEGURA
        z_instancia, z_token, z_client_token = "", "", ""

        # 2. BUSCA CREDENCIAIS E NOTIFICAÇÕES
        try:
            dados_zapi = supabase.table('clientes').select('id_instance, zapi_token, client_token').eq('id', c_id).execute().data
            if dados_zapi:
                z_instancia = dados_zapi[0].get('id_instance', '')
                z_token = dados_zapi[0].get('zapi_token', '')
                z_client_token = dados_zapi[0].get('client_token', '')

            # Notificações Pendentes
            res_notif = supabase.table('notificacoes').select('*').eq('cliente_id', c_id).eq('lida', False).order('created_at', desc=True).execute()
            notificacoes_pendentes = res_notif.data if res_notif.data else []
        except: notificacoes_pendentes = []

        # --- ALERTA VISUAL (NOTIFICAÇÕES) ---
        if notificacoes_pendentes:
            st.error(f"🔔 {len(notificacoes_pendentes)} cliente(s) pedindo ajuda! Verifique a lista abaixo.")

        st.divider()

        # --- LAYOUT DE 3 COLUNAS (LISTA | CHAT | CRM) ---
        # A proporção [1, 2, 1.5] dá bastante espaço pro chat e pra ficha
        c_list, c_chat, c_crm = st.columns([1, 2, 1.5])
        
        # ======================================================================
        # COLUNA 1: LISTA DE CONVERSAS
        # ======================================================================
        with c_list:
            st.markdown("##### 📥 Conversas")
            try:
                # Une clientes do Funil + Notificações
                l_funil = list(set([l['cliente'] for l in leads_list])) if 'leads_list' in locals() and leads_list else []
                l_notif = list(set([n['origem_wa_id'] for n in notificacoes_pendentes if n.get('origem_wa_id')]))
                lista_final = sorted(list(set(l_notif + l_funil)), key=lambda x: x in l_notif, reverse=True) # Prioriza notificações
                
                if lista_final:
                    # Formata visualmente se tiver notificação
                    opcoes_visuais = [f"🔴 {cli}" if cli in l_notif else cli for cli in lista_final]
                    sel_idx = st.radio("Clientes", opcoes_visuais, label_visibility="collapsed")
                    
                    # Limpa o emoji pra pegar o ID real
                    cliente_ativo = sel_idx.replace("🔴 ", "")
                else:
                    cliente_ativo = None
                    st.caption("Nada aqui.")
            except: cliente_ativo = None

        # ======================================================================
        # COLUNA 2: CHAT (MENSAGENS)
        # ======================================================================
        with c_chat:
            with st.container(border=True):
                if cliente_ativo:
                    # Header do Chat
                    bh1, bh2 = st.columns([2,1])
                    with bh1: st.markdown(f"**Chat: {cliente_ativo}**")
                    with bh2:
                        bot_on = st.toggle("🤖 Bot", value=True, key=f"bt_{cliente_ativo}")
                    
                    st.divider()
                    
                    # Limpar notificação se houver
                    if cliente_ativo in l_notif:
                         if st.button("✅ Marcar como Atendido", key=f"cls_{cliente_ativo}", use_container_width=True):
                             supabase.table('notificacoes').update({'lida': True}).eq('origem_wa_id', cliente_ativo).execute()
                             st.rerun()

                    # Área de Mensagens (Visual)
                    chat_box = st.container(height=400)
                    with chat_box:
                        with st.chat_message("user"): st.write("Olá!")
                        with st.chat_message("assistant"): st.write("Opa, tudo bem?")
                        if not bot_on: st.warning("Modo manual ativo.")

                    # Input
                    msg = st.chat_input(f"Falar com {cliente_ativo}...")
                    if msg:
                        with chat_box: 
                            with st.chat_message("assistant"): st.write(msg)
                        
                        # Envio Z-API
                        if z_instancia and z_token:
                            try:
                                u = f"https://api.z-api.io/instances/{z_instancia}/token/{z_token}/send-text"
                                h = {"Client-Token": z_client_token} if z_client_token else {}
                                requests.post(u, json={"phone": cliente_ativo, "message": msg}, headers=h)
                                st.toast("Enviado!", icon="🚀")
                                if not bot_on:
                                    supabase.table('clientes').update({'bot_pausado': True}).eq('id', c_id).execute()
                            except: st.error("Erro envio Z-API")
                else:
                    st.info("Selecione um cliente.")

        # ======================================================================
        # COLUNA 3: FICHA CRM (CAPIVARA)
        # ======================================================================
        with c_crm:
            if cliente_ativo:
                st.markdown(f"### 📋 Ficha do Cliente")
                
                # 1. CÁLCULO DE LTV (LIFETIME VALUE)
                # Filtra os leads desse cliente específico na lista geral carregada
                historico_compras = [l for l in leads_list if l['cliente'] == cliente_ativo]
                
                total_gasto = sum([x['valor'] for x in historico_compras if x['status'] in ['Confirmado', 'Pago', 'Agendado']])
                qtd_compras = len([x for x in historico_compras if x['status'] in ['Confirmado', 'Pago', 'Agendado']])
                ticket_medio = total_gasto / qtd_compras if qtd_compras > 0 else 0
                
                # Métricas Visuais
                m1, m2, m3 = st.columns(3)
                m1.metric("LTV (Total)", f"R${total_gasto:,.0f}")
                m2.metric("Compras", qtd_compras)
                m3.metric("Ticket Médio", f"R${ticket_medio:,.0f}")
                
                st.divider()
                
                # 2. CARREGAR/CRIAR PERFIL CRM (TAGS E NOTAS)
                try:
                    res_crm = supabase.table('crm_clientes_finais').select('*').eq('cliente_id', c_id).eq('wa_id', cliente_ativo).execute()
                    if res_crm.data:
                        perfil_crm = res_crm.data[0]
                        crm_id = perfil_crm['id']
                    else:
                        perfil_crm = {}
                        crm_id = None
                except: perfil_crm = {}; crm_id = None
                
                # Formulário do CRM
                with st.form(key=f"crm_form_{cliente_ativo}"):
                    st.markdown("##### 🏷️ Segmentação")
                    
                    tags_atuais = perfil_crm.get('tags') or []
                    # Opções de Tags Sugeridas
                    opcoes_tags = ["VIP", "Novo", "Recorrente", "Indicação", "Problemático", "Festa Infantil", "Casamento"]
                    # Garante que as tags atuais estejam na lista pra não dar erro
                    for t in tags_atuais:
                        if t not in opcoes_tags: opcoes_tags.append(t)
                        
                    novas_tags = st.multiselect("Etiquetas", opcoes_tags, default=tags_atuais)
                    
                    st.markdown("##### 📝 Notas Internas")
                    notas_atuais = perfil_crm.get('notas', '')
                    novas_notas = st.text_area("Obs. (Não visível pro cliente)", value=notas_atuais, height=150, placeholder="Ex: Cliente prefere contato após as 18h. Alérgica a amendoim.")
                    
                    if st.form_submit_button("💾 Salvar Ficha", type="primary", use_container_width=True):
                        dados_save = {
                            "cliente_id": c_id,
                            "wa_id": cliente_ativo,
                            "tags": novas_tags,
                            "notas": novas_notas
                        }
                        
                        if crm_id:
                            # Update
                            supabase.table('crm_clientes_finais').update(dados_save).eq('id', crm_id).execute()
                        else:
                            # Insert
                            supabase.table('crm_clientes_finais').insert(dados_save).execute()
                        
                        st.success("Ficha atualizada!")
                        time.sleep(1)
                        st.rerun()

                # 3. HISTÓRICO VISUAL
                with st.expander("📜 Histórico de Pedidos", expanded=True):
                    if historico_compras:
                        for compra in historico_compras:
                            icon_st = "✅" if compra['status'] in ['Confirmado', 'Pago'] else "🟡"
                            st.caption(f"{icon_st} **{compra['data']}** - {compra['produto']}")
                            st.caption(f"Valor: R$ {compra['valor']:.2f}")
                            st.markdown("---")
                    else:
                        st.info("Nenhum histórico encontrado.")

            else:
                st.markdown("### 📋 CRM")
                st.info("Selecione uma conversa para ver a ficha do cliente.")

    # --------------------------------------------------------------------------
    # TAB 2: ANALYTICS (GRÁFICOS RESTAURADOS)
    # --------------------------------------------------------------------------
    with tabs[2]:
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

                # LINHA 1 DE GRÁFICOS
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

                st.divider()

                # LINHA 2 DE GRÁFICOS (Adicionada de volta!)
                st.markdown("#### 🚀 Tendências")
                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    st.markdown("##### Faturamento Semanal")
                    try:
                        df_trend = df_filt.copy()
                        df_trend['semana'] = pd.to_datetime(df_trend['dt']).dt.strftime('%Y-W%U')
                        df_w = df_trend.groupby('semana')['v'].sum().reset_index()
                        fig3 = px.bar(df_w, x='semana', y='v')
                        fig3.update_traces(marker_color=C_SIDEBAR_NAVY)
                        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_DARK}, xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title=None), margin=dict(l=0, r=0, t=20, b=20))
                        st.plotly_chart(fig3, use_container_width=True)
                    except: st.info("Dados insuficientes.")
                
                with c_t2:
                    st.markdown("##### Evolução de Produtos")
                    try:
                        df_area = df_filt.groupby(['dt', 'p'])['v'].sum().reset_index()
                        fig4 = px.area(df_area, x='dt', y='v', color='p')
                        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_DARK}, xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=True, gridcolor='#E2E8F0', showticklabels=False, title=None), margin=dict(l=0, r=0, t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig4, use_container_width=True)
                    except: st.info("Dados insuficientes.")

            else: st.info("Sem dados para exibir.")
        except Exception as e: st.error(f"Erro Visual: {e}")

    # --------------------------------------------------------------------------
    # TAB 3: PRODUTOS
    # --------------------------------------------------------------------------
    with tabs[3]:
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
    # TAB 4: AGENDA
    # --------------------------------------------------------------------------
    with tabs[4]:
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
    # TAB 5: CÉREBRO (IA - Harmonizado e com Nomes das Vozes)
    # --------------------------------------------------------------------------
    with tabs[5]:
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
                    st.markdown("##### Personalidade & Regras")
                    new_p = st.text_area("Instruções do Sistema", value=prompt_atual, height=550, label_visibility="collapsed")
                
                # Coluna da Direita: Ajustes Finos (Harmonizado)
                with c_p2:
                    st.markdown("### Configurações")
                    st.markdown("##### 🔊 Personalidade")
                    
                    val_audio = bool(curr_c.get('responde_em_audio', False))
                    val_temp = float(curr_c.get('temperature', 0.5))
                    val_voz = curr_c.get('openai_voice', 'alloy')

                    aud = st.toggle("Respostas em Áudio", value=val_audio)
                    
                    # Mapa de Vozes (Nome Amigável -> Código)
                    mapa_vozes = {
                        "alloy": "Alloy (Neutro)",
                        "echo": "Echo (Suave)",
                        "fable": "Fable (Narrador)",
                        "onyx": "Onyx (Profundo)",
                        "nova": "Nova (Energético)",
                        "shimmer": "Shimmer (Calmo)"
                    }
                    
                    # Se a voz atual não estiver no mapa (ex: erro antigo), usa alloy
                    if val_voz not in mapa_vozes: val_voz = "alloy"
                    
                    # Selectbox mostra os valores (descrições), mas precisamos recuperar a chave
                    voz_desc = st.selectbox(
                        "Voz do Assistente", 
                        list(mapa_vozes.values()), 
                        index=list(mapa_vozes.keys()).index(val_voz)
                    )
                    # Recupera a chave (código) baseada na descrição selecionada
                    voz_final = [k for k, v in mapa_vozes.items() if v == voz_desc][0]
                    
                    st.write("")
                    temp = st.slider("Tom de Voz", 0.0, 1.0, val_temp, 0.1)
                    if temp < 0.5: st.info("🤖 Modo Robótico")
                    else: st.success("✨ Modo Humano")

                    st.divider()
                    st.markdown("##### 🕒 Horário")
                    
                    lista_h = [f"{i:02d}:00" for i in range(24)]
                    try: idx_h_i = lista_h.index(curr_c.get('horario_inicio', '09:00'))
                    except: idx_h_i = 9
                    try: idx_h_f = lista_h.index(curr_c.get('horario_fim', '18:00'))
                    except: idx_h_f = 18

                    c_h1, c_h2 = st.columns(2)
                    with c_h1: h_ini = st.selectbox("Início", lista_h, index=idx_h_i)
                    with c_h2: h_fim = st.selectbox("Fim", lista_h, index=idx_h_f)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.button("💾 SALVAR TUDO", type="primary", use_container_width=True):
                        # Atualiza o dicionário local curr_c com os novos valores
                        curr_c['responde_em_audio'] = aud
                        curr_c['openai_voice'] = voz_final # Salva o código (ex: alloy)
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











