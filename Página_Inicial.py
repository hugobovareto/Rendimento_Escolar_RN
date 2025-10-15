# Importação das bibliotecas
import streamlit as st
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go

# 🔄 COMPARTILHAR DADOS ENTRE PÁGINAS
@st.cache_data
def carregar_dados():
    return pd.read_parquet('dados_tratados/df_EF_EM_bncc_censo.parquet')

# CONFIGURAÇÕES DA PÁGINA
st.set_page_config(
    page_title="Rendimento Escolar - Rede Estadual RN", 
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

# Limpar cache periodicamente
if 'clear_cache' not in st.session_state:
    st.session_state.clear_cache = True
    st.cache_data.clear()

# Carregar dados se não estiverem em cache
if 'df' not in st.session_state:
    st.session_state.df = carregar_dados()

# Acessar dados
df = st.session_state.df


# 🔄 COMPARTILHAR FILTROS ENTRE PÁGINAS
# Inicializar session state para filtros se não existir
if 'filtro_direc' not in st.session_state:
    st.session_state.filtro_direc = 'Todas'
if 'filtro_municipio' not in st.session_state:
    st.session_state.filtro_municipio = 'Todos'
if 'filtro_escola' not in st.session_state:
    st.session_state.filtro_escola = 'Todas'



# Sidebar com os filtros
st.sidebar.title("Filtros")

# 1. Escolher a DIREC
direc_options = ['Todas'] + sorted(df['DIREC'].dropna().unique().tolist())
selected_direc = st.sidebar.selectbox("Selecione a DIREC:",
                                      options=direc_options,
                                      index=direc_options.index(st.session_state.filtro_direc))

# Atualizar session state e resetar filtros dependentes se mudou
if selected_direc != st.session_state.filtro_direc:
    st.session_state.filtro_direc = selected_direc
    st.session_state.filtro_municipio = 'Todos'
    st.session_state.filtro_escola = 'Todas'

# 2. Escolher o Município (usando cache para opções)
@st.cache_data(ttl=300)
def get_municipio_options(_df, direc):
    if direc != 'Todas':
        df_temp = _df[_df['DIREC'] == direc]
    else:
        df_temp = _df
    return ['Todos'] + sorted(df_temp['MUNICÍPIO'].dropna().unique().tolist())

municipio_options = get_municipio_options(df, selected_direc)
selected_municipio = st.sidebar.selectbox("Selecione o Município:",
                                          options=municipio_options,
                                          index=municipio_options.index(st.session_state.filtro_municipio))

# Atualizar session state e resetar filtro dependente se mudou
if selected_municipio != st.session_state.filtro_municipio:
    st.session_state.filtro_municipio = selected_municipio
    st.session_state.filtro_escola = 'Todas'

# 3. Escolher a Escola (usando cache para opções)
@st.cache_data(ttl=300)
def get_escola_options(_df, direc, municipio):
    df_temp = _df.copy()
    if direc != 'Todas':
        df_temp = df_temp[df_temp['DIREC'] == direc]
    if municipio != 'Todos':
        df_temp = df_temp[df_temp['MUNICÍPIO'] == municipio]
    
    df_temp['ESCOLA_FORMATADA'] = (
        df_temp['ESCOLA'].astype(str) + " (cód. Inep: " + df_temp['INEP ESCOLA'].astype(str) + ")"
    )
    return ['Todas'] + sorted(df_temp['ESCOLA_FORMATADA'].dropna().unique().tolist())

escola_options = get_escola_options(df, selected_direc, selected_municipio)
selected_escola_formatada = st.sidebar.selectbox("Selecione a Escola:",
                                                 options=escola_options,
                                                 index=escola_options.index(st.session_state.filtro_escola))

# Atualizar session state
if selected_escola_formatada != st.session_state.filtro_escola:
    st.session_state.filtro_escola = selected_escola_formatada

# APLICAR TODOS OS FILTROS DE UMA VEZ (COM CACHE)
@st.cache_data(ttl=300)
def aplicar_filtros(_df, direc, municipio, escola):
    df_filtrado = _df.copy()
    
    if direc != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['DIREC'] == direc]
    
    if municipio != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['MUNICÍPIO'] == municipio]
    
    # Criar coluna formatada para escolas (apenas se necessário)
    if escola != 'Todas' or 'ESCOLA_FORMATADA' not in df_filtrado.columns:
        df_filtrado['ESCOLA_FORMATADA'] = (
            df_filtrado['ESCOLA'].astype(str) + " (cód. Inep: " + df_filtrado['INEP ESCOLA'].astype(str) + ")"
        )
    
    if escola != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['ESCOLA_FORMATADA'] == escola]
    
    return df_filtrado

df_filtered = aplicar_filtros(df, selected_direc, selected_municipio, selected_escola_formatada)


# Botão para limpar todos os filtros
if st.sidebar.button("🔄 Limpar Todos os Filtros"):
    st.session_state.filtro_direc = 'Todas'
    st.session_state.filtro_municipio = 'Todos'
    st.session_state.filtro_escola = 'Todas'
    st.cache_data.clear()
    st.rerun()

# CONFIGURAÇÕES DA PÁGINA
# Imagem do cabeçalho
st.image("images/logos.png", width=1700)

st.title("🎓 Rendimento Escolar - Rede Estadual RN")

st.markdown("""
            Esta aplicação apresenta informações sobre a aprovação, reprovação e rendimento escolar dos estudantes considerando as notas já lançadas para o  1º e 2º bimestres de 2025.
            \n Os dados são dos estudantes dos **Anos Finais do Ensino Fundamental e do Ensino Médio**, somente para os **componentes curriculares que fazem parte da Base Nacional Comum Curricular (BNCC)**.
            """)

st.write("")
st.markdown("""
**⏱️ Última atualização**:  dados extraídos do SIGEduc em 10/10/2025.
""")

st.write("")

st.markdown("""**Navegue pelas páginas usando a parte superior do menu lateral esquerdo:**
- 📜 **Aprovações e Reprovações por Componente Curricular**
- 📃 **Aprovações e Reprovações dos Estudantes**

Utilize os filtros no menu lateral para selecionar DIREC, Município e Escola específicos.
""")

# Mostrar instruções de uso
with st.expander("ℹ️ Como usar esta aplicação"):
    st.markdown("""
    1. **Navegue entre as páginas** usando a parte superior do menu lateral esquerdo
    2. **Selecione os filtros** na barra lateral para focar sua análise
    3. **Interaja com os gráficos** para ver detalhes
    """)






