import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import json
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Otti Workspace", layout="wide", page_icon="🐙")

# --- CONEXÃO COM CACHE (Singleton) ---
@st.cache_resource
def init_connection():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

supabase = init_connection()

# --- CAMADA DE DADOS (Data Layer) ---
# Usamos @st.cache_data para não bater no banco a cada milissegundo. 
# TTL=60 significa que os dados atualizam a cada 60 segundos sozinhos.

@st.cache_data(ttl=60)
def fetch_kpis(cliente_id=None, perfil='user'):
    """Busca KPIs já processados ou brutos."""
    if not supabase: return None
    try:
        query = supabase.table('view_dashboard_kpis').select("*")
        data = query.execute().data
        df = pd.DataFrame(data)
        
        if perfil != 'admin' and cliente_id:
            df = df[df['cliente_id'] == cliente_id]
            
        return df
    except Exception as e:
        st.error(f"Erro ao buscar KPIs: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300) # Cache maior para histórico (5 min)
def fetch_financial_history(cliente_id):
    """Busca histórico financeiro unificado."""
    try:
        r_s = supabase.table('agendamentos_salao').select('created_at, valor_sinal_registrado, status, produto_salao_id, produtos:produto_salao_id(nome)').eq('cliente_id', cliente_id).execute().data
        r_p = supabase.table('agendamentos').select('created_at, valor_sinal_registrado, status, servico_id').eq('cliente_id', cliente_id).execute().data
        
        lista = []
        # Normalização dos dados aqui no backend, não na view
        for i in r_s:
            prod_name = i.get('produtos', {}).get('nome', 'Salão') if i.get('produtos') else 'Salão'
            lista.append({'dt': i['created_at'], 'v': i.get('valor_sinal_registrado',0), 'st': i['status'], 'p': prod_name})
            
        for i in r_p:
            lista.append({'dt': i['created_at'], 'v': i.get('valor_sinal_registrado',0), 'st': i['status'], 'p': 'Serviço'})
            
        if not lista: return pd.DataFrame()
        
        df = pd.DataFrame(lista)
        df['dt'] = pd.to_datetime(df['dt']).dt.date
        return df[df['st'] != 'Cancelado']
    except Exception as e:
        return pd.DataFrame()

def toggle_bot_status(cliente_id, current_status):
    """Função de ação (não cacheada)"""
    new_status = not current_status
    supabase.table('clientes').update({'bot_pausado': new_status}).eq('id', cliente_id).execute()
    st.cache_data.clear() # Limpa o cache para refletir a mudança imediata
    return new_status