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
st.set_page_config(page_title="Lançamento de Notas", layout="wide")

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

                                                    # 1. Lançamento de Notas
# Imagem do cabeçalho
st.image("images/logos.png", width=1700)

st.write("")

st.title("📈 Lançamento de Notas")

st.markdown("""
**⏱️ Última atualização**:  dados extraídos do SIGEduc em 10/10/2025.
""")


st.write("")

# Calcular contagem_nan primeiro
notas_bimestres = ['NOTA 1º BIMESTRE', 'NOTA 2º BIMESTRE', 'NOTA 3º BIMESTRE']
contagem_nan = {}

for bimestre in notas_bimestres:
    if bimestre in df_filtered.columns:
        contagem_nan[bimestre] = df_filtered[bimestre].isna().sum()
    else:
        contagem_nan[bimestre] = 0  # Caso a coluna não exista

# Calcular os percentuais antes de criar o gráfico
total_registros = len(df_filtered)

# Calcular os percentuais garantindo que estão corretos
perc_1bim = (contagem_nan['NOTA 1º BIMESTRE'] / total_registros * 100).round(1)
perc_2bim = (contagem_nan['NOTA 2º BIMESTRE'] / total_registros * 100).round(1)
perc_3bim = (contagem_nan['NOTA 3º BIMESTRE'] / total_registros * 100).round(1)

# Criar o df_nan com os percentuais calculados
df_nan = pd.DataFrame({
    'Bimestre': ['1º Bimestre', '2º Bimestre', '3º Bimestre'],
    'Notas Faltantes': [
        contagem_nan['NOTA 1º BIMESTRE'], 
        contagem_nan['NOTA 2º BIMESTRE'], 
        contagem_nan['NOTA 3º BIMESTRE']
    ],
    'Percentual': [perc_1bim, perc_2bim, perc_3bim],  # Usando os percentuais já calculados
    'Total de Registros': total_registros  # Adicionando esta coluna
})

# Mostrar métricas detalhadas de notas não lançadas
st.markdown("**❌ Notas Não Lançadas:**")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "1º Bimestre", 
        f"{contagem_nan['NOTA 1º BIMESTRE']:,}", 
        f"{perc_1bim}% faltantes",
        delta_color="inverse"
    )

with col2:
    st.metric(
        "2º Bimestre", 
        f"{contagem_nan['NOTA 2º BIMESTRE']:,}", 
        f"{perc_2bim}% faltantes",
        delta_color="inverse" 
    )

with col3:
    st.metric(
        "3º Bimestre", 
        f"{contagem_nan['NOTA 3º BIMESTRE']:,}", 
        f"{perc_3bim}% faltantes",
        delta_color="inverse"
    )

# Criar o gráfico com Plotly: Notas Não Lançadas
fig = px.bar(
    df_nan,
    x='Bimestre',
    y='Notas Faltantes',
    text='Notas Faltantes',
    title='❌ Quantidade de Notas Não Lançadas por Bimestre',
    color='Bimestre',
    color_discrete_sequence=['#ffcccc', '#ff6666', '#ff0000', '#cc0000', '#990000', '#660000']
)

# Ajustar margens para não cortar as barras
max_valor = df_nan['Notas Faltantes'].max()
fig.update_layout(
    xaxis_title='Bimestre',
    yaxis_title='Quantidade de Notas Faltantes',
    showlegend=False,
    height=500,  
    yaxis=dict(range=[0, max_valor * 1.15]),
    margin=dict(t=50, b=50, l=50, r=50)
)

fig.update_traces(
    textposition='auto',
    textfont_size=12
)

# Exibir o gráfico
st.plotly_chart(fig, use_container_width=True)


# Calcular contagem de Notas Lançadas

# Calcular contagem_lancadas (valores não-NaN)
contagem_lancadas = {}

for bimestre in notas_bimestres:
    if bimestre in df_filtered.columns:
        contagem_lancadas[bimestre] = df_filtered[bimestre].notna().sum()
    else:
        contagem_lancadas[bimestre] = 0

# Calcular os percentuais para notas lançadas
perc_lanc_1bim = (contagem_lancadas['NOTA 1º BIMESTRE'] / total_registros * 100).round(1)
perc_lanc_2bim = (contagem_lancadas['NOTA 2º BIMESTRE'] / total_registros * 100).round(1)
perc_lanc_3bim = (contagem_lancadas['NOTA 3º BIMESTRE'] / total_registros * 100).round(1)

# Criar o df_lancadas com os percentuais calculados
df_lancadas = pd.DataFrame({
    'Bimestre': ['1º Bimestre', '2º Bimestre', '3º Bimestre'],
    'Notas Lançadas': [
        contagem_lancadas['NOTA 1º BIMESTRE'], 
        contagem_lancadas['NOTA 2º BIMESTRE'], 
        contagem_lancadas['NOTA 3º BIMESTRE']
    ],
    'Percentual': [perc_lanc_1bim, perc_lanc_2bim, perc_lanc_3bim],
    'Total de Registros': total_registros
})

st.write("")

# Mostrar métricas detalhadas de notas lançadas
st.markdown("**✅ Notas Lançadas:**")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "1º Bimestre", 
        f"{contagem_lancadas['NOTA 1º BIMESTRE']:,}", 
        f"{perc_lanc_1bim}% lançadas"
    )

with col2:
    st.metric(
        "2º Bimestre", 
        f"{contagem_lancadas['NOTA 2º BIMESTRE']:,}", 
        f"{perc_lanc_2bim}% lançadas"
    )

with col3:
    st.metric(
        "3º Bimestre", 
        f"{contagem_lancadas['NOTA 3º BIMESTRE']:,}", 
        f"{perc_lanc_3bim}% lançadas"
    )

# Criar o gráfico com Plotly: Notas Lançadas
fig_lancadas = px.bar(
    df_lancadas,
    x='Bimestre',
    y='Notas Lançadas',
    text='Notas Lançadas',
    title='✅ Quantidade de Notas Lançadas por Bimestre',
    color='Bimestre',
    color_discrete_sequence=['#1b5e20', '#2e7d32', '#388e3c', '#4caf50', '#66bb6a', '#81c784', '#a5d6a7', '#c8e6c9', '#e8f5e8']  # Tons de verde
)

# Ajustar margens para não cortar as barras
max_valor_lancadas = df_lancadas['Notas Lançadas'].max()
fig_lancadas.update_layout(
    xaxis_title='Bimestre',
    yaxis_title='Quantidade de Notas Lançadas',
    showlegend=False,
    height=500,  
    yaxis=dict(range=[0, max_valor_lancadas * 1.15]),
    margin=dict(t=50, b=50, l=50, r=50)
)

fig_lancadas.update_traces(
    textposition='auto',
    textfont_size=12
)

# Exibir o gráfico de notas lançadas
st.plotly_chart(fig_lancadas, use_container_width=True)

st.write("")
st.write("")

# Percentual de Notas Lançadas e Não Lançadas por DIREC (para 1º e 2º bimestres)
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Percentual de Notas Lançadas e Não Lançadas por DIREC</p>",
    unsafe_allow_html=True)

st.markdown("1️⃣ _1º Bimestre:_")

# Calcular totais por DIREC para o 1º bimestre
df_direc_1bim = df_filtered.groupby('DIREC').agg({
    'NOTA 1º BIMESTRE': [
        ('Total_Registros', 'size'),
        ('Lançadas', lambda x: x.notna().sum()),
        ('Não_Lançadas', lambda x: x.isna().sum())
    ]
}).round(0)

# Reformatar o DataFrame
df_direc_1bim.columns = df_direc_1bim.columns.droplevel(0)
df_direc_1bim = df_direc_1bim.reset_index()

# Calcular percentuais
df_direc_1bim['%_Lançadas'] = (df_direc_1bim['Lançadas'] / df_direc_1bim['Total_Registros'] * 100).round(1)
df_direc_1bim['%_Não_Lançadas'] = (df_direc_1bim['Não_Lançadas'] / df_direc_1bim['Total_Registros'] * 100).round(1)

# Ordenar por nome da DIREC (ordem alfabética crescente)
df_direc_1bim = df_direc_1bim.sort_values('DIREC', ascending=True)

# Truncar nomes das DIRECs para 9 primeiros caracteres (apenas nº da DIREC)
df_direc_1bim['DIREC_Truncada'] = df_direc_1bim['DIREC'].str.slice(0, 9)

# Criar gráfico de barras empilhadas VERTICAIS
fig_direc_1bim = go.Figure()

# Barra de notas lançadas (verde)
fig_direc_1bim.add_trace(go.Bar(
    name='✅ Notas Lançadas',
    x=df_direc_1bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_1bim['%_Lançadas'],
    marker=dict(color='#2e7d32'),
    text=df_direc_1bim['%_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Lançadas: %{y}%<br>Total: ' + df_direc_1bim['Lançadas'].astype(str) + '<extra></extra>'
))

# Barra de notas não lançadas (vermelho)
fig_direc_1bim.add_trace(go.Bar(
    name='❌ Notas Não Lançadas',
    x=df_direc_1bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_1bim['%_Não_Lançadas'],
    marker=dict(color='#c62828'),
    text=df_direc_1bim['%_Não_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Não Lançadas: %{y}%<br>Total: ' + df_direc_1bim['Não_Lançadas'].astype(str) + '<extra></extra>'
))

# Configurar layout
fig_direc_1bim.update_layout(
    title='1º Bimestre: Percentual de Notas Lançadas vs Não Lançadas por DIREC',
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
    margin=dict(t=80, b=100, l=50, r=50)  # Aumentar margem inferior para caber labels
)

# Rodar labels do eixo X em 45 graus e ajustar
fig_direc_1bim.update_xaxes(
    tickangle=-45,
    tickmode='array',
    tickvals=df_direc_1bim['DIREC_Truncada'],
    ticktext=df_direc_1bim['DIREC_Truncada']
)

# Ajustar eixo Y para ir de 0% a 100%
fig_direc_1bim.update_yaxes(range=[0, 100])

# Exibir gráfico
st.plotly_chart(fig_direc_1bim, use_container_width=True)


# Mostrar tabela com dados detalhados e formatação
with st.expander("📋 Ver Dados Detalhados por DIREC"):
    # Criar DataFrame de exibição
    df_display = pd.DataFrame({
        'DIREC': df_direc_1bim['DIREC'],
        'Total de Registros': df_direc_1bim['Total_Registros'],
        'Notas Lançadas': df_direc_1bim['Lançadas'],
        'Notas Não Lançadas': df_direc_1bim['Não_Lançadas'],
        '% Lançadas': df_direc_1bim['%_Lançadas'].astype(str) + ' %',
        '% Não Lançadas': df_direc_1bim['%_Não_Lançadas'].astype(str) + ' %'
    })
    
    # Estilizar a tabela (opcional)
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Total de Registros': st.column_config.NumberColumn(format='%d'),
            'Notas Lançadas': st.column_config.NumberColumn(format='%d'),
            'Notas Não Lançadas': st.column_config.NumberColumn(format='%d')
        })
    

st.write("")
st.markdown("2️⃣ _2º Bimestre:_")

# Calcular totais por DIREC para o 1º bimestre
df_direc_2bim = df_filtered.groupby('DIREC').agg({
    'NOTA 2º BIMESTRE': [
        ('Total_Registros', 'size'),
        ('Lançadas', lambda x: x.notna().sum()),
        ('Não_Lançadas', lambda x: x.isna().sum())
    ]
}).round(0)

# Reformatar o DataFrame
df_direc_2bim.columns = df_direc_2bim.columns.droplevel(0)
df_direc_2bim = df_direc_2bim.reset_index()

# Calcular percentuais
df_direc_2bim['%_Lançadas'] = (df_direc_2bim['Lançadas'] / df_direc_2bim['Total_Registros'] * 100).round(1)
df_direc_2bim['%_Não_Lançadas'] = (df_direc_2bim['Não_Lançadas'] / df_direc_2bim['Total_Registros'] * 100).round(1)

# Ordenar por nome da DIREC (ordem alfabética crescente)
df_direc_2bim = df_direc_2bim.sort_values('DIREC', ascending=True)

# Truncar nomes das DIRECs para 9 primeiros caracteres (apenas nº da DIREC)
df_direc_2bim['DIREC_Truncada'] = df_direc_2bim['DIREC'].str.slice(0, 9)

# Criar gráfico de barras empilhadas VERTICAIS
fig_direc_2bim = go.Figure()

# Barra de notas lançadas (verde)
fig_direc_2bim.add_trace(go.Bar(
    name='✅ Notas Lançadas',
    x=df_direc_2bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_2bim['%_Lançadas'],
    marker=dict(color='#2e7d32'),
    text=df_direc_2bim['%_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Lançadas: %{y}%<br>Total: ' + df_direc_2bim['Lançadas'].astype(str) + '<extra></extra>'
))

# Barra de notas não lançadas (vermelho)
fig_direc_2bim.add_trace(go.Bar(
    name='❌ Notas Não Lançadas',
    x=df_direc_2bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_2bim['%_Não_Lançadas'],
    marker=dict(color='#c62828'),
    text=df_direc_2bim['%_Não_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Não Lançadas: %{y}%<br>Total: ' + df_direc_2bim['Não_Lançadas'].astype(str) + '<extra></extra>'
))

# Configurar layout
fig_direc_2bim.update_layout(
    title='2º Bimestre: Percentual de Notas Lançadas vs Não Lançadas por DIREC',
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
    margin=dict(t=80, b=100, l=50, r=50)  # Aumentar margem inferior para caber labels
)

# Rodar labels do eixo X em 45 graus e ajustar
fig_direc_2bim.update_xaxes(
    tickangle=-45,
    tickmode='array',
    tickvals=df_direc_1bim['DIREC_Truncada'],
    ticktext=df_direc_1bim['DIREC_Truncada']
)

# Ajustar eixo Y para ir de 0% a 100%
fig_direc_2bim.update_yaxes(range=[0, 100])

# Exibir gráfico
st.plotly_chart(fig_direc_2bim, use_container_width=True)


# Mostrar tabela com dados detalhados e formatação
with st.expander("📋 Ver Dados Detalhados por DIREC"):
    # Criar DataFrame de exibição
    df_display = pd.DataFrame({
        'DIREC': df_direc_2bim['DIREC'],
        'Total de Registros': df_direc_2bim['Total_Registros'],
        'Notas Lançadas': df_direc_2bim['Lançadas'],
        'Notas Não Lançadas': df_direc_2bim['Não_Lançadas'],
        '% Lançadas': df_direc_2bim['%_Lançadas'].astype(str) + ' %',
        '% Não Lançadas': df_direc_2bim['%_Não_Lançadas'].astype(str) + ' %'
    })
    
    # Estilizar a tabela (opcional)
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Total de Registros': st.column_config.NumberColumn(format='%d'),
            'Notas Lançadas': st.column_config.NumberColumn(format='%d'),
            'Notas Não Lançadas': st.column_config.NumberColumn(format='%d')
        })


st.write("")
st.markdown("3️⃣ _3º Bimestre:_")

# Calcular totais por DIREC para o 1º bimestre
df_direc_3bim = df_filtered.groupby('DIREC').agg({
    'NOTA 3º BIMESTRE': [
        ('Total_Registros', 'size'),
        ('Lançadas', lambda x: x.notna().sum()),
        ('Não_Lançadas', lambda x: x.isna().sum())
    ]
}).round(0)

# Reformatar o DataFrame
df_direc_3bim.columns = df_direc_3bim.columns.droplevel(0)
df_direc_3bim = df_direc_3bim.reset_index()

# Calcular percentuais
df_direc_3bim['%_Lançadas'] = (df_direc_3bim['Lançadas'] / df_direc_3bim['Total_Registros'] * 100).round(1)
df_direc_3bim['%_Não_Lançadas'] = (df_direc_3bim['Não_Lançadas'] / df_direc_3bim['Total_Registros'] * 100).round(1)

# Ordenar por nome da DIREC (ordem alfabética crescente)
df_direc_3bim = df_direc_3bim.sort_values('DIREC', ascending=True)

# Truncar nomes das DIRECs para 9 primeiros caracteres (apenas nº da DIREC)
df_direc_3bim['DIREC_Truncada'] = df_direc_3bim['DIREC'].str.slice(0, 9)

# Criar gráfico de barras empilhadas VERTICAIS
fig_direc_3bim = go.Figure()

# Barra de notas lançadas (verde)
fig_direc_3bim.add_trace(go.Bar(
    name='✅ Notas Lançadas',
    x=df_direc_3bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_3bim['%_Lançadas'],
    marker=dict(color='#2e7d32'),
    text=df_direc_3bim['%_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Lançadas: %{y}%<br>Total: ' + df_direc_3bim['Lançadas'].astype(str) + '<extra></extra>'
))

# Barra de notas não lançadas (vermelho)
fig_direc_3bim.add_trace(go.Bar(
    name='❌ Notas Não Lançadas',
    x=df_direc_3bim['DIREC_Truncada'],  # Eixo X com nomes truncados
    y=df_direc_3bim['%_Não_Lançadas'],
    marker=dict(color='#c62828'),
    text=df_direc_3bim['%_Não_Lançadas'].astype(str) + '%',
    textposition='inside',
    hovertemplate='<b>%{x}</b><br>Notas Não Lançadas: %{y}%<br>Total: ' + df_direc_3bim['Não_Lançadas'].astype(str) + '<extra></extra>'
))

# Configurar layout
fig_direc_3bim.update_layout(
    title='3º Bimestre: Percentual de Notas Lançadas vs Não Lançadas por DIREC',
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
    margin=dict(t=80, b=100, l=50, r=50)  # Aumentar margem inferior para caber labels
)

# Rodar labels do eixo X em 45 graus e ajustar
fig_direc_3bim.update_xaxes(
    tickangle=-45,
    tickmode='array',
    tickvals=df_direc_1bim['DIREC_Truncada'],
    ticktext=df_direc_1bim['DIREC_Truncada']
)

# Ajustar eixo Y para ir de 0% a 100%
fig_direc_3bim.update_yaxes(range=[0, 100])

# Exibir gráfico
st.plotly_chart(fig_direc_3bim, use_container_width=True)


# Mostrar tabela com dados detalhados e formatação
with st.expander("📋 Ver Dados Detalhados por DIREC"):
    # Criar DataFrame de exibição
    df_display = pd.DataFrame({
        'DIREC': df_direc_3bim['DIREC'],
        'Total de Registros': df_direc_3bim['Total_Registros'],
        'Notas Lançadas': df_direc_3bim['Lançadas'],
        'Notas Não Lançadas': df_direc_3bim['Não_Lançadas'],
        '% Lançadas': df_direc_3bim['%_Lançadas'].astype(str) + ' %',
        '% Não Lançadas': df_direc_3bim['%_Não_Lançadas'].astype(str) + ' %'
    })
    
    # Estilizar a tabela (opcional)
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Total de Registros': st.column_config.NumberColumn(format='%d'),
            'Notas Lançadas': st.column_config.NumberColumn(format='%d'),
            'Notas Não Lançadas': st.column_config.NumberColumn(format='%d')
        })

st.write("")
st.write("")

# Escolas maiores percentuais de notas não lançadas
st.markdown(
    "<p style='font-size:24px; font-weight:bold;'>Escolas com maiores percentuais de notas não lançadas</p>",
    unsafe_allow_html=True)


# Calcular de forma incremental para evitar sobrecarga
try:
    # Primeiro: obter lista de escolas únicas
    escolas = df_filtered[['INEP ESCOLA', 'ESCOLA', 'DIREC', 'MUNICÍPIO']].drop_duplicates()
    
    # Inicializar lista para resultados
    resultados = []
    
    # Calcular para cada escola individualmente (mais lento mas seguro)
    for idx, escola in escolas.iterrows():
        inep = escola['INEP ESCOLA']
        
        # Filtrar dados apenas para esta escola
        df_escola = df_filtered[df_filtered['INEP ESCOLA'] == inep]
        
        # Calcular percentuais
        total = len(df_escola)
        nan_1bim = df_escola['NOTA 1º BIMESTRE'].isna().sum() if 'NOTA 1º BIMESTRE' in df_escola.columns else 0
        nan_2bim = df_escola['NOTA 2º BIMESTRE'].isna().sum() if 'NOTA 2º BIMESTRE' in df_escola.columns else 0
        nan_3bim = df_escola['NOTA 3º BIMESTRE'].isna().sum() if 'NOTA 3º BIMESTRE' in df_escola.columns else 0
        
        perc_1bim = (nan_1bim / total * 100).round(1) if total > 0 else 0
        perc_2bim = (nan_2bim / total * 100).round(1) if total > 0 else 0
        perc_3bim = (nan_3bim / total * 100).round(1) if total > 0 else 0
        
        # Formatar nome da escola
        escola_formatada = f"{escola['ESCOLA']} (cód. Inep: {inep})"
        
        resultados.append({
            'DIREC': escola['DIREC'],
            'Município': escola['MUNICÍPIO'],
            'Escola': escola_formatada,
            '% Notas Não Lançadas - 1º Bimestre': perc_1bim,
            '% Notas Não Lançadas - 2º Bimestre': perc_2bim,
            '% Notas Não Lançadas - 3º Bimestre': perc_3bim
        })
    
    # Converter para DataFrame
    df_tabela_final = pd.DataFrame(resultados)
    
    # Criar duas colunas para os controles
    col_ordenacao, col_paginacao = st.columns([3, 1])  # 3/4 para ordenação, 1/4 para paginação
    
    with col_ordenacao:
        # Ordenação interativa
        col_ordenacao = st.selectbox(
            "Ordenar por:",
            options=[
                '% Notas Não Lançadas - 1º Bimestre',
                '% Notas Não Lançadas - 2º Bimestre', 
                '% Notas Não Lançadas - 3º Bimestre'
            ],
            index=1
        )

    with col_paginacao:
        # Paginação
        itens_por_pagina = 10
        total_itens = len(df_tabela_final)
        total_paginas = max(1, (total_itens + itens_por_pagina - 1) // itens_por_pagina)
        
        # Seletor de página
        pagina_atual = st.number_input(
            f'Página (1 a {total_paginas})', 
            min_value=1, 
            max_value=total_paginas, 
            value=1
        )

    # Ordenar
    df_tabela_final = df_tabela_final.sort_values(col_ordenacao, ascending=False)
    
    # Calcular índices para paginação
    inicio_idx = (pagina_atual - 1) * itens_por_pagina
    fim_idx = min(inicio_idx + itens_por_pagina, total_itens)
    df_pagina_atual = df_tabela_final.iloc[inicio_idx:fim_idx]
    
    st.write(f"Mostrando escolas {inicio_idx + 1} a {fim_idx} de {total_itens}")
    
    # Mostrar tabela
    st.dataframe(
        df_pagina_atual,
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error(f"Erro crítico: {e}")
    st.info("Tente usar filtros mais restritivos para reduzir a quantidade de dados.")





