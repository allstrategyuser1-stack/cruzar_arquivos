import streamlit as st
import pandas as pd
import unicodedata

st.set_page_config(page_title="Cruzamento Descrição × Classificação", page_icon="🔗", layout="wide")

st.title("🔗 Cruzamento Descrição × Classificação")
st.write("""
Carregue dois arquivos CSV — um de **Descrição** e outro de **Classificação**, cada um contendo as colunas:
**Código** e **Nome**.
O sistema fará o cruzamento pelo nome (ignorando acentuação e maiúsculas/minúsculas).
""")

# Função para normalizar texto (remove acentos e deixa minúsculo)
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
    sep = st.radio("Selecione o delimitador dos arquivos CSV:", options=[";", ","], index=0, horizontal=True)

    try:
        # Ler os arquivos
        desc = pd.read_csv(desc_file, dtype=str, sep=sep)
        classif = pd.read_csv(classif_file, dtype=str, sep=sep)

        # Validar colunas
        if not {"Nome", "Código"}.issubset(desc.columns):
            st.error("❌ O arquivo de **Descrição** deve conter as colunas: Código, Nome.")
        elif not {"Nome", "Código"}.issubset(classif.columns):
            st.error("❌ O arquivo de **Classificação** deve conter as colunas: Código, Nome.")
        else:
            # Normalização
            desc["nome_norm"] = desc["Nome"].apply(normalize_text)
            classif["nome_norm"] = classif["Nome"].apply(normalize_text)

            # Detectar duplicidades na classificação
            duplicadas = classif[classif.duplicated("nome_norm", keep=False)]["nome_norm"].unique()

            # Merge
            merged = pd.merge(desc, classif, on="nome_norm", how="left", suffixes=("_desc", "_classif"))

            # Limpa registros com mais de uma correspondência
            merged.loc[merged["nome_norm"].isin(duplicadas), ["Código_classif", "Nome_classif"]] = None

            # DataFrame final com 5 colunas
            resultado = pd.DataFrame({
                "Código (Descrição)": merged["Código_desc"],
                "Nome (Descrição)": merged["Nome_desc"],
                "Código (Classificação)": merged["Código_classif"],
                "Nome (Classificação)": merged["Nome_classif"],
                "Descrição Final": merged["Código_desc"]  # agora usa o código da descrição
            })

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