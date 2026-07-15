from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as PdfImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVIDENCE = DOCS / "evidence"
DOCX_OUT = DOCS / "Informe_Ticket_Resilience_Lab.docx"
PDF_OUT = DOCS / "Informe_Ticket_Resilience_Lab.pdf"
DIAGRAM_OUT = DOCS / "architecture-distribution.png"


TITLE = "Ticket Resilience Lab"
SUBTITLE = "Mecanismos de tolerancia a fallas en Kubernetes"
AUTHORS = "Alexander y Jean Pierre"
REPO_URL = "https://github.com/jean-pierre-valarezo/ticket-resilience-lab.git"


FAILURES = [
    [
        "Inventario Fantasma",
        "Disponibilidad",
        "Escalar deployment/inventory a 0 replicas",
        "Retry con backoff y error controlado",
        "Implementado",
    ],
    [
        "Pasarela Lenta",
        "Latencia",
        "PAYMENT_DELAY_MS=20000",
        "Timeout + circuit breaker",
        "Implementado",
    ],
    [
        "Diluvio de Peticiones",
        "Sobrecarga",
        "25 solicitudes consecutivas al gateway",
        "Rate limiting",
        "Implementado",
    ],
    [
        "Base de Datos Intermitente",
        "Conectividad",
        "Flapping/reinicio controlado de PostgreSQL",
        "Failover, backoff, idempotencia",
        "Analisis teorico",
    ],
    [
        "Correo Perdido",
        "Fallo no critico",
        "Escalar deployment/notifications a 0 replicas",
        "Fallback pending",
        "Implementado",
    ],
    [
        "Condicion de Carrera",
        "Consistencia",
        "Compras concurrentes sobre un mismo asiento",
        "Transacciones y bloqueo pesimista",
        "Analisis teorico",
    ],
]


IMPLEMENTED = [
    {
        "title": "Inventario Fantasma",
        "failure": "El servicio inventory se escala a 0 replicas.",
        "defense": "reservations aplica retry con backoff y responde con un error controlado si no puede validar inventario.",
        "result": "La reserva falla con HTTP 503 y no se confirma una reserva sin inventario.",
        "evidence": ["09-chaos-inventory-down-http-503.png"],
    },
    {
        "title": "Pasarela Lenta",
        "failure": "payments simula 20 segundos de latencia con PAYMENT_DELAY_MS=20000.",
        "defense": "reservations usa timeout y circuit breaker. Despues de tres fallos, el circuito pasa a open.",
        "result": "Los intentos devuelven HTTP 503 y /resilience muestra payment_circuit.state = open.",
        "evidence": [
            "11-chaos-payments-slow-circuit-breaker-open-1.png",
            "12-chaos-payments-slow-circuit-breaker-open-2.png",
        ],
    },
    {
        "title": "Correo Perdido",
        "failure": "notifications se escala a 0 replicas.",
        "defense": "La notificacion se trata como dependencia no critica. La reserva se conserva y la notificacion queda pending.",
        "result": "La respuesta es HTTP 200, status confirmed y notification.status pending.",
        "evidence": ["15-chaos-notifications-down-fallback-pending.png"],
    },
    {
        "title": "Diluvio de Peticiones",
        "failure": "Se envian 25 solicitudes consecutivas contra POST /reserve.",
        "defense": "gateway aplica rate limiting por cliente dentro de una ventana temporal.",
        "result": "El sistema responde HTTP 429 cuando se supera el limite de peticiones.",
        "evidence": ["17-chaos-traffic-spike-rate-limit-429.png"],
    },
]


KEY_EVIDENCE = [
    ("Cluster Kubernetes con dos nodos Ready", "01-k8s-dos-nodos-ready.png"),
    ("Pods desplegados con inventory replicado entre nodos", "02-k8s-pods-inventory-replicado-dos-nodos.png"),
    ("Reserva base confirmada", "06-baseline-reserva-exitosa.png"),
    ("Inventario caido con HTTP 503", "09-chaos-inventory-down-http-503.png"),
    ("Pagos lentos con circuit breaker abierto", "12-chaos-payments-slow-circuit-breaker-open-2.png"),
    ("Notificaciones caidas con fallback pending", "15-chaos-notifications-down-fallback-pending.png"),
    ("Diluvio de peticiones con HTTP 429", "17-chaos-traffic-spike-rate-limit-429.png"),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_paths = [
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf") if bold else Path("C:/Windows/Fonts/calibri.ttf"),
    ]
    for path in font_paths:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def draw_box(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], text: str, fill: str, outline: str) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=outline, width=3)
    lines: list[str] = []
    for part in text.split("\n"):
        lines.extend(wrap(part, 22) or [""])
    f = font(24, bold=True)
    total_h = len(lines) * 30
    y = y1 + ((y2 - y1 - total_h) // 2)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f)
        w = bbox[2] - bbox[0]
        draw.text((x1 + ((x2 - x1 - w) // 2), y), line, fill="#111827", font=f)
        y += 30


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
    draw.line([start, end], fill="#334155", width=4)
    ex, ey = end
    sx, sy = start
    if ex >= sx:
        points = [(ex, ey), (ex - 16, ey - 9), (ex - 16, ey + 9)]
    else:
        points = [(ex, ey), (ex + 16, ey - 9), (ex + 16, ey + 9)]
    draw.polygon(points, fill="#334155")


def build_diagram() -> None:
    img = Image.new("RGB", (1600, 900), "#f8fafc")
    draw = ImageDraw.Draw(img)
    title_font = font(34, bold=True)
    small_font = font(20)
    draw.text((55, 35), "Arquitectura y distribucion observada en Kubernetes", fill="#0f172a", font=title_font)

    draw.rounded_rectangle((55, 110, 760, 820), radius=28, outline="#2563eb", width=4, fill="#eff6ff")
    draw.rounded_rectangle((840, 110, 1545, 820), radius=28, outline="#16a34a", width=4, fill="#f0fdf4")
    draw.text((95, 135), "Nodo ticket-lab", fill="#1d4ed8", font=font(28, bold=True))
    draw.text((880, 135), "Nodo ticket-lab-m02", fill="#15803d", font=font(28, bold=True))

    boxes = {
        "reservations": (170, 250, 420, 360, "Reservations\nCore", "#dbeafe", "#1d4ed8"),
        "inventory-a": (470, 250, 720, 360, "Inventory\nreplica A", "#dbeafe", "#1d4ed8"),
        "gateway": (950, 210, 1200, 320, "API\nGateway", "#dcfce7", "#15803d"),
        "payments": (950, 380, 1200, 490, "Payments\nStub", "#dcfce7", "#15803d"),
        "notifications": (950, 550, 1200, 660, "Notifications\nStub", "#dcfce7", "#15803d"),
        "inventory-b": (1245, 210, 1495, 320, "Inventory\nreplica B", "#dcfce7", "#15803d"),
        "postgres": (1245, 420, 1495, 530, "PostgreSQL", "#dcfce7", "#15803d"),
    }
    for item in boxes.values():
        draw_box(draw, item[:4], item[4], item[5], item[6])

    draw_box(draw, (55, 430, 300, 540), "Cliente /\nDemo", "#ffffff", "#64748b")
    draw_arrow(draw, (300, 485), (950, 265))
    draw_arrow(draw, (950, 265), (420, 305))
    draw_arrow(draw, (420, 305), (470, 305))
    draw_arrow(draw, (720, 305), (1245, 265))
    draw_arrow(draw, (420, 330), (950, 435))
    draw_arrow(draw, (420, 350), (950, 605))
    draw_arrow(draw, (1370, 320), (1370, 420))

    note = "Inventory usa 2 replicas distribuidas entre nodos para cumplir el criterio multi-nodo."
    draw.text((95, 760), note, fill="#334155", font=small_font)
    img.save(DIAGRAM_OUT)


def add_docx_table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for idx, text in enumerate(headers):
        cell = table.rows[0].cells[idx]
        cell.text = text
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(8.5)
    for row in rows:
        cells = table.add_row().cells
        for idx, text in enumerate(row):
            cells[idx].text = text
            cells[idx].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for paragraph in cells[idx].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(8.2)


def add_docx_image(document: Document, image_name: str, caption: str, width: float = 6.2) -> None:
    path = EVIDENCE / image_name
    if not path.exists():
        return
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.add_picture(str(path), width=Inches(width))
    cap = document.add_paragraph(caption)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in cap.runs:
        run.italic = True
        run.font.size = Pt(9)


def build_docx() -> None:
    build_diagram()
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)
    for style_name, size, color in [
        ("Title", 24, RGBColor(15, 23, 42)),
        ("Heading 1", 16, RGBColor(30, 64, 175)),
        ("Heading 2", 13, RGBColor(15, 118, 110)),
    ]:
        style = styles[style_name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.color.rgb = color

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(TITLE)
    run.bold = True
    run.font.size = Pt(26)
    run.font.color.rgb = RGBColor(15, 23, 42)
    subtitle = doc.add_paragraph(SUBTITLE)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.runs[0].font.size = Pt(14)
    doc.add_paragraph(f"Integrantes: {AUTHORS}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Repositorio: {REPO_URL}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Fecha: 2026-07-14").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    doc.add_heading("1. Objetivo", level=1)
    doc.add_paragraph(
        "Implementar y demostrar mecanismos de tolerancia a fallas sobre una arquitectura simplificada de venta de entradas "
        "desplegada en Kubernetes. La practica provoca fallos reales sobre un cluster de dos nodos y verifica, con evidencia "
        "propia, que el sistema responde de forma controlada o se recupera sin colapsar."
    )

    doc.add_heading("2. Arquitectura", level=1)
    doc.add_paragraph(
        "La solucion usa microservicios comunicados por REST: gateway, reservations, inventory, payments, notifications y postgres."
    )
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(DIAGRAM_OUT), width=Inches(6.4))
    doc.add_paragraph(
        "El servicio critico inventory se despliega con 2 replicas y topologySpreadConstraints por hostname para distribuirlo entre nodos."
    )

    doc.add_heading("3. Despliegue Kubernetes", level=1)
    add_docx_table(
        doc,
        ["Elemento", "Valor"],
        [
            ["Cluster", "minikube perfil ticket-lab"],
            ["Nodos", "ticket-lab y ticket-lab-m02"],
            ["Namespace", "ticket-lab"],
            ["Componente critico replicado", "inventory con 2 replicas"],
            ["Manifiestos", "k8s/base"],
        ],
    )

    doc.add_heading("4. Mapeo de fallos", level=1)
    add_docx_table(doc, ["Fallo", "Tipo", "Inyeccion", "Defensa", "Estado"], FAILURES)

    doc.add_heading("5. Mecanismos implementados", level=1)
    for item in IMPLEMENTED:
        doc.add_heading(item["title"], level=2)
        doc.add_paragraph(f"Falla inyectada: {item['failure']}")
        doc.add_paragraph(f"Defensa implementada: {item['defense']}")
        doc.add_paragraph(f"Resultado observado: {item['result']}")
        doc.add_paragraph("Evidencia: " + ", ".join(item["evidence"]))

    doc.add_heading("6. Analisis teorico de fallos no implementados", level=1)
    doc.add_heading("Base de Datos Intermitente", level=2)
    doc.add_paragraph(
        "Una base de datos intermitente afecta operaciones de escritura y obliga a decidir entre disponibilidad y consistencia "
        "durante una particion. En reservas, confirmar sin escritura durable puede producir ventas fantasma."
    )
    doc.add_paragraph(
        "Solucion propuesta: base de datos de alta disponibilidad, failover, pool de conexiones, retries con backoff y jitter, "
        "idempotency keys y patron outbox para eventos posteriores a la escritura."
    )
    doc.add_heading("Condicion de Carrera", level=2)
    doc.add_paragraph(
        "La condicion de carrera aparece cuando dos clientes reservan el mismo asiento simultaneamente. Sin aislamiento transaccional, "
        "ambos pueden observar el asiento como disponible y confirmar ventas duplicadas."
    )
    doc.add_paragraph(
        "Solucion propuesta: transacciones ACID, SELECT FOR UPDATE, restriccion unica por asiento activo, holds temporales con expiracion "
        "y confirmacion final solo si el hold sigue vigente."
    )

    doc.add_heading("7. Conclusiones", level=1)
    doc.add_paragraph(
        "El laboratorio evidencia que cada patron debe ubicarse en el punto correcto: retry con backoff para dependencias transitorias, "
        "circuit breaker para servicios lentos, fallback para dependencias no criticas y rate limiting en el borde del sistema. "
        "La solucion queda reproducible mediante README, manifiestos Kubernetes, scripts de inyeccion y capturas de evidencia."
    )

    doc.add_page_break()
    doc.add_heading("Anexo: evidencias clave", level=1)
    for caption, image_name in KEY_EVIDENCE:
        add_docx_image(doc, image_name, caption)

    doc.save(DOCX_OUT)


def pdf_image(path: Path, max_width: float = 6.4 * inch) -> PdfImage:
    with Image.open(path) as img:
        width, height = img.size
    ratio = max_width / width
    return PdfImage(str(path), width=max_width, height=height * ratio)


def build_pdf() -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCenter", parent=styles["Title"], alignment=TA_CENTER, fontSize=22, leading=26)
    subtitle_style = ParagraphStyle("SubtitleCenter", parent=styles["Normal"], alignment=TA_CENTER, fontSize=12, leading=16)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=colors.HexColor("#1e40af"), spaceBefore=12, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#0f766e"), spaceBefore=8, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.5, leading=13, spaceAfter=6)
    caption_style = ParagraphStyle("Caption", parent=styles["Italic"], alignment=TA_CENTER, fontSize=8.5, leading=11)

    story = [
        Paragraph(TITLE, title_style),
        Paragraph(SUBTITLE, subtitle_style),
        Spacer(1, 0.15 * inch),
        Paragraph(f"Integrantes: {AUTHORS}", subtitle_style),
        Paragraph(f"Repositorio: {REPO_URL}", subtitle_style),
        Paragraph("Fecha: 2026-07-14", subtitle_style),
        PageBreak(),
        Paragraph("1. Objetivo", h1),
        Paragraph(
            "Implementar y demostrar mecanismos de tolerancia a fallas sobre una arquitectura simplificada de venta de entradas "
            "desplegada en Kubernetes. La practica provoca fallos reales sobre un cluster de dos nodos y verifica, con evidencia propia, "
            "que el sistema responde de forma controlada o se recupera sin colapsar.",
            body,
        ),
        Paragraph("2. Arquitectura", h1),
        Paragraph("La solucion usa microservicios comunicados por REST: gateway, reservations, inventory, payments, notifications y postgres.", body),
        pdf_image(DIAGRAM_OUT),
        Spacer(1, 0.1 * inch),
        Paragraph(
            "Inventory se despliega con 2 replicas y topologySpreadConstraints por hostname para distribuirlo entre nodos.",
            body,
        ),
        Paragraph("3. Despliegue Kubernetes", h1),
    ]

    deploy_table = Table(
        [["Elemento", "Valor"], ["Cluster", "minikube perfil ticket-lab"], ["Nodos", "ticket-lab y ticket-lab-m02"], ["Namespace", "ticket-lab"], ["Componente critico", "inventory con 2 replicas"], ["Manifiestos", "k8s/base"]],
        colWidths=[2.0 * inch, 4.4 * inch],
    )
    deploy_table.setStyle(table_style())
    story += [deploy_table, Spacer(1, 0.12 * inch), Paragraph("4. Mapeo de fallos", h1)]

    failure_rows = [["Fallo", "Tipo", "Inyeccion", "Defensa", "Estado"]] + FAILURES
    failure_table = Table(failure_rows, colWidths=[1.25 * inch, 0.9 * inch, 1.55 * inch, 1.55 * inch, 1.05 * inch], repeatRows=1)
    failure_table.setStyle(table_style(font_size=7.4))
    story += [failure_table, Paragraph("5. Mecanismos implementados", h1)]

    for item in IMPLEMENTED:
        story += [
            Paragraph(item["title"], h2),
            Paragraph(f"<b>Falla inyectada:</b> {item['failure']}", body),
            Paragraph(f"<b>Defensa:</b> {item['defense']}", body),
            Paragraph(f"<b>Resultado:</b> {item['result']}", body),
            Paragraph("<b>Evidencia:</b> " + ", ".join(item["evidence"]), body),
        ]

    story += [
        Paragraph("6. Analisis teorico de fallos no implementados", h1),
        Paragraph("Base de Datos Intermitente", h2),
        Paragraph(
            "Una base de datos intermitente afecta operaciones de escritura y obliga a decidir entre disponibilidad y consistencia durante una particion. "
            "En reservas, confirmar sin escritura durable puede producir ventas fantasma.",
            body,
        ),
        Paragraph(
            "Solucion propuesta: base de datos de alta disponibilidad, failover, pool de conexiones, retries con backoff y jitter, idempotency keys y patron outbox.",
            body,
        ),
        Paragraph("Condicion de Carrera", h2),
        Paragraph(
            "La condicion de carrera aparece cuando dos clientes reservan el mismo asiento simultaneamente. Sin aislamiento transaccional, ambos pueden observarlo como disponible.",
            body,
        ),
        Paragraph(
            "Solucion propuesta: transacciones ACID, SELECT FOR UPDATE, restriccion unica por asiento activo y holds temporales con expiracion.",
            body,
        ),
        Paragraph("7. Conclusiones", h1),
        Paragraph(
            "El laboratorio evidencia que cada patron debe ubicarse en el punto correcto: retry con backoff para dependencias transitorias, circuit breaker para servicios lentos, "
            "fallback para dependencias no criticas y rate limiting en el borde del sistema.",
            body,
        ),
        PageBreak(),
        Paragraph("Anexo: evidencias clave", h1),
    ]

    for caption, image_name in KEY_EVIDENCE:
        path = EVIDENCE / image_name
        if path.exists():
            story.append(KeepTogether([pdf_image(path), Spacer(1, 0.05 * inch), Paragraph(caption, caption_style)]))
            story.append(Spacer(1, 0.16 * inch))

    doc = SimpleDocTemplate(str(PDF_OUT), pagesize=letter, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.7 * inch, bottomMargin=0.7 * inch)
    doc.build(story)


def table_style(font_size: float = 8.5) -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )


def main() -> None:
    build_docx()
    build_pdf()
    print(DOCX_OUT)
    print(PDF_OUT)


if __name__ == "__main__":
    main()
