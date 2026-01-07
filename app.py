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

# forcei o initial_sidebar_state="expanded" para tentar manter aberto
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
# 3. CSS (CORRIGIDO E SEGURO)
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

    /* --- CORREÇÃO DAS ABAS (TABS) --- */
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

    /* --- BOTÕES (AGORA CLAROS) --- */
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

    /* --- BOTÃO SIDEBAR --- */
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
    section[data-testid="stSidebar"] button[kind="secondary"] p {{ color: inherit !important; }}

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
# 5. DASHBOARD
# ==============================================================================

user = st.session_state['usuario_logado']
perfil = user.get('perfil', 'user')

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

if not supabase: st.stop()

try: df_kpis = pd.DataFrame(supabase.table('view_dashboard_kpis').select("*").execute().data)
except: df_kpis = pd.DataFrame()

if perfil == 'admin':
    if not df_kpis.empty:
        lista = df_kpis['nome_empresa'].unique()
        if 'last_cli' not in st.session_state: st.session_state['last_cli'] = lista[0]
        if st.session_state['last_cli'] not in lista: st.session_state['last_cli'] = lista[0]
        idx = list(lista).index(st.session_state['last_cli'])
        sel = st.sidebar.selectbox("Cliente:", lista, index=idx, key="cli_selector")
        st.session_state['last_cli'] = sel
        c_data = df_kpis[df_kpis['nome_empresa'] == sel].iloc[0]
    else:
        st.warning("Sem dados de KPI.")
        st.stop()
else:
    filtro = df_kpis[df_kpis['cliente_id'] == user['cliente_id']]
    if filtro.empty: 
        st.error("Cliente não encontrado.")
        st.stop()
    c_data = filtro.iloc[0]

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

# --- CÁLCULO DE KPIS (ATUALIZADO) ---
# Salário Mínimo base 2024/2025 (~R$ 1.518,00)
# Custo Hora = 1518 / (22 dias * 8 horas) = ~8.625
SALARIO_MINIMO = 1518.00
HORAS_MENSAIS = 22 * 8
CUSTO_HORA = SALARIO_MINIMO / HORAS_MENSAIS

tot_msgs = c_data.get('total_mensagens', 0)
horas_economizadas = round((tot_msgs * 1.5) / 60, 1) # 1.5 min por mensagem
valor_economia = horas_economizadas * CUSTO_HORA

receita_direta = float(c_data.get('receita_total', 0) or 0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita Direta", f"R$ {receita_direta:,.2f}")
k2.metric("Economia Estimada", f"R$ {valor_economia:,.2f}", help=f"Baseado em {horas_economizadas}h salvas (Custo hora: R$ {CUSTO_HORA:.2f})")
k3.metric("Atendimentos", c_data.get('total_atendimentos', 0))
k4.metric("Status Atual", "Online 🟢" if active else "Offline 🔴")
st.markdown("<br>", unsafe_allow_html=True)

tabs = st.tabs(["📊 Analytics", "📦 Produtos", "📅 Agenda", "🧠 Cérebro"])

# ------------------------------------------------------------------------------
# TAB 1: ANALYTICS (COM GRÁFICO DE VOLUME)
# ------------------------------------------------------------------------------
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

            # --- LINHA 1 DE GRÁFICOS (RECEITA E VOLUME) ---
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
                st.markdown("##### 📊 Volume de Atendimentos")
                # Contagem de linhas por data
                df_vol = df_filt.groupby('dt').size().reset_index(name='qtd')
                if not df_vol.empty:
                    fig_vol = px.bar(df_vol, x='dt', y='qtd', text='qtd')
                    fig_vol.update_traces(marker_color=C_SIDEBAR_NAVY, textposition='outside')
                    fig_vol.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_DARK}, xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=False, showticklabels=False, title=None), margin=dict(l=0, r=0, t=20, b=20))
                    st.plotly_chart(fig_vol, use_container_width=True)
                else: st.info("Sem dados.")

            st.divider()
            
            st.markdown("#### 🚀 Tendências")
            c_t1, c_t2 = st.columns(2)
            with c_t1:
                st.markdown("##### Tendência de Faturamento (Semanal)")
                try:
                    df_trend = df_filt.copy()
                    df_trend['semana'] = pd.to_datetime(df_trend['dt']).dt.strftime('%Y-Semana %U')
                    df_w = df_trend.groupby('semana')['v'].sum().reset_index()
                    fig3 = px.bar(df_w, x='semana', y='v')
                    fig3.update_traces(marker_color=C_SIDEBAR_NAVY, marker_line_width=0)
                    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_DARK}, xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title=None), margin=dict(l=0, r=0, t=20, b=20))
                    st.plotly_chart(fig3, use_container_width=True)
                except: st.info("Dados insuficientes.")
            with c_t2:
                st.markdown("##### Tendência de Produtos (Evolução)")
                try:
                    df_area = df_filt.groupby(['dt', 'p'])['v'].sum().reset_index()
                    fig4 = px.area(df_area, x='dt', y='v', color='p')
                    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_DARK}, xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=True, gridcolor='#E2E8F0', showticklabels=False, title=None), margin=dict(l=0, r=0, t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig4, use_container_width=True)
                except: st.info("Sem dados.")
        else: st.info("Sem dados.")
    except Exception as e: st.error(f"Erro Visual: {e}")

# ------------------------------------------------------------------------------
# TAB 2: PRODUTOS
# ------------------------------------------------------------------------------
with tabs[1]:
    rp = supabase.table('produtos').select('id, nome, categoria, regras_preco').eq('cliente_id', c_id).order('nome').execute()
    if rp.data:
        df_prod = pd.DataFrame(rp.data)
        def extrair_preco(x):
            try:
                if isinstance(x, dict): return x.get('preco_padrao', 0)
                if isinstance(x, str): return json.loads(x).get('preco_padrao', 0)
                return 0
            except: return 0
        df_prod['Preço (R$)'] = df_prod['regras_preco'].apply(extrair_preco)
    else: df_prod = pd.DataFrame()

    c1, c2 = st.columns([2,1])
    with c1:
        if not df_prod.empty:
            df_display = df_prod[['nome', 'categoria', 'Preço (R$)']]
            df_display.columns = ['Nome', 'Categoria', 'Preço (R$)']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else: st.info("Nenhum produto.")

    with c2:
        with st.form("add"):
            st.markdown("#### 🆕 Novo Item")
            n = st.text_input("Nome")
            c = st.selectbox("Categoria", ["Serviço", "Produto", "Serviço Salão"])
            p = st.number_input("Preço", min_value=0.0, step=10.0)
            if st.form_submit_button("Salvar", type="primary"):
                js = {"preco_padrao": p, "duracao_minutos": 60}
                try:
                    supabase.table('produtos').insert({"cliente_id": c_id, "nome": n, "categoria": c, "ativo": True, "regras_preco": js}).execute()
                    st.success("Salvo!"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")
        
        st.divider()
        if not df_prod.empty:
            map_del = {row['nome']: row['id'] for i, row in df_prod.iterrows()}
            sel_del = st.selectbox("🗑️ Excluir Item", list(map_del.keys()))
            if st.button("Confirmar Exclusão"):
                supabase.table('produtos').delete().eq('id', map_del[sel_del]).execute()
                st.success("Removido!"); time.sleep(1); st.rerun()

# ------------------------------------------------------------------------------
# TAB 3: AGENDA
# ------------------------------------------------------------------------------
with tabs[2]:
    try:
        res_prod = supabase.table('produtos').select('id, nome, categoria').eq('cliente_id', c_id).execute()
        map_prod = {}
        cats_disponiveis = set()
        if res_prod.data:
            for p in res_prod.data:
                map_prod[p['id']] = p['nome']
                if p.get('categoria'): 
                    cats_disponiveis.add(p['categoria'])
        
        map_prod_inv = {v: k for k, v in map_prod.items()}
        map_prof = {}
        try:
            res_prof = supabase.table('profissionais').select('id, nome').eq('cliente_id', c_id).execute()
            if res_prof.data: map_prof = {p['id']: p['nome'] for p in res_prof.data}
        except: pass
        map_prof_inv = {v: k for k, v in map_prof.items()}
    except: map_prod, cats_disponiveis = {}, set()

    ca_left, ca_right = st.columns([2, 1])
    with ca_left:
        st.subheader("📅 Próximos Agendamentos")
        lista_agenda, delete_map = [], {}
        try:
            rs = supabase.table('agendamentos_salao').select('*').eq('cliente_id', c_id).order('created_at', desc=True).limit(20).execute()
            for i in (rs.data or []):
                nm = map_prod.get(i.get('produto_salao_id'), 'Evento')
                dt = i['data_reserva']
                cli = i.get('cliente_final_waid') or 'Cliente'
                lb = f"[EVT] {dt} - {cli}"
                delete_map[lb] = {'id': i['id'], 't': 'salao'}
                lista_agenda.append({'Data': i['data_reserva'], 'Cliente': i.get('cliente_final_waid'), 'Item': nm, 'Profissional': '-', 'Tipo': 'Evento'})
        except: pass
        
        try:
            rv = supabase.table('agendamentos').select('*').eq('cliente_id', c_id).order('created_at', desc=True).limit(20).execute()
            for i in (rv.data or []):
                nm = map_prod.get(i.get('servico_id'), 'Serviço')
                dt = i.get('data_hora_inicio')
                nome_prof = map_prof.get(i.get('profissional_id'), '-')
                try: dt = pd.to_datetime(dt).strftime('%d/%m %H:%M')
                except: pass
                cli = i.get('cliente_final_waid') or i.get('cliente_final_nome') or 'Cliente'
                lb = f"[SVC] {dt} - {cli}"
                delete_map[lb] = {'id': i['id'], 't': 'servico'}
                lista_agenda.append({'Data': dt, 'Cliente': cli, 'Item': nm, 'Profissional': nome_prof, 'Tipo': 'Serviço'})
        except: pass

        if lista_agenda:
            st.dataframe(pd.DataFrame(lista_agenda), use_container_width=True, hide_index=True)
        else: st.info("Agenda vazia.")
        
        st.divider()
        if delete_map:
            s_del = st.selectbox("🗑️ Apagar:", list(delete_map.keys()))
            if st.button("Confirmar Apagar"):
                tb = 'agendamentos_salao' if delete_map[s_del]['t'] == 'salao' else 'agendamentos'
                supabase.table(tb).delete().eq('id', delete_map[s_del]['id']).execute()
                st.success("Apagado!"); time.sleep(1); st.rerun()

    with ca_right:
        st.markdown("#### ➕ Novo")
        tem_salao = any('Salão' in c for c in cats_disponiveis)
        tem_servico = any('Serviço' in c and 'Salão' not in c for c in cats_disponiveis)
        
        opts = []
        if tem_servico: opts.append("Serviço (Horário)")
        if tem_salao: opts.append("Evento (Salão)")
        
        if len(opts) == 1: tipo_add = opts[0]
        elif len(opts) > 1: tipo_add = st.radio("Tipo:", opts)
        else: tipo_add = "Serviço (Horário)" 
        
        with st.form("add_agd"):
            cli = st.text_input("Cliente (Nome/WhatsApp)")
            d_date = st.date_input("Data", value=datetime.now().date())
            
            if "Horário" in tipo_add:
                d_time = st.time_input("Hora", value=dt_time(9,0))
                s_serv = st.selectbox("Serviço", list(map_prod_inv.keys()))
                s_prof = st.selectbox("Profissional", list(map_prof_inv.keys())) if map_prof else None
                val = st.number_input("R$", 0.0)
                
                if st.form_submit_button("Agendar", type="primary"):
                    try:
                        dt_iso = datetime.combine(d_date, d_time).isoformat()
                        pl = {"cliente_id": c_id, "data_hora_inicio": dt_iso, "cliente_final_waid": cli, "servico_id": map_prod_inv.get(s_serv), "valor_total_registrado": val, "status":"Confirmado"}
                        if s_prof: pl["profissional_id"] = map_prof_inv[s_prof]
                        supabase.table('agendamentos').insert(pl).execute()
                        st.success("Ok!"); time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")
            else:
                s_prod = st.selectbox("Pacote", list(map_prod_inv.keys()))
                val = st.number_input("R$", 0.0)
                if st.form_submit_button("Agendar", type="primary"):
                    try:
                        pl = {"cliente_id": c_id, "data_reserva": str(d_date), "cliente_final_waid": cli, "produto_salao_id": map_prod_inv.get(s_prod), "valor_total_registrado": val, "status":"Confirmado"}
                        supabase.table('agendamentos_salao').insert(pl).execute()
                        st.success("Ok!"); time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

# ------------------------------------------------------------------------------
# TAB 4: CÉREBRO (AGORA COM CONTROLES COMPLETOS)
# ------------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Configuração da IA")

    try:
        res = supabase.table('clientes').select('config_fluxo, prompt_full').eq('id', c_id).execute()
        
        if res.data and len(res.data) > 0:
            d = res.data[0]
            
            # --- TRATAMENTO SEGURO DE DADOS ---
            curr_c = d.get('config_fluxo')
            if curr_c is None: curr_c = {}
            elif isinstance(curr_c, str):
                try: curr_c = json.loads(curr_c)
                except: curr_c = {}
            elif not isinstance(curr_c, dict): curr_c = {}

            prompt_atual = d.get('prompt_full') or ""
            
            # Temperatura (Vírgula vs Ponto)
            raw_temp = curr_c.get('temperature', 0.5)
            try:
                if isinstance(raw_temp, str): raw_temp = raw_temp.replace(',', '.')
                temp_atual = float(raw_temp)
            except: temp_atual = 0.5

            # Novos Campos (Com defaults seguros)
            audio_ativo = bool(curr_c.get('audio_ativo', True))
            
            # Horários (Padrão 09:00 - 18:00)
            h_ini_str = curr_c.get('horario_inicio', "09:00")
            h_fim_str = curr_c.get('horario_fim', "18:00")
            try: t_ini = datetime.strptime(h_ini_str, "%H:%M").time()
            except: t_ini = dt_time(9,0)
            try: t_fim = datetime.strptime(h_fim_str, "%H:%M").time()
            except: t_fim = dt_time(18,0)

            # Sinal
            sinal_val = float(curr_c.get('sinal_minimo_reais', 0.0))
            
            c_p1, c_p2 = st.columns([2, 1])
            with c_p1:
                st.markdown("##### Personalidade & Regras")
                new_p = st.text_area("Instruções do Sistema", value=prompt_atual, height=450, help="Descreva como o Otti deve se comportar.")
            
            with c_p2:
                # --- CÓDIGO NOVO (ORGANIZADO) ---
                st.header("Configurações")  # Mudamos de "Ajustes Finos" para "Configurações"
                
                # =========================================================
                # 1. PERSONALIDADE E ÁUDIO (Agrupamos tudo aqui)
                # =========================================================
                st.subheader("🔊 Personalidade e Voz")
                
                # Toggle de Áudio
                openai_audio = st.toggle(
                    "Respostas em Áudio", 
                    value=config_fluxo.get('responde_em_audio', False),
                    help="Se ativado, o Otti responderá mensagens de voz enviando áudios também."
                )
                
                # Definição das vozes com explicação (Legenda)
                # Mapeia o nome técnico (key) para o nome bonito (value)
                mapa_vozes = {
                    "alloy": "Alloy (Neutro e Versátil)",
                    "echo": "Echo (Masculino e Suave)",
                    "fable": "Fable (Masculino e Narrador)",
                    "onyx": "Onyx (Masculino e Profundo)",
                    "nova": "Nova (Feminino e Energético)",
                    "shimmer": "Shimmer (Feminino e Calmo)"
                }
                
                voz_atual_code = config_fluxo.get('openai_voice', 'alloy')
                
                # Selectbox mostrando a descrição amigável
                voz_display = st.selectbox(
                    "Voz do Assistente",
                    options=list(mapa_vozes.values()),
                    # Encontra o índice da voz atual baseada na descrição
                    index=list(mapa_vozes.keys()).index(voz_atual_code) if voz_atual_code in mapa_vozes else 0
                )
                
                # Converte de volta o nome bonito para o código (ex: "Nova..." -> "nova")
                # Isso garante que salve certo no JSON depois
                openai_voice = [k for k, v in mapa_vozes.items() if v == voz_display][0]
                
                st.write("") # Espaço visual
                
                # Slider de Criatividade (Agora "Tom de Voz")
                temperature = st.slider(
                    "Tom de Voz (Criatividade)",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(config_fluxo.get('temperature', 0.8)),
                    step=0.1,
                    help="Define o quão criativa ou exata será a IA."
                )
                
                # Legenda explicativa dinâmica
                if temperature < 0.5:
                    st.info("🤖 **Modo Mais Robótico (0.0 - 0.4):** Respostas curtas, objetivas e factuais. Segue scripts à risca.")
                else:
                    st.success("✨ **Modo Mais Humano (0.5 - 1.0):** Respostas fluidas, empáticas e conversacionais. Ideal para atendimento ao cliente.")
                
                st.divider() # Linha divisória
            
            # =========================================================
            # 2. HORÁRIO DE ATENDIMENTO
            # =========================================================
            st.subheader("🕒 Horário de Atendimento")
            
            col_h1, col_h2 = st.columns(2)
            
            # Gera lista de horários "00:00" até "23:00"
            lista_horarios = [f"{i:02d}:00" for i in range(24)]
            
            # Tenta pegar o index salvo, se der erro usa padrão (09:00 e 18:00)
            try:
                idx_inicio = lista_horarios.index(config_fluxo.get('horario_inicio', '09:00'))
            except:
                idx_inicio = 9
            
            try:
                idx_fim = lista_horarios.index(config_fluxo.get('horario_fim', '18:00'))
            except:
                idx_fim = 18
            
            with col_h1:
                horario_inicio = st.selectbox("Início", options=lista_horarios, index=idx_inicio)
            
            with col_h2:
                horario_fim = st.selectbox("Fim", options=lista_horarios, index=idx_fim)
            
            st.divider() # Linha divisória
            
            # =========================================================
            # 3. FINANCEIRO
            # =========================================================
            st.subheader("💰 Financeiro")
            
            sinal_minimo_reais = st.number_input(
                "Valor do Sinal para Reserva (R$)",
                min_value=0.0,
                value=float(config_fluxo.get('sinal_minimo_reais', 100.0)),
                step=10.0,
                format="%.2f"
            )
            
            col_save, _ = st.columns([1,3])
            with col_save:
                if st.button("💾 SALVAR CONFIGURAÇÕES", type="primary", use_container_width=True):
                    try:
                        # Atualiza Dicionário
                        curr_c['openai_voice'] = nova_voz
                        curr_c['temperature'] = nova_temp
                        curr_c['audio_ativo'] = novo_audio
                        curr_c['horario_inicio'] = novo_ini.strftime("%H:%M")
                        curr_c['horario_fim'] = novo_fim.strftime("%H:%M")
                        curr_c['sinal_minimo_reais'] = novo_sinal
                        
                        supabase.table('clientes').update({'prompt_full': new_p, 'config_fluxo': curr_c}).eq('id', c_id).execute()
                        st.success("Configurações atualizadas com sucesso!")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
        else:
            st.warning("Não foi possível carregar as configurações deste cliente.")
    except Exception as e:
        st.error(f"Erro de conexão com o Banco de Dados: {e}")


