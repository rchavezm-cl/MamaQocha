"""
Módulo de Generación de Reportes Oficiales en PDF (Trazabilidad SEREMI / HACCP).
Genera documentos en memoria (bytes) con ReportLab para:
  1. Actas de Baja por Merma e Inocuidad
  2. Guías de Despacho y Traslado entre Sucursales (Individual y Manifiesto Ida/Retorno)
  3. Actas de Recepción de Materias Primas y Control de Cadena de Frío (HACCP)
  4. Actas de Manipulación y Producción en Cocina (Trazabilidad de Manipulador)
  5. Expediente Completo de Trazabilidad por Lote (Extremo a Extremo)
  6. Libros Consolidados por Período (Auditoría SEREMI)
"""

import io
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

TZ_CHILE = ZoneInfo("America/Santiago")

# Paleta corporativa alineada con app.py y generar_manual_pdf.py
C_PRIMARY = colors.HexColor("#0d2b45")
C_SECONDARY = colors.HexColor("#1a4d6f")
C_TEAL = colors.HexColor("#2a9d8f")
C_DANGER = colors.HexColor("#b91c1c")
C_WARN = colors.HexColor("#b45309")
C_INFO = colors.HexColor("#0369a1")
C_DARK = colors.HexColor("#1e293b")
C_MUTED = colors.HexColor("#64748b")
C_LIGHT = colors.HexColor("#f8fafc")
C_ZEBRA = colors.HexColor("#f1f5f9")
C_BORDER = colors.HexColor("#cbd5e1")


class SeremiNumberedCanvas(canvas.Canvas):
    """Canvas de dos pasos con encabezado corporativo, marca de auditoría SEREMI y 'Página X de Y'."""

    def __init__(self, *args, doc_title: str = "", doc_subtitle: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []
        self._doc_title = doc_title
        self._doc_subtitle = doc_subtitle

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_decorations(self, page_count: int):
        page_w, page_h = self._pagesize
        margin = 40
        self.saveState()

        # Encabezado superior
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(C_PRIMARY)
        self.drawString(margin, page_h - 26, f"MAMÁ QOCHA | {self._doc_title}")

        self.setFont("Helvetica", 7.5)
        self.setFillColor(C_MUTED)
        self.drawRightString(page_w - margin, page_h - 26, self._doc_subtitle)

        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.7)
        self.line(margin, page_h - 32, page_w - margin, page_h - 32)

        # Pie de página
        self.line(margin, 34, page_w - margin, 34)
        generado_str = datetime.now(TZ_CHILE).strftime("%d-%m-%Y %H:%M")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(C_MUTED)
        self.drawString(
            margin,
            22,
            f"Registro Oficial de Trazabilidad Sanitaria (SEREMI / HACCP) | Emitido: {generado_str}",
        )
        self.drawRightString(page_w - margin, 22, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


def _esc(val: Any) -> str:
    """Escapa caracteres XML básicos para evitar errores en ReportLab Paragraph."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "-"
    txt = str(val)
    return txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt_dt(val: Any, incluir_hora: bool = True) -> str:
    """Formatea fechas y timestamps (convirtiendo UTC/aware a hora local de Chile)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "-"
    if isinstance(val, pd.Timestamp):
        if pd.isna(val):
            return "-"
        dt = val.to_pydatetime()
    elif isinstance(val, datetime):
        dt = val
    elif isinstance(val, date):
        return val.strftime("%d-%m-%Y")
    else:
        return str(val)

    if dt.tzinfo is not None:
        dt = dt.astimezone(TZ_CHILE)
    return dt.strftime("%d-%m-%Y %H:%M" if incluir_hora else "%d-%m-%Y")


def _fmt_num(val: Any, decimales: int = 3) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "0"
    return f"{float(val):,.{decimales}f}"


def _fmt_clp(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "$0"
    return f"${float(val):,.0f}"


def _fmt_rol(rol: Any) -> str:
    if not rol or str(rol).strip() in ("-", "None"):
        return ""
    return str(rol).replace("_", " ").title()


def _estado_haccp(temp: Any) -> Tuple[str, str]:
    """Clasifica la temperatura de ingreso según protocolo sanitario HACCP (≤ 4°C)."""
    t = float(temp) if temp is not None and not pd.isna(temp) else 2.0
    if t > 5.0:
        return "NO CONFORME (>5°C)", "#b91c1c"
    if t > 4.0:
        return "LÍMITE (4.1-5°C)", "#b45309"
    return "CUMPLE (≤4°C)", "#15803d"


def _get_styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.white,
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#e2e8f0"),
        ),
        "h2": ParagraphStyle(
            "SectionH2",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=C_PRIMARY,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "BodyText",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=C_DARK,
        ),
        "cell": ParagraphStyle(
            "CellText",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=9.8,
            textColor=C_DARK,
        ),
        "cell_bold": ParagraphStyle(
            "CellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=9.8,
            textColor=C_DARK,
        ),
        "cell_right": ParagraphStyle(
            "CellRight",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=9.8,
            textColor=C_DARK,
            alignment=2,
        ),
        "th": ParagraphStyle(
            "TableHead",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=9.8,
            textColor=colors.white,
        ),
        "th_right": ParagraphStyle(
            "TableHeadRight",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=9.8,
            textColor=colors.white,
            alignment=2,
        ),
        "note": ParagraphStyle(
            "NoteBox",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=C_DARK,
        ),
    }


def _header_banner(
    titulo: str,
    folio_label: str,
    subtitulo: str,
    accent_color: colors.Color,
    content_width: float,
    styles: Dict[str, ParagraphStyle],
) -> Table:
    """Construye el banner superior corporativo del documento oficial."""
    left = [
        Paragraph(f"<b>{_esc(titulo)}</b>", styles["title"]),
        Spacer(1, 2),
        Paragraph(_esc(subtitulo), styles["subtitle"]),
    ]
    right = Paragraph(
        f"<font color='#cbd5e1' size='7.5'>FOLIO OFICIAL</font><br/>"
        f"<font color='#ffffff' size='12'><b>{_esc(folio_label)}</b></font>",
        ParagraphStyle(
            "FolioRight",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=2,
            textColor=colors.white,
        ),
    )
    tbl = Table([[left, right]], colWidths=[content_width * 0.74, content_width * 0.26])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), accent_color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return tbl


def _kv_grid(
    rows: List[List[Tuple[str, str]]],
    content_width: float,
    styles: Dict[str, ParagraphStyle],
) -> Table:
    """Renderiza una grilla de metadatos clave-valor con 2 o 3 pares por fila."""
    num_cols = max(len(r) for r in rows)
    col_w = content_width / num_cols
    table_data = []
    for row in rows:
        cells = []
        for label, val in row:
            cells.append(
                Paragraph(
                    f"<font color='#64748b' size='7'><b>{_esc(label).upper()}</b></font><br/>"
                    f"<font color='#1e293b' size='8.5'>{_esc(val)}</font>",
                    styles["cell"],
                )
            )
        while len(cells) < num_cols:
            cells.append(Paragraph("", styles["cell"]))
        table_data.append(cells)

    tbl = Table(table_data, colWidths=[col_w] * num_cols)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.75, C_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return tbl


def _styled_table(
    headers: Sequence[str],
    rows: List[List[Any]],
    col_widths: Sequence[float],
    styles: Dict[str, ParagraphStyle],
    right_cols: Optional[set] = None,
    header_bg: colors.Color = C_PRIMARY,
) -> Table:
    """Construye una tabla tabular con cabecera repetida y filas alternadas."""
    right_cols = right_cols or set()
    head_row = [
        Paragraph(_esc(h), styles["th_right"] if idx in right_cols else styles["th"])
        for idx, h in enumerate(headers)
    ]
    data = [head_row] + rows

    tbl = Table(data, colWidths=list(col_widths), repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.75, C_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, C_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for r_idx in range(1, len(data)):
        if r_idx % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, r_idx), (-1, r_idx), C_ZEBRA))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _observations_box(
    titulo: str,
    texto: str,
    content_width: float,
    styles: Dict[str, ParagraphStyle],
    bg_color: colors.Color = C_LIGHT,
    border_color: colors.Color = C_BORDER,
) -> Table:
    contenido = texto.strip() if texto and texto.strip() else "Sin observaciones adicionales registradas."
    tbl = Table(
        [[
            Paragraph(
                f"<b>{_esc(titulo)}:</b> {_esc(contenido)}",
                styles["note"],
            )
        ]],
        colWidths=[content_width],
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                ("BOX", (0, 0), (-1, -1), 0.75, border_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return tbl


def _signature_block(
    firmas: List[Tuple[str, str, str]],
    content_width: float,
    styles: Dict[str, ParagraphStyle],
) -> Table:
    """Genera bloques de firma física: lista de (etiqueta_cargo, nombre, rol)."""
    col_w = content_width / len(firmas)
    row_cells = []
    for cargo, nombre, rol in firmas:
        rol_txt = f" ({_fmt_rol(rol)})" if _fmt_rol(rol) else ""
        p = Paragraph(
            f"<br/><br/>________________________________________<br/>"
            f"<b>{_esc(nombre)}</b>{_esc(rol_txt)}<br/>"
            f"<font color='#64748b' size='7.5'>{_esc(cargo)}</font>",
            ParagraphStyle(
                "SigCenter",
                parent=styles["cell"],
                alignment=1,
                leading=11,
            ),
        )
        row_cells.append(p)

    tbl = Table([row_cells], colWidths=[col_w] * len(firmas))
    tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, C_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return KeepTogether([Spacer(1, 10), tbl])


def _render_pdf(
    story: List[Any],
    pagesize,
    doc_title: str,
    doc_subtitle: str,
) -> bytes:
    """Compila el flujo Platypus en memoria y retorna los bytes del PDF."""
    buf = io.BytesIO()
    margin = 40
    doc = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=46,
        bottomMargin=46,
    )
    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: SeremiNumberedCanvas(
            *args, doc_title=doc_title, doc_subtitle=doc_subtitle, **kwargs
        ),
    )
    return buf.getvalue()


# ==============================================================================
# 1. ACTA OFICIAL DE BAJA POR MERMA E INOCUIDAD
# ==============================================================================
def generar_pdf_acta_merma(data: Dict[str, Any]) -> bytes:
    """Genera el PDF del Acta de Baja por Merma (individual o consolidada)."""
    cab = data["cabecera"]
    items: pd.DataFrame = data["items"]
    pagesize = letter
    content_width = pagesize[0] - 80
    styles = _get_styles()

    ref_raw = str(cab.get("referencia") or "")
    causa_raiz = ref_raw.replace("MERMA:", "").strip() or "No especificada"

    story: List[Any] = [
        _header_banner(
            titulo="ACTA OFICIAL DE BAJA POR MERMA E INOCUIDAD",
            folio_label=f"ACTA #{cab['id_movimiento']}",
            subtitulo="Control Sanitario SEREMI / Prevención de Riesgos e Inocuidad Alimentaria",
            accent_color=C_DANGER,
            content_width=content_width,
            styles=styles,
        ),
        Spacer(1, 8),
        _kv_grid(
            [
                [
                    ("Sucursal / Establecimiento", f"{cab['local_origen']} ({cab.get('direccion_origen') or 'Sin dirección'})"),
                    ("Fecha y Hora de Baja", _fmt_dt(cab["fecha_movimiento"])),
                    ("Estado del Acta", str(cab.get("estado", "confirmado")).upper()),
                ],
                [
                    ("Causa Raíz Tipificada", causa_raiz),
                    (
                        "Responsable / Manipulador que Declara",
                        f"{cab['responsable_origen']} ({_fmt_rol(cab.get('rol_origen')) or 'Operador'})",
                    ),
                    ("Usuario Sistema", cab.get("username_origen", "-")),
                ],
            ],
            content_width,
            styles,
        ),
        Spacer(1, 8),
        Paragraph("Detalle de Lotes Dados de Baja y Trazabilidad de Origen", styles["h2"]),
    ]

    col_widths = [
        content_width * 0.07,
        content_width * 0.22,
        content_width * 0.14,
        content_width * 0.18,
        content_width * 0.10,
        content_width * 0.09,
        content_width * 0.09,
        content_width * 0.11,
    ]
    rows = []
    total_qty = 0.0
    total_perdida = 0.0
    for _, r in items.iterrows():
        qty = float(r["cantidad"])
        sub = float(r["costo_subtotal"])
        total_qty += qty
        total_perdida += sub
        rows.append(
            [
                Paragraph(f"#{int(r['id_lote'])}", styles["cell_bold"]),
                Paragraph(_esc(r["producto"]), styles["cell"]),
                Paragraph(_esc(r["codigo_lote_proveedor"]), styles["cell"]),
                Paragraph(_esc(r["proveedor"]), styles["cell"]),
                Paragraph(_fmt_dt(r["fecha_vencimiento"], incluir_hora=False), styles["cell"]),
                Paragraph(f"{_fmt_num(qty)} {r['unidad_medida']}", styles["cell_right"]),
                Paragraph(_fmt_clp(r["costo_unitario"]), styles["cell_right"]),
                Paragraph(f"<b>{_fmt_clp(sub)}</b>", styles["cell_right"]),
            ]
        )

    rows.append(
        [
            Paragraph("<b>TOTAL</b>", styles["cell_bold"]),
            Paragraph(f"<b>{len(items)} lote(s) descartado(s)</b>", styles["cell_bold"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph(f"<b>{_fmt_num(total_qty)}</b>", styles["cell_right"]),
            Paragraph("", styles["cell"]),
            Paragraph(f"<b>{_fmt_clp(total_perdida)}</b>", styles["cell_right"]),
        ]
    )

    story.append(
        _styled_table(
            ["Lote", "Materia Prima", "Lote Prov.", "Proveedor", "Vencimiento", "Descarte", "Costo/u", "Pérdida CLP"],
            rows,
            col_widths,
            styles,
            right_cols={5, 6, 7},
            header_bg=C_DANGER,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        _observations_box(
            "Justificación / Detalle de Causa Raíz y Disposición Final",
            str(cab.get("observaciones") or ""),
            content_width,
            styles,
            bg_color=colors.HexColor("#fef2f2"),
            border_color=colors.HexColor("#fecaca"),
        )
    )
    story.append(
        _signature_block(
            [
                ("Declara y Ejecuta Baja Física", str(cab["responsable_origen"]), str(cab.get("rol_origen") or "")),
                ("V°B° Jefatura de Local / Auditoría SEREMI", "___________________________", "Control Sanitario"),
            ],
            content_width,
            styles,
        )
    )
    return _render_pdf(
        story,
        pagesize=pagesize,
        doc_title=f"Acta de Merma #{cab['id_movimiento']}",
        doc_subtitle=f"Sucursal: {cab['local_origen']}",
    )


# ==============================================================================
# 2. GUÍA DE DESPACHO Y TRASLADO ENTRE SUCURSALES
# ==============================================================================
def _build_traslado_section(
    t_data: Dict[str, Any],
    titulo_doc: str,
    accent: colors.Color,
    content_width: float,
    styles: Dict[str, ParagraphStyle],
) -> List[Any]:
    cab = t_data["cabecera"]
    items: pd.DataFrame = t_data["items"]

    elems: List[Any] = [
        _header_banner(
            titulo=titulo_doc,
            folio_label=f"GUÍA #{cab['id_movimiento']}",
            subtitulo="Traslado Inter-Local con Preservación Estricta de Lote de Origen (Trazabilidad Continua)",
            accent_color=accent,
            content_width=content_width,
            styles=styles,
        ),
        Spacer(1, 8),
        _kv_grid(
            [
                [
                    ("Local Origen (Despacha)", f"{cab['local_origen']} ({cab.get('direccion_origen') or 'Sin dirección'})"),
                    ("Local Destino (Recibe)", f"{cab['local_destino']} ({cab.get('direccion_destino') or 'Sin dirección'})"),
                    ("Fecha y Hora Emisión", _fmt_dt(cab["fecha_movimiento"])),
                ],
                [
                    ("Referencia / Manifiesto", str(cab.get("referencia") or "-")),
                    (
                        "Responsable que Despacha",
                        f"{cab['responsable_origen']} ({_fmt_rol(cab.get('rol_origen')) or 'Operador'})",
                    ),
                    (
                        "Responsable que Recibe",
                        f"{cab['responsable_destino']} ({_fmt_rol(cab.get('rol_destino')) or 'Receptor'})",
                    ),
                ],
            ],
            content_width,
            styles,
        ),
        Spacer(1, 8),
        Paragraph("Partidas Trasladadas y Control FEFO / Cadena de Frío", styles["h2"]),
    ]

    col_widths = [
        content_width * 0.07,
        content_width * 0.22,
        content_width * 0.14,
        content_width * 0.18,
        content_width * 0.10,
        content_width * 0.08,
        content_width * 0.10,
        content_width * 0.11,
    ]
    rows = []
    total_qty = 0.0
    total_val = 0.0
    for _, r in items.iterrows():
        qty = float(r["cantidad"])
        sub = float(r["costo_subtotal"])
        total_qty += qty
        total_val += sub
        rows.append(
            [
                Paragraph(f"#{int(r['id_lote'])}", styles["cell_bold"]),
                Paragraph(_esc(r["producto"]), styles["cell"]),
                Paragraph(_esc(r["codigo_lote_proveedor"]), styles["cell"]),
                Paragraph(_esc(r["proveedor"]), styles["cell"]),
                Paragraph(_fmt_dt(r["fecha_vencimiento"], incluir_hora=False), styles["cell"]),
                Paragraph(f"{float(r['temperatura_recepcion']):.1f} °C", styles["cell_right"]),
                Paragraph(f"<b>{_fmt_num(qty)} {r['unidad_medida']}</b>", styles["cell_right"]),
                Paragraph(_fmt_clp(sub), styles["cell_right"]),
            ]
        )

    rows.append(
        [
            Paragraph("<b>TOTAL</b>", styles["cell_bold"]),
            Paragraph(f"<b>{len(items)} lote(s) trasladado(s)</b>", styles["cell_bold"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph(f"<b>{_fmt_num(total_qty)}</b>", styles["cell_right"]),
            Paragraph(f"<b>{_fmt_clp(total_val)}</b>", styles["cell_right"]),
        ]
    )

    elems.append(
        _styled_table(
            ["Lote", "Materia Prima", "Lote Prov.", "Proveedor Origen", "Venc. FEFO", "Temp. Ing", "Cantidad", "Valor Ref."],
            rows,
            col_widths,
            styles,
            right_cols={5, 6, 7},
            header_bg=accent,
        )
    )
    elems.append(Spacer(1, 8))
    elems.append(
        _observations_box(
            "Observaciones Logísticas y Condiciones de Transporte",
            str(cab.get("observaciones") or ""),
            content_width,
            styles,
        )
    )
    elems.append(
        _signature_block(
            [
                ("Despachó en Origen", str(cab["responsable_origen"]), str(cab.get("rol_origen") or "")),
                ("Recibió Conforme en Destino", str(cab["responsable_destino"]), str(cab.get("rol_destino") or "")),
            ],
            content_width,
            styles,
        )
    )
    return elems


def generar_pdf_guia_traslado(
    data: Dict[str, Any],
    data_retorno: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Genera PDF de Guía de Traslado individual o manifiesto combinado Ida + Retorno."""
    pagesize = letter
    content_width = pagesize[0] - 80
    styles = _get_styles()

    cab = data["cabecera"]
    titulo = "GUÍA DE DESPACHO IDA (TRASLADO INTER-LOCAL)" if data_retorno else "GUÍA DE DESPACHO Y TRASLADO ENTRE SUCURSALES"
    story = _build_traslado_section(data, titulo, C_PRIMARY, content_width, styles)

    if data_retorno:
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
        story.append(Spacer(1, 10))
        story.extend(
            _build_traslado_section(
                data_retorno,
                "GUÍA DE DESPACHO RETORNO (BACKHAUL)",
                C_INFO,
                content_width,
                styles,
            )
        )

    return _render_pdf(
        story,
        pagesize=pagesize,
        doc_title=f"Guía de Traslado #{cab['id_movimiento']}",
        doc_subtitle=f"{cab['local_origen']} -> {cab['local_destino']}",
    )


# ==============================================================================
# 3. ACTA DE RECEPCIÓN DE COMPRAS Y CONTROL HACCP
# ==============================================================================
def generar_pdf_recepcion(data: Dict[str, Any]) -> bytes:
    """Genera el PDF del Acta de Recepción de Materias Primas y Control de Frío HACCP."""
    cab = data["cabecera"]
    items: pd.DataFrame = data["items"]
    pagesize = letter
    content_width = pagesize[0] - 80
    styles = _get_styles()

    story: List[Any] = [
        _header_banner(
            titulo="ACTA DE RECEPCIÓN DE COMPRAS Y CONTROL HACCP",
            folio_label=f"REC #{cab['id_compra']}",
            subtitulo="Verificación de Proveedor, Lote, Vencimiento y Cadena de Frío (≤ 4.0°C)",
            accent_color=C_TEAL,
            content_width=content_width,
            styles=styles,
        ),
        Spacer(1, 8),
        _kv_grid(
            [
                [
                    ("Proveedor", f"{cab['proveedor']} (RUT: {cab['rut_proveedor']})"),
                    ("Documento Fiscal", f"{cab['tipo_documento']} N° {cab['numero_documento']}"),
                    ("Fecha Emisión / Recepción", f"{_fmt_dt(cab['fecha_compra'], False)} / {_fmt_dt(cab['fecha_recepcion'], False)}"),
                ],
                [
                    ("Local Receptor", f"{cab['local_receptor']} ({cab.get('direccion_local') or 'Sin dirección'})"),
                    ("Recepcionado por (Control Frío)", f"{cab['recibido_por']} ({_fmt_rol(cab.get('rol_receptor')) or 'Operador'})"),
                    ("Contacto Proveedor", f"{cab.get('telefono_proveedor', '-')} | {cab.get('correo_proveedor', '-')}"),
                ],
            ],
            content_width,
            styles,
        ),
        Spacer(1, 8),
        Paragraph("Lotes Recepcionados y Auditoría Sanitaria HACCP", styles["h2"]),
    ]

    col_widths = [
        content_width * 0.07,
        content_width * 0.21,
        content_width * 0.14,
        content_width * 0.10,
        content_width * 0.08,
        content_width * 0.13,
        content_width * 0.09,
        content_width * 0.08,
        content_width * 0.10,
    ]
    rows = []
    total_qty = 0.0
    total_monto = 0.0
    alertas_haccp = 0

    for _, r in items.iterrows():
        qty = float(r["cantidad_inicial"])
        sub = float(r["subtotal"])
        temp = float(r["temperatura_recepcion"])
        estado_txt, estado_hex = _estado_haccp(temp)
        if temp > 4.0:
            alertas_haccp += 1
        total_qty += qty
        total_monto += sub
        rows.append(
            [
                Paragraph(f"#{int(r['id_lote'])}", styles["cell_bold"]),
                Paragraph(_esc(r["producto"]), styles["cell"]),
                Paragraph(_esc(r["codigo_lote_proveedor"]), styles["cell"]),
                Paragraph(_fmt_dt(r["fecha_vencimiento"], False), styles["cell"]),
                Paragraph(f"<b>{temp:.1f} °C</b>", styles["cell_right"]),
                Paragraph(f"<font color='{estado_hex}'><b>{_esc(estado_txt)}</b></font>", styles["cell"]),
                Paragraph(f"{_fmt_num(qty)} {r['unidad_medida']}", styles["cell_right"]),
                Paragraph(_fmt_clp(r["costo_unitario"]), styles["cell_right"]),
                Paragraph(f"<b>{_fmt_clp(sub)}</b>", styles["cell_right"]),
            ]
        )

    rows.append(
        [
            Paragraph("<b>TOTAL</b>", styles["cell_bold"]),
            Paragraph(f"<b>{len(items)} lote(s) ingresado(s)</b>", styles["cell_bold"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph(
                f"<b>{'Con observaciones' if alertas_haccp else '100% Conforme'}</b>",
                styles["cell"],
            ),
            Paragraph(f"<b>{_fmt_num(total_qty)}</b>", styles["cell_right"]),
            Paragraph("", styles["cell"]),
            Paragraph(f"<b>{_fmt_clp(total_monto)}</b>", styles["cell_right"]),
        ]
    )

    story.append(
        _styled_table(
            ["Lote", "Materia Prima", "Lote Prov.", "Venc.", "Temp.", "Estado HACCP", "Cantidad", "Costo/u", "Subtotal"],
            rows,
            col_widths,
            styles,
            right_cols={4, 6, 7, 8},
            header_bg=C_TEAL,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        _observations_box(
            "Observaciones de Recepción, Embalaje y Cadena de Frío",
            str(cab.get("observaciones") or ""),
            content_width,
            styles,
        )
    )
    story.append(
        _signature_block(
            [
                ("Recepcionó y Controló Temperatura", str(cab["recibido_por"]), str(cab.get("rol_receptor") or "")),
                ("Entrega Proveedor / Transportista", "___________________________", "Despacho Externo"),
            ],
            content_width,
            styles,
        )
    )
    return _render_pdf(
        story,
        pagesize=pagesize,
        doc_title=f"Recepción #{cab['id_compra']} ({cab['tipo_documento']} {cab['numero_documento']})",
        doc_subtitle=f"Sucursal: {cab['local_receptor']}",
    )


# ==============================================================================
# 4. ACTA DE MANIPULACIÓN Y PRODUCCIÓN EN COCINA (TRAZABILIDAD ETA / SEREMI)
# ==============================================================================
def generar_pdf_operacion_cocina(data: Dict[str, Any]) -> bytes:
    """
    Genera el PDF de Manipulación y Producción en Cocina (salida_cocina sin merma).
    Identifica exactamente qué manipulador preparó/utilizó qué lotes en caso de auditoría SEREMI o ETA.
    """
    cab = data["cabecera"]
    items: pd.DataFrame = data["items"]
    pagesize = letter
    content_width = pagesize[0] - 80
    styles = _get_styles()

    story: List[Any] = [
        _header_banner(
            titulo="ACTA DE MANIPULACIÓN Y PRODUCCIÓN EN COCINA (FEFO)",
            folio_label=f"COCINA #{cab['id_movimiento']}",
            subtitulo="Registro de Trazabilidad de Manipulador y Lotes Utilizados para Exigencia SEREMI",
            accent_color=C_SECONDARY,
            content_width=content_width,
            styles=styles,
        ),
        Spacer(1, 8),
        _kv_grid(
            [
                [
                    ("Sucursal / Cocina", f"{cab['local_origen']} ({cab.get('direccion_origen') or 'Sin dirección'})"),
                    ("Fecha y Hora de Manipulación", _fmt_dt(cab["fecha_movimiento"])),
                    ("Estado", str(cab.get("estado", "confirmado")).upper()),
                ],
                [
                    (
                        "Manipulador / Chef Responsable",
                        f"{cab['responsable_origen']} ({_fmt_rol(cab.get('rol_origen')) or 'Cocina'})",
                    ),
                    ("Usuario / Turno Sistema", cab.get("username_origen", "-")),
                    ("Comanda / Turno / Estación", str(cab.get("referencia") or "-")),
                ],
            ],
            content_width,
            styles,
        ),
        Spacer(1, 8),
        Paragraph("Materias Primas y Lotes Manipulados en la Operación", styles["h2"]),
    ]

    col_widths = [
        content_width * 0.07,
        content_width * 0.21,
        content_width * 0.14,
        content_width * 0.18,
        content_width * 0.10,
        content_width * 0.08,
        content_width * 0.10,
        content_width * 0.12,
    ]
    rows = []
    total_qty = 0.0
    total_costo = 0.0
    for _, r in items.iterrows():
        qty = float(r["cantidad"])
        sub = float(r["costo_subtotal"])
        total_qty += qty
        total_costo += sub
        rows.append(
            [
                Paragraph(f"#{int(r['id_lote'])}", styles["cell_bold"]),
                Paragraph(_esc(r["producto"]), styles["cell"]),
                Paragraph(_esc(r["codigo_lote_proveedor"]), styles["cell"]),
                Paragraph(f"{_esc(r['proveedor'])}<br/><font color='#64748b' size='6.8'>{_esc(r['tipo_documento']).upper()} {_esc(r['numero_documento'])}</font>", styles["cell"]),
                Paragraph(_fmt_dt(r["fecha_vencimiento"], False), styles["cell"]),
                Paragraph(f"{float(r['temperatura_recepcion']):.1f} °C", styles["cell_right"]),
                Paragraph(f"<b>{_fmt_num(qty)} {r['unidad_medida']}</b>", styles["cell_right"]),
                Paragraph(_esc(r.get("obs_detalle") or "-"), styles["cell"]),
            ]
        )

    rows.append(
        [
            Paragraph("<b>TOTAL</b>", styles["cell_bold"]),
            Paragraph(f"<b>{len(items)} lote(s) manipulado(s)</b>", styles["cell_bold"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph("", styles["cell"]),
            Paragraph(f"<b>{_fmt_num(total_qty)}</b>", styles["cell_right"]),
            Paragraph(f"<b>Costo: {_fmt_clp(total_costo)}</b>", styles["cell"]),
        ]
    )

    story.append(
        _styled_table(
            ["Lote", "Materia Prima", "Lote Prov.", "Proveedor / Doc.", "Venc. FEFO", "T° Ing.", "Consumo", "Uso / Detalle"],
            rows,
            col_widths,
            styles,
            right_cols={5, 6},
            header_bg=C_SECONDARY,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        _observations_box(
            "Observaciones de Elaboración, Comanda o Sincronización KDS",
            str(cab.get("observaciones") or ""),
            content_width,
            styles,
        )
    )
    story.append(
        _signature_block(
            [
                ("Manipulador Responsable en Cocina", str(cab["responsable_origen"]), str(cab.get("rol_origen") or "")),
                ("V°B° Jefe de Cocina / Control Calidad", "___________________________", "Auditoría Interna"),
            ],
            content_width,
            styles,
        )
    )
    return _render_pdf(
        story,
        pagesize=pagesize,
        doc_title=f"Acta de Cocina #{cab['id_movimiento']}",
        doc_subtitle=f"Manipulador: {cab['responsable_origen']} | {cab['local_origen']}",
    )


# ==============================================================================
# 5. EXPEDIENTE COMPLETO DE TRAZABILIDAD POR LOTE (SEREMI)
# ==============================================================================
def generar_pdf_expediente_lote(trazabilidad: Dict[str, Any]) -> bytes:
    """
    Genera el Expediente Forense de Trazabilidad Extremo a Extremo de un Lote:
    Proveedor -> Recepción HACCP -> Distribución Actual -> Traslados, Cocina (Manipuladores) y Mermas.
    """
    info = trazabilidad["info"]
    stock_df: pd.DataFrame = trazabilidad["stock_locales"]
    mov_df: pd.DataFrame = trazabilidad["movimientos"]

    pagesize = letter
    content_width = pagesize[0] - 80
    styles = _get_styles()

    temp = float(info.get("temperatura_recepcion", 2.0))
    haccp_txt, _ = _estado_haccp(temp)

    story: List[Any] = [
        _header_banner(
            titulo="EXPEDIENTE DE TRAZABILIDAD COMPLETA DE LOTE (SEREMI)",
            folio_label=f"LOTE #{info['id_lote']}",
            subtitulo=f"Materia Prima: {info['producto']} | Código Proveedor: {info['codigo_lote_proveedor']}",
            accent_color=C_PRIMARY,
            content_width=content_width,
            styles=styles,
        ),
        Spacer(1, 8),
        Paragraph("1. Origen, Compra y Control de Ingreso HACCP", styles["h2"]),
        _kv_grid(
            [
                [
                    ("Proveedor", f"{info['proveedor']} (RUT: {info.get('rut_proveedor') or '-'})"),
                    ("Documento Compra", f"{str(info['tipo_documento']).upper()} {info['documento_compra']}"),
                    ("Fecha Compra / Recepción", f"{_fmt_dt(info['fecha_compra'], False)} / {_fmt_dt(info['fecha_recepcion'], False)}"),
                ],
                [
                    ("Local Receptor Inicial", info["local_receptor_original"]),
                    ("Recepcionado por", info.get("recibido_por", "Operador Central")),
                    ("Temp. Ingreso / HACCP", f"{temp:.1f} °C — {haccp_txt}"),
                ],
                [
                    ("Volumen Inicial", f"{_fmt_num(info['cantidad_inicial'])} {info['unidad_medida']}"),
                    ("Fecha Vencimiento", _fmt_dt(info["fecha_vencimiento"], False)),
                    ("Costo Unitario", _fmt_clp(info.get("costo_unitario", 0))),
                ],
            ],
            content_width,
            styles,
        ),
        Spacer(1, 8),
        Paragraph("2. Existencia Física Actual por Sucursal", styles["h2"]),
    ]

    if stock_df.empty:
        story.append(
            _observations_box(
                "Stock Remanente",
                "Lote consumido o dado de baja al 100% (0.000 unidades remanentes en inventario).",
                content_width,
                styles,
            )
        )
    else:
        s_rows = [
            [
                Paragraph(_esc(r["local"]), styles["cell"]),
                Paragraph(f"<b>{_fmt_num(r['cantidad'])} {info['unidad_medida']}</b>", styles["cell_right"]),
                Paragraph(_fmt_dt(r["actualizado_en"]), styles["cell"]),
            ]
            for _, r in stock_df.iterrows()
        ]
        story.append(
            _styled_table(
                ["Sucursal", "Stock Disponible", "Última Actualización"],
                s_rows,
                [content_width * 0.45, content_width * 0.25, content_width * 0.30],
                styles,
                right_cols={1},
                header_bg=C_TEAL,
            )
        )

    story.append(Spacer(1, 8))
    story.append(Paragraph("3. Cadena de Custodia, Manipulación en Cocina, Traslados y Mermas", styles["h2"]))

    if mov_df.empty:
        story.append(
            _observations_box(
                "Historial de Movimientos",
                "El lote aún no registra salidas a cocina, traslados ni bajas por merma.",
                content_width,
                styles,
            )
        )
    else:
        m_widths = [
            content_width * 0.06,
            content_width * 0.13,
            content_width * 0.13,
            content_width * 0.15,
            content_width * 0.15,
            content_width * 0.09,
            content_width * 0.14,
            content_width * 0.15,
        ]
        m_rows = []
        for _, r in mov_df.iterrows():
            ref = str(r.get("referencia") or "")
            if r["tipo_movimiento"] == "traslado":
                op_label = "TRASLADO"
            elif ref.startswith("MERMA:"):
                op_label = "MERMA / BAJA"
            else:
                op_label = "COCINA / PROD."

            m_rows.append(
                [
                    Paragraph(f"#{int(r['id_movimiento'])}", styles["cell_bold"]),
                    Paragraph(_fmt_dt(r["fecha_movimiento"]), styles["cell"]),
                    Paragraph(f"<b>{op_label}</b>", styles["cell"]),
                    Paragraph(_esc(r["local_origen"]), styles["cell"]),
                    Paragraph(_esc(r["destino"]), styles["cell"]),
                    Paragraph(f"{_fmt_num(r['cantidad'])} {info['unidad_medida']}", styles["cell_right"]),
                    Paragraph(
                        f"<b>Op:</b> {_esc(r.get('despachado_por', '-'))}<br/>"
                        f"<font color='#64748b' size='6.8'>Rec: {_esc(r.get('recibido_por', '-'))}</font>",
                        styles["cell"],
                    ),
                    Paragraph(_esc(ref or r.get("observaciones") or "-"), styles["cell"]),
                ]
            )
        story.append(
            _styled_table(
                ["Folio", "Fecha/Hora", "Operación", "Origen", "Destino", "Cant.", "Manipulador / Receptor", "Referencia / Causa"],
                m_rows,
                m_widths,
                styles,
                right_cols={5},
                header_bg=C_PRIMARY,
            )
        )

    return _render_pdf(
        story,
        pagesize=pagesize,
        doc_title=f"Expediente Lote #{info['id_lote']}",
        doc_subtitle=f"{info['producto']} ({info['codigo_lote_proveedor']})",
    )


# ==============================================================================
# 6. LIBROS CONSOLIDADOS POR PERÍODO (AUDITORÍA SEREMI EN HORIZONTAL)
# ==============================================================================
def generar_pdf_libro_consolidado(
    tipo: str,
    df: pd.DataFrame,
    sucursal_label: str,
    fecha_desde: date,
    fecha_hasta: date,
) -> bytes:
    """
    Genera el Libro Oficial Consolidado en orientación horizontal para fiscalización SEREMI:
    tipo in ('merma', 'traslado', 'cocina', 'recepcion').
    """
    pagesize = landscape(letter)
    content_width = pagesize[0] - 80
    styles = _get_styles()

    config = {
        "merma": ("LIBRO CONSOLIDADO DE ACTAS DE MERMA Y DESECHO", C_DANGER, "Control de Bajas e Inocuidad"),
        "traslado": ("LIBRO CONSOLIDADO DE TRASLADOS ENTRE SUCURSALES", C_PRIMARY, "Trazabilidad Inter-Local"),
        "cocina": ("BITÁCORA CONSOLIDADA DE MANIPULACIÓN EN COCINA", C_SECONDARY, "Trazabilidad de Manipuladores y Lotes"),
        "recepcion": ("REGISTRO CONSOLIDADO DE RECEPCIONES Y CONTROL HACCP", C_TEAL, "Control de Proveedores y Cadena de Frío"),
    }
    if tipo not in config:
        raise ValueError(f"Tipo de libro consolidado no válido: {tipo}")

    titulo, accent, subtitulo = config[tipo]
    periodo_str = f"{fecha_desde.strftime('%d-%m-%Y')} al {fecha_hasta.strftime('%d-%m-%Y')}"

    story: List[Any] = [
        _header_banner(
            titulo=titulo,
            folio_label="LIBRO SEREMI",
            subtitulo=f"{subtitulo} | Alcance: {sucursal_label} | Período: {periodo_str}",
            accent_color=accent,
            content_width=content_width,
            styles=styles,
        ),
        Spacer(1, 8),
    ]

    if df.empty:
        story.append(
            _observations_box(
                "Resultado de Búsqueda",
                "No existen registros para los filtros seleccionados en este período.",
                content_width,
                styles,
            )
        )
        return _render_pdf(story, pagesize, titulo, f"{sucursal_label} | {periodo_str}")

    if tipo == "recepcion":
        total_docs = df["id_compra"].nunique()
        total_qty = float(df["cantidad_inicial"].sum())
        total_val = float(df["subtotal"].sum())
        alertas = int((df["temperatura_recepcion"] > 4.0).sum())
        resumen_pairs = [
            [
                ("Recepciones / Compras", str(total_docs)),
                ("Lotes Ingresados", str(len(df))),
                ("Volumen Total", _fmt_num(total_qty)),
                ("Alertas T° (>4.0°C)", str(alertas)),
                ("Valor Total", _fmt_clp(total_val)),
            ]
        ]
        headers = ["Folio", "Fecha", "Documento", "Proveedor", "Sucursal", "Receptor", "Producto", "Lote Prov.", "Venc.", "T° °C", "Cant.", "Subtotal"]
        widths = [
            content_width * 0.05,
            content_width * 0.08,
            content_width * 0.10,
            content_width * 0.13,
            content_width * 0.10,
            content_width * 0.10,
            content_width * 0.13,
            content_width * 0.09,
            content_width * 0.07,
            content_width * 0.05,
            content_width * 0.05,
            content_width * 0.05,
        ]
        right_cols = {9, 10, 11}
        rows = [
            [
                Paragraph(f"#{int(r['id_compra'])}", styles["cell_bold"]),
                Paragraph(_fmt_dt(r["fecha_recepcion"], False), styles["cell"]),
                Paragraph(f"{_esc(r['tipo_documento'])} {_esc(r['numero_documento'])}", styles["cell"]),
                Paragraph(_esc(r["proveedor"]), styles["cell"]),
                Paragraph(_esc(r["local_receptor"]), styles["cell"]),
                Paragraph(_esc(r["recibido_por"]), styles["cell"]),
                Paragraph(_esc(r["producto"]), styles["cell"]),
                Paragraph(_esc(r["codigo_lote_proveedor"]), styles["cell"]),
                Paragraph(_fmt_dt(r["fecha_vencimiento"], False), styles["cell"]),
                Paragraph(f"{float(r['temperatura_recepcion']):.1f}", styles["cell_right"]),
                Paragraph(_fmt_num(r["cantidad_inicial"], 2), styles["cell_right"]),
                Paragraph(_fmt_clp(r["subtotal"]), styles["cell_right"]),
            ]
            for _, r in df.iterrows()
        ]
    else:
        total_docs = df["id_movimiento"].nunique()
        total_qty = float(df["cantidad"].sum())
        total_val = float(df["costo_total"].sum())
        resumen_pairs = [
            [
                ("Documentos / Folios", str(total_docs)),
                ("Partidas / Lotes", str(len(df))),
                ("Cantidad Total", _fmt_num(total_qty)),
                ("Valorización Total", _fmt_clp(total_val)),
            ]
        ]

        if tipo == "traslado":
            headers = ["Guía", "Fecha/Hora", "Origen", "Destino", "Despachó", "Recibió", "Producto", "Lote Prov.", "Venc.", "Cant.", "Referencia"]
            widths = [
                content_width * 0.05,
                content_width * 0.10,
                content_width * 0.10,
                content_width * 0.10,
                content_width * 0.10,
                content_width * 0.10,
                content_width * 0.14,
                content_width * 0.09,
                content_width * 0.07,
                content_width * 0.06,
                content_width * 0.09,
            ]
            right_cols = {9}
            rows = [
                [
                    Paragraph(f"#{int(r['id_movimiento'])}", styles["cell_bold"]),
                    Paragraph(_fmt_dt(r["fecha_movimiento"]), styles["cell"]),
                    Paragraph(_esc(r["local_origen"]), styles["cell"]),
                    Paragraph(_esc(r["local_destino"]), styles["cell"]),
                    Paragraph(_esc(r["manipulador"]), styles["cell"]),
                    Paragraph(_esc(r["receptor"]), styles["cell"]),
                    Paragraph(_esc(r["producto"]), styles["cell"]),
                    Paragraph(_esc(r["codigo_lote_proveedor"]), styles["cell"]),
                    Paragraph(_fmt_dt(r["fecha_vencimiento"], False), styles["cell"]),
                    Paragraph(_fmt_num(r["cantidad"], 2), styles["cell_right"]),
                    Paragraph(_esc(r["referencia"]), styles["cell"]),
                ]
                for _, r in df.iterrows()
            ]
        else:
            col_ref_titulo = "Causa Raíz / Motivo" if tipo == "merma" else "Comanda / Turno"
            headers = ["Folio", "Fecha/Hora", "Sucursal", "Manipulador / Resp.", "Producto", "Lote Prov.", "Proveedor", "Venc.", "Cant.", "Costo CLP", col_ref_titulo]
            widths = [
                content_width * 0.05,
                content_width * 0.10,
                content_width * 0.10,
                content_width * 0.11,
                content_width * 0.14,
                content_width * 0.09,
                content_width * 0.11,
                content_width * 0.07,
                content_width * 0.06,
                content_width * 0.07,
                content_width * 0.10,
            ]
            right_cols = {8, 9}
            rows = []
            for _, r in df.iterrows():
                ref_txt = str(r["referencia"] or "-")
                if tipo == "merma":
                    ref_txt = ref_txt.replace("MERMA:", "").strip()
                rows.append(
                    [
                        Paragraph(f"#{int(r['id_movimiento'])}", styles["cell_bold"]),
                        Paragraph(_fmt_dt(r["fecha_movimiento"]), styles["cell"]),
                        Paragraph(_esc(r["local_origen"]), styles["cell"]),
                        Paragraph(f"{_esc(r['manipulador'])}<br/><font color='#64748b' size='6.5'>{_esc(_fmt_rol(r['rol_manipulador']))}</font>", styles["cell"]),
                        Paragraph(_esc(r["producto"]), styles["cell"]),
                        Paragraph(_esc(r["codigo_lote_proveedor"]), styles["cell"]),
                        Paragraph(_esc(r["proveedor"]), styles["cell"]),
                        Paragraph(_fmt_dt(r["fecha_vencimiento"], False), styles["cell"]),
                        Paragraph(_fmt_num(r["cantidad"], 2), styles["cell_right"]),
                        Paragraph(_fmt_clp(r["costo_total"]), styles["cell_right"]),
                        Paragraph(_esc(ref_txt), styles["cell"]),
                    ]
                )

    story.append(_kv_grid(resumen_pairs, content_width, styles))
    story.append(Spacer(1, 8))
    story.append(_styled_table(headers, rows, widths, styles, right_cols=right_cols, header_bg=accent))
    return _render_pdf(story, pagesize, titulo, f"{sucursal_label} | {periodo_str}")
