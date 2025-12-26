import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import json
import time
import os
import random
from datetime import datetime, timedelta

# ==============================================================================
# 1. SETUP
# ==============================================================================
st.set_page_config(page_title="Otti Workspace", layout="wide", page_icon="🐙")

# --- CORES DO NOVO DESIGN (OCTO) ---
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
# 3. CSS
# ==============================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;800&family=Inter:wght@300;400;600&display=swap');

    .stApp {{ background-color: {C_BG_OCTO_LIGHT}; color: {C_TEXT_DARK}; font-family: 'Inter', sans-serif; }}
    
    section[data-testid="stSidebar"] {{ 
        background-color: {C_SIDEBAR_NAVY}; 
        border-right: 1px solid rgba(255,255,255,0.1); 
    }}
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label {{ color: #FFFFFF !important; }}

    h1 {{ font-family: 'Sora', sans-serif; color: {C_SIDEBAR_NAVY} !important; font-weight: 800; }}
    h2, h3, h4 {{ font-family: 'Sora', sans-serif; color: {C_TEXT_DARK} !important; font-weight: 700; }}
    p, label {{ color: {C_TEXT_DARK} !important; }}

    .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
    }}
    
    div[data-baseweb="select"] > div {{
        background-color: #FFFFFF !important;
        border-color: #CBD5E1 !important;
    }}
    div[data-baseweb="select"] span {{ color: #000000 !important; }}
    div[data-baseweb="popover"] {{ background-color: #FFFFFF !important; }}
    div[data-baseweb="option"] {{ color: #000000 !important; }}

    button[kind="primary"] {{
        background: linear-gradient(90deg, #3F00FF 0%, #031A89 100%) !important;
        color: #FFFFFF !important; border: none !important; padding: 0.6rem 1.2rem; border-radius: 6px;
    }}

    div[data-testid="stAppViewContainer"] .main .stButton > button {{
        background-color: {C_BTN_DARK} !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    div[data-testid="stAppViewContainer"] .main .stButton > button:hover {{
        background-color: #3F00FF !important;
        color: #FFFFFF !important;
    }}

    section[data-testid="stSidebar"] button {{
        background-color: transparent !important; border: 1px solid rgba(255,255,255,0.5) !important;
    }}
    section[data-testid="stSidebar"] button p {{ color: #FFFFFF !important; }}

    div[data-testid="stMetric"] {{ 
        background-color: {C_CARD_WHITE}; 
        border: 1px solid #E2E8F0; 
        border-radius: 10px; 
        padding: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.03); 
    }}
    div[data-testid="stMetricValue"] {{ color: {C_ACCENT_NEON} !important; font-family: 'Sora', sans-serif; font-weight: 700; }}
    label[data-testid="stMetricLabel"] {{ color: #64748B !important; font-weight: 500; }}

    .login-wrapper {{ margin-top: 10vh; max-width: 400px; margin-left: auto; margin-right: auto; text-align: center; }}
    .block-container {{padding-top: 2rem;}}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LOGIN
# ==============================================================================
def render_logo(width=100):
    if os.path.exists("logo.png"): st.image("logo.png", width=width)
    else: st.markdown(f"<h1 style='color:{C_ACCENT_NEON}; margin:0; font-family:Sora; text-align:center;'>OCTO</h1>", unsafe_allow_html=True)

if 'usuario_logado' not in st.session_state: st.session_state['usuario_logado'] = None

def render_login_screen():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
        render_logo(width=120)
        st.markdown(f"<h3 style='margin-bottom:30px; color:{C_TEXT_DARK}; text-align:center;'>Otti Workspace</h3>", unsafe_allow_html=True)
        
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
    lbl = "⏸️ PAUSAR SISTEMA" if active else "▶️ ATIVAR SISTEMA"
    if st.button(lbl, use_container_width=True):
        supabase.table('clientes').update({'bot_pausado': active}).eq('id', c_id).execute()
        st.rerun()

st.divider()

tot = c_data['total_mensagens']
sav = round((tot * 1.5) / 60, 1)
rev = float(c_data['receita_total'] or 0)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita Total", f"R$ {rev:,.2f}")
k2.metric("Economia Tempo", f"{sav}h")
k3.metric("Atendimentos", c_data['total_atendimentos'])
k4.metric("Status Atual", "Online 🟢" if active else "Offline 🔴")
st.markdown("<br>", unsafe_allow_html=True)

tabs = st.tabs(["📊 Analytics", "📦 Produtos", "📅 Agenda", "🧠 Cérebro"])

# ==============================================================================
# ABA 1: ANALYTICS
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
                st.markdown("##### 🍕 Share de Produtos")
                df_top = df_filt.groupby('p')['v'].sum().reset_index()
                if not df_top.empty:
                    fig2 = px.pie(df_top, values='v', names='p', hole=0.5, color_discrete_sequence=px.colors.sequential.Bluyl)
                    fig2.update_traces(textinfo='percent+label', textposition='inside')
                    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': C_TEXT_DARK}, showlegend=False, margin=dict(l=0, r=0, t=20, b=20))
                    st.plotly_chart(fig2, use_container_width=True)
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

# ==============================================================================
# ABA 2: PRODUTOS
# ==============================================================================
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
    else:
        df_prod = pd.DataFrame()

    c1, c2 = st.columns([2,1])
    
    with c1:
        if not df_prod.empty:
            df_display = df_prod[['nome', 'categoria', 'Preço (R$)']]
            df_display.columns = ['Nome', 'Categoria', 'Preço (R$)']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum produto cadastrado.")

    with c2:
        with st.form("add"):
            st.markdown("#### 🆕 Novo Item")
            n = st.text_input("Nome")
            c = st.selectbox("Categoria", ["Serviço", "Produto"])
            p = st.number_input("Preço", min_value=0.0, step=10.0)
            
            if st.form_submit_button("Salvar", type="primary"):
                js = {"preco_padrao": p, "duracao_minutos": 60}
                try:
                    supabase.table('produtos').insert({
                        "cliente_id": c_id, 
                        "nome": n, 
                        "categoria": c, 
                        "ativo": True, 
                        "regras_preco": js 
                    }).execute()
                    
                    st.success(f"Item '{n}' salvo!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        st.divider()

        st.markdown("#### 🗑️ Excluir Item")
        if not df_prod.empty:
            map_del = {row['nome']: row['id'] for i, row in df_prod.iterrows()}
            sel_del = st.selectbox("Selecione o produto", list(map_del.keys()), key="del_sel")
            
            if st.button("Confirmar Exclusão", type="secondary"):
                try:
                    id_to_del = map_del[sel_del]
                    supabase.table('produtos').delete().eq('id', id_to_del).execute()
                    st.success("Produto removido!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")
        else:
            st.caption("Sem itens para excluir.")

# ==============================================================================
# ABA 3: AGENDA (NOMES DOS SERVIÇOS E PROFISSIONAIS)
# ==============================================================================
with tabs[2]:
    st.subheader("📅 Próximos Agendamentos")
    
    # 1. Carrega Dicionários para DE-PARA (ID -> Nome)
    try:
        # MAPA DE PRODUTOS/SERVIÇOS
        res_prod = supabase.table('produtos').select('id, nome').eq('cliente_id', c_id).execute()
        map_prod = {p['id']: p['nome'] for p in res_prod.data} if res_prod.data else {}

        # MAPA DE PROFISSIONAIS
        map_prof = {}
        try:
            # Tenta buscar, se a tabela não existir ou estiver vazia, não quebra o código
            res_prof = supabase.table('profissionais').select('id, nome').eq('cliente_id', c_id).execute()
            if res_prof.data:
                map_prof = {p['id']: p['nome'] for p in res_prof.data}
        except: 
            pass # Segue a vida se não tiver profissionais

        lista_agenda = []

        # A) AGENDA SALÃO (Tabela agendamentos_salao)
        try:
            rs = supabase.table('agendamentos_salao').select('*').eq('cliente_id', c_id).order('created_at', desc=True).limit(30).execute()
            if rs.data:
                for item in rs.data:
                    # Busca nome do produto (Se não achar, usa 'Salão')
                    nome_prod = map_prod.get(item.get('produto_salao_id'), 'Salão/Evento')
                    
                    lista_agenda.append({
                        'Data': item.get('data_reserva'),
                        'Cliente': item.get('cliente_final_waid', 'Cliente'), # Poderia buscar nome se tivesse tabela de clientes finais
                        'Serviço/Produto': nome_prod,
                        'Profissional': '-', # Salão geralmente não tem profissional no agendamento simples
                        'Valor': item.get('valor_total_registrado', 0),
                        'Status': item.get('status')
                    })
        except: pass

        # B) AGENDA SERVIÇOS/SALÃO CABELEIREIRO (Tabela agendamentos)
        try:
            rv = supabase.table('agendamentos').select('*').eq('cliente_id', c_id).order('created_at', desc=True).limit(30).execute()
            if rv.data:
                for item in rv.data:
                    # Busca nome do serviço
                    nome_serv = map_prod.get(item.get('servico_id'), 'Serviço')
                    # Busca nome do profissional
                    nome_prof = map_prof.get(item.get('profissional_id'), '-')
                    
                    # Formata data se for timestamp
                    data_full = item.get('data_hora_inicio')
                    
                    lista_agenda.append({
                        'Data': data_full,
                        'Cliente': item.get('cliente_final_nome') or 'Cliente',
                        'Serviço/Produto': nome_serv,
                        'Profissional': nome_prof,
                        'Valor': item.get('valor_total_registrado', 0),
                        'Status': item.get('status', 'Confirmado')
                    })
        except: pass

        # 3. Monta Tabela Final
        if lista_agenda:
            df_final = pd.DataFrame(lista_agenda)
            
            # Tenta formatar as datas para ficar bonito
            try:
                df_final['Data'] = pd.to_datetime(df_final['Data']).dt.strftime('%d/%m/%Y %H:%M')
            except: pass # Se falhar, deixa como texto original

            # Ordenação final das colunas
            cols = ['Data', 'Cliente', 'Serviço/Produto', 'Profissional', 'Valor', 'Status']
            # Filtra colunas que existem no dataframe (segurança)
            cols = [c for c in cols if c in df_final.columns]
            
            st.dataframe(df_final[cols], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum agendamento encontrado.")

    except Exception as e:
        st.error(f"Erro ao carregar agenda: {e}")

# ==============================================================================
# ABA 4: CÉREBRO
# ==============================================================================
if perfil == 'admin' and len(tabs) > 3:
    with tabs[3]:
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
                
                st.markdown("<br>", unsafe_allow_html=True)
                
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
