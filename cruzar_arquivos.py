import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Formatar Estrutura", page_icon="📊", layout="centered")

st.title("📊 Formatador de Estrutura Hierárquica")
st.write("Faça upload de um arquivo `.xlsx` no formato da estrutura para gerar o CSV formatado.")

uploaded_file = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        
        dados_formatados = []
        nivel_1 = nivel_2 = nivel_3 = None
        nome_1 = nome_2 = nome_3 = None

        for _, row in df.iterrows():
            # Coluna 0: código do nível 1
            if pd.notna(row[0]):
                nivel_1 = str(row[0]).strip().replace(".0", "")
                nome_1 = str(row[1]).strip() if pd.notna(row[1]) else ""
                dados_formatados.append({
                    "Estrutura": nivel_1,
                    "Nível superior": "",
                    "Nome": nome_1,
                    "Tipo": "S"
                })
            
            # Coluna 1: código do nível 2
            elif pd.notna(row[1]) and str(row[1]).replace(".", "").isdigit():
                nivel_2 = str(row[1]).strip()
                nome_2 = str(row[2]).strip() if pd.notna(row[2]) else ""
                dados_formatados.append({
                    "Estrutura": nivel_2,
                    "Nível superior": nivel_1,
                    "Nome": nome_2,
                    "Tipo": "S"
                })
            
            # Coluna 2: código do nível 3
            elif pd.notna(row[2]) and str(row[2]).replace(".", "").isdigit():
                nivel_3 = str(row[2]).strip()
                nome_3 = str(row[3]).strip() if pd.notna(row[3]) else ""
                dados_formatados.append({
                    "Estrutura": nivel_3,
                    "Nível superior": nivel_2,
                    "Nome": nome_3,
                    "Tipo": "S"
                })

            # Coluna 3: código do nível 4 (item A)
            elif pd.notna(row[3]) and str(row[3]).replace(".", "").isdigit():
                estrutura = str(row[3]).strip()
                nome = str(row[4]).strip() if pd.notna(row[4]) else ""
                dados_formatados.append({
                    "Estrutura": estrutura,
                    "Nível superior": nivel_3,
                    "Nome": nome,
                    "Tipo": "A"
                })

        df_final = pd.DataFrame(dados_formatados)

        # Converter para CSV (separado por ;)
        csv_buffer = StringIO()
        df_final.to_csv(csv_buffer, sep=";", index=False)
        csv_data = csv_buffer.getvalue()

        st.success("✅ Estrutura formatada com sucesso!")
        st.download_button(
            label="📥 Baixar CSV formatado",
            data=csv_data,
            file_name="estrutura_formatada.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")