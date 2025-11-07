import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Formatador Hierarquia XLSX → CSV", layout="wide")
st.title("🧾 Formatador de Estrutura Hierárquica (XLSX → CSV) — versão robusta")

uploaded_file = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

def looks_like_code(s):
    return bool(re.fullmatch(r"\d+(?:\.\d+)*", s.strip()))

def extract_code_and_name_from_line(line):
    """
    Tenta extrair código no início da linha e o restante como nome.
    Ex: "   01.01.01   PRE PAGAMENTO/CUSTO" -> ("01.01.01", "PRE PAGAMENTO/CUSTO")
    Se não achar, retorna (None, line)
    """
    m = re.match(r"^\s*(\d+(?:\.\d+)*)\s*(?:[\t\-–—:]+|\s{2,}|\s)?(.*)$", line)
    if m:
        code = m.group(1).strip()
        name = m.group(2).strip()
        return code, name
    return None, line.strip()

def parent_code(code):
    parts = code.split(".")
    if len(parts) == 1:
        return ""
    return ".".join(parts[:-1])

def classify_type(code):
    depth = len(code.split("."))
    # Ajuste: consideramos nivel sumarizador (S) até 3 níveis (ex.: 01, 01.01, 01.01.01)
    # itens (A) são profundos > 3. Ajuste conforme sua regra se necessário.
    return "S" if depth <= 3 else "A"

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file)
    except ImportError:
        st.error("❌ O pacote 'openpyxl' não está instalado. Execute `pip install openpyxl` e reinicie o app.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        st.stop()

    # Transformar colunas para strings (segurança)
    df_raw = df_raw.astype(str)

    # Estratégia 1: se primeira coluna aparenta ser código para a maioria, usamos col1=code, col2=name
    first_col = df_raw.columns[0]
    second_col = df_raw.columns[1] if df_raw.shape[1] > 1 else None

    parsed = []
    unparsed_lines = []

    if second_col is not None:
        # Verifica se maioria da primeira coluna parece código
        sample = df_raw[first_col].dropna().astype(str).head(50).tolist()
        code_like_count = sum(1 for s in sample if looks_like_code(s.strip()))
        if code_like_count >= len(sample) * 0.6:  # 60% ou mais -> usar col1=code, col2=nome
            for idx, row in df_raw.iterrows():
                code = str(row[first_col]).strip()
                name_parts = [str(row[c]).strip() for c in df_raw.columns[1:]]  # junta demais colunas como nome, se houver
                name = " ".join([p for p in name_parts if p and p.lower() != "nan"]).strip()
                if not code or code.lower() == "nan":
                    # tentar extrair do name
                    code_extr, name_extr = extract_code_and_name_from_line(name)
                    if code_extr:
                        code, name = code_extr, name_extr
                    else:
                        unparsed_lines.append(" | ".join([str(x) for x in row.tolist()]))
                        continue
                if not looks_like_code(code):
                    # talvez haja indentação antes do código
                    code_extr, name_extr = extract_code_and_name_from_line(str(row[first_col]) + " " + name)
                    if code_extr:
                        code, name = code_extr, name_extr
                    else:
                        unparsed_lines.append(" | ".join([str(x) for x in row.tolist()]))
                        continue
                parsed.append((code, name))
        else:
            # cai para a estratégia por linha (tenta extrair código do início da concatenação das colunas)
            for idx, row in df_raw.iterrows():
                line = " ".join([str(row[c]) for c in df_raw.columns])
                code, name = extract_code_and_name_from_line(line)
                if code:
                    parsed.append((code, name))
                else:
                    unparsed_lines.append(line)
    else:
        # Apenas uma coluna: tenta extrair código do começo de cada linha
        for idx, row in df_raw.iterrows():
            line = str(row[first_col])
            code, name = extract_code_and_name_from_line(line)
            if code:
                parsed.append((code, name))
            else:
                unparsed_lines.append(line)

    # Se nada foi parseado, tenta última tentativa: cada linha pode ser "código[tab]nome"
    if not parsed:
        for idx, row in df_raw.iterrows():
            s = str(row[first_col])
            if "\t" in s:
                parts = s.split("\t", 1)
                code = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else ""
                if looks_like_code(code):
                    parsed.append((code, name))
                else:
                    unparsed_lines.append(s)
            else:
                unparsed_lines.append(s)

    # Monta DataFrame final
    rows = []
    for code, name in parsed:
        nivel_sup = parent_code(code)
        tipo = classify_type(code)
        rows.append({"Estrutura": code, "Nível superior": nivel_sup, "Nome": name, "Tipo": tipo})

    df_out = pd.DataFrame(rows, columns=["Estrutura", "Nível superior", "Nome", "Tipo"])

    if df_out.empty:
        st.error("Nenhuma linha foi reconhecida como estrutura válida. Verifique o layout do Excel (códigos como 01, 01.01, 01.01.01...).")
        # Mostra algumas linhas brutas para ajudar
        st.markdown("### Linhas de entrada (amostra)")
        st.write(df_raw.head(20))
        st.stop()

    # Mostra somente o resultado final (sem pré-visualização do raw)
    st.subheader("📋 Estrutura formatada")
    st.dataframe(df_out, use_container_width=True)

    # Oferece download em CSV separado por ;
    csv_buffer = io.StringIO()
    df_out.to_csv(csv_buffer, sep=";", index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    st.download_button(
        label="⬇️ Baixar CSV formatado",
        data=csv_bytes,
        file_name="estrutura_formatada.csv",
        mime="text/csv"
    )

    # Se houver linhas que não foram parseadas, mostra um alerta e fornece botão para baixar arquivo com elas
    if unparsed_lines:
        st.warning(f"{len(unparsed_lines)} linhas não puderam ser parseadas automaticamente — verifique manualmente se necessário.")
        # mostra apenas algumas amostras
        with st.expander("Ver amostras das linhas não parseadas"):
            for i, line in enumerate(unparsed_lines[:50], 1):
                st.text(f"{i}. {line}")

        # permite baixar as linhas não parseadas
        unparsed_buf = io.StringIO()
        unparsed_buf.write("\n".join(unparsed_lines))
        st.download_button(
            label="⬇️ Baixar linhas não parseadas (txt)",
            data=unparsed_buf.getvalue().encode("utf-8"),
            file_name="linhas_nao_parseadas.txt",
            mime="text/plain"
        )

    st.success("Processamento concluído ✅")

else:
    st.info("Envie um arquivo Excel (.xlsx) para começar.")