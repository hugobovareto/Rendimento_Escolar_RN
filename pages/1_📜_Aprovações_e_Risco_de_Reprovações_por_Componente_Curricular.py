# Importação das bibliotecas
import streamlit as st
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go

# 🔄 COMPARTILHAR DADOS ENTRE PÁGINAS
@st.cache_data
def carregar_dados_componentes():
    return pd.read_parquet('dados_tratados/df_componentes.parquet')

# CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Aprovações e Risco de Reprovações por Componente Curricular", layout="wide")

# Carregar dados se não estiverem em cache
if 'df' not in st.session_state:
    st.session_state.df_componentes = carregar_dados_componentes()


# Carregar dados se não estiverem em cache
if 'df' not in st.session_state:
    st.session_state.df = carregar_dados_componentes()

# Acessar dados
df = st.session_state.df_componentes

# VERIFICAÇÃO INICIAL CRÍTICA
if 'COMPONENTE CURRICULAR' not in df.columns:
    st.error("🚨 ERRO GRAVE: Coluna 'COMPONENTE CURRICULAR' não encontrada no DataFrame original!")
    st.write("Isso indica um problema com o arquivo de dados ou com o processo de carregamento.")
    st.write(f"Colunas carregadas: {list(df.columns)}")
    st.stop()




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
    
    # GARANTIR que as colunas essenciais estão presentes
    colunas_essenciais = ['COMPONENTE CURRICULAR', 'Aprovados', 'Reprovados', 'ETAPA_RESUMIDA', 'SÉRIE']
    
    # Verificar se todas as colunas essenciais existem
    colunas_faltantes = [col for col in colunas_essenciais if col not in df_filtrado.columns]
    if colunas_faltantes:
        st.error(f"❌ Colunas essenciais faltantes antes da filtragem: {colunas_faltantes}")
        st.stop()
    
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
    
    # VERIFICAR novamente após filtragem
    colunas_faltantes_pos = [col for col in colunas_essenciais if col not in df_filtrado.columns]
    if colunas_faltantes_pos:
        st.error(f"❌ Colunas essenciais removidas durante filtragem: {colunas_faltantes_pos}")
        st.info(f"DataFrame após filtragem tem {len(df_filtrado)} linhas e {len(df_filtrado.columns)} colunas")
        st.stop()
    
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
left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.image("images/LOGO SEEC 2o SEMESTRE.1.png", width=400)

st.write("")

st.title("📜 Aprovações e Risco de Reprovações por Componente Curricular")

st.markdown("""
**⏱️ Última atualização**:  dados extraídos do SIGEduc em 07/08/2026.
""")

st.write("")

st.markdown("""
            Componentes são considerados aprovados caso possuam média igual ou superior a 6.0.
            \n São consideradas as notas para o 1º e 2º bimestres de 2026. Caso alguma nota ainda não tenho sido lançada, a média é feita considerando somente as notas disponíveis.
            """)

st.write("")
st.write("")


# =============================================================================
# GRÁFICO 1: PERCENTUAL DE APROVAÇÃO E RISCO DE REPROVAÇÃO POR COMPONENTE CURRICULAR
# =============================================================================
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Percentual de Aprovação e Risco de Reprovação por Componente Curricular</p>",
    unsafe_allow_html=True)

# Filtros para Etapa e Série
col_filtro1, col_filtro2 = st.columns(2)

with col_filtro1:
    etapas_options = ['Todas'] + sorted(df_filtered['ETAPA_RESUMIDA'].dropna().unique().tolist())
    etapa_selecionada = st.selectbox(
        "Selecione a Etapa:",
        options=etapas_options,
        key="filtro_etapa_componente_aprov"
    )

with col_filtro2:
    series_options = ['Todas'] + sorted(df_filtered['SÉRIE'].dropna().unique().tolist())
    serie_selecionada = st.selectbox(
        "Selecione a Série:",
        options=series_options,
        key="filtro_serie_componente_aprov"
    )

# Aplicar filtros de etapa e série COM VERIFICAÇÃO
df_filtrado_grafico1 = df_filtered.copy()

if etapa_selecionada != 'Todas':
    df_filtrado_grafico1 = df_filtrado_grafico1[df_filtrado_grafico1['ETAPA_RESUMIDA'] == etapa_selecionada]

if serie_selecionada != 'Todas':
    df_filtrado_grafico1 = df_filtrado_grafico1[df_filtrado_grafico1['SÉRIE'] == serie_selecionada]


# Verificar se há dados após os filtros
if df_filtrado_grafico1.empty:
    st.warning("Não há dados disponíveis para os filtros selecionados.")
else:
    # Agrupamento por componente
    df_componente = df_filtrado_grafico1.groupby('COMPONENTE CURRICULAR').agg({
        'Aprovados': 'sum',
        'Reprovados': 'sum'
    }).reset_index()

# Calcular totais e percentuais
df_componente['Total'] = df_componente['Aprovados'] + df_componente['Reprovados']
df_componente['%_Aprovados'] = (df_componente['Aprovados'] / df_componente['Total'] * 100).round(1)
df_componente['%_Reprovados'] = (df_componente['Reprovados'] / df_componente['Total'] * 100).round(1)

# Ordenar os componentes por ordem alfabética
df_componente = df_componente.sort_values('%_Reprovados', ascending=False)


# Verificar se há dados após os filtros
if df_filtrado_grafico1.empty:
    st.warning("Não há dados disponíveis para os filtros selecionados.")
else:
    # Adicionar métricas resumidas
    col1, col2 = st.columns(2)

    with col1:
        taxa_aprovacao_geral = (df_componente['Aprovados'].sum() / (df_componente['Total'].sum()) * 100).round(1)
        st.metric("Taxa de Aprovação Geral", f"{taxa_aprovacao_geral}%")

    with col2:
        taxa_reprovacao_geral = (df_componente['Reprovados'].sum() / (df_componente['Total'].sum()) * 100).round(1)
        st.metric("Taxa de Risco de Reprovação Geral", f"{taxa_reprovacao_geral}%")

    # Criar gráfico de barras empilhadas
    fig_componente = go.Figure()

    # Barra de aprovados (verde)
    fig_componente.add_trace(go.Bar(
        name='Aprovados',
        x=df_componente['COMPONENTE CURRICULAR'],
        y=df_componente['%_Aprovados'],
        marker=dict(color='#2e7d32'),
        text=df_componente['%_Aprovados'].astype(str) + '%',
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Aprovados: %{y}%<br>Total: ' + df_componente['Aprovados'].astype(str) + '<extra></extra>'
    ))

    # Barra de reprovados (vermelho)
    fig_componente.add_trace(go.Bar(
        name='Risco de Reprovação',
        x=df_componente['COMPONENTE CURRICULAR'],
        y=df_componente['%_Reprovados'],
        marker=dict(color='#c62828'),
        text=df_componente['%_Reprovados'].astype(str) + '%',
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Risco de Reprovação: %{y}%<br>Total: ' + df_componente['Reprovados'].astype(str) + '<extra></extra>'
    ))

    # Configurar layout
    fig_componente.update_layout(
        title=f'Percentual de Aprovação e Risco de Reprovação por Componente Curricular',
        xaxis_title='Componente Curricular',
        yaxis_title='Percentual (%)',
        barmode='stack',
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=80, b=150, l=50, r=50)
    )

    # Rodar labels do eixo X para melhor visualização
    fig_componente.update_xaxes(tickangle=-45)

    # Ajustar eixo Y para ir de 0% a 100%
    fig_componente.update_yaxes(range=[0, 100])

    # Exibir gráfico
    st.plotly_chart(fig_componente, use_container_width=True)

    # Informação sobre filtros aplicados
    info_filtros = []
    if etapa_selecionada != 'Todas':
        info_filtros.append(f"Etapa: {etapa_selecionada}")
    if serie_selecionada != 'Todas':
        info_filtros.append(f"Série: {serie_selecionada}")
    
    if info_filtros:
        st.info(f"💡 **Filtros aplicados:** {', '.join(info_filtros)}")
    else:
        st.info("💡 **Filtros aplicados:** Todas as etapas e séries")

    # Mostrar tabela com dados detalhados
    with st.expander("📋 Ver Dados Detalhados por Componente Curricular"):
        # Criar DataFrame de exibição
        df_display_componente = pd.DataFrame({
            'Componente Curricular': df_componente['COMPONENTE CURRICULAR'],
            'Total': df_componente['Total'],
            'Aprovados': df_componente['Aprovados'],
            'Risco de Reprovação': df_componente['Reprovados'],
            '% Aprovados': df_componente['%_Aprovados'].astype(str) + ' %',
            '% Risco de Reprovação': df_componente['%_Reprovados'].astype(str) + ' %'
        })
        
        # Estilizar a tabela
        st.dataframe(
            df_display_componente,
            width='stretch',
            hide_index=True,
            column_config={
                'Total': st.column_config.NumberColumn(format='%d'),
                'Aprovados': st.column_config.NumberColumn(format='%d'),
                'Risco de Reprovação': st.column_config.NumberColumn(format='%d')
            }
        )


st.write("")
st.write("")


# =============================================================================
# GRÁFICO 2: PERCENTUAL DE APROVAÇÃO E RISCO DE REPROVAÇÃO POR ANO/SÉRIE ESCOLAR 
# =============================================================================
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Percentual de Aprovação e Risco de Reprovação por Ano/Série Escolar</p>",
    unsafe_allow_html=True)

# Filtro para Componente Curricular
componentes_options = ['Todos'] + sorted(df_filtered['COMPONENTE CURRICULAR'].dropna().unique().tolist())
componente_selecionado = st.selectbox(
    "Selecione o Componente Curricular:",
    options=componentes_options,
    key="filtro_componente_serie_aprov"
)

# Aplicar filtro de componente
df_filtrado_grafico5 = df_filtered.copy()

if componente_selecionado != 'Todos':
    df_filtrado_grafico5 = df_filtrado_grafico5[df_filtrado_grafico5['COMPONENTE CURRICULAR'] == componente_selecionado]

# Verificar se há dados após os filtros
if df_filtrado_grafico5.empty:
    st.warning("Não há dados disponíveis para o componente selecionado.")
else:
    # Calcular totais por Série
    df_serie = df_filtrado_grafico5.groupby('SÉRIE').agg({
        'Aprovados': 'sum',
        'Reprovados': 'sum'
    }).reset_index()

    # Calcular totais e percentuais
    df_serie['Total'] = df_serie['Aprovados'] + df_serie['Reprovados']
    df_serie['%_Aprovados'] = (df_serie['Aprovados'] / df_serie['Total'] * 100).round(1)
    df_serie['%_Reprovados'] = (df_serie['Reprovados'] / df_serie['Total'] * 100).round(1)

    # Ordenar as séries de forma lógica
    try:
        df_serie['SERIE_ORDENADA'] = pd.Categorical(
            df_serie['SÉRIE'], 
            categories=sorted(df_serie['SÉRIE'].unique(), key=lambda x: (float(x.split()[0]) if x.split()[0].isdigit() else float('inf'), x)),
            ordered=True
        )
        df_serie = df_serie.sort_values('SERIE_ORDENADA')
    except:
        df_serie = df_serie.sort_values('SÉRIE')

    # Adicionar métricas resumidas
    col1, col2 = st.columns(2)

    with col1:
        taxa_aprovacao_geral = (df_serie['Aprovados'].sum() / (df_serie['Total'].sum()) * 100).round(1)
        st.metric("Taxa de Aprovação Geral", f"{taxa_aprovacao_geral}%")

    with col2:
        taxa_reprovacao_geral = (df_serie['Reprovados'].sum() / (df_serie['Total'].sum()) * 100).round(1)
        st.metric("Taxa de Risco de Reprovação Geral", f"{taxa_reprovacao_geral}%")

    # Criar gráfico de barras empilhadas
    fig_serie = go.Figure()

    # Barra de aprovados (verde)
    fig_serie.add_trace(go.Bar(
        name='Aprovados',
        x=df_serie['SÉRIE'],
        y=df_serie['%_Aprovados'],
        marker=dict(color='#2e7d32'),
        text=df_serie['%_Aprovados'].astype(str) + '%',
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Aprovados: %{y}%<br>Total: ' + df_serie['Aprovados'].astype(str) + '<extra></extra>'
    ))

    # Barra de reprovados (vermelho)
    fig_serie.add_trace(go.Bar(
        name='Risco de Reprovação',
        x=df_serie['SÉRIE'],
        y=df_serie['%_Reprovados'],
        marker=dict(color='#c62828'),
        text=df_serie['%_Reprovados'].astype(str) + '%',
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Risco de Reprovação: %{y}%<br>Total: ' + df_serie['Reprovados'].astype(str) + '<extra></extra>'
    ))

    # Configurar layout
    fig_serie.update_layout(
        title=f'Percentual de Aprovação e Risco de Reprovação por Série - {componente_selecionado if componente_selecionado != "Todos" else "Todos os Componentes"}',
        xaxis_title='Série',
        yaxis_title='Percentual (%)',
        barmode='stack',
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=80, b=100, l=50, r=50)
    )

    # Rodar labels do eixo X para melhor visualização
    fig_serie.update_xaxes(tickangle=-45)

    # Ajustar eixo Y para ir de 0% a 100%
    fig_serie.update_yaxes(range=[0, 100])

    # Exibir gráfico
    st.plotly_chart(fig_serie, use_container_width=True)

    # Informação sobre filtro aplicado
    if componente_selecionado != 'Todos':
        st.info(f"💡 **Filtro aplicado:** Componente Curricular: {componente_selecionado}")
    else:
        st.info("💡 **Filtro aplicado:** Todos os Componentes Curriculares")

    # Mostrar tabela com dados detalhados
    with st.expander("📋 Ver Dados Detalhados por Série"):
        # Criar DataFrame de exibição
        df_display_serie = pd.DataFrame({
            'Série': df_serie['SÉRIE'],
            'Total': df_serie['Total'],
            'Aprovados': df_serie['Aprovados'],
            'Risco de Reprovação': df_serie['Reprovados'],
            '% Aprovados': df_serie['%_Aprovados'].astype(str) + ' %',
            '% Risco de Reprovação': df_serie['%_Reprovados'].astype(str) + ' %'
        })
        
        # Estilizar a tabela
        st.dataframe(
            df_display_serie,
            width='stretch',
            hide_index=True,
            column_config={
                'Total': st.column_config.NumberColumn(format='%d'),
                'Aprovados': st.column_config.NumberColumn(format='%d'),
                'Risco de Reprovação': st.column_config.NumberColumn(format='%d')
            }
        )


st.write("")
st.write("")


# =============================================================================
# GRÁFICO 3: MÉDIA DE NOTAS POR COMPONENTE CURRICULAR
# =============================================================================
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Média de Notas por Componente Curricular</p>",
    unsafe_allow_html=True)

# Adicionar filtro para ETAPA_RESUMIDA
if 'ETAPA_RESUMIDA' in df_filtered.columns:
    etapas_options = ['Todas'] + sorted(df_filtered['ETAPA_RESUMIDA'].dropna().unique().tolist())
    etapa_selecionada = st.selectbox(
        "Selecione a Etapa:",
        options=etapas_options,
        key="filtro_etapa_medias_dropdown"
    )
    
    # Aplicar filtro de etapa
    if etapa_selecionada != 'Todas':
        df_filtrado_etapa = df_filtered[df_filtered['ETAPA_RESUMIDA'] == etapa_selecionada]
    else:
        df_filtrado_etapa = df_filtered
else:
    st.error("Coluna 'ETAPA_RESUMIDA' não encontrada no DataFrame.")
    df_filtrado_etapa = df_filtered

# Calcular médias por componente curricular
df_medias = df_filtrado_etapa.groupby('COMPONENTE CURRICULAR').agg({
    'NOTA_1_BIMESTRE': 'mean',
    'NOTA_2_BIMESTRE': 'mean',
    'NOTA_3_BIMESTRE': 'mean',
    'NOTA_4_BIMESTRE': 'mean',
    'MEDIA_NOTAS': 'mean'
}).round(2)

# Resetar índice para ter 'COMPONENTE CURRICULAR' como coluna
df_medias = df_medias.reset_index()

# Ordenar pela média de nota (MEDIA_NOTAS) - menor para o maior
df_medias = df_medias.sort_values('MEDIA_NOTAS', ascending=True)

# Verificar se há dados após o filtro
if df_medias.empty:
    st.warning("Não há dados disponíveis para os filtros selecionados.")
else:
    # Adicionar métricas resumidas
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        media_geral_1bim = df_medias['NOTA_1_BIMESTRE'].mean().round(2)
        st.metric("Média 1º Bimestre", f"{media_geral_1bim:.2f}")

    with col2:
        media_geral_2bim = df_medias['NOTA_2_BIMESTRE'].mean().round(2)
        st.metric("Média 2º Bimestre", f"{media_geral_2bim:.2f}")

    # with col3:
        # media_geral_3bim = df_medias['NOTA_3_BIMESTRE'].mean().round(2)
        # st.metric("Média 3º Bimestre", f"{media_geral_3bim:.2f}")

    # with col4:
        # media_geral_4bim = df_medias['NOTA_4_BIMESTRE'].mean().round(2)
        # st.metric("Média 4º Bimestre", f"{media_geral_4bim:.2f}")

    with col5:
        media_geral_final = df_medias['MEDIA_NOTAS'].mean().round(2)
        st.metric("Média Geral", f"{media_geral_final:.2f}")
    
    # Criar gráfico de barras agrupadas
    fig_medias = go.Figure()

    # Adicionar barras para cada tipo de nota
    fig_medias.add_trace(go.Bar(
        name='1º BIMESTRE',
        x=df_medias['COMPONENTE CURRICULAR'],
        y=df_medias['NOTA_1_BIMESTRE'],
        marker_color='#e6b17e',  # Marrom claro
        text=df_medias['NOTA_1_BIMESTRE'].astype(str),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>1º Bimestre: %{y}<extra></extra>'
    ))

    fig_medias.add_trace(go.Bar(
        name='2º BIMESTRE',
        x=df_medias['COMPONENTE CURRICULAR'],
        y=df_medias['NOTA_2_BIMESTRE'],
        marker_color=   '#d39c6b',  # Marrom médio
        text=df_medias['NOTA_2_BIMESTRE'].astype(str),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>2º Bimestre: %{y}<extra></extra>'
    ))

    # fig_medias.add_trace(go.Bar(
        # name='3º BIMESTRE',
        # x=df_medias['COMPONENTE CURRICULAR'],
        # y=df_medias['NOTA_3_BIMESTRE'],
        # marker_color='#cc8a42',  # Marrom escuro
        # text=df_medias['NOTA_3_BIMESTRE'].astype(str),
        # textposition='auto',
        # hovertemplate='<b>%{x}</b><br>3º Bimestre: %{y}<extra></extra>'
    # ))

    # fig_medias.add_trace(go.Bar(
        # name='4º BIMESTRE',
        # x=df_medias['COMPONENTE CURRICULAR'],
        # y=df_medias['NOTA_4_BIMESTRE'],
        # marker_color='#b7794f',  # Marrom escuro
        # text=df_medias['NOTA_4_BIMESTRE'].astype(str),
        # textposition='auto',
        # hovertemplate='<b>%{x}</b><br>4º Bimestre: %{y}<extra></extra>'
    # ))


    fig_medias.add_trace(go.Bar(
        name='MÉDIA GERAL',
        x=df_medias['COMPONENTE CURRICULAR'],
        y=df_medias['MEDIA_NOTAS'],
        marker_color="#794625",  # Marrom especificado
        text=df_medias['MEDIA_NOTAS'].astype(str),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Média Geral: %{y}<extra></extra>'
    ))

    # Configurar layout
    fig_medias.update_layout(
        title='Médias das Notas por Componente Curricular',
        xaxis_title='Componente Curricular',
        yaxis_title='Média das Notas (0-10)',
        barmode='group',  # Barras agrupadas
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=80, b=150, l=50, r=50)
    )

    # Rodar labels do eixo X para melhor visualização
    fig_medias.update_xaxes(
        tickangle=-45,
        tickmode='array',
        tickvals=df_medias['COMPONENTE CURRICULAR'],
        ticktext=df_medias['COMPONENTE CURRICULAR']
    )

    # Ajustar eixo Y para ir de 0 a 10
    fig_medias.update_yaxes(range=[0, 10])

    # Exibir gráfico
    st.plotly_chart(fig_medias, use_container_width=True)

    # Informação sobre filtros aplicados
    if 'ETAPA_RESUMIDA' in df_filtered.columns:
        if etapa_selecionada != 'Todas':
            st.info(f"💡 **Filtro aplicado:** Etapa: {etapa_selecionada}")
        else:
            st.info("💡 **Filtro aplicado:** Todas as etapas")

    # Mostrar tabela com dados detalhados
    with st.expander("📋 Ver Dados Detalhados das Médias"):
        # Criar DataFrame de exibição
        df_display_medias = pd.DataFrame({
            'Componente Curricular': df_medias['COMPONENTE CURRICULAR'],
            'Média 1º Bimestre': df_medias['NOTA_1_BIMESTRE'],
            'Média 2º Bimestre': df_medias['NOTA_2_BIMESTRE'],
            # 'Média 3º Bimestre': df_medias['NOTA_3_BIMESTRE'],
            # 'Média 4º Bimestre': df_medias['NOTA_4_BIMESTRE'],
            'Média Geral': df_medias['MEDIA_NOTAS']
        })
        
        # Estilizar a tabela
        st.dataframe(
            df_display_medias,
            width='stretch',
            hide_index=True,
            column_config={
                'Média 1º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                'Média 2º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                # 'Média 3º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                # 'Média 4º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                'Média Geral': st.column_config.NumberColumn(format='%.2f')
            }
        )

st.write("")
st.write("")

# =============================================================================
# GRÁFICO 4: MÉDIA DE NOTAS POR DIREC
# =============================================================================
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Média de Notas por DIREC</p>",
    unsafe_allow_html=True)

col_filtro1, col_filtro2 = st.columns(2)

with col_filtro1:
    # Filtro para ETAPA_RESUMIDA (dropdown com "Todas")
    if 'ETAPA_RESUMIDA' in df_filtered.columns:
        etapas_options = ['Todas'] + sorted(df_filtered['ETAPA_RESUMIDA'].dropna().unique().tolist())
        etapa_selecionada = st.selectbox(
            "Selecione a Etapa:",
            options=etapas_options,
            key="filtro_etapa_direc_select"
        )
    else:
        st.error("Coluna 'ETAPA_RESUMIDA' não encontrada.")
        etapa_selecionada = 'Todas'

with col_filtro2:
    # Filtro para COMPONENTE CURRICULAR (dropdown com "Todos")
    componentes_options = ['Todos'] + sorted(df_filtered['COMPONENTE CURRICULAR'].dropna().unique().tolist())
    componente_selecionado = st.selectbox(
        "Selecione o Componente Curricular:",
        options=componentes_options,
        key="filtro_componente_direc_select"
    )

# Aplicar filtros
df_filtrado_grafico = df_filtered.copy()

if etapa_selecionada != 'Todas':
    df_filtrado_grafico = df_filtrado_grafico[df_filtrado_grafico['ETAPA_RESUMIDA'] == etapa_selecionada]

if componente_selecionado != 'Todos':
    df_filtrado_grafico = df_filtrado_grafico[df_filtrado_grafico['COMPONENTE CURRICULAR'] == componente_selecionado]

# Verificar se há dados após os filtros
if df_filtrado_grafico.empty:
    st.warning("Não há dados disponíveis para os filtros selecionados.")
else:
    # Calcular médias por DIREC
    df_medias_direc = df_filtrado_grafico.groupby('DIREC').agg({
        'NOTA_1_BIMESTRE': 'mean',
        'NOTA_2_BIMESTRE': 'mean',
        'NOTA_3_BIMESTRE': 'mean',
        'NOTA_4_BIMESTRE': 'mean',
        'MEDIA_NOTAS': 'mean'
    }).round(2)

    # Resetar índice para ter 'DIREC' como coluna
    df_medias_direc = df_medias_direc.reset_index()

    # Ordenar pela média geral (MEDIA_NOTAS) - menor para maior
    df_medias_direc = df_medias_direc.sort_values('MEDIA_NOTAS', ascending=True)

    # Truncar nomes das DIRECs para melhor visualização
    df_medias_direc['DIREC_Truncada'] = df_medias_direc['DIREC'].astype(str).str.slice(0, 9)

    # Adicionar métricas resumidas
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        media_geral_1bim = df_medias_direc['NOTA_1_BIMESTRE'].mean().round(2)
        st.metric("Média 1º Bimestre", f"{media_geral_1bim:.2f}")

    with col2:
        media_geral_2bim = df_medias_direc['NOTA_2_BIMESTRE'].mean().round(2)
        st.metric("Média 2º Bimestre", f"{media_geral_2bim:.2f}")

    # with col3:
        # media_geral_3bim = df_medias_direc['NOTA_3_BIMESTRE'].mean().round(2)
        # st.metric("Média 3º Bimestre", f"{media_geral_3bim:.2f}")

    # with col4:
        # media_geral_4bim = df_medias_direc['NOTA_4_BIMESTRE'].mean().round(2)
        # st.metric("Média 4º Bimestre", f"{media_geral_4bim:.2f}")

    with col5:
        media_geral_final = df_medias_direc['MEDIA_NOTAS'].mean().round(2)
        st.metric("Média Geral", f"{media_geral_final:.2f}")

    # Criar gráfico de barras agrupadas
    fig_medias_direc = go.Figure()

    # Adicionar barras para cada tipo de nota
    fig_medias_direc.add_trace(go.Bar(
        name='1º BIMESTRE',
        x=df_medias_direc['DIREC_Truncada'],
        y=df_medias_direc['NOTA_1_BIMESTRE'],
        marker_color='#e6b17e',  # Marrom claro
        text=df_medias_direc['NOTA_1_BIMESTRE'].astype(str),
        textposition='auto',
        customdata=df_medias_direc['DIREC'],  # Passamos a coluna com o nome completo
        hovertemplate='<b>%{customdata}</b><br>1º Bimestre: %{y}<extra></extra>'
    ))

    fig_medias_direc.add_trace(go.Bar(
        name='2º BIMESTRE',
        x=df_medias_direc['DIREC_Truncada'],
        y=df_medias_direc['NOTA_2_BIMESTRE'],
        marker_color='#d39c6b',  # Marrom médio
        text=df_medias_direc['NOTA_2_BIMESTRE'].astype(str),
        textposition='auto',
        customdata=df_medias_direc['DIREC'],  # Passamos a coluna com o nome completo
        hovertemplate='<b>%{customdata}</b><br>2º Bimestre: %{y}<extra></extra>'
    ))

    # fig_medias_direc.add_trace(go.Bar(
        # name='3º BIMESTRE',
        # x=df_medias_direc['DIREC_Truncada'],
        # y=df_medias_direc['NOTA_3_BIMESTRE'],
        # marker_color='#cc8a42',  # Marrom escuro
        # text=df_medias_direc['NOTA_3_BIMESTRE'].astype(str),
        # textposition='auto',
        # customdata=df_medias_direc['DIREC'],  # Passamos a coluna com o nome completo
        # hovertemplate='<b>%{customdata}</b><br>3º Bimestre: %{y}<extra></extra>'
    # ))

    # fig_medias_direc.add_trace(go.Bar(
        # name='4º BIMESTRE',
        # x=df_medias_direc['DIREC_Truncada'],
        # y=df_medias_direc['NOTA_4_BIMESTRE'],
        # marker_color='#b7794f',  # Marrom escuro
        # text=df_medias_direc['NOTA_4_BIMESTRE'].astype(str),
        # textposition='auto',
        # customdata=df_medias_direc['DIREC'],  # Passamos a coluna com o nome completo
        # hovertemplate='<b>%{customdata}</b><br>4º Bimestre: %{y}<extra></extra>'
    # ))


    fig_medias_direc.add_trace(go.Bar(
        name='MÉDIA GERAL',
        x=df_medias_direc['DIREC_Truncada'],
        y=df_medias_direc['MEDIA_NOTAS'],
        marker_color="#794625",  # Marrom especificado
        text=df_medias_direc['MEDIA_NOTAS'].astype(str),
        textposition='auto',
        customdata=df_medias_direc['DIREC'],  # Passamos a coluna com o nome completo
        hovertemplate='<b>%{customdata}</b><br>Média Geral: %{y}<extra></extra>'
    ))

    # Configurar layout
    fig_medias_direc.update_layout(
        title='Médias das Notas por DIREC',
        xaxis_title='DIREC',
        yaxis_title='Média das Notas (0-10)',
        barmode='group',
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=80, b=150, l=50, r=50)
    )

    # Rodar labels do eixo X para melhor visualização
    fig_medias_direc.update_xaxes(
        tickangle=-45,
        tickmode='array',
        tickvals=df_medias_direc['DIREC_Truncada'],
        ticktext=df_medias_direc['DIREC_Truncada']
    )

    # Ajustar eixo Y para ir de 0 a 10
    fig_medias_direc.update_yaxes(range=[0, 10])

    # Exibir gráfico
    st.plotly_chart(fig_medias_direc, use_container_width=True)

    # Informação sobre filtros aplicados
    info_filtros = []
    if etapa_selecionada != 'Todas':
        info_filtros.append(f"Etapa: {etapa_selecionada}")
    if componente_selecionado != 'Todos':
        info_filtros.append(f"Componente: {componente_selecionado}")
    
    if info_filtros:
        st.info(f"💡 **Filtros aplicados:** {', '.join(info_filtros)}")
    else:
        st.info("💡 **Filtros aplicados:** Todas as etapas e componentes")

    # Mostrar tabela com dados detalhados
    with st.expander("📋 Ver Dados Detalhados por DIREC"):
        # Criar DataFrame de exibição
        df_display_direc = pd.DataFrame({
            'DIREC': df_medias_direc['DIREC'],
            'Média 1º Bimestre': df_medias_direc['NOTA_1_BIMESTRE'],
            'Média 2º Bimestre': df_medias_direc['NOTA_2_BIMESTRE'],
            # 'Média 3º Bimestre': df_medias_direc['NOTA_3_BIMESTRE'],
            # 'Média 4º Bimestre': df_medias_direc['NOTA_4_BIMESTRE'],
            'Média Geral': df_medias_direc['MEDIA_NOTAS']
        })
        
        # Estilizar a tabela
        st.dataframe(
            df_display_direc,
            width='stretch',
            hide_index=True,
            column_config={
                'Média 1º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                'Média 2º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                # 'Média 3º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                # 'Média 4º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                'Média Geral': st.column_config.NumberColumn(format='%.2f')
            }
        )


