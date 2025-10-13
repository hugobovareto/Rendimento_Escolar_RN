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
st.set_page_config(page_title="Aprovações e Reprovações por Componente Curricular", layout="wide")

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
                                                    #2. Aprovação e Reprovação por componente curricular
# Imagem do cabeçalho
st.image("images/logos.png", width=1700)

st.write("")

st.title("📜 Aprovações e Reprovações por Componente Curricular")



st.markdown("""
**⏱️ Última atualização**:  dados extraídos do SIGEduc em 10/10/2025.
""")

st.write("")

st.markdown("""
            Componentes são considerados aprovados caso possuam média do 1º semestre igual ou superior a 6.0.
            \n São consideradas as notas para o 1º e 2º bimestres de 2025. Caso alguma nota ainda não tenho sido lançada, a média é feita considerando somente as notas disponíveis.
            """)


st.write("")
st.write("")
# Percentual de Aprovação e Reprovação por Componente Curricular
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Percentual de Aprovação e Reprovação por Componente Curricular</p>",
    unsafe_allow_html=True)


# Adicionar filtros para este gráfico
col_filtro1, col_filtro2 = st.columns(2)

with col_filtro1:
    # Filtro para ETAPA_RESUMIDA
    if 'ETAPA_RESUMIDA' in df_filtered.columns:
        etapas_options = ['Todas'] + sorted(df_filtered['ETAPA_RESUMIDA'].dropna().unique().tolist())
        etapa_selecionada = st.selectbox(
            "Selecione a Etapa:",
            options=etapas_options,
            key="filtro_etapa_componente"
        )
    else:
        st.error("Coluna 'ETAPA_RESUMIDA' não encontrada.")
        etapa_selecionada = 'Todas'

with col_filtro2:
    # Filtro para SÉRIE
    if 'SÉRIE' in df_filtered.columns:
        series_options = ['Todas'] + sorted(df_filtered['SÉRIE'].dropna().unique().tolist())
        serie_selecionada = st.selectbox(
            "Selecione a Série:",
            options=series_options,
            key="filtro_serie_componente"
        )
    else:
        st.error("Coluna 'SÉRIE' não encontrada.")
        serie_selecionada = 'Todas'

# Aplicar filtros antes do processamento
df_filtrado_grafico = df_filtered.copy()

if etapa_selecionada != 'Todas':
    df_filtrado_grafico = df_filtrado_grafico[df_filtrado_grafico['ETAPA_RESUMIDA'] == etapa_selecionada]

if serie_selecionada != 'Todas':
    df_filtrado_grafico = df_filtrado_grafico[df_filtrado_grafico['SÉRIE'] == serie_selecionada]

# Filtrar apenas registros que têm status definido (excluir 'Sem nota')
df_com_status = df_filtrado_grafico[df_filtrado_grafico['STATUS'].notna() & (df_filtrado_grafico['STATUS'] != 'Sem nota')]

# Verificar se há dados após os filtros
if df_com_status.empty:
    st.warning("Não há dados disponíveis para os filtros selecionados.")
else:
    # Calcular totais por Componente Curricular
    df_componente = df_com_status.groupby('COMPONENTE CURRICULAR', observed=True).agg({
        'STATUS': [
            ('Total_Com_Status', 'size'),
            ('Aprovados', lambda x: (x == 'Aprovado').sum()),
            ('Reprovados', lambda x: (x == 'Reprovado').sum())
        ]
    }).round(0)

    # Reformatar o DataFrame
    df_componente.columns = df_componente.columns.droplevel(0)
    df_componente = df_componente.reset_index()

    # Calcular percentuais
    df_componente['%_Aprovados'] = (df_componente['Aprovados'] / df_componente['Total_Com_Status'] * 100).round(1)
    df_componente['%_Reprovados'] = (df_componente['Reprovados'] / df_componente['Total_Com_Status'] * 100).round(1)

    # Ordenar por nome do Componente Curricular (ordem alfabética)
    df_componente = df_componente.sort_values('%_Aprovados', ascending=True)

    # Adicionar métricas resumidas
    col1, col2 = st.columns(2)

    with col1:
        taxa_aprovacao_geral = (df_componente['Aprovados'].sum() / (df_componente['Total_Com_Status'].sum()) * 100).round(1)
        st.metric("Taxa de Aprovação Geral", f"{taxa_aprovacao_geral}%")

    with col2:
        taxa_reprovacao_geral = (df_componente['Reprovados'].sum() / (df_componente['Total_Com_Status'].sum()) * 100).round(1)
        st.metric("Taxa de Reprovação Geral", f"{taxa_reprovacao_geral}%")

    # Criar gráfico de barras empilhadas
    fig_componente = go.Figure()

    # Barra de aprovados (verde)
    fig_componente.add_trace(go.Bar(
        name='✅ Aprovados',
        x=df_componente['COMPONENTE CURRICULAR'],
        y=df_componente['%_Aprovados'],
        marker=dict(color='#2e7d32'),
        text=df_componente['%_Aprovados'].astype(str) + '%',
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Aprovados: %{y}%<br>Total: ' + df_componente['Aprovados'].astype(str) + '<extra></extra>'
    ))

    # Barra de reprovados (vermelho)
    fig_componente.add_trace(go.Bar(
        name='❌ Reprovados',
        x=df_componente['COMPONENTE CURRICULAR'],
        y=df_componente['%_Reprovados'],
        marker=dict(color='#c62828'),
        text=df_componente['%_Reprovados'].astype(str) + '%',
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>Reprovados: %{y}%<br>Total: ' + df_componente['Reprovados'].astype(str) + '<extra></extra>'
    ))

    # Configurar layout
    fig_componente.update_layout(
        title='Percentual de Aprovação e Reprovação por Componente Curricular',
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
        margin=dict(t=80, b=150, l=50, r=50)  # Aumentar margem inferior para caber labels
    )

    # Rodar labels do eixo X em 45 graus para melhor visualização
    fig_componente.update_xaxes(
        tickangle=-45,
        tickmode='array',
        tickvals=df_componente['COMPONENTE CURRICULAR'],
        ticktext=df_componente['COMPONENTE CURRICULAR']
    )

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
            'Total (excluídas notas não lançadas)': df_componente['Total_Com_Status'],
            'Aprovados': df_componente['Aprovados'],
            'Reprovados': df_componente['Reprovados'],
            '% Aprovados': df_componente['%_Aprovados'].astype(str) + ' %',
            '% Reprovados': df_componente['%_Reprovados'].astype(str) + ' %'
        })
        
        # Estilizar a tabela
        st.dataframe(
            df_display_componente,
            width='stretch',
            hide_index=True,
            column_config={
                'Total (excluídas notas não lançadas)': st.column_config.NumberColumn(format='%d'),
                'Aprovados': st.column_config.NumberColumn(format='%d'),
                'Reprovados': st.column_config.NumberColumn(format='%d')
            }
        )


st.write("")
st.write("")
# Média de Notas por Componente Curricular
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Média de Notas por Componente Curricular</p>",
    unsafe_allow_html=True)


# Adicionar filtro para ETAPA_RESUMIDA

# Verificar se a coluna ETAPA_RESUMIDA existe no DataFrame
if 'ETAPA_RESUMIDA' in df_filtered.columns:
    # Obter opções únicas para ETAPA_RESUMIDA
    etapas_options = ['Todas'] + sorted(df_filtered['ETAPA_RESUMIDA'].dropna().unique().tolist())
    
    # Selectbox (dropdown) para ETAPA_RESUMIDA
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

# Calcular médias por componente curricular (ignorando NaN)
df_medias = df_filtrado_etapa.groupby('COMPONENTE CURRICULAR', observed=True).agg({
    'NOTA 1º BIMESTRE': lambda x: x.dropna().mean(),
    'NOTA 2º BIMESTRE': lambda x: x.dropna().mean(),
    'MEDIA_1_2_BIM': lambda x: x.dropna().mean()
}).round(2)

# Resetar índice para ter 'COMPONENTE CURRICULAR' como coluna
df_medias = df_medias.reset_index()

# Ordenar pela média do 1º semestre (MEDIA_1_2_BIM) - menor para o maior
df_medias = df_medias.sort_values('MEDIA_1_2_BIM', ascending=True)

# Verificar se há dados após o filtro
if df_medias.empty:
    st.warning("Não há dados disponíveis para os filtros selecionados.")
else:
    # Adicionar métricas resumidas
    col1, col2, col3 = st.columns(3)

    with col1:
        media_geral_1bim = df_medias['NOTA 1º BIMESTRE'].mean().round(2)
        st.metric("Média Geral 1º Bimestre", f"{media_geral_1bim:.2f}")

    with col2:
        media_geral_2bim = df_medias['NOTA 2º BIMESTRE'].mean().round(2)
        st.metric("Média Geral 2º Bimestre", f"{media_geral_2bim:.2f}")

    with col3:
        media_geral_final = df_medias['MEDIA_1_2_BIM'].mean().round(2)
        st.metric("Média Geral 1º Semestre", f"{media_geral_final:.2f}")
    
    # Criar gráfico de barras agrupadas
    fig_medias = go.Figure()

    # Adicionar barras para cada tipo de nota
    fig_medias.add_trace(go.Bar(
        name='1º BIMESTRE',
        x=df_medias['COMPONENTE CURRICULAR'],
        y=df_medias['NOTA 1º BIMESTRE'],
        marker_color='#e6b17e',  # Marrom claro
        text=df_medias['NOTA 1º BIMESTRE'].astype(str),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>1º Bimestre: %{y}<extra></extra>'
    ))

    fig_medias.add_trace(go.Bar(
        name='2º BIMESTRE',
        x=df_medias['COMPONENTE CURRICULAR'],
        y=df_medias['NOTA 2º BIMESTRE'],
        marker_color='#d39c6b',  # Marrom médio
        text=df_medias['NOTA 2º BIMESTRE'].astype(str),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>2º Bimestre: %{y}<extra></extra>'
    ))

    fig_medias.add_trace(go.Bar(
        name='MÉDIA 1º SEMESTRE',
        x=df_medias['COMPONENTE CURRICULAR'],
        y=df_medias['MEDIA_1_2_BIM'],
        marker_color='#cc8a42',  # Marrom especificado
        text=df_medias['MEDIA_1_2_BIM'].astype(str),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Média 1º Semestre: %{y}<extra></extra>'
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
            'Média 1º Bimestre': df_medias['NOTA 1º BIMESTRE'],
            'Média 2º Bimestre': df_medias['NOTA 2º BIMESTRE'],
            'Média 1º Semestre': df_medias['MEDIA_1_2_BIM']
        })
        
        # Estilizar a tabela
        st.dataframe(
            df_display_medias,
            width='stretch',
            hide_index=True,
            column_config={
                'Média 1º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                'Média 2º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                'Média 1º Semestre': st.column_config.NumberColumn(format='%.2f')
            }
        )


st.write("")
st.write("")
# Média de Notas por DIREC
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
    # Calcular médias por DIREC (ignorando NaN)
    df_medias_direc = df_filtrado_grafico.groupby('DIREC', observed=True).agg({
        'NOTA 1º BIMESTRE': lambda x: x.dropna().mean(),
        'NOTA 2º BIMESTRE': lambda x: x.dropna().mean(),
        'MEDIA_1_2_BIM': lambda x: x.dropna().mean()
    }).round(2)

    # Resetar índice para ter 'DIREC' como coluna
    df_medias_direc = df_medias_direc.reset_index()

    # Ordenar pela média do 1º Semestre (MEDIA_1_2_BIM) - menor para maior
    df_medias_direc = df_medias_direc.sort_values('MEDIA_1_2_BIM', ascending=True)

    # Truncar nomes das DIRECs para melhor visualização
    df_medias_direc['DIREC_Truncada'] = df_medias_direc['DIREC'].astype(str).str.slice(0, 9)

    # Adicionar métricas resumidas
    col1, col2, col3 = st.columns(3)

    with col1:
        media_geral_1bim = df_medias_direc['NOTA 1º BIMESTRE'].mean().round(2)
        st.metric("Média Geral 1º Bimestre", f"{media_geral_1bim:.2f}")

    with col2:
        media_geral_2bim = df_medias_direc['NOTA 2º BIMESTRE'].mean().round(2)
        st.metric("Média Geral 2º Bimestre", f"{media_geral_2bim:.2f}")

    with col3:
        media_geral_final = df_medias_direc['MEDIA_1_2_BIM'].mean().round(2)
        st.metric("Média Geral 1º Semestre", f"{media_geral_final:.2f}")

    # Criar gráfico de barras agrupadas
    fig_medias_direc = go.Figure()

    # Adicionar barras para cada tipo de nota
    fig_medias_direc.add_trace(go.Bar(
        name='1º BIMESTRE',
        x=df_medias_direc['DIREC_Truncada'],
        y=df_medias_direc['NOTA 1º BIMESTRE'],
        marker_color='#e6b17e',  # Marrom claro
        text=df_medias_direc['NOTA 1º BIMESTRE'].astype(str),
        textposition='auto',
        customdata=df_medias_direc['DIREC'],  # Passamos a coluna com o nome completo
        hovertemplate='<b>%{customdata}</b><br>1º Bimestre: %{y}<extra></extra>'
    ))

    fig_medias_direc.add_trace(go.Bar(
        name='2º BIMESTRE',
        x=df_medias_direc['DIREC_Truncada'],
        y=df_medias_direc['NOTA 2º BIMESTRE'],
        marker_color='#d39c6b',  # Marrom médio
        text=df_medias_direc['NOTA 2º BIMESTRE'].astype(str),
        textposition='auto',
        customdata=df_medias_direc['DIREC'],  # Passamos a coluna com o nome completo
        hovertemplate='<b>%{customdata}</b><br>1º Bimestre: %{y}<extra></extra>'
    ))

    fig_medias_direc.add_trace(go.Bar(
        name='MÉDIA FINAL',
        x=df_medias_direc['DIREC_Truncada'],
        y=df_medias_direc['MEDIA_1_2_BIM'],
        marker_color='#cc8a42',  # Marrom especificado
        text=df_medias_direc['MEDIA_1_2_BIM'].astype(str),
        textposition='auto',
        customdata=df_medias_direc['DIREC'],  # Passamos a coluna com o nome completo
        hovertemplate='<b>%{customdata}</b><br>1º Bimestre: %{y}<extra></extra>'
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
            'Média 1º Bimestre': df_medias_direc['NOTA 1º BIMESTRE'],
            'Média 2º Bimestre': df_medias_direc['NOTA 2º BIMESTRE'],
            'Média Final': df_medias_direc['MEDIA_1_2_BIM']
        })
        
        # Estilizar a tabela
        st.dataframe(
            df_display_direc,
            width='stretch',
            hide_index=True,
            column_config={
                'Média 1º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                'Média 2º Bimestre': st.column_config.NumberColumn(format='%.2f'),
                'Média 1º Semestre': st.column_config.NumberColumn(format='%.2f')
            }
        )













































