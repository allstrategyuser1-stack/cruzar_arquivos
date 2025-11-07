import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Formatador Hierárquico XLSX → CSV", layout="wide")
st.title("🧾 Formatador de Estrutura Hierárquica (XLSX → CSV)")

st.write("Envie um arquivo Excel (.xlsx) com até 5 colunas hierárquicas (cada par código/nome representa um nível).")

# Funções auxiliares
def is_code(value: str):
    return bool(re.fullmatch(r"\d+(?:\.\d+)*", str(value).strip()))

def parent_code(code: str):
    parts = code.split(".")
    if len(parts) == 1:
        return ""
    return ".".join(parts[:-1])

def get_type(code: str):
    depth = len(code.split("."))
    return "A" if depth >= 4 else "S"

uploaded_file = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file, header=None)
    except ImportError:
        st.error("❌ O pacote 'openpyxl' não está instalado. Execute `pip install openpyxl` e reinicie o app.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        st.stop()

    # Converte tudo para string e remove valores nulos
    df_raw = df_raw.fillna("").astype(str)

    registros = []

    # Percorre linha a linha
    for _, row in df_raw.iterrows():
        # Cada linha pode ter até 5 colunas (níveis)
        col_values = [v.strip() for v in row.tolist() if v.strip()]
        if not col_values:
            continue

        # Vamos percorrer pares código/nome
        i = 0
        while i < len(col_values):
            val = col_values[i]

            # Detecta código
            if is_code(val):
                codigo = val
                nome = ""
                # Pega o nome logo após o código (se existir)
                if i + 1 < len(col_values) and not is_code(col_values[i + 1]):
                    nome = col_values[i + 1]
                    i += 1  # pula o nome
                registros.append([codigo, parent_code(codigo), nome, get_type(codigo)])
            i += 1

    if not registros:
        st.error("❌ Nenhum registro válido foi identificado. Verifique se o arquivo segue o formato com colunas hierárquicas.")
        st.stop()

    df = pd.DataFrame(registros, columns=["Estrutura", "Nível superior", "Nome", "Tipo"]).drop_duplicates()

    st.subheader("📋 Estrutura formatada")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Gera CSV separado por ';'
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, sep=";", index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    st.download_button(
        label="⬇️ Baixar CSV formatado",
        data=csv_bytes,
        file_name="estrutura_formatada.csv",
        mime="text/csv"
    )

    st.success(f"✅ Processado com sucesso! {len(df)} registros gerados.")
else:
    st.info("Envie um arquivo Excel (.xlsx) para começar.")