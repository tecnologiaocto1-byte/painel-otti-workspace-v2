import streamlit as st

def apply_styling():
    # --- PALETA LIGHT PREMIUM ---
    C_BG_MAIN    = "#F8FAFC"      # Cinza Gelo (Fundo Geral)
    C_SIDEBAR    = "#FFFFFF"      # Branco Puro (Sidebar)
    C_CARD       = "#FFFFFF"      # Branco (Cards)
    C_TEXT_MAIN  = "#0F172A"      # Azul Quase Preto (Leitura perfeita)
    C_TEXT_SEC   = "#64748B"      # Cinza Médio (Subtítulos)
    C_ACCENT     = "#3F00FF"      # Seu Azul Elétrico (Destaques)
    C_ACCENT_HOVR= "#3200CC"      # Azul Escuro (Hover)
    C_BORDER     = "#E2E8F0"      # Borda sutil para separar elementos

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* --- GERAL --- */
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: {C_TEXT_MAIN};
            background-color: {C_BG_MAIN};
        }}

        /* Força o fundo do app */
        .stApp {{
            background-color: {C_BG_MAIN};
        }}

        /* --- SIDEBAR --- */
        section[data-testid="stSidebar"] {{
            background-color: {C_SIDEBAR};
            border-right: 1px solid {C_BORDER};
            box-shadow: 2px 0 10px rgba(0,0,0,0.02);
        }}
        /* Textos da Sidebar */
        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] span, 
        section[data-testid="stSidebar"] label {{
            color: {C_TEXT_MAIN} !important;
        }}

        /* --- CARDS E METRICAS --- */
        div[data-testid="stMetric"] {{
            background-color: {C_CARD};
            border: 1px solid {C_BORDER};
            border-radius: 12px;
            padding: 20px;
            /* Sombra suave para destacar no fundo branco */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); 
            transition: all 0.2s ease;
        }}
        
        div[data-testid="stMetric"]:hover {{
            border-color: {C_ACCENT};
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(63, 0, 255, 0.1);
        }}

        /* Cor do Valor da Métrica (Destaque) */
        div[data-testid="stMetricValue"] {{
            color: {C_ACCENT} !important;
            font-weight: 700;
        }}
        div[data-testid="stMetricLabel"] {{
            color: {C_TEXT_SEC} !important;
            font-weight: 500;
        }}

        /* --- BOTÕES --- */
        /* Botão Primário (Ação Principal) */
        button[kind="primary"] {{
            background-color: {C_ACCENT} !important;
            color: #FFFFFF !important;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: background-color 0.2s;
        }}
        button[kind="primary"]:hover {{
            background-color: {C_ACCENT_HOVR} !important;
        }}

        /* Botão Secundário (Ação Secundária) */
        button[kind="secondary"] {{
            background-color: #FFFFFF !important;
            color: {C_TEXT_MAIN} !important;
            border: 1px solid {C_BORDER} !important;
            border-radius: 8px;
        }}
        button[kind="secondary"]:hover {{
            border-color: {C_ACCENT} !important;
            color: {C_ACCENT} !important;
        }}

        /* --- INPUTS E SELECTBOXES --- */
        /* Fundo branco e texto escuro */
        .stTextInput > div > div > input, 
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {{
            background-color: #FFFFFF !important;
            color: {C_TEXT_MAIN} !important;
            border-color: {C_BORDER} !important;
            border-radius: 8px;
        }}
        
        /* Foco no input */
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: {C_ACCENT} !important;
            box-shadow: 0 0 0 1px {C_ACCENT} !important;
        }}

        /* --- TABS --- */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 24px;
            border-bottom: 1px solid {C_BORDER};
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border: none;
            color: {C_TEXT_SEC};
            font-weight: 600;
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            color: {C_ACCENT};
            border-bottom: 2px solid {C_ACCENT};
        }}
        
        /* Ajuste do Título */
        h1, h2, h3 {{
            color: {C_TEXT_MAIN} !important;
            font-weight: 700;
        }}
        
    </style>
    """, unsafe_allow_html=True)