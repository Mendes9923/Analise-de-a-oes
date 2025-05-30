import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# Configuração inicial
st.set_page_config(page_title="Análise Fundamentalista", layout="wide")

# Título do app
st.title("📊 Análise Fundamentalista de Ações")

# CSS personalizado
st.markdown("""
<style>
    .st-bq {
        border-left: 5px solid #4CAF50;
        padding-left: 1rem;
    }
    .st-ck {
        font-weight: bold;
    }
    .metric-box {
        border-radius: 5px;
        padding: 15px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Leitura do arquivo
file = st.file_uploader("📁 Faça upload do arquivo .xlsx", type=["xlsx"])

if file:
    try:
        df = pd.read_excel(file)
        
        # Limpeza dos dados
        st.subheader("🧹 Pré-processamento dos Dados")
        
        # Remover linhas completamente vazias
        df = df.dropna(how='all')
        
        # Identificar colunas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Tratamento de valores infinitos e outliers
        for col in numeric_cols:
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            
            # Winsorização para outliers extremos (opcional)
            if df[col].nunique() > 10:  # Apenas para colunas com vários valores
                q_low = df[col].quantile(0.01)
                q_hi = df[col].quantile(0.99)
                df[col] = df[col].clip(lower=q_low, upper=q_hi)
        
        # Mostrar dados processados
        with st.expander("Visualizar dados processados"):
            st.dataframe(df.head())
        
        # Configuração da análise
        st.subheader("⚙️ Configuração da Análise")
        
        # Definir pesos para os indicadores (customizável pelo usuário)
        default_weights = {
            'P/L': -1,     # Quanto menor, melhor
            'P/VP': -1,    # Quanto menor, melhor
            'Div.Yield': 1, # Quanto maior, melhor
            'ROE': 1,      # Quanto maior, melhor
            'ROIC': 1,     # Quanto maior, melhor
            'Mrg. Líq.': 1 # Quanto maior, melhor
        }
        
        # Selecionar colunas para análise
        selected_cols = st.multiselect(
            "Selecione os indicadores para análise",
            options=numeric_cols,
            default=list(default_weights.keys())
        )
        
        # Configurar pesos
        weights = {}
        for col in selected_cols:
            default_weight = default_weights.get(col, 0)
            weight = st.slider(
                f"Peso para {col}",
                min_value=-2,
                max_value=2,
                value=default_weight,
                key=f"weight_{col}"
            )
            weights[col] = weight
        
        # Cálculo do score
        st.subheader("🧮 Calculando Scores")
        
        score_df = pd.DataFrame()
        for col in selected_cols:
            if df[col].nunique() > 1:  # Apenas normalizar se houver variação
                normalized = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
                score_df[col] = normalized * weights.get(col, 0)
            else:
                score_df[col] = 0  # Se não houver variação, não contribui para o score
        
        df['Score'] = score_df.sum(axis=1)
        df_sorted = df.sort_values(by="Score", ascending=False)
        
        # Visualização dos resultados
        st.subheader("📊 Resultados da Análise")
        
        # Abas para organização
        tab1, tab2, tab3 = st.tabs(["🏆 Ranking", "📈 Visualizações", "🔍 Análise Detalhada"])
        
        with tab1:
            st.write("Top 20 ações por score fundamentalista")
            st.dataframe(
                df_sorted.head(20).style.background_gradient(
                    subset=['Score'], 
                    cmap='Greens'
                ),
                height=800
            )
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de barras horizontais
                st.write("Top 10 Ações por Score")
                top10 = df_sorted.head(10)
                
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.barh(top10['Papel'], top10['Score'], color='#4CAF50')
                ax.bar_label(bars, fmt='%.2f', padding=3)
                ax.set_xlabel('Score Fundamentalista')
                ax.set_title('Top 10 Ações')
                plt.gca().invert_yaxis()
                st.pyplot(fig)
            
            with col2:
                # Gráfico de radar para análise multidimensional
                st.write("Análise Multidimensional das Top 5")
                top5 = df_sorted.head(5)
                
                if len(selected_cols) >= 3:  # Radar precisa de pelo menos 3 indicadores
                    fig2 = plt.figure(figsize=(8, 8))
                    ax = fig2.add_subplot(111, polar=True)
                    
                    for idx, row in top5.iterrows():
                        valores = row[selected_cols].values
                        valores = np.append(valores, valores[0])  # Fechar o polígono
                        
                        angles = np.linspace(0, 2*np.pi, len(selected_cols), endpoint=False)
                        angles = np.append(angles, angles[0])
                        
                        ax.plot(angles, valores, 'o-', label=row['Papel'])
                        ax.fill(angles, valores, alpha=0.1)
                    
                    ax.set_thetagrids(angles[:-1] * 180/np.pi, selected_cols)
                    ax.set_title('Comparação Multidimensional')
                    ax.legend(bbox_to_anchor=(1.3, 1.1))
                    st.pyplot(fig2)
                else:
                    st.warning("Selecione pelo menos 3 indicadores para o gráfico de radar")
        
        with tab3:
            # Análise detalhada por ação
            st.write("Análise Detalhada por Ação")
            acao_selecionada = st.selectbox(
                "Selecione uma ação",
                options=df_sorted['Papel'].unique()
            )
            
            detalhes = df_sorted[df_sorted['Papel'] == acao_selecionada].iloc[0]
            
            # Métricas principais
            cols = st.columns(4)
            cols[0].metric("Score", f"{detalhes['Score']:.2f}")
            cols[1].metric("Cotação", f"R$ {detalhes['Cotação']:.2f}")
            cols[2].metric("P/L", f"{detalhes.get('P/L', '-')}")
            cols[3].metric("P/VP", f"{detalhes.get('P/VP', '-')}")
            
            # Gráfico de indicadores
            indicadores = [col for col in selected_cols if col in detalhes]
            valores = [detalhes[col] for col in indicadores]
            
            fig3, ax3 = plt.subplots(figsize=(10, 4))
            ax3.bar(indicadores, valores, color='teal')
            ax3.set_title(f"Indicadores de {acao_selecionada}")
            ax3.tick_params(axis='x', rotation=45)
            st.pyplot(fig3)
            
            # Tabela com todos os indicadores
            with st.expander("Ver todos os indicadores"):
                st.dataframe(detalhes)
        
        # Exportação dos resultados
        st.subheader("💾 Exportar Resultados")
        
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_sorted.to_excel(writer, sheet_name='Ranking Completo', index=False)
                df_sorted.head(20).to_excel(writer, sheet_name='Top 20', index=False)
                df.describe().to_excel(writer, sheet_name='Estatísticas')
            return output.getvalue()
        
        excel_data = to_excel(df_sorted)
        st.download_button(
            label="📥 Baixar Análise Completa",
            data=excel_data,
            file_name='analise_fundamentalista.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Seção de ajuda
        with st.expander("ℹ️ Como interpretar os resultados"):
            st.markdown("""
            **Score Fundamentalista**: Pontuação composta que considera múltiplos indicadores financeiros. 
            Quanto maior, melhor o desempenho fundamentalista da ação.
            
            **Indicadores-chave**:
            - **P/L (Preço/Lucro)**: Relação entre preço da ação e lucro por ação. Valores muito altos podem indicar sobrevalorização.
            - **P/VP (Preço/Valor Patrimonial)**: Relação entre preço e valor contábil. Abaixo de 1 pode indicar subvalorização.
            - **Div. Yield**: Dividendos pagos em relação ao preço da ação. Importante para investidores de renda.
            - **ROE (Return on Equity)**: Mede a eficiência na geração de lucros com o capital próprio.
            - **ROIC (Return on Invested Capital)**: Mede o retorno sobre o capital investido.
            
            **Pesos**: Você pode ajustar a importância de cada indicador na análise. 
            Valores positivos indicam que quanto maior o indicador, melhor. 
            Valores negativos indicam que quanto menor o indicador, melhor.
            """)
    
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {str(e)}")
else:
    st.info("Por favor, faça upload de um arquivo Excel para começar a análise.")

# Rodapé
st.markdown("---")
st.markdown("Desenvolvido com Streamlit | Análise Fundamentalista de Ações")