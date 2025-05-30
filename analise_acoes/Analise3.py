import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Título do app
st.title("📊 Análise Fundamentalista de Ações")

# Leitura do arquivo
file = st.file_uploader("📁 Faça upload do arquivo .xlsx", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    st.subheader("📌 Dados Originais")
    st.dataframe(df)

    # Remover colunas não numéricas para análise
    fundamentos = df.select_dtypes(include='number')

    # Normalizar os dados para criar um "score"
    st.subheader("⚙️ Normalizando indicadores para pontuação")
    score_df = (fundamentos - fundamentos.min()) / (fundamentos.max() - fundamentos.min())
    df['Score'] = score_df.sum(axis=1)

    # Ordenar por Score
    df_sorted = df.sort_values(by="Score", ascending=False)

    st.subheader("⭐ Ranking das Melhores Ações")
    st.dataframe(df_sorted.head(10))

    # Gráfico das Top 10
    st.subheader("📈 Gráfico das Top 10 Ações")
    top10 = df_sorted.head(10)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(top10[df.columns[0]], top10["Score"], color='green')
    plt.xticks(rotation=45)
    plt.ylabel("Pontuação")
    plt.title("Top 10 Ações por Score")
    st.pyplot(fig)

    # Download da planilha
    st.subheader("⬇️ Baixar planilha com ranking")
    def convert_df_to_excel(dataframe):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Ranking')
        return output.getvalue()

    excel_data = convert_df_to_excel(df_sorted)
    st.download_button(
        label="📥 Baixar Excel",
        data=excel_data,
        file_name='ranking_acoes.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
