import streamlit as st
import pandas as pd
import io

st.title("🧾 Formatador de Estrutura Hierárquica (XLSX → CSV)")

st.write("Envie um arquivo Excel (.xlsx) com as informações brutas e o app formatará automaticamente os níveis hierárquicos.")

# Upload do arquivo XLSX
uploaded_file = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Lê a primeira aba do Excel
    try:
        df_raw = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        st.stop()

    st.subheader("📄 Pré-visualização dos dados importados")
    st.dataframe(df_raw.head(), use_container_width=True)

    # Detecta a primeira coluna com código e nome
    # Supõe que a primeira coluna contém algo como "01	ENTRADAS"
    col = df_raw.columns[0]

    lines = df_raw[col].dropna().astype(str).tolist()

    data = []
    for line in lines:
        # Divide cada linha em código e nome
        parts = line.strip().split("\t") if "\t" in line else line.strip().split(maxsplit=1)

        if len(parts) == 1:
            codigo = parts[0]
            nome = ""
        else:
            codigo, nome = parts[0], parts[1]

        # Determina nível superior e tipo
        if "." not in codigo:
            nivel_superior = ""
            tipo = "S"
        else:
            partes = codigo.split(".")
            nivel_superior = ".".join(partes[:-1])
            tipo = "A" if len(partes) > 3 else "S"

        data.append([codigo, nivel_superior, nome.strip(), tipo])

    # Cria DataFrame formatado
    df = pd.DataFrame(data, columns=["Estrutura", "Nível superior", "Nome", "Tipo"])

    st.subheader("📋 Estrutura formatada")
    st.dataframe(df, use_container_width=True)

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

    st.success("Arquivo formatado com sucesso! ✅")
else:
    st.info("Envie um arquivo Excel (.xlsx) para começar.")