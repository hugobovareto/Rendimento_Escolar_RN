# Importação das bibliotecas
import streamlit as st
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go

# 🔄 COMPARTILHAR DADOS ENTRE PÁGINAS
@st.cache_data
def carregar_dados_estudantes():
     return pd.read_parquet('dados_tratados/df_estudantes.parquet')

# CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Aprovações e Risco de Reprovações dos Estudantes", layout="wide")

# Carregar dados se não estiverem em cache
if 'df' not in st.session_state:
    st.session_state.df_estudantes = carregar_dados_estudantes()

# Acessar dados
df = st.session_state.df_estudantes

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
                                                    # 3. Aprovação e Risco de Reprovação por estudante
# Imagem do cabeçalho
st.image("images/logos.png", width=1700)

st.write("")

st.title("📃 Aprovações e Risco de Reprovações dos Estudantes")

st.markdown("""
**⏱️ Última atualização**:  dados extraídos do SIGEduc em 11/12/2025.
""")

st.write("")

st.markdown("""
            O estudante é considerado em risco de reprovação se possui média inferior a 6.0 de acordo com a etapa de ensino:
- **Ensino Fundamental:** 4 ou mais componentes curriculares com nota inferior a 6.0.
- **Ensino Médio:** 7 ou mais componentes curriculares com nota inferior a 6.0.
            \n São consideradas as notas para o 1º, 2º e 3º bimestres de 2025. Caso alguma nota ainda não tenho sido lançada, a média é feita considerando somente as notas disponíveis.
            """)

st.write("")


# GRÁFICO 1: APROVAÇÕES E RISCO DE REPROVAÇÕES GERAL
# GERAL: APROVAÇÕES E RISCO DE REPROVAÇÕES
# Adicionar filtros para esta análise
col1, col2 = st.columns(2)

with col1:
    # Filtro para ETAPA_RESUMIDA
    if 'ETAPA_RESUMIDA' in df_filtered.columns:
        etapas_options = ['Todas'] + sorted(df_filtered['ETAPA_RESUMIDA'].dropna().unique().tolist())
        etapa_selecionada = st.selectbox(
            "Selecione a Etapa:",
            options=etapas_options,
            key="filtro_etapa_estudante"
        )
    else:
        st.error("Coluna 'ETAPA_RESUMIDA' não encontrada.")
        etapa_selecionada = 'Todas'

with col2:
    # Filtro para SÉRIE
    if 'SÉRIE' in df_filtered.columns:
        series_options = ['Todas'] + sorted(df_filtered['SÉRIE'].dropna().unique().tolist())
        serie_selecionada = st.selectbox(
            "Selecione a Série:",
            options=series_options,
            key="filtro_serie_estudante"
        )
    else:
        st.error("Coluna 'SÉRIE' não encontrada.")
        serie_selecionada = 'Todas'

# Aplicar filtros
df_filtrado_estudante = df_filtered.copy()

if etapa_selecionada != 'Todas':
    df_filtrado_estudante = df_filtrado_estudante[df_filtrado_estudante['ETAPA_RESUMIDA'] == etapa_selecionada]

if serie_selecionada != 'Todas':
    df_filtrado_estudante = df_filtrado_estudante[df_filtrado_estudante['SÉRIE'] == serie_selecionada]

# Verificar se há dados após os filtros
if df_filtrado_estudante.empty:
    st.warning("Não há dados disponíveis para os filtros selecionados.")
else:
    
    # CALCULAR TOTAIS DIRETAMENTE DO DATAFRAME AGRUPADO
    total_aprovados = df_filtrado_estudante['Aprovados'].sum()
    total_reprovados = df_filtrado_estudante['Reprovados'].sum()
    total_estudantes = total_aprovados + total_reprovados

    # Calcular percentuais
    percentual_aprovados = round(total_aprovados / total_estudantes * 100, 2) if total_estudantes > 0 else 0
    percentual_reprovados = round(total_reprovados / total_estudantes * 100, 2) if total_estudantes > 0 else 0

    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Estudantes", f"{total_estudantes:,.0f}")

    with col2:
        st.metric("Aprovados", f"{total_aprovados:,}")

    with col3:
        st.metric("Risco de Reprovação", f"{total_reprovados:,}")

    with col4:
        st.metric("Taxa de Aprovação", f"{percentual_aprovados}%")

    # Criar gráfico de pizza
    fig_pizza = go.Figure()

    fig_pizza.add_trace(go.Pie(
        labels=['Aprovados', 'Risco de Reprovação'],
        values=[total_aprovados, total_reprovados],
        hole=0.4,
        marker=dict(colors=['#2e7d32', '#c62828']),
        textinfo='percent+label+value',
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
    ))

    fig_pizza.update_layout(
        title='Distribuição de Aprovações e Risco de Reprovações',
        height=500,
        showlegend=False
    )

    st.plotly_chart(fig_pizza, use_container_width=True)

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


st.write("")
st.write("")

# GRÁFICO 2: PERCENTUAL DE APROVAÇÕES E RISCO DE REPROVAÇÕES POR DIREC
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Percentual de Aprovações e Risco de Reprovações por DIREC</p>",
    unsafe_allow_html=True
)

# Adicionar filtros para este gráfico
col_filtro1, col_filtro2 = st.columns(2)

with col_filtro1:
    # Filtro para ETAPA_RESUMIDA
    if 'ETAPA_RESUMIDA' in df_filtered.columns:
        etapas_options = ['Todas'] + sorted(df_filtered['ETAPA_RESUMIDA'].dropna().unique().tolist())
        etapa_selecionada = st.selectbox(
            "Selecione a Etapa:",
            options=etapas_options,
            key="filtro_etapa_direc_aprov"
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
            key="filtro_serie_direc_aprov"
        )
    else:
        st.error("Coluna 'SÉRIE' não encontrada.")
        serie_selecionada = 'Todas'

# Aplicar filtros
df_filtrado_direc = df_filtered.copy()

if etapa_selecionada != 'Todas':
    df_filtrado_direc = df_filtrado_direc[df_filtrado_direc['ETAPA_RESUMIDA'] == etapa_selecionada]

if serie_selecionada != 'Todas':
    df_filtrado_direc = df_filtrado_direc[df_filtrado_direc['SÉRIE'] == serie_selecionada]

# Agrupar por DIREC e calcular totais
situacao_por_direc = df_filtrado_direc.groupby('DIREC').agg({
    'Aprovados': 'sum',
    'Reprovados': 'sum'
}).reset_index()

# Calcular totais e percentuais
situacao_por_direc['Total_Estudantes'] = situacao_por_direc['Aprovados'] + situacao_por_direc['Reprovados']
situacao_por_direc['%_Aprovados'] = (situacao_por_direc['Aprovados'] / situacao_por_direc['Total_Estudantes'] * 100).round(1)
situacao_por_direc['%_Reprovados'] = (situacao_por_direc['Reprovados'] / situacao_por_direc['Total_Estudantes'] * 100).round(1)

# Ordenar as DIRECs em ordem decrescente de reprovações (maiores reprovações primeiro)
situacao_por_direc = situacao_por_direc.sort_values('%_Reprovados', ascending=False)

# Truncar nomes das DIRECs para 9 caracteres
situacao_por_direc['DIREC_Truncada'] = situacao_por_direc['DIREC'].astype(str).str.slice(0, 9)

# Verificar se há dados após os filtros
if situacao_por_direc.empty:
    st.warning("Não há dados disponíveis para os filtros selecionados.")
else:
    # Criar gráfico de barras empilhadas
    fig_direc = go.Figure()

    # Barra de aprovados (verde)
    fig_direc.add_trace(go.Bar(
        name='✅ Aprovados',
        x=situacao_por_direc['DIREC_Truncada'],
        y=situacao_por_direc['%_Aprovados'],
        marker=dict(color='#2e7d32'),
        text=situacao_por_direc['%_Aprovados'].astype(str) + '%',
        textposition='inside',
        hovertemplate='<b>%{customdata}</b><br>Aprovados: %{y}%<br>Total: ' + situacao_por_direc['Aprovados'].astype(str) + '<extra></extra>',
        customdata=situacao_por_direc['DIREC']
    ))

    # Barra de reprovados (vermelho)
    fig_direc.add_trace(go.Bar(
        name='❌ Risco de Reprovação',
        x=situacao_por_direc['DIREC_Truncada'],
        y=situacao_por_direc['%_Reprovados'],
        marker=dict(color='#c62828'),
        text=situacao_por_direc['%_Reprovados'].astype(str) + '%',
        textposition='inside',
        hovertemplate='<b>%{customdata}</b><br>Risco de Reprovação: %{y}%<br>Total: ' + situacao_por_direc['Reprovados'].astype(str) + '<extra></extra>',
        customdata=situacao_por_direc['DIREC']
    ))

    # Configurar layout
    fig_direc.update_layout(
        title='Percentual de Aprovações e Risco de Reprovações por DIREC',
        xaxis_title='DIREC',
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
    fig_direc.update_xaxes(
        tickangle=-45,
        tickmode='array',
        tickvals=situacao_por_direc['DIREC_Truncada'],
        ticktext=situacao_por_direc['DIREC_Truncada']
    )

    # Ajustar eixo Y para ir de 0% a 100%
    fig_direc.update_yaxes(range=[0, 100])

    # Exibir gráfico
    st.plotly_chart(fig_direc, use_container_width=True)

    # Mostrar tabela com dados detalhados
    with st.expander("📋 Ver Dados Detalhados por DIREC"):
        # Criar DataFrame de exibição
        df_display_direc = pd.DataFrame({
            'DIREC': situacao_por_direc['DIREC'],
            'Total de Estudantes': situacao_por_direc['Total_Estudantes'],
            'Aprovados': situacao_por_direc['Aprovados'],
            'Risco de Reprovação': situacao_por_direc['Reprovados'],
            '% Aprovados': situacao_por_direc['%_Aprovados'].astype(str) + ' %',
            '% Risco de Reprovação': situacao_por_direc['%_Reprovados'].astype(str) + ' %'
        })
        
        # Estilizar a tabela
        st.dataframe(
            df_display_direc,
            width='stretch',
            hide_index=True,
            column_config={
                'Total de Estudantes': st.column_config.NumberColumn(format='%d'),
                'Aprovados': st.column_config.NumberColumn(format='%d'),
                'Risco de Reprovação': st.column_config.NumberColumn(format='%d')
            }
        )

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

st.write("")
st.write("")

# GRÁFICO 3: PERCENTUAL DE APROVAÇÕES E RISCO DE REPROVAÇÕES POR ANO/SÉRIE ESCOLAR
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Percentual de Aprovações e Risco de Reprovações por Ano/Série Escolar</p>",
    unsafe_allow_html=True
)

# Agrupar por Série e calcular totais
situacao_por_serie = df_filtered.groupby('SÉRIE').agg({
    'Aprovados': 'sum',
    'Reprovados': 'sum'
}).reset_index()

# Calcular totais e percentuais
situacao_por_serie['Total_Estudantes'] = situacao_por_serie['Aprovados'] + situacao_por_serie['Reprovados']
situacao_por_serie['%_Aprovados'] = (situacao_por_serie['Aprovados'] / situacao_por_serie['Total_Estudantes'] * 100).round(1)
situacao_por_serie['%_Reprovados'] = (situacao_por_serie['Reprovados'] / situacao_por_serie['Total_Estudantes'] * 100).round(1)

# Ordenar as séries de forma lógica
try:
    situacao_por_serie['SERIE_ORDENADA'] = pd.Categorical(
        situacao_por_serie['SÉRIE'], 
        categories=sorted(situacao_por_serie['SÉRIE'].unique(), key=lambda x: (float(x.split()[0]) if x.split()[0].isdigit() else float('inf'), x)),
        ordered=True
    )
    situacao_por_serie = situacao_por_serie.sort_values('SERIE_ORDENADA')
except:
    situacao_por_serie = situacao_por_serie.sort_values('SÉRIE')

# Criar gráfico de barras empilhadas
fig_serie = go.Figure()

# Barra de aprovados (verde)
fig_serie.add_trace(go.Bar(
    name='✅ Aprovados',
    x=situacao_por_serie['SÉRIE'],
    y=situacao_por_serie['%_Aprovados'],
    marker=dict(color='#2e7d32'),
    text=situacao_por_serie['%_Aprovados'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Aprovados: %{y}%<br>Total: ' + situacao_por_serie['Aprovados'].astype(str) + '<extra></extra>'
))

# Barra de reprovados (vermelho)
fig_serie.add_trace(go.Bar(
    name='❌ Risco de Reprovação',
    x=situacao_por_serie['SÉRIE'],
    y=situacao_por_serie['%_Reprovados'],
    marker=dict(color='#c62828'),
    text=situacao_por_serie['%_Reprovados'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Risco de Reprovação: %{y}%<br>Total: ' + situacao_por_serie['Reprovados'].astype(str) + '<extra></extra>'
))

# Configurar layout
fig_serie.update_layout(
    title='Percentual de Aprovações e Risco de Reprovações por Série',
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

# Rodar labels do eixo X se necessário
fig_serie.update_xaxes(tickangle=-45)

# Ajustar eixo Y para ir de 0% a 100%
fig_serie.update_yaxes(range=[0, 100])

# Exibir gráfico
st.plotly_chart(fig_serie, use_container_width=True)

# Mostrar tabela com dados detalhados
with st.expander("📋 Ver Dados Detalhados por Série"):
    # Criar DataFrame de exibição
    df_display_serie = pd.DataFrame({
        'Série': situacao_por_serie['SÉRIE'],
        'Total de Estudantes': situacao_por_serie['Total_Estudantes'],
        'Aprovados': situacao_por_serie['Aprovados'],
        'Risco de Reprovações': situacao_por_serie['Reprovados'],
        '% Aprovados': situacao_por_serie['%_Aprovados'].astype(str) + ' %',
        '% Risco de Reprovações': situacao_por_serie['%_Reprovados'].astype(str) + ' %'
    })
    
    # Estilizar a tabela
    st.dataframe(
        df_display_serie,
        width='stretch',
        hide_index=True,
        column_config={
            'Total de Estudantes': st.column_config.NumberColumn(format='%d'),
            'Aprovados': st.column_config.NumberColumn(format='%d'),
            'Risco de Reprovações': st.column_config.NumberColumn(format='%d')
        }
    )






