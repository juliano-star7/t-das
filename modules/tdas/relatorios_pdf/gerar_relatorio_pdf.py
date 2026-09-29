import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relatorio_tdas_app.pdf")
NAVY = HexColor("#243782")
LIGHT = HexColor("#F3F7FF")
BLUE = HexColor("#00D2F2")
DARK = HexColor("#1D1D1D")
GRAY = HexColor("#5F6673")
BORDER = HexColor("#D9E2F2")


def draw_header(c, title):
    w, h = A4
    c.setFillColor(NAVY)
    c.rect(0, h - 2.3 * cm, w, 2.2 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(1.2 * cm, h - 1.2 * cm, title)
    c.setFont("Helvetica", 9)
    c.drawString(1.2 * cm, h - 1.7 * cm, "Relatório técnico do aplicativo T-DAS")


def write_paragraph(c, x, y, text, font_name="Helvetica", font_size=10, color=DARK, width=16.5 * cm):
    c.setFillColor(color)
    c.setFont(font_name, font_size)
    lines = []
    words = text.split()
    current = ""
    for word in words:
        candidate = current + (" " if current else "") + word
        if c.stringWidth(candidate, font_name, font_size) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    for line in lines:
        c.drawString(x, y, line)
        y -= font_size * 1.3
    return y


def draw_section(c, title, y, page_height=A4[1]):
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.2 * cm, y, title)
    c.setFillColor(BORDER)
    c.rect(1.2 * cm, y - 0.18 * cm, 14.5 * cm, 0.08 * cm, fill=1, stroke=0)
    return y - 0.7 * cm


def draw_bullet_list(c, x, y, items, bullet="• ", font_size=10.):
    c.setFillColor(DARK)
    c.setFont("Helvetica", font_size)
    line_gap = font_size * 1.35
    for item in items:
        c.drawString(x, y, bullet + item)
        y -= line_gap
    return y


def draw_box(c, x, y, w, h, title, color_fill=LIGHT, title_color=NAVY, border_color=NAVY, text_color=DARK):
    c.setFillColor(color_fill)
    c.setStrokeColor(border_color)
    c.setLineWidth(1.2)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
    c.setFillColor(title_color)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + w / 2, y + h - 0.42 * cm, title)
    c.setFillColor(text_color)
    c.setFont("Helvetica", 8.2)
    return


def draw_flowchart(c, y_start=15.2 * cm):
    page_w, _ = A4
    box_w = 3.0 * cm
    box_h = 1.7 * cm
    gap = 0.7 * cm
    total_w = (5 * box_w) + (4 * gap)
    x0 = (page_w - total_w) / 2

    positions = []
    for i in range(5):
        x = x0 + i * (box_w + gap)
        if i == 0:
            label = "Entrada"
            txt = "Upload\nCSV/XLSX"
        elif i == 1:
            label = "UI"
            txt = "Metadados\n+ filtro"
        elif i == 2:
            label = "Process"
            txt = "Leitura e\nlimpeza"
        elif i == 3:
            label = "Core"
            txt = "Detecte\nveículo +\nFases"
        else:
            label = "Saída"
            txt = "Gráficos +\nPDF"
        positions.append((x, y_start, txt, label))

    for x, y, txt, label in positions:
        draw_box(c, x, y, box_w, box_h, label, color_fill=LIGHT, title_color=NAVY)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 8.1)
        lines = txt.split("\n")
        start_y = y + box_h - 0.85 * cm
        for line in lines:
            c.drawCentredString(x + box_w / 2, start_y, line)
            start_y -= 0.3 * cm

    for i in range(len(positions) - 1):
        x1, y1, _, _ = positions[i]
        x2, y2, _, _ = positions[i + 1]
        c.setStrokeColor(NAVY)
        c.setLineWidth(1.2)
        start_x = x1 + box_w
        end_x = x2
        y_mid = y1 + box_h / 2
        c.line(start_x, y_mid, end_x, y_mid)
        c.line(end_x, y_mid, end_x - 0.22 * cm, y_mid + 0.16 * cm)
        c.line(end_x, y_mid, end_x - 0.22 * cm, y_mid - 0.16 * cm)


def main():
    c = canvas.Canvas(OUTPUT_PATH, pagesize=A4)
    w, h = A4

    draw_header(c, "T-DAS - Relatório do aplicativo")

    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(1.2 * cm, h - 3.5 * cm, "Resumo executivo")

    c.setFont("Helvetica", 11)
    intro = (
        "O app T-DAS automatiza a leitura, limpeza, mapeamento e visualização de arquivos de teste térmico "
        "e de desempenho, com foco em provas como Cool Down e US City."
    )
    write_paragraph(c, 1.2 * cm, h - 5.2 * cm, intro, font_name="Helvetica", font_size=11, width=15 * cm)

    bullet_items = [
        "Recebe arquivos CSV, XLS e XLSX contendo sinais de temperatura, pressão, velocidade e outras variáveis do veículo.",
        "Identifica o tipo de veículo, faz o alinhamento de tempo, detecta fases do ensaio e monta gráficos de diagnóstico.",
        "Exporta dados tratados em Excel/CSV e gera um relatório PDF com gráficos, comentários e tabela CPIT para provas Cool Down."
    ]
    y = h - 7.5 * cm
    y = draw_bullet_list(c, 1.5 * cm, y, bullet_items, font_size=10.5)

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(NAVY)
    c.drawString(1.2 * cm, y - 0.7 * cm, "Objetivo da aplicação")
    c.setFillColor(DARK)
    c.setFont("Helvetica", 10.5)
    obj = (
        "O objetivo principal é transformar dados brutos de ensaios em um pacote analítico estruturado, com "
        "gráficos, fases do teste e documentação pronta para revisão técnica, exportação e entrega ao cliente."
    )
    y = write_paragraph(c, 1.2 * cm, y - 1.7 * cm, obj, font_name="Helvetica", font_size=10.5, width=15.2 * cm)

    c.showPage()

    draw_header(c, "T-DAS - Arquitetura e fluxo")
    y = h - 2.7 * cm
    y = draw_section(c, "1. Entradas do sistema", y)
    y = draw_bullet_list(c, 1.5 * cm, y - 0.2 * cm, [
        "Arquivo carregado via st.file_uploader em app.py.",
        "Dados de metadados do ensaio, como projeto, marca, motor, fase, data e observações.",
        "Dados do Databricks para listas de seleção (projetos, motores, chassis, anos, fases, etc.).",
        "Tipo de prova selecionado: Cool Down, US City, Heavy Urban, TVM e outros."
    ], font_size=10.2)

    y = draw_section(c, "2. Fluxo principal do app", y - 0.5 * cm)
    draw_flowchart(c, y - 2.8 * cm)

    c.showPage()

    draw_header(c, "T-DAS - Entradas, saídas e blocos principais")
    y = h - 2.7 * cm
    y = draw_section(c, "3. Pontos de entrada", y)
    y = draw_bullet_list(c, 1.5 * cm, y - 0.2 * cm, [
        "app.py: aba '1. Setup & Processing' — carregamento do arquivo e metadados do ensaio.",
        "st.selectbox e st.date_input — escolhe data, projeto, motor, fase, engineers e tipo de prova.",
        "combobox_dinamico — permite seleção ou adição de valores e gravação em Databricks.",
        "if st.button('Load and Process Data') — dispara a rotina de processamento e validação."
    ], font_size=10.1)

    y = draw_section(c, "4. Pontos de processamento", y - 0.4 * cm)
    y = draw_bullet_list(c, 1.5 * cm, y - 0.2 * cm, [
        "carregar_e_tratar_dados(): identifica cabeçalho, lê CSV/XLSX, normaliza separador e converte números.",
        "detectar_tipo_veiculo(): busca nomes de colunas para inferir o tipo do veículo.",
        "filtrar_e_resetar_tempo(): remove início de idle e reseta o tempo do ensaio.",
        "detectar_fases_do_teste(): separa fases como Phase 1, Phase 2, Idle e outras.",
        "executar_logica_processamento(): mapeia variáveis conforme o tipo de prova e monta o DataFrame final."
    ], font_size=10.1)

    y = draw_section(c, "5. Pontos de saída", y - 0.4 * cm)
    y = draw_bullet_list(c, 1.5 * cm, y - 0.2 * cm, [
        "st.download_button — gera Excel e CSV limpos do DataFrame final.",
        "Plotly — monta gráficos interativos na aba de visualização.",
        "gerar_imagem_grafico_matplotlib() — cria imagens estáticas do gráfico para o PDF.",
        "Process PDF Report — gera relatório completo com capa, gráficos e CPIT.",
        "template.html / HTML_TEMPLATE_REPORT — template HTML usado para a capa e páginas do relatório PDF."
    ], font_size=10.1)

    c.showPage()

    draw_header(c, "T-DAS - Principais trechos de código")
    y = h - 2.9 * cm
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1.2 * cm, y, "Blocos importantes do código")
    y -= 0.8 * cm
    entries = [
        "app.py: ponto central do app, com UI, processamento principal, gráficos, export e geração do PDF.",
        "carregar_dados_do_databricks(): consulta o banco e alimenta dropdowns com listas de projeto, motores, marcas e fases.",
        "adicionar_item_databricks(): grava novo valor no banco quando o usuário adiciona uma opção manualmente.",
        "detectar_fases_do_teste(): separa ciclos e fases por velocidade e janela móvel.",
        "gerar_imagem_grafico_matplotlib(): desenha gráficos com fases e marcações para inclusão no relatório PDF.",
        "calcular_cpit(): estrutura a tabela de resultados para o caso Cool Down."
    ]
    y = draw_bullet_list(c, 1.5 * cm, y, entries, font_size=9.8)

    y -= 0.3 * cm
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1.2 * cm, y, "Arquivos relevantes no workspace")
    y -= 0.7 * cm
    files = [
        "app.py — código principal do app Streamlit.",
        "template.html — modelo base do relatório em PDF.",
        "app.yaml — configuração de deploy / runtime da aplicação.",
        "requirements.txt — dependências da solução (Streamlit, pandas, xhtml2pdf, plotly, etc.)."
    ]
    y = draw_bullet_list(c, 1.5 * cm, y, files, font_size=9.8)

    c.setFillColor(GRAY)
    c.setFont("Helvetica-Oblique", 8)
    c.drawRightString(w - 1.2 * cm, 0.7 * cm, "Gerado automaticamente para documentação do projeto T-DAS")

    c.save()
    print(f"PDF criado em: {OUTPUT_PATH}")
