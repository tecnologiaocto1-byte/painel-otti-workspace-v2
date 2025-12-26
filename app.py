import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

# Importa as funções robustas
from services import (
    supabase, get_kpis, get_financial_data, get_messages, get_chat_history,
    get_products, get_agenda, toggle_bot, create_product,
    get_client_config, update_brain
)
from styles import apply_original_style

# 1. SETUP
st.set_page_config(page_title="Otti Workspace", layout="wide", page_icon="🐙")
apply_original_style() # Mantendo seu estilo Dark Neon

# 2. LOGIN (Mantido simplificado para focar no resto)
if 'usuario_logado' not in st.session_state: st.session_state['usuario_logado'] = None
if not st.session_state['usuario_logado']:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:#3F00FF'>OCTO</h1>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR", type="primary", use_container_width=True):
                res = supabase.table('acesso_painel').select('*').eq('email', email).eq('senha', senha).execute()
                if res.data:
                    st.session_state['usuario_logado'] = res.data[0]
                    st.rerun()
                else: st.error("Login inválido")
    st.stop()

# 3. DADOS DO USUÁRIO
user = st.session_state['usuario_logado']
perfil = user['perfil']

# Sidebar
with st.sidebar:
    st.title("🐙 Otti")
    st.write(f"Olá, **{user['nome_usuario']}**")
    if st.button("SAIR"):
        st.session_state['usuario_logado'] = None
        st.rerun()

# Seleção de Cliente
df_kpis = get_kpis()
if perfil == 'admin':
    lista = df_kpis['nome_empresa'].unique()
    sel = st.sidebar.selectbox("Cliente:", lista)
    c_data = df_kpis[df_kpis['nome_empresa'] == sel].iloc[0]
else:
    c_data = df_kpis[df_kpis['cliente_id'] == user['cliente_id']].iloc[0]

c_id = int(c_data['cliente_id'])
active = not bool(c_data['bot_pausado'])

# Header
c1, c2 = st.columns([3, 1])
with c1: st.title(c_data['nome_empresa'])
with c2:
    lbl = "⏸️ PAUSAR" if active else "▶️ ATIVAR"
    if st.button(lbl, use_container_width=True):
        toggle_bot(c_id, bool(c_data['bot_pausado']))
        st.rerun()

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Receita", f"R$ {float(c_data['receita_total'] or 0):,.2f}")
k2.metric("Tempo", f"{round((c_data['total_mensagens']*1.5)/60, 1)}h")
k3.metric("Atendimentos", c_data['total_atendimentos'])
k4.metric("Status", "Online" if active else "Offline")
st.divider()

# --- ABAS ---
tabs = st.tabs(["Analytics", "Espião", "Produtos", "Agenda", "Cérebro"])

# 1. ANALYTICS
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
            fig.update_traces(line_color="#3F00FF")
            st.plotly_chart(fig, use_container_width=True)
        with c_g2:
            st.markdown("##### Produtos Mais Vendidos")
            df_top = df['p'].value_counts().reset_index().head(5)
            fig2 = px.bar(df_top, x='count', y='p', orientation='h', template='plotly_dark')
            fig2.update_traces(marker_color="#5396FF")
            st.plotly_chart(fig2, use_container_width=True)
    else: st.info("Sem dados financeiros.")

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
            with st.container(height=500):
                for m in msgs:
                    av = "👤" if m['role']=='user' else "🐙"
                    with st.chat_message(m['role'], avatar=av): st.write(m['content'])

# 3. PRODUTOS
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
            if st.form_submit_button("Salvar Item", type="primary"):
                if create_product(c_id, n, c, p):
                    st.success("Produto criado!")
                    st.rerun()

# 4. AGENDA
with tabs[3]:
    st.subheader("Próximos Agendamentos")
    df_agenda = get_agenda(c_id)
    if not df_agenda.empty:
        st.dataframe(df_agenda, use_container_width=True)
    else: st.info("Nenhum agendamento futuro encontrado.")

# 5. CÉREBRO (A Lógica Pesada voltou!)
with tabs[4]:
    if perfil == 'admin':
        st.subheader("Configuração da Inteligência")
        
        # Busca dados brutos
        prompt_atual, config_atual = get_client_config(c_id)
        
        c_p1, c_p2 = st.columns([2, 1])
        with c_p1:
            new_prompt = st.text_area("Prompt (Personalidade)", value=prompt_atual or '', height=400)
            
        with c_p2:
            st.markdown("##### Configurações de Voz")
            
            # Tratamento de erro da temperatura (mantendo sua lógica original)
            raw_temp = config_atual.get('temperature', 0.5)
            temp_val = 0.5
            try:
                if isinstance(raw_temp, str):
                    temp_val = float(raw_temp.replace(',', '.'))
                else:
                    temp_val = float(raw_temp)
            except: temp_val = 0.5
            
            vozes = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            v_atual = config_atual.get('openai_voice', 'alloy')
            if v_atual not in vozes: v_atual = 'alloy'
            
            new_voice = st.selectbox("Voz:", vozes, index=vozes.index(v_atual))
            new_temp = st.slider("Criatividade:", 0.0, 1.0, value=temp_val, step=0.1)
            
            if st.button("💾 Atualizar Cérebro", type="primary", use_container_width=True):
                if update_brain(c_id, new_prompt, new_voice, new_temp, config_atual):
                    st.success("IA Reconfigurada com Sucesso!")
                    st.balloons()
    else:
        st.warning("Acesso restrito a administradores.")
