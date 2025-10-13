# Importação das bibliotecas
import streamlit as st
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go

# 🔄 COMPARTILHAR DADOS ENTRE PÁGINAS
@st.cache_data
def carregar_dados():
    return pd.read_parquet('dados_tratados/df_EF_EM_bncc.parquet')

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

# Aplicar filtro de DIREC
if selected_direc != 'Todas':
    df_filtered = df[df['DIREC'] == selected_direc].copy()
else:
    df_filtered = df.copy()

# 2. Escolher o Município
municipio_options = ['Todos'] + sorted(df_filtered['MUNICÍPIO'].dropna().unique().tolist())
selected_municipio = st.sidebar.selectbox("Selecione o Município:",
                                          options=municipio_options,
                                          index=municipio_options.index(st.session_state.filtro_municipio))

# Atualizar session state e resetar filtro dependente se mudou
if selected_municipio != st.session_state.filtro_municipio:
    st.session_state.filtro_municipio = selected_municipio
    st.session_state.filtro_escola = 'Todas'

# Aplicar filtro de MUNICÍPIO
if selected_municipio != 'Todos':
    df_filtered = df_filtered[df_filtered['MUNICÍPIO'] == selected_municipio]

# 3. Escolher a Escola
# Criar a coluna formatada combinando nome + código INEP
df_filtered['ESCOLA_FORMATADA'] = (
    df_filtered['ESCOLA'].astype(str) + " (cód. Inep: " + df_filtered['INEP ESCOLA'].astype(str) + ")")

escola_options = ['Todas'] + sorted(df_filtered['ESCOLA_FORMATADA'].dropna().unique().tolist())
selected_escola_formatada = st.sidebar.selectbox("Selecione a Escola:",
                                                 options=escola_options,
                                                 index=escola_options.index(st.session_state.filtro_escola))

# Atualizar session state
if selected_escola_formatada != st.session_state.filtro_escola:
    st.session_state.filtro_escola = selected_escola_formatada

# Aplicar filtro de ESCOLA
if selected_escola_formatada != 'Todas':
    df_filtered = df_filtered[df_filtered['ESCOLA_FORMATADA'] == selected_escola_formatada]


# Botão para limpar todos os filtros
if st.sidebar.button("🔄 Limpar Todos os Filtros"):
    st.session_state.filtro_direc = 'Todas'
    st.session_state.filtro_municipio = 'Todos'
    st.session_state.filtro_escola = 'Todas'
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
- 📈 **Lançamento de Notas**
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






