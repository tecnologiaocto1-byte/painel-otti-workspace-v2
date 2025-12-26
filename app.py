

apply_styling()

# ================= LOGIN SIMPLIFICADO =================
if 'user' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("## 🐙 Otti Admin")
        with st.form("login"):
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                try:
                    res = supabase.table('acesso_painel').select('*').eq('email', email).eq('senha', senha).execute()
                    if res.data:
                        st.session_state['user'] = res.data[0]
                        st.rerun()
                    else:
                        st.error("Acesso negado.")
                except:
                    st.error("Erro de conexão.")
    st.stop()

# ================= DASHBOARD =================
user = st.session_state['user']

# --- SIDEBAR ---
with st.sidebar:
    st.title("🐙 Otti")
    st.write(f"Bem-vindo, **{user['nome_usuario']}**")
    st.markdown("---")
    if st.button("Sair", use_container_width=True):
        st.session_state.pop('user')
        st.rerun()

# --- SELEÇÃO DE CLIENTE (Lógica Admin/User) ---
df_kpis = fetch_kpis(user.get('cliente_id'), user.get('perfil'))

if df_kpis.empty:
    st.warning("Nenhum dado encontrado para este perfil.")
    st.stop()

if user['perfil'] == 'admin':
    clientes_list = df_kpis['nome_empresa'].unique()
    selected_cli = st.selectbox("Selecione o Cliente", clientes_list)
    c_data = df_kpis[df_kpis['nome_empresa'] == selected_cli].iloc[0]
else:
    c_data = df_kpis.iloc[0]

c_id = int(c_data['cliente_id'])
bot_active = not bool(c_data['bot_pausado'])

# --- HEADER & CONTROLES ---
col_head, col_action = st.columns([3, 1])
with col_head:
    st.title(c_data['nome_empresa'])
    st.caption(f"Status do Sistema: {'🟢 Online' if bot_active else '🔴 Pausado'}")

with col_action:
    # Botão de Ação com Feedback Visual
    btn_label = "⏸️ PAUSAR OTTI" if bot_active else "▶️ ATIVAR OTTI"
    btn_type = "secondary" if bot_active else "primary"
    if st.button(btn_label, type=btn_type, use_container_width=True):
        toggle_bot_status(c_id, bool(c_data['bot_pausado']))
        st.rerun()

# --- METRICAS PRINCIPAIS (Cards) ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Receita Total", f"R$ {float(c_data['receita_total'] or 0):,.2f}")
m2.metric("Tempo Economizado", f"{((c_data['total_mensagens'] * 1.5) / 60):.1f}h")
m3.metric("Atendimentos", c_data['total_atendimentos'])
m4.metric("Taxa de Conversão", "N/A", delta_color="off") # Placeholder pra feature futura

st.markdown("---")

# --- TABS DE CONTEÚDO ---
tab_dash, tab_chat, tab_config = st.tabs(["📊 Analytics", "💬 Espião de Conversas", "⚙️ Configurações"])

with tab_dash:
    df_fin = fetch_financial_history(c_id)
    
    if not df_fin.empty:
        c_g1, c_g2 = st.columns([2, 1])
        with c_g1:
            st.markdown("### 📈 Evolução de Vendas")
            df_g = df_fin.groupby('dt')['v'].sum().reset_index()
            fig = px.area(df_g, x='dt', y='v', template="plotly_dark")
            fig.update_traces(line_color="#3F00FF", fillcolor="rgba(63, 0, 255, 0.2)")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
            
        with c_g2:
            st.markdown("### 🏆 Top Produtos")
            df_top = df_fin['p'].value_counts().reset_index().head(5)
            fig2 = px.bar(df_top, x='count', y='p', orientation='h', template="plotly_dark")
            fig2.update_traces(marker_color="#5396FF")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=0,b=0), yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Ainda não há dados financeiros suficientes para gerar gráficos.")

with tab_chat:
    st.markdown("### 🕵️ Monitoramento em Tempo Real")
    # Lógica de chat mantida, mas coloque dentro de um container com altura fixa
    # para não quebrar o layout da página
    
    col_list, col_msgs = st.columns([1, 2])
    with col_list:
        st.caption("Últimas Conversas")
        # (Sua lógica de listar conversas aqui...)
        # DICA: Use st.pills ou st.radio horizontal se forem poucos
        
    with col_msgs:
        container_chat = st.container(height=500, border=True)
        with container_chat:
            st.markdown("Selecione uma conversa ao lado...")
            # (Sua lógica de renderizar mensagens aqui...)

with tab_config:
    st.markdown("### 🧠 Cérebro do Otti")
    # Apenas Admin pode ver o prompt
    if user['perfil'] == 'admin':
        prompt = st.text_area("Prompt do Sistema", height=300, help="Instruções base para a IA")
        if st.button("Salvar Prompt", type="primary"):
            st.toast("Prompt atualizado com sucesso! (Simulação)")
    else:
        st.info("Entre em contato com o suporte para alterar a personalidade do seu Otti.")