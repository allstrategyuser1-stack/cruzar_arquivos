import streamlit as st
import pandas as pd
import re
from io import StringIO

st.set_page_config(page_title="Formatar Estrutura", page_icon="📊", layout="centered")

st.title("📊 Formatador de Estrutura Hierárquica")
st.write("Envie o arquivo `.xlsx` da estrutura e o sistema formatará automaticamente os níveis e códigos.")

uploaded_file = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

# 🔧 Função para padronizar o código (dois dígitos por parte)
def padronizar_codigo(codigo):
    partes = codigo.split(".")
    partes_formatadas = [f"{int(p):02d}" if p.isdigit() else p for p in partes]
    return ".".join(partes_formatadas)

# 🔧 Função para limpar e encurtar nomes longos (>45 caracteres)
def ajustar_nome(nome):
    if not isinstance(nome, str):
        return ""

    nome = nome.strip()
    if len(nome) <= 45:
        return nome  # mantém o original se já estiver no limite

    nome_limpo = nome.upper()
    nome_limpo = re.sub(r"[-_/()]+", " ", nome_limpo)
    nome_limpo = re.sub(r"\s+", " ", nome_limpo)

    substituicoes = {
        "OPERACIONAL": "OPERAC.",
        "COOPERADO": "COOP.",
        "PREMIUM": "PREM.",
        "ECONOMICO": "ECON.",
        "FEDERATIVO": "FEDERAT.",
        "PARTICIPATIVO": "PARTIC.",
        "CONVENIO": "CONV.",
        "UNIMED": "UNIM.",
        "PLANO": "PLN.",
        "PAGAMENTO": "PAGTO",
        "SUPERIOR": "SUP.",
        "HOSPITALAR": "HOSPIT."
    }

    for termo, sub in substituicoes.items():
        nome_limpo = nome_limpo.replace(termo, sub)

    # Corta para no máximo 45 caracteres
    nome_final = nome_limpo[:45].rstrip()
    return nome_final

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, header=None)
        
        dados_formatados = []
        nivel_1 = nivel_2 = nivel_3 = None
        nome_1 = nome_2 = nome_3 = None

        for _, row in df.iterrows():
            # Coluna 0: código do nível 1
            if pd.notna(row[0]):
                nivel_1_raw = str(row[0]).strip().replace(".0", "")
                nivel_1 = padronizar_codigo(nivel_1_raw)
                nome_1 = ajustar_nome(str(row[1]).strip() if pd.notna(row[1]) else "")
                dados_formatados.append({
                    "Estrutura": nivel_1,
                    "Nível superior": "",
                    "Nome": nome_1,
                    "Tipo": "S"
                })
            
            # Coluna 1: código do nível 2
            elif pd.notna(row[1]) and str(row[1]).replace(".", "").isdigit():
                nivel_2 = padronizar_codigo(str(row[1]).strip())
                nome_2 = ajustar_nome(str(row[2]).strip() if pd.notna(row[2]) else "")
                dados_formatados.append({
                    "Estrutura": nivel_2,
                    "Nível superior": nivel_1,
                    "Nome": nome_2,
                    "Tipo": "S"
                })
            
            # Coluna 2: código do nível 3
            elif pd.notna(row[2]) and str(row[2]).replace(".", "").isdigit():
                nivel_3 = padronizar_codigo(str(row[2]).strip())
                nome_3 = ajustar_nome(str(row[3]).strip() if pd.notna(row[3]) else "")
                dados_formatados.append({
                    "Estrutura": nivel_3,
                    "Nível superior": nivel_2,
                    "Nome": nome_3,
                    "Tipo": "S"
                })

            # Coluna 3: código do nível 4 (item A)
            elif pd.notna(row[3]) and str(row[3]).replace(".", "").isdigit():
                estrutura = padronizar_codigo(str(row[3]).strip())
                nome = ajustar_nome(str(row[4]).strip() if pd.notna(row[4]) else "")
                dados_formatados.append({
                    "Estrutura": estrutura,
                    "Nível superior": nivel_3,
                    "Nome": nome,
                    "Tipo": "A"
                })

        df_final = pd.DataFrame(dados_formatados)

        # Converter para CSV separado por ";"
        csv_buffer = StringIO()
        df_final.to_csv(csv_buffer, sep=";", index=False)
        csv_data = csv_buffer.getvalue()

        st.success(f"✅ Estrutura formatada com sucesso! {len(df_final)} registros gerados.")
        st.download_button(
            label="📥 Baixar CSV formatado",
            data=csv_data,
            file_name="estrutura_formatada.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")