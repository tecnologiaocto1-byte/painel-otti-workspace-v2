import streamlit as st
import pandas as pd
from supabase import create_client
import json

# --- CONEXÃO ---
@st.cache_resource
def init_connection():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url: return None
    return create_client(url, key)

supabase = init_connection()

# --- LEITURA (CACHED) ---
@st.cache_data(ttl=60)
def get_kpis():
    if not supabase: return pd.DataFrame()
    return pd.DataFrame(supabase.table('view_dashboard_kpis').select("*").execute().data)

@st.cache_data(ttl=60)
def get_financial_data(c_id):
    """Busca dados de agendamentos de salão e serviços gerais"""
    try:
        r_s = supabase.table('agendamentos_salao').select('created_at, valor_sinal_registrado, status, produto_salao_id, produtos:produto_salao_id(nome)').eq('cliente_id', c_id).execute().data
        r_p = supabase.table('agendamentos').select('created_at, valor_sinal_registrado, status, servico_id').eq('cliente_id', c_id).execute().data
        return r_s, r_p
    except: return [], []

def get_messages(c_id):
    """Busca lista de conversas recentes (Sem cache para ser real-time)"""
    return supabase.table('conversas').select('id, cliente_wa_id, updated_at, metadata').eq('cliente_id', c_id).order('updated_at', desc=True).limit(20).execute()

def get_chat_history(conversa_id):
    """Busca histórico de mensagens de uma conversa específica"""
    return supabase.table('historico_mensagens').select('*').eq('conversa_id', conversa_id).order('created_at', desc=True).limit(40).execute()

def get_products(c_id):
    """Busca lista de produtos"""
    return supabase.table('produtos').select('nome, categoria, ativo').eq('cliente_id', c_id).order('nome').execute()

def get_agenda(c_id):
    """Busca agenda futura"""
    try:
        rs = supabase.table('agendamentos_salao').select('data_reserva, valor_total_registrado, cliente_final_waid').eq('cliente_id', c_id).order('created_at', desc=True).limit(50).execute()
        if rs.data: return pd.DataFrame(rs.data)
        
        rv = supabase.table('agendamentos').select('data_hora_inicio, valor_total_registrado').eq('cliente_id', c_id).order('created_at', desc=True).limit(50).execute()
        if rv.data: return pd.DataFrame(rv.data)
        
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- ESCRITA E LÓGICA COMPLEXA (SEM CACHE) ---

def toggle_bot(c_id, current_status):
    """Pausa ou Ativa o Bot"""
    new_status = not current_status
    supabase.table('clientes').update({'bot_pausado': new_status}).eq('id', c_id).execute()
    st.cache_data.clear()

def create_product(c_id, nome, categoria, preco):
    """Cria novo produto formatando o JSON de regras corretamente"""
    try:
        # Lógica de negócio encapsulada aqui
        regras_json = {"preco_padrao": float(preco), "duracao_minutos": 60}
        
        payload = {
            "cliente_id": c_id,
            "nome": nome,
            "categoria": categoria,
            "ativo": True,
            "regras_preco": json.dumps(regras_json)
        }
        supabase.table('produtos').insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao criar produto: {e}")
        return False

def get_client_config(c_id):
    """Recupera configuração bruta do cliente para edição"""
    try:
        res = supabase.table('clientes').select('config_fluxo, prompt_full').eq('id', c_id).execute()
        if res.data:
            data = res.data[0]
            # Tratamento do JSON que pode vir como string ou dict
            config = data.get('config_fluxo') or {}
            if isinstance(config, str):
                config = json.loads(config)
            return data.get('prompt_full'), config
        return "", {}
    except:
        return "", {}

def update_brain(c_id, prompt_text, new_voice, new_temp, current_config):
    """Atualiza o Cérebro (Prompt e Configurações JSON)"""
    try:
        # Atualiza o dicionário de config mantendo outros dados que possam existir
        current_config['openai_voice'] = new_voice
        current_config['temperature'] = new_temp
        
        payload = {
            'prompt_full': prompt_text,
            'config_fluxo': json.dumps(current_config) # Serializa de volta para salvar
        }
        
        supabase.table('clientes').update(payload).eq('id', c_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar cérebro: {e}")
        return False
