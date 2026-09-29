import streamlit as st
import pandas as pd
import logging
import os
import base64
import zipfile
import reportlab
from io import BytesIO

# --- FORÇAR TEMA E CORES DA TABELA (AZUL STELLANTIS) ---
try:
    from databricks.sql import connect as databricks_connect
    DB_SQL_AVAILABLE = True
except ImportError as e:
    DB_SQL_AVAILABLE = False
    DB_INSTALL_ERROR = str(e)

# 2. Dependências de PDF (ReportLab)
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    PDF_AVAILABLE = True
except ImportError as e:
    PDF_AVAILABLE = False
    PDF_INSTALL_ERROR = str(e)

# --- CONFIGURAÇÕES DATABRICKS E AMBIENTE ---
WORKSPACE_HOST = "adb-5678659344564033.13.azuredatabricks.net"
HTTP_PATH = "/sql/1.0/warehouses/f50f8042564c0ed4"
ACCESS_TOKEN = "dapic65c47237f40bd19d998aeee624511fd-2"
CATALOGO_SCHEMA = "eng_lab.`cwt-acquisition-setup-tool`"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FUNÇÕES DE CONEXÃO E DADOS ---
def get_connection():
    return databricks_connect(
        server_hostname=WORKSPACE_HOST,
        http_path=HTTP_PATH,
        access_token=ACCESS_TOKEN
    )

@st.cache_data(ttl=3600)
def get_available_tables():
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SHOW TABLES IN {CATALOGO_SCHEMA}")
                rows = cursor.fetchall()
                tabelas = [row[1] for row in rows if "projeto" in row[1].lower()]
                return sorted(tabelas)
    except Exception as e:
        logger.error(f"Erro ao buscar a lista de tabelas: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_databricks_table(table_name):
    query = f"SELECT * FROM {CATALOGO_SCHEMA}.`{table_name}`"
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                try:
                    df_result = cursor.fetchall_arrow().to_pandas()
                except Exception:
                    rows = cursor.fetchall()
                    cols = [desc[0] for desc in cursor.description]
                    df_result = pd.DataFrame(rows, columns=cols)
                    
        if df_result.shape[1] >= 3:
            df_result = df_result.iloc[:, [1, 2]].copy()
            df_result.columns = ["Ponto", "Descrição"]
            df_result = df_result.iloc[2:].reset_index(drop=True)
            df_result = df_result.replace({'nan': pd.NA, 'None': pd.NA, 'NaN': pd.NA, '': pd.NA})
            df_result = df_result.dropna(how='all')
            
        return df_result, True, ""
    except Exception as e:
        return pd.DataFrame(), False, str(e)

def save_project_channel(table_name, point, description):
    """Insere um canal padrão na tabela do projeto no Databricks."""
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                table_ref = f"{CATALOGO_SCHEMA}.`{table_name}`"
                cursor.execute(f"SELECT * FROM {table_ref} LIMIT 0")
                columns = [column[0] for column in cursor.description]
                if len(columns) < 3:
                    return False, "A tabela do projeto não possui as colunas esperadas de ponto e descrição."

                # As colunas 2 e 3 são as exibidas pela aplicação como Ponto e Descrição.
                point_column = columns[1].replace("`", "``")
                description_column = columns[2].replace("`", "``")
                point_value = str(point).replace("'", "''")
                description_value = str(description).replace("'", "''")
                query = (
                    f"INSERT INTO {table_ref} (`{point_column}`, `{description_column}`) "
                    f"VALUES ('{point_value}', '{description_value}')"
                )
                cursor.execute(query)
        fetch_databricks_table.clear()
        return True, ""
    except Exception as e:
        logger.exception("Erro ao salvar canal padrão no Databricks")
        return False, str(e)

@st.cache_data(ttl=3600)
def fetch_loggers_table():
    query = f"SELECT * FROM {CATALOGO_SCHEMA}.`loggers`"
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                try:
                    df_result = cursor.fetchall_arrow().to_pandas()
                except Exception:
                    rows = cursor.fetchall()
                    cols = [desc[0] for desc in cursor.description]
                    df_result = pd.DataFrame(rows, columns=cols)
        
        if "Front_No" in df_result.columns:
            df_result["Front_No"] = df_result["Front_No"].astype(str).str.strip()
        if "Qnt_de_canais" in df_result.columns:
            df_result["Qnt_de_canais"] = pd.to_numeric(df_result["Qnt_de_canais"], errors='coerce').fillna(16)
            
        return df_result, True, ""
    except Exception as e:
        logger.error(f"Erro ao buscar loggers: {e}")
        return pd.DataFrame(), False, str(e)

def aplicar_toggle_exportacao(session_key, toggle_key):
    """Aplica o estado do toggle a todos os canais do projeto selecionado."""
    df = st.session_state.get(session_key)
    if df is not None:
        df["Exportar?"] = bool(st.session_state.get(toggle_key, False))
        st.session_state[session_key] = df

# --- FUNÇÕES DE UI E CONTRASTE VISUAL ---
def generate_pdf(df, title, info_teste=None):
    if not PDF_AVAILABLE: return None
    try:
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], textColor=colors.HexColor("#243782"), alignment=TA_CENTER, fontSize=16, spaceAfter=20)
        elements.append(Paragraph(title, title_style))
        
        # --- NOVO: Adicionando as informações do teste (Project, Chassi, Test ID) ---
        if info_teste:
            info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=11, spaceAfter=6, textColor=colors.HexColor("#243782"))
            for chave, valor in info_teste.items():
                texto_valor = valor if valor.strip() != "" else "N/A"
                elements.append(Paragraph(f"<b>{chave}:</b> {texto_valor}", info_style))
            elements.append(Spacer(1, 15)) # Espaço entre as informações e a tabela
        # --------------------------------------------------------------------------

        cell_style = styles["Normal"]
        cell_style.fontSize = 9
        data = [df.columns.tolist()] 
        
        for index, row in df.iterrows():
            wrapped_row = []
            for item in row:
                wrapped_row.append(Paragraph(str(item), cell_style))
            data.append(wrapped_row)

        col_widths = [90, 235, 110, 100]
        t = Table(data, colWidths=col_widths, repeatRows=1) 
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#243782")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10), ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
        ]))
        elements.append(t)
        doc.build(elements)
        return pdf_buffer.getvalue()
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}")
        return None

# --- TELA 1: HOME (MENU PRINCIPAL) ---
def render_visualizador():
    st.markdown("<br>", unsafe_allow_html=True)

    if not DB_SQL_AVAILABLE:
        st.markdown(f"<div style='color: #ff5252; font-weight: bold; font-size: 1.1rem; margin-bottom: 10px;'>🚨 Erro Crítico: Dependências do Databricks pendentes. Detalhes: {DB_INSTALL_ERROR}</div>", unsafe_allow_html=True)
        return

    tabelas_disponiveis = get_available_tables()
    df_loggers, loggers_ok, _ = fetch_loggers_table()
    
    if loggers_ok and not df_loggers.empty:
        lista_modulos = df_loggers["Front_No"].tolist()
        dict_max_canais = dict(zip(df_loggers["Front_No"], df_loggers["Qnt_de_canais"]))
    else:
        lista_modulos = ["10259", "4179", "6722", "6723", "3020"]
        dict_max_canais = {m: 16 for m in lista_modulos}

    if not tabelas_disponiveis:
        tabelas_disponiveis = ["pontos_projetos_na", "pontos_projetos_turbo", "pontos_projetos_turbo_diesel"]

    st.markdown("### 📋 Seleção de Canais e Módulos IPETRONIK")
    st.markdown("<br>", unsafe_allow_html=True)

    def formatar_nome_tabela(nome_bruto):
        return nome_bruto.replace("_", " ").title().replace(" Na", " NA")

    col_tabela, _ = st.columns([1, 2])
    with col_tabela:
        tabela_selecionada = st.selectbox("Selecione a tabela de projetos:", tabelas_disponiveis, index=None, placeholder="Selecione uma tabela...", format_func=formatar_nome_tabela)

    if tabela_selecionada:
        session_key = f"df_{tabela_selecionada}"
        
        with st.spinner(f"A carregar dados de '{tabela_selecionada}'..."):
            df_raw, sucesso, erro_msg = fetch_databricks_table(tabela_selecionada)
            
        if sucesso and not df_raw.empty:
            
            # BLINDAGEM DE TIPOS (Evita crash do Databricks pd.NA)
            if session_key not in st.session_state:
                df_filtrado = df_raw.copy()
                df_filtrado['_sort_key'] = pd.to_numeric(df_filtrado['Ponto'], errors='coerce')
                df_filtrado = df_filtrado.sort_values(by=['_sort_key', 'Ponto']).drop(columns=['_sort_key']).reset_index(drop=True)
                
                df_filtrado.insert(2, "Módulo IPETRONIK", pd.Series([pd.NA] * len(df_filtrado), dtype="string"))
                df_filtrado.insert(3, "Canal do Módulo", pd.Series([pd.NA] * len(df_filtrado), dtype="Int64"))
                df_filtrado.insert(4, "Exportar?", pd.Series([True] * len(df_filtrado), dtype="bool"))
                
                st.session_state[session_key] = df_filtrado

            # FILTROS (Seu código atual)
            st.markdown("<div style='margin-top: 15px;'><h5 style='color: #FAFAFA; margin-bottom: 5px;'>🔍 Filtros e Ordenação</h5>", unsafe_allow_html=True)
            col_f1, col_f2, col_f3, _ = st.columns([1.5, 2, 2.5, 1.5])
            with col_f1: ordem_ponto = st.selectbox("📍 Ordem do Ponto:", ["Crescente", "Decrescente"])
            with col_f2: filtro_exp = st.selectbox("📥 Status de Exportação:", ["Mostrar Todos", "Apenas Marcados", "Apenas Desmarcados"])
            with col_f3:
                toggle_key = f"toggle_state_{tabela_selecionada}"
                if toggle_key not in st.session_state: st.session_state[toggle_key] = True
                st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                st.toggle(
                    "Marcar todos os canais",
                    key=toggle_key,
                    help="Ative para incluir todos os canais na exportação; desative para desmarcar todos.",
                    on_change=aplicar_toggle_exportacao,
                    args=(session_key, toggle_key),
                )
            st.markdown("</div><br>", unsafe_allow_html=True)

            # --- NOVO: Campos de Informação do Teste ---
            st.markdown("<h5 style='color: #FAFAFA; margin-bottom: 5px;'>📝 Informações do Teste (Para o PDF)</h5>", unsafe_allow_html=True)
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1: project_input = st.text_input("Project", placeholder="Ex: Projeto X")
            with col_info2: chassi_input = st.text_input("Chassi", placeholder="Ex: 9B00000...")
            with col_info3: test_id_input = st.text_input("Test ID", placeholder="Ex: T-12345")
            st.markdown("<br>", unsafe_allow_html=True)
            # -------------------------------------------

            # PREPARAÇÃO (Seu código atual continua aqui...)

            # PREPARAÇÃO
            df_current = st.session_state[session_key]
            df_display = df_current.copy()
            if filtro_exp == "Apenas Marcados": df_display = df_display[df_display["Exportar?"] == True]
            elif filtro_exp == "Apenas Desmarcados": df_display = df_display[df_display["Exportar?"] == False]
                
            df_display['_sort_key'] = pd.to_numeric(df_display['Ponto'], errors='coerce')
            ordem_ascendente = (ordem_ponto == "Crescente")
            df_display = df_display.sort_values(by=['_sort_key', 'Ponto'], ascending=[ordem_ascendente, ordem_ascendente]).drop(columns=['_sort_key'])
            pontos_manuais_key = f"pontos_manuais_{tabela_selecionada}"
            pontos_manuais = st.session_state.get(pontos_manuais_key, [])
            if pontos_manuais:
                mask_manuais = df_display["Ponto"].astype(str).isin(pontos_manuais)
                df_display = pd.concat([df_display.loc[~mask_manuais], df_display.loc[mask_manuais]])
            calc_height = 45 + (len(df_display) * 36) + 20
            
            # --- RENDERIZAR TABELA EM LOTE (SEM LAG) ---
            st.markdown("<p style='font-size: 1rem; color: #00E5FF; font-weight: bold;'> Edição em Lote: Selecione os módulos e canais livremente e clique no botão abaixo para preparar o arquivo.</p>", unsafe_allow_html=True)
            
            with st.form(key=f"form_editor_{tabela_selecionada}"):
                df_editado = st.data_editor(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    height=calc_height,
                    column_config={
                        "Ponto": st.column_config.TextColumn("📍 Ponto", disabled=True, width="small"),
                        "Descrição": st.column_config.TextColumn("🏷️ Descrição do Canal", disabled=True, width="large"),
                        "Módulo IPETRONIK": st.column_config.SelectboxColumn("🎛️ Módulo", options=lista_modulos, width="medium"),
                        "Canal do Módulo": st.column_config.NumberColumn("🔌 Canal", disabled=False, width="small"),
                        "Exportar?": st.column_config.CheckboxColumn("📥 Exportar?", width="small"),
                    }
                )
                
                # O botão que dispara o processamento todo de uma vez
                submit_edits = st.form_submit_button("Salvar Tabela", type="primary", use_container_width=True)

            # --- LÓGICA DE COMPARAÇÃO (RODA APENAS NO CLIQUE DO BOTÃO) ---
            if submit_edits:
                if not df_editado.equals(df_display):
                    def mudou(v1, v2):
                        if pd.isna(v1) and pd.isna(v2): return False
                        if pd.isna(v1) != pd.isna(v2): return True
                        return v1 != v2

                    for idx in df_editado.index:
                        mod_editado = df_editado.at[idx, "Módulo IPETRONIK"]
                        canal_editado = df_editado.at[idx, "Canal do Módulo"]
                        exp_editado = df_editado.at[idx, "Exportar?"]
                        
                        mod_orig = df_current.at[idx, "Módulo IPETRONIK"]
                        canal_orig = df_current.at[idx, "Canal do Módulo"]
                        exp_orig = df_current.at[idx, "Exportar?"]
                        changed_modulo = False
                        
                        if mudou(exp_editado, exp_orig):
                            df_current.at[idx, "Exportar?"] = exp_editado
                            
                        if mudou(mod_editado, mod_orig):
                            df_current.at[idx, "Módulo IPETRONIK"] = pd.NA if pd.isna(mod_editado) or str(mod_editado).strip() == "" else str(mod_editado)
                            changed_modulo = True
                            
                        if mudou(canal_editado, canal_orig):
                            modulo_atual = df_current.at[idx, "Módulo IPETRONIK"]
                            if pd.notna(modulo_atual) and str(modulo_atual).strip() != "":
                                max_permitido = int(dict_max_canais.get(str(modulo_atual), 16))
                                if pd.notna(canal_editado) and canal_editado > max_permitido:
                                    df_current.at[idx, "Canal do Módulo"] = pd.NA
                                else:
                                    df_current.at[idx, "Canal do Módulo"] = int(canal_editado) if pd.notna(canal_editado) else pd.NA
                            else:
                                df_current.at[idx, "Canal do Módulo"] = pd.NA
                            changed_modulo = True

                        if changed_modulo:
                            modulo = df_current.at[idx, "Módulo IPETRONIK"]
                            if pd.notna(modulo) and str(modulo).strip() != "":
                                max_permitido = int(dict_max_canais.get(str(modulo), 16))
                                mask = df_current["Módulo IPETRONIK"] == modulo
                                
                                canais_preenchidos = pd.to_numeric(df_current.loc[mask, "Canal do Módulo"], errors='coerce').dropna().astype(int).tolist()
                                canais_em_uso = set([c for c in canais_preenchidos if c <= max_permitido])
                                canais_livres = [c for c in range(1, max_permitido + 1) if c not in canais_em_uso]
                                canal_atual = df_current.at[idx, "Canal do Módulo"]
                                
                                if pd.isna(canal_atual) or (isinstance(canal_atual, (int, float)) and canal_atual > max_permitido):
                                    if canais_livres:
                                        df_current.at[idx, "Canal do Módulo"] = int(canais_livres.pop(0))
                                    else:
                                        df_current.at[idx, "Módulo IPETRONIK"] = pd.NA
                                        df_current.at[idx, "Canal do Módulo"] = pd.NA

                    st.session_state[session_key] = df_current
                    st.rerun()

            # Permite cadastrar um ponto que ainda não existe na tabela do projeto.
            st.markdown("#### ➕ Adicionar canal manualmente")
            with st.form(key=f"form_novo_canal_{tabela_selecionada}"):
                col_ponto, col_descricao, col_adicionar = st.columns([1, 3, 1])
                with col_ponto:
                    novo_ponto = st.text_input("Ponto", placeholder="Ex: 101")
                with col_descricao:
                    nova_descricao = st.text_input("Descrição do Canal", placeholder="Ex: Temperatura do motor")
                adicionar_como_padrao = st.checkbox("Adicionar como padrão?", value=False)
                with col_adicionar:
                    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                    adicionar_canal = st.form_submit_button("Adicionar canal", use_container_width=True)

            if adicionar_canal:
                ponto = novo_ponto.strip()
                descricao = nova_descricao.strip()
                if not ponto or not descricao:
                    st.warning("Informe o ponto e a descrição para adicionar o canal.")
                elif st.session_state[session_key]["Ponto"].astype(str).str.strip().eq(ponto).any():
                    st.warning(f"Já existe um canal com o ponto '{ponto}' neste projeto.")
                else:
                    salvo_no_databricks = True
                    erro_salvamento = ""
                    if adicionar_como_padrao:
                        salvo_no_databricks, erro_salvamento = save_project_channel(
                            tabela_selecionada, ponto, descricao
                        )

                    if not salvo_no_databricks:
                        st.error(f"Não foi possível salvar o canal padrão no Databricks: {erro_salvamento}")
                    else:
                        df_atualizado = st.session_state[session_key].copy()
                        nova_linha = {col: pd.NA for col in df_atualizado.columns}
                        nova_linha.update({
                            "Ponto": ponto,
                            "Descrição": descricao,
                            "Módulo IPETRONIK": pd.NA,
                            "Canal do Módulo": pd.NA,
                            "Exportar?": True,
                        })
                        st.session_state[session_key] = pd.concat(
                            [df_atualizado, pd.DataFrame([nova_linha])], ignore_index=True
                        )
                        st.session_state[pontos_manuais_key] = pontos_manuais + [ponto]
                        if adicionar_como_padrao:
                            st.session_state[f"canal_padrao_msg_{tabela_selecionada}"] = (
                                "Canal salvo como padrão no Databricks para este tipo de projeto."
                            )
                            fetch_databricks_table.clear()
                        st.rerun()

            mensagem_padrao_key = f"canal_padrao_msg_{tabela_selecionada}"
            if mensagem_padrao_key in st.session_state:
                st.success(st.session_state.pop(mensagem_padrao_key))

            # --- VALIDAÇÕES DE EXPORTAÇÃO E ALERTAS ---
            df_selecionados = st.session_state[session_key][st.session_state[session_key]["Exportar?"] == True].copy()
            total_selecionados = len(df_selecionados)
            
            contagem_modulos = df_selecionados["Módulo IPETRONIK"].dropna().value_counts()
            linhas_sem_modulo = df_selecionados["Módulo IPETRONIK"].isna().sum()
            
            # Exibe um contador visual para o usuário
            cor_contador = "#00E676" if total_selecionados <= 16 else "#ff5252"
            st.markdown(f"<p style='font-size: 1.1rem; font-weight: bold; color: {cor_contador};'>Canais selecionados para exportação: {total_selecionados} / 16</p>", unsafe_allow_html=True)

            modulos_excedidos = []
            for modulo, count in contagem_modulos.items():
                max_permitido = dict_max_canais.get(str(modulo), 16)
                if count > max_permitido:
                    modulos_excedidos.append(f"{modulo} (Máx {int(max_permitido)})")

            st.markdown("<br>", unsafe_allow_html=True)
            pode_exportar = True

            # Validação 1: Limite Global de 16 Canais
            if total_selecionados > 16:
                pode_exportar = False
                st.markdown(f"<div style='color: #ff5252; font-weight: bold; font-size: 1rem; margin-bottom: 10px;'>⚠️ Limite máximo atingido! Você selecionou {total_selecionados} canais, mas o limite é 16.</div>", unsafe_allow_html=True)
            
            # Validação 2: Limites por Hardware (Módulo)
            elif modulos_excedidos:
                pode_exportar = False
                modulos_erro = ", ".join(modulos_excedidos)
                st.markdown(f"<div style='color: #ff5252; font-weight: bold; font-size: 1rem; margin-bottom: 10px;'>⚠️ Limites de hardware excedidos. Reduza a seleção: {modulos_erro}.</div>", unsafe_allow_html=True)
            
            # Validação 3: Canais sem Módulo
            elif linhas_sem_modulo > 0:
                pode_exportar = False
                st.markdown("<div style='color: #ff5252; font-weight: bold; font-size: 1rem; margin-bottom: 10px;'>⚠️ Existem canais selecionados para exportação sem Módulo associado.</div>", unsafe_allow_html=True)

            if pode_exportar and not df_selecionados.empty:
                st.markdown("<div style='color: #00E676; font-weight: bold; font-size: 1.1rem; margin-bottom: 10px; margin-top: 10px;'>✅ Sucesso! Os arquivos estão processados e prontos.</div>", unsafe_allow_html=True)
                
                df_selecionados["Canal do Módulo"] = pd.to_numeric(df_selecionados["Canal do Módulo"], errors='coerce').astype(int)
                
                if loggers_ok and not df_loggers.empty:
                    df_final_export = df_selecionados.merge(df_loggers, left_on="Módulo IPETRONIK", right_on="Front_No", how="left")
                else:
                    df_final_export = df_selecionados.copy()
                    for col in ["MP_Type", "Sensor_Unit_/_Phys_Unit", "Sample_Freq", "Sensor_Min", "Sensor_Max"]:
                        df_final_export[col] = pd.NA
                
                df_ipemotion = pd.DataFrame({
                    "MP Identifier": df_final_export["Descrição"], 
                    "MP Type": df_final_export["MP_Type"].fillna("M-THERMO 16"), 
                    "Supply Voltage": "",
                    "Sensor Min": df_final_export["Sensor_Min"].fillna("-60"),
                    "Sensor Max": df_final_export["Sensor_Max"].fillna("1370"),
                    "Sensor Unit": df_final_export["Sensor_Unit_/_Phys_Unit"].fillna("°C"),
                    "Phys Min": df_final_export["Sensor_Min"].fillna("-60"),
                    "Phys Max": df_final_export["Sensor_Max"].fillna("1370"),
                    "Phys Unit": df_final_export["Sensor_Unit_/_Phys_Unit"].fillna("°C"),
                    "Sample Freq": df_final_export["Sample_Freq"].fillna("1"),
                    "Active": "1",
                    "Front No": df_final_export["Módulo IPETRONIK"],
                    "Channel No": df_final_export["Canal do Módulo"], 
                    "Description": df_final_export["Ponto"], 
                    "Hardware Filter": "",
                    "Sw Filter Type": "",
                    "Sw Filter Freq": ""
                })
                
                csv_bytes = df_ipemotion.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                
                pdf_bytes = None
                if PDF_AVAILABLE:
                    df_para_pdf = df_selecionados[["Ponto", "Descrição", "Módulo IPETRONIK", "Canal do Módulo"]].copy()
                    df_para_pdf = df_para_pdf.sort_values(by=["Módulo IPETRONIK", "Canal do Módulo"])
                    titulo_pdf = f"Relatório de Setup de Canais - {formatar_nome_tabela(tabela_selecionada)}"
                    
                    # --- NOVO: Empacotando as informações e enviando para a função ---
                    info_dict = {
                        "Project": project_input,
                        "Chassi": chassi_input,
                        "Test ID": test_id_input
                    }
                    pdf_bytes = generate_pdf(df_para_pdf, titulo_pdf, info_teste=info_dict)
                    # -----------------------------------------------------------------

                col_btn, _ = st.columns([4, 4])
                with col_btn:
                    if pdf_bytes:
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                            zf.writestr(f"setup_canais_ipemotion_{tabela_selecionada}.csv", csv_bytes)
                            zf.writestr(f"relatorio_setup_{tabela_selecionada}.pdf", pdf_bytes)
                            
                        st.download_button(
                            label="📥 Baixar Pacote (CSV + PDF)", 
                            data=zip_buffer.getvalue(), 
                            file_name=f"setup_completo_{tabela_selecionada}.zip", 
                            mime="application/zip", 
                            type="primary", 
                            use_container_width=True
                        )
                    else:
                        st.download_button(
                            label="📥 Exportar IPEmotion (CSV)", 
                            data=csv_bytes, 
                            file_name=f"setup_canais_ipemotion_{tabela_selecionada}.csv", 
                            mime='text/csv', 
                            type="primary", 
                            use_container_width=True
                        )
                        if not PDF_AVAILABLE: st.warning("⚠️ O PDF não foi incluído porque a biblioteca 'reportlab' não está instalada. No seu terminal, execute: pip install reportlab")
                        else: st.error("⚠️ Ocorreu um erro interno ao gerar o PDF. Apenas o CSV foi disponibilizado.")
            
        elif not sucesso:
            st.markdown(f"<div style='color: #ff5252; font-weight: bold; font-size: 1.1rem; margin-top: 15px;'>🚨 Erro ao ligar ao Databricks:<br>{erro_msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color: #ffb300; font-weight: bold; font-size: 1.1rem; margin-top: 15px;'>⚠️ A tabela selecionada não contém dados.</div>", unsafe_allow_html=True)

# --- EXECUÇÃO PRINCIPAL ---
