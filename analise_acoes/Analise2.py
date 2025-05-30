import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

st.set_page_config(layout="wide")

# Função para calcular score com base nos fundamentos
def calcular_score(df):
    df_numeric = df.select_dtypes(include=['float64', 'int64']).copy()

    # Colunas em que valores maiores são melhores
    colunas_boas = ['Div.Yield', 'Mrg Ebit', 'Mrg. Líq.', 'Liq. Corr.', 'ROIC', 'ROE', 'Cresc. Rec.5a']

    # Colunas em que valores menores são melhores
    colunas_ruins = ['P/L', 'P/VP', 'PSR', 'P/Ativo', 'P/Cap.Giro', 'P/EBIT', 'EV/EBIT', 'EV/EBITDA', 'Dív.Brut/ Patrim.']

    # Limpar valores extremos ou nulos
    df_numeric.replace([float('inf'), float('-inf')], pd.NA, inplace=True)
    df_numeric.fillna(0, inplace=True)

    # Normalização
    scaler = MinMaxScaler()
    df_normalizado = pd.DataFrame(scaler.fit_transform(df_numeric), columns=df_numeric.columns)

    # Score: soma das boas menos a soma das ruins
    df['Score'] = df_normalizado[colunas_boas].sum(axis=1) - df_normalizado[colunas_ruins].sum(axis=1)

    return df

# Upload do arquivo
st.title("Análise Fundamentalista de Ações")

arquivo = st.file_uploader("Envie sua planilha Excel", type=[".xlsx"])

if arquivo:
    xls = pd.ExcelFile(arquivo)
    planilhas = xls.sheet_names

    aba = st.selectbox("Escolha a aba com os dados", planilhas)
    df = pd.read_excel(arquivo, sheet_name=aba)

    if 'Papel' in df.columns:
        df_resultado = calcular_score(df)

        # Filtros adicionais
        setores_disponiveis = df_resultado['Setor'].dropna().unique().tolist() if 'Setor' in df_resultado.columns else []
        setor_selecionado = st.selectbox("Filtrar por setor", ["Todos"] + setores_disponiveis)

        if setor_selecionado != "Todos" and 'Setor' in df_resultado.columns:
            df_resultado = df_resultado[df_resultado['Setor'] == setor_selecionado]

        # Filtro para mostrar apenas as que você possui
        destacar_minha_carteira = st.checkbox("Destacar apenas ações que eu possuo")
        if destacar_minha_carteira and 'Tenho' in df_resultado.columns:
            df_resultado = df_resultado[df_resultado['Tenho'] > 0]

        # Filtro para maiores pagadoras de dividendos
        top_dividendos = st.checkbox("Mostrar apenas maiores pagadoras de dividendos")
        if top_dividendos and 'Div.Yield' in df_resultado.columns:
            df_resultado = df_resultado.sort_values(by='Div.Yield', ascending=False).head(10)
        else:
            df_resultado = df_resultado.sort_values(by='Score', ascending=False)

        st.subheader("Top Ações Recomendadas")
        st.dataframe(df_resultado[['Papel', 'Score', 'Div.Yield']].head(10))

        st.subheader("Gráfico de Scores")
        st.bar_chart(df_resultado.set_index('Papel')['Score'].head(10))

        # Download da planilha com os resultados
        df_download = df_resultado.to_excel(index=False)
        st.download_button("Baixar Resultados em Excel", data=df_download, file_name="analise_acoes_resultado.xlsx")

    else:
        st.error("A planilha precisa ter uma coluna chamada 'Papel'")
