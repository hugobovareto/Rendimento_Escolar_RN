# Importação das bibliotecas
import pandas as pd
import glob
import os
from tqdm import tqdm  # Para barra de progresso
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def processar_dados_brutos():
    # caminho da pasta onde estão os arquivos
    pasta = r"C:\Users\hugob\Downloads\Notas"

    # lista todos os arquivos .xlsx da pasta
    arquivos = glob.glob(os.path.join(pasta, "*.xlsx"))

    # lista para armazenar os dataframes
    dfs = []

    for arquivo in tqdm(arquivos, desc="Processando arquivos"):
        # lê cada arquivo, pulando as 2 primeiras linhas
        df_unico = pd.read_excel(arquivo, skiprows=2)
        dfs.append(df_unico)

    # concatena todos em um único dataframe
    df = pd.concat(dfs, ignore_index=True)


    # Excluir colunas que não são de interesse
    df = df.drop(columns=['ID DIREC', 'ID MUNICÍPIO', 'ID ESCOLA', 'ID ETAPA ENSINO', 'PERIODICIDADE ETAPA ENSINO', 'ID SÉRIE', 'ID TURMA', 'TURMA', 'TURNO', 'ID PESSOA (PROFESSOR)', 'MATRICULA (PROFESSOR)', 'VÍNCULO', 'NOME DO PROFESSOR', 'DATA INÍCIO ALOCAÇÃO', 'DATA FIM ALOCAÇÃO', 'ID COMPONENTE CURRICULAR', 'PERIODICIDADE COMPONENTE CURRICULAR', 'ID PESSOA', 'MATRÍCULA ESTUDANTE', 'RESULTADO FINAL', 'APROVEITAMENTO DE ESTUDO'])

    # Substituir vírgula por ponto para reconhecimento das notas como números:
    colunas_para_converter = [
        "NOTA 1º BIMESTRE",
        "NOTA 2º BIMESTRE",
        "NOTA 3º BIMESTRE",
        "NOTA 4º BIMESTRE",
        "MÉDIA ANUAL",
        "EXAME FINAL",
        "AVALIAÇÃO ESPECIAL",
        "MÉDIA FINAL"
    ] 

    for col in colunas_para_converter:
        if col in df.columns:  # só executa se a coluna estiver no DataFrame
            # Substitui vírgula por ponto
            df[col] = df[col].str.replace(",", ".")
            # Converte para float, erros viram NaN
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Manter só Anos Finais e Ensino Médio:
    valores_desejados = ['1ª SÉRIE',
                        '2ª SÉRIE',
                        '3ª SÉRIE',
                        '6º Ano',
                        '7º Ano',
                        '8º Ano',
                        '9º Ano',
                        '6º ANO',
                        '7º ANO',
                        '8º ANO',
                        '9º ANO']

    df_EF_EM = df[df['SÉRIE'].isin(valores_desejados)]

    # substituição das séries e manter padronização
    mapeamento = {
        '6º Ano': '6º ANO',
        '7º Ano': '7º ANO',
        '8º Ano': '8º ANO',
        '9º Ano': '9º ANO'
    }

    df_EF_EM['SÉRIE'] = df_EF_EM['SÉRIE'].replace(mapeamento)


    # Manter só componentes da BNCC:
    bncc = ['Arte',
            'Biologia',
            'Educação Física',
            'Filosofia',
            'Física',
            'Geografia',
            'História',
            'Língua Inglesa',
            'Língua Portuguesa',
            'Matemática',
            'Química',
            'Sociologia', 
            'Ciências']
    
    df_EF_EM_bncc = df_EF_EM[df_EF_EM['COMPONENTE CURRICULAR'].isin(bncc)]

    # Criar coluna de "ETAPA_RESUMIDA" para indicar Anos Finais ou Ensino Médio, de acordo com a série
    # (São 46 etapas de ensino na base já filtrada pelas séries dos Anos Finais e Ensino Médio e pelos componentes da BNCC)
    mapeamento_etapa = {
        '1ª SÉRIE': 'Ensino Médio',
        '2ª SÉRIE': 'Ensino Médio',
        '3ª SÉRIE': 'Ensino Médio',
        '6º ANO': 'Ens. Fund. - Anos Finais',
        '7º ANO': 'Ens. Fund. - Anos Finais',
        '8º ANO': 'Ens. Fund. - Anos Finais',
        '9º ANO': 'Ens. Fund. - Anos Finais'
    }

    df_EF_EM_bncc['ETAPA_RESUMIDA'] = df_EF_EM_bncc['SÉRIE'].map(mapeamento_etapa)

    # Criar coluna com nota final média do 1º semestre, considerando as notas do 1º e 2º bimestres:
    # (ignora os valores NaN e fazem a média somente com os valores presentes. Se só tiver 1 nota disponível, a média será essa nota)
    '''
    Se as duas colunas têm valores → média das duas.
    Se apenas uma tem valor → retorna esse valor.
    Se ambas são NaN → retorna NaN.
    '''
    df_EF_EM_bncc['MEDIA_1_2_BIM'] = df_EF_EM_bncc[['NOTA 1º BIMESTRE','NOTA 2º BIMESTRE']].mean(axis=1, skipna=True)

    # Criar uma coluna para Aprovado ou Reprovado por componente (reprovação caso a média seja menor que 6)
                                    ###### MODIFICAR AQUI QUANDO TIVER MAIS NOTAS LANÇADAS ######
    # (sem nota caso os dois bimestres sejam NaN)
    df_EF_EM_bncc['STATUS'] = np.where(
        df_EF_EM_bncc['MEDIA_1_2_BIM'].isna(),           # 1️⃣ caso: sem média
        'Sem nota',
        np.where(
            df_EF_EM_bncc['MEDIA_1_2_BIM'] >= 6,         # 2️⃣ caso: média suficiente
            'Aprovado',
            'Reprovado'                                  # 3️⃣ caso: média < 6
        )
    )

    # Otimizar o DataFrame para reduzir uso de memória
    # Função otimizada para reduzir o uso de memória, com tratamento de erros
    def otimizar_tipos(df):
        """
        Função para otimizar tipos de colunas de um DataFrame.
        
        Procura por colunas de tipo inteiro e float, e as converte para tipos mais eficientes.
        
        Também procura por colunas de tipo string e as converte para tipo category, se houver
        pelo menos 50% de valores únicos.
        
        Caso encontre algum erro durante a conversão, mantém o tipo original da coluna.
        
        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame a ser otimizado.
        
        Returns
        -------
        pandas.DataFrame
            DataFrame com tipos de colunas otimizados.
        """
        df_otimizado = df.copy()
        
        # Inteiros - com verificações extras
        int_cols = df.select_dtypes(include=['int']).columns
        for col in int_cols:
            try:
                if df[col].min() >= 0:  # Só positivos
                    if df[col].max() < 256:  # 0-255
                        df_otimizado[col] = df[col].astype('uint8')
                    elif df[col].max() < 65536:  # 0-65535
                        df_otimizado[col] = df[col].astype('uint16')
                    elif df[col].max() < 4294967296:  # 0-4294967295
                        df_otimizado[col] = df[col].astype('uint32')
                    else:
                        df_otimizado[col] = df[col].astype('uint64')  # Para valores muito grandes
                else:  # Com negativos
                    if df[col].min() >= -128 and df[col].max() < 128:
                        df_otimizado[col] = df[col].astype('int8')
                    elif df[col].min() >= -32768 and df[col].max() < 32768:
                        df_otimizado[col] = df[col].astype('int16')
                    elif df[col].min() >= -2147483648 and df[col].max() < 2147483648:
                        df_otimizado[col] = df[col].astype('int32')
                    else:
                        df_otimizado[col] = df[col].astype('int64')  # Mantém original
                        
            except (ValueError, TypeError) as e:
                print(f"⚠️  Erro na coluna {col}: {e}. Mantendo tipo original.")
                df_otimizado[col] = df[col]  # Mantém original em caso de erro
        
        # Floats (seguro)
        float_cols = df.select_dtypes(include=['float']).columns
        for col in float_cols:
            df_otimizado[col] = df[col].astype('float32')
        
        # Strings → categoria (com threshold ajustável)
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            if df[col].nunique() / len(df) < 0.5:  # Mais conservador: 50% únicos
                try:
                    df_otimizado[col] = df[col].astype('category')
                except Exception as e:
                    print(f"⚠️  Erro convertendo {col} para category: {e}")
        
        return df_otimizado

    # Executar a função de otimização
    df_EF_EM_bncc = otimizar_tipos(df_EF_EM_bncc)


    # Filtrar linhas somente com os CPFs na base dados que foi enviada para o Censo Escolar no dia 28/05
    # Ler o arquivo enviado para o Censo Escolar em 28/05 (em Excel)
    df_censo = pd.read_excel(r"C:\Users\hugob\Downloads\20250528_Censo Escolar_DADOS CONSOLIDADOS.xlsx")

    # Criar uma lista dos CPFs do Excel (Censo 28/05) (garantindo que sejam strings e sem espaços)
    cpf_lista = df_censo["CPF"].astype(str).str.strip().unique()

    # Filtrar o df_EF_EM_bncc mantendo apenas linhas cujo CPF PESSOA esteja na lista
    df_EF_EM_bncc_censo = df_EF_EM_bncc[df_EF_EM_bncc["CPF PESSOA"].astype(str).isin(cpf_lista)]
    
    # =============================================================================
    # CRIAR DF_COMPONENTES
    # =============================================================================

    # colunas usadas para o df_compnoentes
    cols_componentes = ['DIREC','MUNICÍPIO','ESCOLA','INEP ESCOLA','ETAPA_RESUMIDA','SÉRIE','COMPONENTE CURRICULAR',
            'STATUS','NOTA 1º BIMESTRE','NOTA 2º BIMESTRE','MEDIA_1_2_BIM']

    df2_componentes = df_EF_EM_bncc_censo[cols_componentes].copy()

    # Transformar as colunas no tipo 'categoria' para otimizar tipos de dados para memória
    grp_cols_componentes = ['DIREC','MUNICÍPIO','ESCOLA','INEP ESCOLA','ETAPA_RESUMIDA','SÉRIE','COMPONENTE CURRICULAR']
    for c in grp_cols_componentes:
        df2_componentes[c] = df2_componentes[c].astype('category')

    # criar colunas binárias para contagem de aprovados e reprovados
    df2_componentes['is_aprovado'] = df2_componentes['STATUS'].eq('Aprovado').astype('uint8')
    df2_componentes['is_reprovado'] = df2_componentes['STATUS'].eq('Reprovado').astype('uint8')

    # garantir notas numéricas
    df2_componentes['NOTA 1º BIMESTRE'] = pd.to_numeric(df2_componentes['NOTA 1º BIMESTRE'], errors='coerce')
    df2_componentes['NOTA 2º BIMESTRE'] = pd.to_numeric(df2_componentes['NOTA 2º BIMESTRE'], errors='coerce')
    df2_componentes['MEDIA_1_2_BIM'] = pd.to_numeric(df2_componentes['MEDIA_1_2_BIM'], errors='coerce')

    # Agrupar e agregar para fazer o df_componentes
    df_componentes = (
        df2_componentes
        .groupby(grp_cols_componentes, observed=True, sort=False)
        .agg(
            Aprovados=('is_aprovado', 'sum'),
            Reprovados=('is_reprovado', 'sum'),
            NOTA_1_BIMESTRE=('NOTA 1º BIMESTRE', 'mean'),
            NOTA_2_BIMESTRE=('NOTA 2º BIMESTRE', 'mean'),
            MEDIA_1_2_BIM=('MEDIA_1_2_BIM', 'mean')
        )
        .reset_index()
    )


    # =============================================================================
    # CRIAR DF_ESTUDANTES
    # =============================================================================
    # 1) Colunas que vamos usar
    cols_estudantes = ['CPF PESSOA',
            'DIREC','MUNICÍPIO','ESCOLA','INEP ESCOLA',
            'ETAPA_RESUMIDA','SÉRIE','STATUS']

    df2_estudantes = df_EF_EM_bncc_censo[cols_estudantes].copy()

    # 2) Tipos: transformar agrupamentos em category para economizar memória
    grp_cols_estudantes = ['DIREC','MUNICÍPIO','ESCOLA','INEP ESCOLA','ETAPA_RESUMIDA','SÉRIE']
    for c in grp_cols_estudantes:
        df2_estudantes[c] = df2_estudantes[c].astype('category')

    # 3) Coluna binária de reprovação por registro (0/1)
    df2_estudantes['is_reprovado'] = (df2_estudantes['STATUS'] == 'Reprovado').astype('uint8')

    # 4) Agregar por estudante + escola + série -> contar quantas reprovações cada aluno tem naquele contexto
    #    Resultado: uma linha por CPF PESSOA x escola x série
    student_grp = ['CPF PESSOA'] + grp_cols_estudantes
    estudante_por_contexto = (
        df2_estudantes
        .groupby(student_grp, observed=True, sort=False, as_index=False)
        .agg(reprovacoes_aluno=('is_reprovado', 'sum'))
    )

    # 5) Classificar cada aluno como Aprovado/Reprovado segundo a regra por ETAPA_RESUMIDA
    #    Regras:
    #      - "Ens. Fund. - Anos Finais": Reprovado se reprovacoes_aluno >= 4
    #      - "Ensino Médio": Reprovado se reprovacoes_aluno >= 7
    #      - caso contrário: Aprovado (fallback)
    ef_mask = estudante_por_contexto['ETAPA_RESUMIDA'] == "Ens. Fund. - Anos Finais"
    em_mask = estudante_por_contexto['ETAPA_RESUMIDA'] == "Ensino Médio"

    cond_reprovado = (ef_mask & (estudante_por_contexto['reprovacoes_aluno'] >= 4)) | \
                    (em_mask & (estudante_por_contexto['reprovacoes_aluno'] >= 7))

    # Criar coluna CLASSIFICACAO como uint8 (0 = Aprovado, 1 = Reprovado) para economizar memória
    estudante_por_contexto['is_reprovado_aluno'] = cond_reprovado.astype('uint8')

    # 6) Agregar por escola + série para contar Aprovados/Reprovados
    school_grp = ['DIREC','MUNICÍPIO','ESCOLA','INEP ESCOLA','ETAPA_RESUMIDA','SÉRIE']
    df_estudantes = (
        estudante_por_contexto
        .groupby(school_grp, observed=True, sort=False)
        .agg(
            Reprovados=('is_reprovado_aluno', 'sum'),
            Total_Alunos=('CPF PESSOA', 'count')  # opcional, útil para checagens
        )
        .reset_index()
    )

    # 7) Calcular Aprovados a partir do total
    df_estudantes['Aprovados'] = df_estudantes['Total_Alunos'] - df_estudantes['Reprovados']

    # 8) Reordenar colunas com a ordem que você pediu
    df_estudantes = df_estudantes[['DIREC','MUNICÍPIO','ESCOLA','INEP ESCOLA','ETAPA_RESUMIDA','SÉRIE','Aprovados','Reprovados','Total_Alunos']]


    # Salvar os 2 dataframes 
    df_estudantes.to_parquet("dados_tratados/df_estudantes.parquet", index=False)
    df_componentes.to_parquet("dados_tratados/df_componentes.parquet", index=False)
    
    print("DataFrames salvos com sucesso!")
    print(f"df_estudantes: {df_estudantes.shape}")
    print(f"df_componentes: {df_componentes.shape}")
    
    return df_estudantes, df_componentes

# Executar o código acima se rodado diretamente e não como importação em outro módulo
if __name__ == "__main__":
    df_estudantes, df_componentes = processar_dados_brutos()




