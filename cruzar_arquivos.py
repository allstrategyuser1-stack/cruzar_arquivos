import streamlit as st
import pandas as pd
import unicodedata
from io import BytesIO

st.set_page_config(page_title="Cruzamento Descrição × Classificação", page_icon="🔗", layout="wide")

st.title("🔗 Cruzamento Descrição × Classificação")
st.write("Carregue dois arquivos CSV (`Descrição` e `Classificação`) para cruzar por nome, ignorando acentuação e maiúsculas/minúsculas.")

# Função para normalizar texto
def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).lower().strip()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

# Upload dos arquivos
col1, col2 = st.columns(2)
with col1:
    desc_file = st.file_uploader("📂 Arquivo de Descrição", type=["csv"])
with col2:
    classif_file = st.file_uploader("📂 Arquivo de Classificação", type=["csv"])

if desc_file and classif_file:
    # Opção de separador
    sep = st.radio("Selecione o delimitador dos arquivos CSV:", options=[";", ","], index=0, horizontal=True)

    try:
        desc = pd.read_csv(desc_file, dtype=str, sep=sep)
        classif = pd.read_csv(classif_file, dtype=str, sep=sep)

        # Verificar colunas obrigatórias
        if not {"Nome", "Código"}.issubset(desc.columns) or not {"Nome", "Estrutura"}.issubset(classif.columns):
            st.error("Os arquivos devem conter as colunas corretas: \
                     **Descrição:** Nome, Código | **Classificação:** Nome, Estrutura")
        else:
            # Normalizar nomes
            desc["nome_norm"] = desc["Nome"].apply(normalize_text)
            classif["nome_norm"] = classif["Nome"].apply(normalize_text)

            # Detectar duplicidades na Classificação
            duplicadas = classif[classif.duplicated("nome_norm", keep=False)]["nome_norm"].unique()

            # Fazer merge
            merged = pd.merge(desc, classif, on="nome_norm", how="left", suffixes=("_desc", "_classif"))

            # Remover correspondências duplicadas
            merged.loc[merged["nome_norm"].isin(duplicadas), ["Estrutura", "Nome_classif"]] = None

            # Selecionar colunas finais
            resultado = merged[["Código", "Nome_desc", "Estrutura", "Nome_classif"]]
            resultado.columns = [
                "Código (Descrição)",
                "Nome (Descrição)",
                "Estrutura (Classificação)",
                "Nome (Classificação correspondido)"
            ]

            st.success("✅ Cruzamento realizado com sucesso!")

            # Mostrar preview
            st.dataframe(resultado.head(20), use_container_width=True)

            # Gerar CSV para download
            csv_bytes = resultado.to_csv(index=False, sep=sep, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="💾 Baixar resultado completo (.csv)",
                data=csv_bytes,
                file_name="Cruzamento_Descricao_Classificacao.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Erro ao processar os arquivos: {e}")
else:
    st.info("⬆️ Envie os dois arquivos CSV para iniciar o cruzamento.")
