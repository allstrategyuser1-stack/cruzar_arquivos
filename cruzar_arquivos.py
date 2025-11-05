import streamlit as st
import pandas as pd
import unicodedata
from rapidfuzz import fuzz, process

st.set_page_config(page_title="Cruzamento Descrição × Classificação", page_icon="🔗", layout="wide")

st.title("🔗 Cruzamento Descrição × Classificação")
st.write("""
Carregue dois arquivos CSV — um de **Descrição** e outro de **Classificação**, cada um contendo as colunas:
**Código** e **Nome**.

Você pode escolher entre:
- **Correspondência exata** → iguala nomes (ignorando acentuação e maiúsculas);
- **Correspondência aproximada** → busca o nome mais parecido, com base em similaridade textual.
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
    match_mode = st.radio("Tipo de correspondência:", options=["Exata", "Aproximada"], index=1, horizontal=True)

    try:
        desc = pd.read_csv(desc_file, dtype=str, sep=sep)
        classif = pd.read_csv(classif_file, dtype=str, sep=sep)

        if not {"Nome", "Código"}.issubset(desc.columns):
            st.error("❌ O arquivo de **Descrição** deve conter as colunas: Código, Nome.")
        elif not {"Nome", "Código"}.issubset(classif.columns):
            st.error("❌ O arquivo de **Classificação** deve conter as colunas: Código, Nome.")
        else:
            # Normaliza nomes
            desc["nome_norm"] = desc["Nome"].apply(normalize_text)
            classif["nome_norm"] = classif["Nome"].apply(normalize_text)

            if match_mode == "Exata":
                # --- Modo exato ---
                merged = pd.merge(desc, classif, on="nome_norm", how="left", suffixes=("_desc", "_classif"))
                merged["similaridade"] = merged.apply(
                    lambda x: 100 if pd.notna(x["Código_classif"]) else 0, axis=1
                )

            else:
                # --- Modo aproximado ---
                st.info("🔍 Buscando correspondências aproximadas (pode levar alguns segundos)...")
                threshold = st.slider("Grau mínimo de similaridade (%)", 50, 100, 80)

                matches = []
                for _, row in desc.iterrows():
                    nome = row["nome_norm"]
                    match = process.extractOne(nome, classif["nome_norm"], scorer=fuzz.token_sort_ratio)
                    if match and match[1] >= threshold:
                        matched_row = classif[classif["nome_norm"] == match[0]].iloc[0]
                        matches.append({
                            "Código_desc": row["Código"],
                            "Nome_desc": row["Nome"],
                            "Código_classif": matched_row["Código"],
                            "Nome_classif": matched_row["Nome"],
                            "similaridade": round(match[1], 1)
                        })
                    else:
                        matches.append({
                            "Código_desc": row["Código"],
                            "Nome_desc": row["Nome"],
                            "Código_classif": None,
                            "Nome_classif": None,
                            "similaridade": 0
                        })

                merged = pd.DataFrame(matches)

            # Cria a coluna "Descrição Final" somente se houver classificação
            merged["Descrição Final"] = merged.apply(
                lambda x: x["Código_desc"] if pd.notna(x["Código_classif"]) else "",
                axis=1
            )

            # DataFrame final com 6 colunas (agora com Similaridade)
            resultado = merged[[
                "Código_desc", "Nome_desc", "Código_classif", "Nome_classif", "Descrição Final", "similaridade"
            ]].rename(columns={
                "Código_desc": "Código (Descrição)",
                "Nome_desc": "Nome (Descrição)",
                "Código_classif": "Código (Classificação)",
                "Nome_classif": "Nome (Classificação)",
                "similaridade": "Similaridade (%)"
            })

            st.success("✅ Cruzamento concluído!")

            # Mostrar preview
            st.dataframe(resultado.head(20), use_container_width=True)

            # Baixar CSV
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