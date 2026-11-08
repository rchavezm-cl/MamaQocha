import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Canvas de dos pasos para calcular el total dinámico de páginas ("Página X de Y")
    y dibujar encabezados y pies de página corporativos.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Omitir encabezado y pie en la portada (página 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0d2b45"))
        
        # Encabezado
        self.drawString(54, 11 * inch - 36, "MAMÁ QOCHA | Manual de Operación y Trazabilidad en Nube")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "Versión 2.2 - PostgreSQL 18 & Neon")
        
        # Línea de encabezado
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Línea de pie de página
        self.line(54, 46, 8.5 * inch - 54, 46)

        # Pie de página
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidencial - Cadena de Restaurantes Mamá Qocha (5 Locales) | Sistema Anti-Mermas")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(8.5 * inch - 54, 32, page_text)
        self.restoreState()


def generar_manual():
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Manual_de_Usuario_MamaQocha.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Colores temáticos
    c_primary = colors.HexColor("#0d2b45")
    c_secondary = colors.HexColor("#1a4d6f")
    c_accent = colors.HexColor("#f59e0b")
    c_danger = colors.HexColor("#e63946")
    c_success = colors.HexColor("#2a9d8f")
    c_dark = colors.HexColor("#1e293b")
    c_light = colors.HexColor("#f8fafc")
    c_border = colors.HexColor("#e2e8f0")

    # Modificación y creación de estilos tipográficos
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        alignment=0,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        alignment=0,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_dark,
        leftIndent=15,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # =========================================================================
    # PORTADA
    # =========================================================================
    story.append(Spacer(1, 40))
    # Badge superior
    badge_data = [[
        Paragraph("<font color='#0d2b45'><b>GUÍA OFICIAL DE PROCEDIMIENTO OPERATIVO Y SISTEMA CLOUD</b></font>", callout_style)
    ]]
    badge_table = Table(badge_data, colWidths=[500])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#e0f2fe")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#7dd3fc")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("MAMÁ QOCHA", title_style))
    story.append(Paragraph("Manual de Operación de la Plataforma de Trazabilidad, Control FEFO y Gestión Anti-Mermas", subtitle_style))

    story.append(HRFlowable(width="100%", thickness=3, color=c_primary, spaceBefore=5, spaceAfter=20))

    intro_box_data = [
        [Paragraph("<b>Objetivo Institucional del Sistema:</b>", ParagraphStyle('B1', fontName='Helvetica-Bold', fontSize=10, textColor=c_primary))],
        [Paragraph(
            "Dotar a la cadena de restaurantes <b>Mamá Qocha (5 Sucursales)</b> de un estándar operativo digitalizado en la nube "
            "que erradique las pérdidas por vencimiento de materias primas críticas (pescados, mariscos y carnes), garantice la "
            "inocuidad alimentaria bajo normativa HACCP y rescate a la empresa del déficit financiero provocado por mermas no controladas (4,5% según diagnóstico INACAP).",
            body_style
        )]
    ]
    t_intro = Table(intro_box_data, colWidths=[500])
    t_intro.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_intro)
    story.append(Spacer(1, 20))

    # Ficha técnica del documento
    meta_data = [
        [Paragraph("<b>Entorno Tecnológico:</b>", body_style), Paragraph("Python 3 + Streamlit Web + Neon Serverless PostgreSQL 18", body_style)],
        [Paragraph("<b>Cobertura Operacional:</b>", body_style), Paragraph("5 Sucursales: Centro, Norte, Sur, Oriente, Poniente", body_style)],
        [Paragraph("<b>Usuarios Destinatarios:</b>", body_style), Paragraph("Jefes de Cocina, Encargados de Bodega, Administradores y Gerencia", body_style)],
        [Paragraph("<b>Reglas Críticas:</b>", body_style), Paragraph("Despacho FEFO (First Expired, First Out) + Termometría HACCP (≤ 4.0 °C) + Logística Backhaul", body_style)],
        [Paragraph("<b>Fecha de Emisión:</b>", body_style), Paragraph("Noviembre 2026 - Versión 2.2 Productiva", body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[150, 350])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_meta)

    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 1: INTRODUCCIÓN Y ARQUITECTURA
    # =========================================================================
    story.append(Paragraph("1. Introducción y Arquitectura del Sistema", h1_style))
    story.append(Paragraph(
        "Mamá Qocha es una plataforma centralizada en la nube diseñada específicamente para resolver la fragilidad operativa "
        "de restaurantes con alto volumen de insumos perecibles. La aplicación opera sobre una base de datos PostgreSQL alojada "
        "en <b>Neon Cloud</b> con ramas de alta disponibilidad, permitiendo que las cinco sucursales compartan información de compras, "
        "stock, temperaturas y transferencias en tiempo real sin requerir servidores locales.",
        body_style
    ))

    # Diagrama de flujo conceptual en tabla
    flujo_data = [
        [Paragraph("<b>Pilar 1: Recepción HACCP</b>", h2_style), Paragraph("<b>Pilar 2: Semáforo FEFO</b>", h2_style), Paragraph("<b>Pilar 3: Bajas & Traslados</b>", h2_style)],
        [
            Paragraph("Control de termometría (≤ 4°C), factura y registro de lote/caducidad de proveedores.", body_style),
            Paragraph("Monitoreo continuo de días de vida útil y asignación prioritaria a recetas del día.", body_style),
            Paragraph("Actas formales de merma para erradicar robo hormiga y traslados preventivos inter-local.", body_style)
        ]
    ]
    t_flujo = Table(flujo_data, colWidths=[160, 170, 170])
    t_flujo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light),
        ('GRID', (0, 0), (-1, -1), 1, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_flujo)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECCIÓN 2: ACCESO Y BARRA LATERAL (SIDEBAR)
    # =========================================================================
    story.append(Paragraph("2. Navegación y Selección de Sucursal (Barra Lateral)", h1_style))
    story.append(Paragraph(
        "La barra lateral izquierda contiene los selectores y controles globales de contexto:",
        body_style
    ))
    story.append(Paragraph("• <b>Local Activo en Pantalla:</b> Permite conmutar entre el <i>Modo Consolidado (5 Locales)</i> —exclusivo para gerencia y auditoría— y una sucursal específica (Local 1 Centro, Local 2 Norte, Local 3 Sur, Local 4 Oriente, Local 5 Poniente).", bullet_style))
    story.append(Paragraph("• <b>Métricas Rápidas de Bodega:</b> Al seleccionar un local, la barra exhibe automáticamente el número de lotes activos, kilogramos totales disponibles, valor monetario total en bodega y el monto exacto en riesgo de caducidad.", bullet_style))
    story.append(Paragraph("• <b>Motor Activo:</b> Confirma la conexión con PostgreSQL 18 y el motor de despacho <b>FEFO / FIFO</b>.", bullet_style))

    story.append(Spacer(1, 10))

    # =========================================================================
    # SECCIÓN 3: PESTAÑA 1 - SEMÁFORO Y COSTOS EN RIESGO
    # =========================================================================
    story.append(Paragraph("3. Módulo 1: Semáforo y Costos en Riesgo (Monitor Financiero)", h1_style))
    story.append(Paragraph(
        "Este módulo es el tablero de control principal. Evalúa en tiempo real la proximidad de vencimiento de cada lote y "
        "calcula el impacto en dinero del stock inmovilizado.",
        body_style
    ))

    # Tabla de criterios de semáforo
    semaforo_data = [
        [Paragraph("<b>Estado</b>", body_style), Paragraph("<b>Rango de Días</b>", body_style), Paragraph("<b>Acción Operativa Requerida</b>", body_style)],
        [Paragraph("<font color='#e63946'><b>VENCIDO</b></font>", body_style), Paragraph("<= 0 días", body_style), Paragraph("<b>Bloqueo Inmediato:</b> No puede consumirse en cocina. Proceder al Tab 5 para acta formal de merma.", body_style)],
        [Paragraph("<font color='#f77f00'><b>CRÍTICO</b></font>", body_style), Paragraph("1 a 7 días", body_style), Paragraph("<b>Plan de Choque:</b> Priorizar elaboración de platos recomendados o solicitar traslado preventivo.", body_style)],
        [Paragraph("<font color='#e0a912'><b>PREVENTIVO</b></font>", body_style), Paragraph("8 a 15 días", body_style), Paragraph("<b>Monitoreo:</b> Rotación estándar según despacho FEFO programado.", body_style)],
        [Paragraph("<font color='#2a9d8f'><b>ÓPTIMO</b></font>", body_style), Paragraph("> 15 días", body_style), Paragraph("<b>Seguro:</b> Materia prima con margen suficiente de rotación.", body_style)]
    ]
    t_sem = Table(semaforo_data, colWidths=[80, 90, 330])
    t_sem.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_sem)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Oportunidad Comercial: Plan de Choque en Cocina</b>", h2_style))
    story.append(Paragraph(
        "Cuando el sistema detecta materias primas críticas (naranja), calcula automáticamente el potencial de transformación "
        "en platos de la carta (ej. convertir 15 kg de reineta crítica en 75 porciones de Ceviche Clásico). Esto permite a los chefs "
        "lanzar sugerencias del chef o promociones ejecutivas para vender el producto antes de que caduque, transformando pérdidas en ingresos.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 4: PESTAÑA 2 - RECEPCIÓN DE COMPRAS Y CONTROL HACCP
    # =========================================================================
    story.append(Paragraph("4. Módulo 2: Recepción de Compras con Control HACCP", h1_style))
    story.append(Paragraph(
        "Toda materia prima que ingresa a la cadena debe registrarse en este módulo antes de ser almacenada o procesada.",
        body_style
    ))

    pasos_recepcion = [
        [Paragraph("<b>Paso 1: Cabecera</b>", body_style), Paragraph("Seleccionar el Proveedor formal, la Sucursal Receptora, tipo de documento (Factura/Guía) y número de folio fiscal.", body_style)],
        [Paragraph("<b>Paso 2: Fechas</b>", body_style), Paragraph("Ingresar la Fecha de Compra y la Fecha de Recepción Física (validando que recepción >= compra).", body_style)],
        [Paragraph("<b>Paso 3: Ítems y Lotes</b>", body_style), Paragraph("Por cada producto: indicar cantidad recibida (kg), costo unitario ($), código de lote del proveedor y fecha de vencimiento impresa.", body_style)],
        [Paragraph("<b>Paso 4: Termometría</b>", body_style), Paragraph("<b>CRÍTICO HACCP:</b> Medir con termómetro calibrado la temperatura interna de la partida e ingresar el valor. Si supera los 4.0 °C en pescados/carnes refrigeradas, el sistema alerta quiebre de cadena de frío para rechazo en andén.", body_style)],
        [Paragraph("<b>Paso 5: Confirmación</b>", body_style), Paragraph("Al presionar <i>Guardar y Generar Lotes Trazables</i>, la base de datos genera el registro en compras, detalle_compra, lotes y actualiza el stock disponible en una única transacción atómica.", body_style)]
    ]
    t_pasos = Table(pasos_recepcion, colWidths=[120, 380])
    t_pasos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_pasos)

    story.append(Spacer(1, 10))

    # =========================================================================
    # SECCIÓN 5: PESTAÑA 3 - SALIDAS DE COCINA Y MOTOR FEFO
    # =========================================================================
    story.append(Paragraph("5. Módulo 3: Salidas por Consumo en Cocina (FEFO y Recetas)", h1_style))
    story.append(Paragraph(
        "Para descontar materias primas por consumo real, la plataforma provee dos modalidades:",
        body_style
    ))
    story.append(Paragraph("• <b>Modalidad A: Producción por Recetas Estandarizadas (Comanda por Turno):</b> "
                           "El jefe de cocina selecciona el plato (ej. <i>Lomo Saltado Tradicional</i>) y la cantidad de porciones preparadas (ej. 20 platos). "
                           "El sistema calcula los insumos requeridos según la ficha técnica y <b>aplica automáticamente el algoritmo FEFO</b>, "
                           "descontando primero los kilogramos de los lotes que vencen más pronto en esa sucursal.", bullet_style))
    story.append(Paragraph("• <b>Modalidad B: Salida Manual por Lote Individual:</b> "
                           "Permite seleccionar directamente un lote específico del inventario para rebajas por porcionado previo, preparaciones base o eventos especiales.", bullet_style))

    story.append(Spacer(1, 10))

    # =========================================================================
    # SECCIÓN 6: PESTAÑA 4 - TRASLADOS INTELIGENTES, TOP 7 Y OPTIMIZACIÓN DE FLETE (BACKHAUL)
    # =========================================================================
    story.append(Paragraph("6. Módulo 4: Traslados Inteligentes, Top 7 en Riesgo y Optimización de Flete (Backhaul)", h1_style))
    story.append(Paragraph(
        "Herramienta avanzada de logística inversa y redistribución prescriptiva. Erradica el flete vacío "
        "y rescata capital inmovilizado mediante un manifiesto de carga consolidado bidireccional:",
        body_style
    ))
    story.append(Paragraph("• <b>Panel 1: Flete de Salida (Top 7 en Riesgo FEFO de Origen):</b> "
                           "El sistema calcula y exhibe automáticamente los 7 insumos con menor vida útil de la sucursal emisora, "
                           "ordenados por fecha límite de caducidad y valor en riesgo ($ CLP). Cuenta con botón rápido <i>[➕ Cargar]</i> "
                           "y <i>[⚡ Cargar 7]</i> para añadir las partidas al manifiesto sin búsquedas manuales.", bullet_style))
    story.append(Paragraph("• <b>Panel 2: Flete de Retorno Oportuno (Top 7 en Destino - Backhaul):</b> "
                           "Al seleccionar el local destino, la plataforma audita inmediatamente sus 7 insumos críticos. "
                           "Permite al operador aprovechar la vuelta del camión para traer partidas próximas a vencer en destino hacia el origen "
                           "mediante los botones <i>[➕ Retorno]</i> y <i>[⚡ Cargar 7]</i>, alcanzando un aprovechamiento del flete del 100%.", bullet_style))
    story.append(Paragraph("• <b>Vista Previa de Guías en Dos Tablas (Preview Dinámico):</b> "
                           "Al pie de los paneles se generan dos tablas interactivas en paralelo: "
                           "<b>Tabla 1 (Guía de Despacho IDA)</b> y <b>Tabla 2 (Guía de Despacho RETORNO)</b>. "
                           "El usuario puede editar en vivo los kilogramos a trasladar con <code>st.data_editor</code> o remover partidas no deseadas con un clic.", bullet_style))
    story.append(Paragraph("• <b>Balance Logístico y Emisión Consolidada:</b> "
                           "Calcula en tiempo real los kilogramos totales movilizados (ida + retorno), el capital total rescatado y la eficiencia de viaje redondo. "
                           "Al presionar <i>[Confirmar y Emitir Ambas Guías]</i>, el motor ejecuta una única transacción atómica multi-lote en PostgreSQL "
                           "preservando de forma estricta los identificadores originales de lote para garantizar trazabilidad continua.", bullet_style))

    story.append(PageBreak())

    # =========================================================================
    # SECCIÓN 7: PESTAÑA 5 - CONTROL FORMAL DE MERMAS Y CAUSA RAÍZ (ETAPA 2)
    # =========================================================================
    story.append(Paragraph("7. Módulo 5: Control Formal de Mermas y Causa Raíz Tipificada (Etapa 2)", h1_style))
    story.append(Paragraph(
        "<b>Norma Obligatoria de la Cadena:</b> Ningún alimento puede ser desechado o descartado en cocina sin emitir "
        "previamente el <i>Acta de Baja por Merma</i>. Cada descarte debe clasificar de manera obligatoria en una de las "
        "<b>4 Causas Raíz Oficiales</b> para auditoría sanitaria y control financiero de pérdidas:",
        body_style
    ))

    # Motivos de merma oficiales Etapa 2
    motivos_data = [
        [Paragraph("<b>Causa Raíz Tipificada (Oficial)</b>", body_style), Paragraph("<b>Descripción Técnica y Plan de Mitigación</b>", body_style)],
        [Paragraph("<font color='#0284c7'><b>Ruptura de cadena de frío en cocina</b></font>", body_style), Paragraph("Temperatura registrada > 5.0 °C por falla eléctrica, desconexión o mal cierre de visicoolers/cámaras. Requiere revisión técnica de refrigeración.", body_style)],
        [Paragraph("<font color='#e63946'><b>Vencimiento de fecha límite FEFO</b></font>", body_style), Paragraph("Lote superó su fecha límite de aptitud sin ser elaborado. Exige auditoría a compras y aplicación estricta del Plan de Choque en carta.", body_style)],
        [Paragraph("<font color='#f59e0b'><b>Deterioro organoléptico en recepción</b></font>", body_style), Paragraph("Textura, color u olor no conforme detectado al abrir empaque primario. Requiere notificación formal y reclamo a proveedor.", body_style)],
        [Paragraph("<font color='#8b5cf6'><b>Manipulación / Error de porcionado</b></font>", body_style), Paragraph("Derrame, sobrecocción, corte defectuoso o contaminación cruzada en línea de producción. Exige reinducción del personal de cocina.", body_style)]
    ]
    t_motivos = Table(motivos_data, colWidths=[170, 330])
    t_motivos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_motivos)
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Auditoría y Estadísticas Ejecutivas:</b> La pestaña incluye un gráfico Donut de Apache ECharts y una "
        "<b>Matriz Cuantitativa de Pérdidas</b> que cuantifica el porcentaje de impacto de cada causa raíz y permite "
        "exportar el reporte en formato CSV para los informes de gerencia e INACAP.",
        body_style
    ))

    story.append(Spacer(1, 10))

    # =========================================================================
    # SECCIÓN 8: PESTAÑA 6 Y 7 - TRAZABILIDAD Y MAESTROS
    # =========================================================================
    story.append(Paragraph("8. Módulo 6 y 7: Expediente de Trazabilidad y Catálogos Maestros", h1_style))
    story.append(Paragraph(
        "• <b>Ficha 360° de Trazabilidad por Lote:</b> Permite auditar la historia de cualquier lote desde el día que ingresó al camión proveedor hasta su última porción consumida o trasladada. Es la herramienta de respaldo ante inspecciones sanitarias de la SEREMI de Salud.",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Catálogos Maestros:</b> Administración centralizada de Proveedores (RUT y contacto comercial), Catálogo de Productos Cárnicos y Fichas Técnicas de Recetas (gramajes por plato y precios de venta de carta).",
        body_style
    ))

    story.append(Spacer(1, 15))

    # =========================================================================
    # SECCIÓN 9: DECÁLOGO DE CUMPLIMIENTO OPERATIVO
    # =========================================================================
    story.append(Paragraph("9. Decálogo de Cumplimiento Operativo para Salvar a Mamá Qocha", h1_style))
    
    decalogo_items = [
        "1. <b>Cero Ingresos a Ciegas:</b> No se recibe ninguna materia prima sin verificar termometría (<= 4.0 °C) y código de lote.",
        "2. <b>Respeto Estricto al FEFO:</b> En cocina se cocina siempre con el lote más próximo a caducar; prohibido abrir partidas nuevas teniendo lotes antiguos vigentes.",
        "3. <b>Revisión Diaria del Semáforo:</b> A primera hora de cada turno, el administrador y chef deben revisar el 'Plan de Choque' de la Pestaña 1.",
        "4. <b>Cero Mermas Fantasma:</b> Todo descarte de insumos debe contar con su acta digital de baja en la Pestaña 5 con su motivo real.",
        "5. <b>Traslados Preventivos Activos:</b> Si un local tiene sobrestock a 5 días de vencer, se coordina inmediatamente el traslado a una sucursal con mayor salida.",
        "6. <b>Recetas Estandarizadas:</b> Se debe respetar el gramaje fijado en la ficha técnica para evitar mermas por sobreporción.",
        "7. <b>Cierre Diario de Inventario:</b> Al finalizar el turno nocturno, las comandas deben cuadrar contra el descuento automático de cocina.",
        "8. <b>Respaldo en Nube:</b> La sincronización con Neon PostgreSQL asegura que toda la información gerencial esté protegida contra fallas físicas.",
        "9. <b>Capacitación Continua:</b> Todo nuevo manipulador de alimentos o bodeguero debe ser inducido en el uso de esta plataforma.",
        "10. <b>Foco en Margen:</b> Cada kilogramo rescatado es utilidad limpia que fortalece la caja y garantiza la continuidad laboral de Mamá Qocha."
    ]

    for item in decalogo_items:
        story.append(Paragraph(item, bullet_style))

    # Construir documento
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generado exitosamente en: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    generar_manual()
