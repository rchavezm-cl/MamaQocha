from datetime import date, timedelta
from typing import Optional

import pandas as pd

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

import importlib
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

import db
importlib.reload(db)

# ==============================================================================
# CONFIGURACIÓN GENERAL Y ESTILOS
# ==============================================================================
st.set_page_config(
    page_title="Mamá Qocha - Control de Trazabilidad e Inventario",
    page_icon="🦙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inyección de estilos CSS para pulir la apariencia visual ("Theme Mamá Qocha")
st.markdown(
    """
    <style>
    /* Estilos globales y tipografía */
    .hero-container {
        background: linear-gradient(135deg, #0d2b45 0%, #203c56 60%, #1a4d6f 100%);
        border-radius: 12px;
        padding: 22px 28px;
        color: #ffffff;
        margin-bottom: 22px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.12);
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #d0e1fd;
        margin-top: 4px;
        margin-bottom: 12px;
    }
    .hero-badge-container {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }
    .hero-badge {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.8rem;
        font-weight: 500;
        color: #f1f7ff;
    }

    /* Tarjetas de métricas visuales (KPIs) */
    .kpi-card {
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        transition: transform 0.15s ease-in-out;
        border: 1px solid #e2e8f0;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-vencido {
        background: #fff5f5;
        border-left: 5px solid #e63946;
    }
    .kpi-critico {
        background: #fffaf0;
        border-left: 5px solid #f77f00;
    }
    .kpi-preventivo {
        background: #fffdf0;
        border-left: 5px solid #e0a912;
    }
    .kpi-optimo {
        background: #f0fdf4;
        border-left: 5px solid #2a9d8f;
    }
    .kpi-num {
        font-size: 1.7rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-desc {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 2px;
    }

    /* Timeline Stepper de trazabilidad */
    .timeline-wrapper {
        display: flex;
        justify-content: space-between;
        position: relative;
        margin: 20px 0 25px 0;
    }
    .timeline-step {
        flex: 1;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px;
        margin: 0 6px;
        position: relative;
    }
    .timeline-step-active {
        border-top: 4px solid #1a4d6f;
        background: #ffffff;
    }
    .timeline-header {
        font-size: 0.85rem;
        font-weight: 700;
        color: #0d2b45;
        margin-bottom: 6px;
    }
    .timeline-body {
        font-size: 0.8rem;
        color: #475569;
        line-height: 1.4;
    }

    /* Comprobante / Voucher Card */
    .voucher-card {
        background: #f8fafc;
        border: 1px dashed #94a3b8;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Carga de datos base con control de errores
try:
    locales_df = db.load_locales()
    proveedores_df = db.load_proveedores(solo_activos=True)
    productos_df = db.load_productos(solo_activos=True)
except SQLAlchemyError as err:
    st.error(
        f"❌ Error al conectar con PostgreSQL: {err}. "
        "Verifica que el servicio de base de datos esté activo y el archivo .env sea correcto."
    )
    st.stop()

if locales_df.empty:
    st.warning("No se encontraron locales configurados en la base de datos.")
    st.stop()

# ==============================================================================
# SIDEBAR: EMULACIÓN DE SESIÓN MULTI-LOCAL
# ==============================================================================
st.sidebar.markdown(
    """
    <div style='text-align: center; padding: 10px 0 15px 0;'>
        <h2 style='margin:0; font-size:1.5rem; color:#0d2b45;'>🦙 Mamá Qocha</h2>
        <p style='margin:0; font-size:0.8rem; color:#64748b;'>Gestión de Trazabilidad y Stock</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### 🏢 Simulación de Local")

opciones_locales = {"0": "🌐 Vista Consolidada (Administrador)"}
for _, fila in locales_df.iterrows():
    opciones_locales[str(fila["id_local"])] = f"📍 {fila['nombre']}"

seleccion_local_key = st.sidebar.selectbox(
    "Local Activo en Pantalla:",
    options=list(opciones_locales.keys()),
    format_func=lambda k: opciones_locales[k],
    index=0,
    help="Permite emular la perspectiva de un operador de sucursal específica o del Administrador General.",
)

id_local_activo: Optional[int] = (
    int(seleccion_local_key) if seleccion_local_key != "0" else None
)
nombre_local_activo = (
    opciones_locales[seleccion_local_key].replace("📍 ", "").replace("🌐 ", "")
)

if id_local_activo:
    st.sidebar.success(f"Sesión activa: **{nombre_local_activo}**")
else:
    st.sidebar.info("Modo activo: **Consolidado General (5 Locales)**")

st.sidebar.markdown("---")

# Resumen de métricas en la barra lateral
metricas = db.load_resumen_metricas(id_local=id_local_activo)
st.sidebar.markdown("### 📦 Stock del Local")
col_s1, col_s2 = st.sidebar.columns(2)
col_s1.metric("Lotes", metricas["total_lotes"])
col_s2.metric("Total (kg)", f"{metricas['total_cantidad']:,.1f}")

col_s3, col_s4 = st.sidebar.columns(2)
col_s3.metric("Valor Total", f"${metricas['total_valor']/1000:,.0f}k")
col_s4.metric("En Riesgo", f"${metricas['valor_en_riesgo']/1000:,.0f}k")

st.sidebar.caption("Base de datos: **PostgreSQL 18**")
st.sidebar.caption("Lógica de Despacho: **FEFO / FIFO**")
st.sidebar.markdown("---")
st.sidebar.caption("Proyecto Académico Demo Funcional")

# ==============================================================================
# HERO HEADER BANNER
# ==============================================================================
modo_badge = f"📍 {nombre_local_activo}" if id_local_activo else "🌐 Modo Consolidado (Todos los locales)"
st.markdown(
    f"""
    <div class="hero-container">
        <h1 class="hero-title">🦙 Mamá Qocha — Trazabilidad & Inventario</h1>
        <div class="hero-subtitle">
            Control de existencias multi-sucursal, alertas tempranas de caducidad, costeo de existencias y control de mermas.
        </div>
        <div class="hero-badge-container">
            <span class="hero-badge">🟢 PostgreSQL Conectado</span>
            <span class="hero-badge">🏢 5 Sucursales</span>
            <span class="hero-badge">📅 Fecha: {date.today().strftime('%d-%m-%Y')}</span>
            <span class="hero-badge" style="background: rgba(255,255,255,0.3); font-weight:600;">{modo_badge}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Pestañas principales de navegación
tab_alertas, tab_recepcion, tab_cocina, tab_traslados, tab_mermas, tab_trazabilidad, tab_maestros = st.tabs(
    [
        "🚦 Semáforo y Costos en Riesgo",
        "📥 Recepción de Compras",
        "🍳 Salidas a Cocina (FEFO)",
        "🚚 Traspasos entre Locales",
        "🗑️ Control de Mermas (Bajas)",
        "🔍 Trazabilidad y Auditoría",
        "⚙️ Maestros (Catálogos)",
    ]
)

# ==============================================================================
# TAB 1: SEMÁFORO Y ALERTAS DE VENCIMIENTO CON VALORIZACIÓN
# ==============================================================================
with tab_alertas:
    st.markdown("### 🚦 Monitor de Caducidad y Semáforo Financiero de Riesgo")
    st.caption(
        "Detección oportuna de partidas de insumos para priorizar su consumo inmediato "
        "en cocina, erradicar pérdidas por caducidad y cuantificar el capital inmovilizado en riesgo."
    )

    # Tarjetas financieras superiores
    c_fin1, c_fin2 = st.columns([1.4, 1.2])
    with c_fin1:
        st.markdown(
            f"""
            <div style="background:#f8fafc; border:1px solid #cbd5e1; border-left:5px solid #0d2b45; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
                <span style="font-size:0.8rem; color:#64748b; font-weight:600; text-transform:uppercase;">Valorización del Inventario Activo</span>
                <div style="font-size:1.6rem; font-weight:700; color:#0d2b45;">${metricas['total_valor']:,.0f} CLP</div>
                <span style="font-size:0.8rem; color:#475569;">Calculado según costo unitario real registrado en facturas de compra.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_fin2:
        color_riesgo = "#e63946" if metricas["valor_en_riesgo"] > 0 else "#2a9d8f"
        st.markdown(
            f"""
            <div style="background:#fff5f5; border:1px solid #fecaca; border-left:5px solid {color_riesgo}; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
                <span style="font-size:0.8rem; color:#991b1b; font-weight:600; text-transform:uppercase;">Capital en Riesgo de Vencimiento</span>
                <div style="font-size:1.6rem; font-weight:700; color:{color_riesgo};">${metricas['valor_en_riesgo']:,.0f} CLP <span style="font-size:0.9rem; font-weight:500;">({metricas['pct_en_riesgo']:.1f}%)</span></div>
                <span style="font-size:0.8rem; color:#7f1d1d;">Lotes vencidos o con menos de 7 días de vida útil.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # KPI Cards estilizadas
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown(
            f"""
            <div class="kpi-card kpi-vencido">
                <div class="kpi-label" style="color: #e63946;">🔴 Vencidos</div>
                <div class="kpi-num" style="color: #e63946;">{metricas['vencidos']} <span style="font-size:0.85rem; font-weight:500;">(${metricas['valor_vencidos']:,.0f})</span></div>
                <div class="kpi-desc">Caducados (Acción inmediata)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col2:
        st.markdown(
            f"""
            <div class="kpi-card kpi-critico">
                <div class="kpi-label" style="color: #f77f00;">🟠 Crítico (≤ 7 d)</div>
                <div class="kpi-num" style="color: #f77f00;">{metricas['criticos']} <span style="font-size:0.85rem; font-weight:500;">(${metricas['valor_criticos']:,.0f})</span></div>
                <div class="kpi-desc">Prioridad máxima en cocina</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col3:
        st.markdown(
            f"""
            <div class="kpi-card kpi-preventivo">
                <div class="kpi-label" style="color: #b38600;">🟡 Preventivo (8-30 d)</div>
                <div class="kpi-num" style="color: #b38600;">{metricas['preventivos']} <span style="font-size:0.85rem; font-weight:500;">(${metricas['valor_preventivos']:,.0f})</span></div>
                <div class="kpi-desc">En observación y rotación regular</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col4:
        st.markdown(
            f"""
            <div class="kpi-card kpi-optimo">
                <div class="kpi-label" style="color: #2a9d8f;">🟢 Óptimo (> 30 d)</div>
                <div class="kpi-num" style="color: #2a9d8f;">{metricas['optimos']} <span style="font-size:0.85rem; font-weight:500;">(${metricas['valor_optimos']:,.0f})</span></div>
                <div class="kpi-desc">Vida útil segura y holgada</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    inventario_df = db.load_inventario_alertas(id_local=id_local_activo)

    if inventario_df.empty:
        st.info("ℹ️ No hay existencias registradas para el local seleccionado.")
    else:
        # Gráficos interactivos
        col_g1, col_g2 = st.columns([1, 1.4])

        with col_g1:
            with st.container(border=True):
                st.markdown("##### 🥧 Distribución del Semáforo")
                resumen_alertas = inventario_df["estado_alerta"].value_counts().reset_index()
                resumen_alertas.columns = ["Estado", "Cantidad de Lotes"]

                if HAS_PLOTLY:
                    colores_map = {
                        "🔴 Vencido": "#e63946",
                        "🟠 Crítico (≤ 7 días)": "#f77f00",
                        "🟡 Preventivo (8-30 días)": "#fcbf49",
                        "🟢 Óptimo (> 30 días)": "#2a9d8f",
                    }
                    fig_donut = px.pie(
                        resumen_alertas,
                        names="Estado",
                        values="Cantidad de Lotes",
                        hole=0.55,
                        color="Estado",
                        color_discrete_map=colores_map,
                    )
                    fig_donut.update_traces(
                        textposition="inside",
                        textinfo="percent+value",
                        marker=dict(line=dict(color="#ffffff", width=2)),
                    )
                    fig_donut.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                        height=270,
                    )
                    st.plotly_chart(fig_donut, use_container_width=True)
                else:
                    st.dataframe(resumen_alertas, hide_index=True, use_container_width=True)

        with col_g2:
            with st.container(border=True):
                st.markdown("##### 🥩 Stock Total por Producto (kg)")
                stock_producto = (
                    inventario_df.groupby("producto")["cantidad"]
                    .sum()
                    .reset_index()
                    .sort_values(by="cantidad", ascending=True)
                )

                if HAS_PLOTLY:
                    fig_bar = px.bar(
                        stock_producto,
                        x="cantidad",
                        y="producto",
                        orientation="h",
                        labels={"cantidad": "Kilos (kg)", "producto": "Producto"},
                        color="cantidad",
                        color_continuous_scale=["#8da9c4", "#0d2b45"],
                    )
                    fig_bar.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        coloraxis_showscale=False,
                        height=270,
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.bar_chart(stock_producto.set_index("producto"))

        # Gráfica de Riesgo de Venta y Exposición por Local
        st.markdown("---")
        st.markdown("#### 🏢 Exposición y Riesgo de Venta por Sucursal")
        st.caption(
            "Análisis comparativo de los 5 locales. Identifica qué sucursales concentran el mayor "
            "capital inmovilizado en riesgo de caducidad para coordinar traspasos preventivos o promociones comerciales."
        )

        col_rv1, col_rv2 = st.columns([1.7, 1.1])

        df_todas_sucursales = db.load_inventario_alertas(id_local=None)

        with col_rv1:
            with st.container(border=True):
                st.markdown("##### 📊 Valor de Inventario por Local según Nivel de Riesgo")
                if HAS_PLOTLY:
                    df_chart_loc = df_todas_sucursales.groupby(
                        ["local", "estado_alerta", "severidad_alerta"]
                    )["valor_inventario"].sum().reset_index()
                    df_chart_loc = df_chart_loc.sort_values(by="severidad_alerta")

                    fig_riesgo_local = px.bar(
                        df_chart_loc,
                        x="local",
                        y="valor_inventario",
                        color="estado_alerta",
                        barmode="stack",
                        color_discrete_map={
                            "🔴 Vencido": "#e63946",
                            "🟠 Crítico (≤ 7 días)": "#f77f00",
                            "🟡 Preventivo (8-30 días)": "#fcbf49",
                            "🟢 Óptimo (> 30 días)": "#2a9d8f",
                        },
                        labels={
                            "local": "Sucursal",
                            "valor_inventario": "Monto en Stock ($CLP)",
                            "estado_alerta": "Estado",
                        },
                    )
                    fig_riesgo_local.update_layout(
                        margin=dict(t=20, b=10, l=10, r=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=290,
                        yaxis=dict(tickformat="$,.0f"),
                    )
                    st.plotly_chart(fig_riesgo_local, use_container_width=True)
                else:
                    st.dataframe(df_todas_sucursales.groupby("local")["valor_inventario"].sum())

        with col_rv2:
            with st.container(border=True):
                st.markdown("##### 🎯 Diagnóstico Ejecutivo de Riesgo")
                tot_por_local = df_todas_sucursales.groupby("local")["valor_inventario"].sum()
                rsk_por_local = df_todas_sucursales[df_todas_sucursales["severidad_alerta"] <= 2].groupby("local")["valor_inventario"].sum()

                df_ranking = pd.DataFrame({
                    "Total ($)": tot_por_local,
                    "Riesgo ($)": rsk_por_local,
                }).fillna(0)
                df_ranking["% Riesgo"] = (df_ranking["Riesgo ($)"] / df_ranking["Total ($)"] * 100).fillna(0)
                df_ranking = df_ranking.sort_values(by="Riesgo ($)", ascending=False)

                peor_local = df_ranking.index[0]
                peor_monto_riesgo = df_ranking.iloc[0]["Riesgo ($)"]
                peor_pct = df_ranking.iloc[0]["% Riesgo"]
                venta_riesgo_estimada = peor_monto_riesgo * 3.0

                st.markdown(
                    f"""
                    <div style="background:#fff5f5; border:1px solid #fecaca; border-radius:8px; padding:10px 14px; margin-bottom:10px;">
                        <span style="font-size:0.75rem; font-weight:700; color:#991b1b; text-transform:uppercase;">Sucursal con Mayor Exposición</span>
                        <div style="font-size:1.15rem; font-weight:700; color:#b91c1c;">{peor_local}</div>
                        • <strong>Costo en riesgo:</strong> ${peor_monto_riesgo:,.0f} CLP ({peor_pct:.1f}% de su stock)<br>
                        • <strong>Venta potencial en riesgo:</strong> <span style="color:#b91c1c; font-weight:700;">${venta_riesgo_estimada:,.0f} CLP</span> (Factor 3×)
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("###### Ranking de Exposición por Local:")
                for loc_nombre, fila_rk in df_ranking.iterrows():
                    rsk_val = fila_rk["Riesgo ($)"]
                    pct_val = fila_rk["% Riesgo"]
                    icono_sem = "🔴" if pct_val > 20 else ("🟠" if pct_val > 0 else "🟢")
                    st.write(f"{icono_sem} **{loc_nombre}**: ${rsk_val:,.0f} CLP *({pct_val:.1f}% en riesgo)*")

        st.markdown("---")

        # Filtros y tabla interactiva
        st.markdown("#### 📋 Detalle de Lotes en Stock")
        col_filtro1, col_filtro2 = st.columns([1, 2])
        with col_filtro1:
            filtro_alerta = st.selectbox(
                "Filtrar por nivel de riesgo:",
                ["Todos los niveles", "🔴 Vencido", "🟠 Crítico (≤ 7 días)", "🟡 Preventivo (8-30 días)", "🟢 Óptimo (> 30 días)"],
            )
        with col_filtro2:
            filtro_busqueda = st.text_input(
                "Buscar por producto, proveedor o código de lote:",
                placeholder="Ej. Atún, Vacuno Demo, L-2026...",
            )

        datos_filtrados = inventario_df.copy()
        if filtro_alerta != "Todos los niveles":
            datos_filtrados = datos_filtrados[datos_filtrados["estado_alerta"] == filtro_alerta]

        if filtro_busqueda.strip():
            patron = filtro_busqueda.strip().lower()
            datos_filtrados = datos_filtrados[
                datos_filtrados["producto"].str.lower().str.contains(patron)
                | datos_filtrados["codigo_lote_proveedor"].str.lower().str.contains(patron)
                | datos_filtrados["proveedor"].str.lower().str.contains(patron)
            ]

        # Alerta visual de criticidad
        criticos_totales = datos_filtrados[datos_filtrados["severidad_alerta"] <= 2]
        if not criticos_totales.empty:
            st.warning(
                f"⚠️ Hay **{len(criticos_totales)} lotes prioritarios** (vencidos o críticos). "
                "Recuerda priorizar su despacho aplicando la recomendación de orden FEFO."
            )

        columnas_mostrar = [
            "estado_alerta",
            "dias_para_vencer",
            "fecha_vencimiento",
            "producto",
            "codigo_lote_proveedor",
            "temperatura_recepcion",
            "cantidad",
            "unidad_medida",
            "costo_unitario",
            "valor_inventario",
            "local",
            "proveedor",
            "documento_compra",
        ]

        # Asegurar columnas requeridas para evitar errores de caché en caliente
        for col_req, val_defecto in [
            ("temperatura_recepcion", 2.0),
            ("costo_unitario", 0.0),
            ("valor_inventario", 0.0),
        ]:
            if col_req not in datos_filtrados.columns:
                datos_filtrados[col_req] = val_defecto

        st.dataframe(
            datos_filtrados[columnas_mostrar],
            use_container_width=True,
            hide_index=True,
            column_config={
                "estado_alerta": st.column_config.TextColumn("Alerta", width="medium"),
                "dias_para_vencer": st.column_config.NumberColumn(
                    "Días restantes",
                    format="%d d",
                    help="Días calendario hasta la fecha de expiración",
                ),
                "fecha_vencimiento": st.column_config.DateColumn("Vencimiento", format="YYYY-MM-DD"),
                "producto": "Materia Prima",
                "codigo_lote_proveedor": "Lote Proveedor",
                "temperatura_recepcion": st.column_config.NumberColumn("Temp. Ingreso", format="%.1f °C"),
                "cantidad": st.column_config.NumberColumn("Stock Actual", format="%.3f"),
                "unidad_medida": "Unidad",
                "costo_unitario": st.column_config.NumberColumn("Costo/kg", format="$%d"),
                "valor_inventario": st.column_config.NumberColumn("Valor Stock", format="$%d"),
                "local": "Local Físico",
                "proveedor": "Proveedor",
                "documento_compra": "Documento",
            },
        )

# ==============================================================================
# TAB 2: RECEPCIÓN DE COMPRAS Y GENERACIÓN DE LOTES
# ==============================================================================
with tab_recepcion:
    st.markdown("### 📥 Recepción de Compras y Alta de Lotes")
    st.caption(
        "Ingreso físico de materias primas. Se crea el lote de trazabilidad "
        "y se suma el stock de forma inmediata a la sucursal receptora."
    )

    if "voucher_recepcion" in st.session_state:
        v_rec = st.session_state.pop("voucher_recepcion")
        st.success("✅ ¡Ingreso registrado con éxito en PostgreSQL!")
        st.markdown(
            f"""
            <div class="voucher-card" style="border-left: 5px solid #2a9d8f; background: #f0fdf4;">
                <strong>🧾 Comprobante de Recepción de Lote</strong><br>
                • <strong>Lote Interno Creado:</strong> #{v_rec['id_lote']}<br>
                • <strong>Compra Registrada:</strong> #{v_rec['id_compra']} ({v_rec['tipo_doc']} {v_rec['num_doc']})<br>
                • <strong>Cantidad asignada a stock:</strong> {v_rec['cantidad']:.3f} kg en el local receptor.<br>
                • <strong>Vencimiento:</strong> {v_rec['vencimiento']}<br>
                • <strong>Temp. de Ingreso:</strong> {v_rec.get('temperatura', 2.0):.1f} °C (Control Cadena de Frío)
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        with st.form("form_recepcion_lote", clear_on_submit=False):
            col_f1, col_f2 = st.columns(2)

            with col_f1:
                st.markdown("##### 📄 1. Datos del Proveedor y Factura")

                if id_local_activo:
                    local_receptor_id = id_local_activo
                    st.text_input("Local receptor (fijado por sesión):", value=nombre_local_activo, disabled=True)
                else:
                    opciones_rec = {row["id_local"]: row["nombre"] for _, row in locales_df.iterrows()}
                    local_receptor_id = st.selectbox(
                        "Local receptor del insumo:*",
                        options=list(opciones_rec.keys()),
                        format_func=lambda k: opciones_rec[k],
                    )

                dict_proveedores = {row["id_proveedor"]: f"{row['nombre']} ({row['rut']})" for _, row in proveedores_df.iterrows()}
                prov_seleccionado = st.selectbox(
                    "Proveedor:*",
                    options=list(dict_proveedores.keys()),
                    format_func=lambda k: dict_proveedores[k],
                )

                col_doc1, col_doc2 = st.columns(2)
                with col_doc1:
                    tipo_doc = st.selectbox("Tipo de documento:*", ["factura", "guia", "boleta"])
                with col_doc2:
                    num_doc = st.text_input("N° Documento:*", placeholder="FAC-2026-0045").strip()

                col_sub_f1, col_sub_f2 = st.columns(2)
                with col_sub_f1:
                    fecha_compra = st.date_input("Fecha de emisión/compra:*", value=date.today())
                with col_sub_f2:
                    fecha_recepcion = st.date_input("Fecha de recepción física:*", value=date.today())

            with col_f2:
                st.markdown("##### 🏷️ 2. Especificación de Materia Prima y Lote")

                dict_productos = {row["id_producto"]: f"{row['nombre']} ({row['unidad_medida']})" for _, row in productos_df.iterrows()}
                prod_seleccionado = st.selectbox(
                    "Producto recibido:*",
                    options=list(dict_productos.keys()),
                    format_func=lambda k: dict_productos[k],
                )

                col_sub_p1, col_sub_p2 = st.columns(2)
                with col_sub_p1:
                    cantidad = st.number_input("Cantidad recibida:*", min_value=0.001, max_value=10000.0, value=25.0, step=0.5, format="%.3f")
                with col_sub_p2:
                    costo_unitario = st.number_input("Costo unitario ($):", min_value=0.0, value=0.0, step=500.0, format="%.2f")

                col_l1, col_l2, col_l3 = st.columns([1.2, 1, 1])
                with col_l1:
                    codigo_lote_prov = st.text_input("Lote del proveedor:*", placeholder="Ej. L-VAC-2026-X8").strip()
                with col_l2:
                    fecha_vencimiento = st.date_input(
                        "Fecha de vencimiento:*",
                        value=date.today() + timedelta(days=25),
                        help="Fecha de caducidad estipulada en el rótulo o ficha técnica.",
                    )
                with col_l3:
                    temperatura_recepcion = st.number_input(
                        "Temp. Ingreso (°C):*",
                        min_value=-20.0,
                        max_value=25.0,
                        value=2.0,
                        step=0.5,
                        format="%.1f",
                        help="Protocolo sanitario HACCP: Pescados y carnes refrigeradas deben ingresar entre 0°C y 4°C (máx. 5.0°C).",
                    )

                if temperatura_recepcion > 5.0:
                    st.error(f"⚠️ ALERTA SANITARIA (HACCP): {temperatura_recepcion:.1f}°C supera el límite de seguridad (5.0°C). Riesgo de pérdida de cadena de frío e intoxicación.")
                elif temperatura_recepcion > 4.0:
                    st.warning(f"⚠️ ADVERTENCIA: {temperatura_recepcion:.1f}°C está en el límite superior de refrigeración.")

                observaciones = st.text_area(
                    "Observaciones de recepción y control de calidad:",
                    placeholder="Temperatura de recepción en frío, estado de embalaje al vacío...",
                    height=68,
                )

            st.markdown("---")
            submit_registro = st.form_submit_button("📥 Registrar Recepción e Incorporar al Stock", type="primary", use_container_width=True)

    if submit_registro:
        if not num_doc:
            st.error("Debes ingresar el número de documento de la compra.")
        elif not codigo_lote_prov:
            st.error("Debes ingresar el código de lote provisto por el proveedor.")
        elif fecha_recepcion < fecha_compra:
            st.error("La fecha de recepción física no puede ser anterior a la fecha de compra.")
        elif fecha_vencimiento <= fecha_recepcion:
            st.warning("Advertencia: La fecha de vencimiento es igual o anterior a la fecha de recepción.")
        else:
            try:
                resultado = db.registrar_recepcion_compra(
                    id_proveedor=int(prov_seleccionado),
                    id_local_receptor=int(local_receptor_id),
                    tipo_documento=tipo_doc,
                    numero_documento=num_doc,
                    fecha_compra=fecha_compra,
                    fecha_recepcion=fecha_recepcion,
                    id_producto=int(prod_seleccionado),
                    cantidad=float(cantidad),
                    codigo_lote_proveedor=codigo_lote_prov,
                    fecha_vencimiento=fecha_vencimiento,
                    temperatura_recepcion=float(temperatura_recepcion),
                    costo_unitario=float(costo_unitario) if costo_unitario > 0 else None,
                    observaciones=observaciones.strip() if observaciones.strip() else None,
                )
                st.session_state["voucher_recepcion"] = {
                    "id_lote": resultado["id_lote"],
                    "id_compra": resultado["id_compra"],
                    "tipo_doc": tipo_doc.upper(),
                    "num_doc": num_doc,
                    "cantidad": cantidad,
                    "vencimiento": fecha_vencimiento.strftime('%d-%m-%Y'),
                    "temperatura": float(temperatura_recepcion),
                }
                st.rerun()
            except SQLAlchemyError as err:
                st.error(f"Error en la base de datos: {err}")
            except Exception as err:
                st.error(f"Error de validación: {err}")

# ==============================================================================
# TAB 3: SALIDAS POR CONSUMO EN COCINA (FEFO)
# ==============================================================================
with tab_cocina:
    st.markdown("### 🍳 Registro de Salida a Cocina (Consumo Interno)")
    st.caption(
        "Descuenta materias primas para preparación culinaria aplicando la "
        "recomendación estricta **FEFO** (First Expired, First Out)."
    )

    if "voucher_cocina" in st.session_state:
        v_coc = st.session_state.pop("voucher_cocina")
        st.success("✅ Salida a cocina descontada satisfactoriamente del stock.")
        st.markdown(
            f"""
            <div class="voucher-card" style="border-left: 5px solid #2a9d8f; background: #f0fdf4;">
                <strong>🍳 Vale de Salida a Cocina #{v_coc['id_movimiento']}</strong><br>
                • <strong>Insumo:</strong> {v_coc['producto']} (Lote: <code>{v_coc['lote']}</code>)<br>
                • <strong>Cantidad consumida:</strong> <code>{v_coc['cantidad']:.3f} {v_coc['unidad']}</code><br>
                • <strong>Nuevo stock remanente en este local:</strong> <code>{v_coc['nuevo_stock']:.3f} {v_coc['unidad']}</code><br>
                • <strong>Referencia:</strong> {v_coc['referencia']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if id_local_activo:
        local_cocina_id = id_local_activo
        st.info(f"📍 Registrando consumo para la cocina del: **{nombre_local_activo}**")
    else:
        opciones_locales_cocina = {row["id_local"]: row["nombre"] for _, row in locales_df.iterrows()}
        local_cocina_id = st.selectbox(
            "Seleccionar Local donde se prepara el insumo:",
            options=list(opciones_locales_cocina.keys()),
            format_func=lambda k: opciones_locales_cocina[k],
            key="sel_local_cocina",
        )

    stock_disp_cocina = db.load_stock_disponible_local(int(local_cocina_id))

    if stock_disp_cocina.empty:
        st.warning("⚠️ Este local no dispone de lotes con existencias positivas para consumir.")
    else:
        st.info(
            "💡 **Criterio FEFO Activo**: La lista de selección sugiere y ordena automáticamente "
            "los lotes cuya fecha de caducidad está más cercana para evitar mermas."
        )

        dict_lotes_cocina = {
            int(row["id_lote"]): row["display_label"]
            for _, row in stock_disp_cocina.iterrows()
        }

        with st.container(border=True):
            with st.form("form_salida_cocina", clear_on_submit=False):
                lote_cocina_sel = st.selectbox(
                    "Selecciona el lote a utilizar (ordenado por FEFO):*",
                    options=list(dict_lotes_cocina.keys()),
                    format_func=lambda k: dict_lotes_cocina[k],
                    key="sel_lote_cocina_form",
                )

                fila_lote_sel = stock_disp_cocina[stock_disp_cocina["id_lote"] == lote_cocina_sel].iloc[0]
                max_disponible = float(fila_lote_sel["stock_disponible"])
                unidad_medida = fila_lote_sel["unidad_medida"]
                dias_rest = int(fila_lote_sel["dias_para_vencer"])

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    cant_cocina = st.number_input(
                        f"Cantidad a consumir ({unidad_medida}):*",
                        min_value=0.001,
                        max_value=max_disponible,
                        value=min(1.0, max_disponible),
                        step=0.5,
                        format="%.3f",
                        help=f"Máximo disponible en el local: {max_disponible:.3f} {unidad_medida}",
                    )
                    ref_cocina = st.text_input(
                        "Estación de cocina o partida:",
                        placeholder="Ej. Cevichería, Parrilla, Turno Noche, Menú Almuerzo",
                    )

                with col_c2:
                    urgencia_badge = "🔴 Urgente" if dias_rest <= 7 else "🟢 Normal"
                    st.markdown(
                        f"""
                        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px;">
                            <strong>Ficha rápida del lote seleccionado:</strong><br>
                            • <strong>Insumo:</strong> {fila_lote_sel['producto']}<br>
                            • <strong>Lote Proveedor:</strong> <code>{fila_lote_sel['codigo_lote_proveedor']}</code><br>
                            • <strong>Vencimiento:</strong> {fila_lote_sel['fecha_vencimiento']} ({dias_rest} días restantes) — {urgencia_badge}<br>
                            • <strong>Stock disponible en local:</strong> <code>{max_disponible:.3f} {unidad_medida}</code>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    obs_cocina = st.text_area("Observaciones del consumo:", placeholder="Porciones elaboradas, control de mermas...", height=60)

                st.markdown("---")
                btn_salida_cocina = st.form_submit_button("🍳 Confirmar Salida a Cocina", type="primary", use_container_width=True)

        if btn_salida_cocina:
            try:
                res_cocina = db.registrar_salida_cocina(
                    id_local=int(local_cocina_id),
                    id_lote=int(lote_cocina_sel),
                    cantidad=float(cant_cocina),
                    referencia=ref_cocina.strip() or "Salida a cocina",
                    observaciones=obs_cocina.strip() or None,
                )
                st.session_state["voucher_cocina"] = {
                    "id_movimiento": res_cocina["id_movimiento"],
                    "producto": fila_lote_sel["producto"],
                    "lote": fila_lote_sel["codigo_lote_proveedor"],
                    "cantidad": res_cocina["cantidad"],
                    "unidad": unidad_medida,
                    "nuevo_stock": res_cocina["nuevo_stock"],
                    "referencia": ref_cocina.strip() or "Consumo estándar",
                }
                st.rerun()
            except Exception as e:
                st.error(f"Error al registrar salida a cocina: {e}")

# ==============================================================================
# TAB 4: TRASPASOS ENTRE LOCALES
# ==============================================================================
with tab_traslados:
    st.markdown("### 🚚 Traspaso de Insumos entre Locales")
    st.caption(
        "Redistribución de inventario entre sucursales. El identificador de lote de origen "
        "se preserva de forma estricta para garantizar trazabilidad continua."
    )

    if "voucher_traslado" in st.session_state:
        v_tr = st.session_state.pop("voucher_traslado")
        st.success("✅ ¡Traslado completado en base de datos!")
        st.markdown(
            f"""
            <div class="voucher-card" style="border-left: 5px solid #2a9d8f; background: #f0fdf4;">
                <h4 style="margin:0 0 8px 0; color:#0d2b45;">🚚 Guía de Traspaso #{v_tr['id_movimiento']}</h4>
                • <strong>Insumo:</strong> {v_tr['producto']} (Lote: <code>{v_tr['lote']}</code>)<br>
                • <strong>Ruta:</strong> <strong>{v_tr['origen']}</strong> ➡️ <strong>{v_tr['destino']}</strong><br>
                • <strong>Cantidad trasladada:</strong> <code>{v_tr['cantidad']:.3f} {v_tr['unidad']}</code><br>
                • <strong>Nuevo saldo en Origen ({v_tr['origen']}):</strong> <code>{v_tr['nuevo_origen']:.3f} {v_tr['unidad']}</code><br>
                • <strong>Nuevo saldo en Destino ({v_tr['destino']}):</strong> <code>{v_tr['nuevo_destino']:.3f} {v_tr['unidad']}</code><br>
                • <strong>Trazabilidad:</strong> El lote preserva intacto su código de origen en la sucursal receptora.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        col_t_orig, col_arrow, col_t_dest = st.columns([1, 0.2, 1])

        with col_t_orig:
            if id_local_activo:
                local_traslado_origen_id = id_local_activo
                st.text_input("Local de Origen (fijado por sesión):", value=nombre_local_activo, disabled=True)
            else:
                opciones_locales_traslado = {row["id_local"]: row["nombre"] for _, row in locales_df.iterrows()}
                local_traslado_origen_id = st.selectbox(
                    "Local de Origen:*",
                    options=list(opciones_locales_traslado.keys()),
                    format_func=lambda k: opciones_locales_traslado[k],
                    key="sel_local_traslado_origen",
                )

        with col_arrow:
            st.markdown(
                "<div style='text-align:center; padding-top:28px; font-size:1.5rem;'>➡️</div>",
                unsafe_allow_html=True,
            )

        with col_t_dest:
            locales_destino_posibles = locales_df[locales_df["id_local"] != int(local_traslado_origen_id)]
            opciones_destino = {row["id_local"]: row["nombre"] for _, row in locales_destino_posibles.iterrows()}
            local_traslado_destino_id = st.selectbox(
                "Local de Destino:*",
                options=list(opciones_destino.keys()),
                format_func=lambda k: opciones_destino[k],
                key="sel_local_traslado_destino",
            )

    stock_disp_traslado = db.load_stock_disponible_local(int(local_traslado_origen_id))

    if stock_disp_traslado.empty:
        st.warning("El local de origen seleccionado no cuenta con insumos disponibles para traspasar.")
    else:
        dict_lotes_traslado = {
            int(row["id_lote"]): row["display_label"]
            for _, row in stock_disp_traslado.iterrows()
        }

        with st.container(border=True):
            with st.form("form_traslado_lotes", clear_on_submit=False):
                lote_traslado_sel = st.selectbox(
                    "Lote a transferir hacia la otra sucursal:*",
                    options=list(dict_lotes_traslado.keys()),
                    format_func=lambda k: dict_lotes_traslado[k],
                )

                fila_traslado_sel = stock_disp_traslado[stock_disp_traslado["id_lote"] == lote_traslado_sel].iloc[0]
                max_traslado = float(fila_traslado_sel["stock_disponible"])
                unidad_traslado = fila_traslado_sel["unidad_medida"]

                col_sub_t1, col_sub_t2 = st.columns(2)
                with col_sub_t1:
                    cant_traslado = st.number_input(
                        f"Cantidad a trasladar ({unidad_traslado}):*",
                        min_value=0.001,
                        max_value=max_traslado,
                        value=min(5.0, max_traslado),
                        step=0.5,
                        format="%.3f",
                        help=f"Stock máximo disponible en origen: {max_traslado:.3f} {unidad_traslado}",
                    )
                    ref_traslado = st.text_input("N° de Guía o Referencia de Traslado:", placeholder="Ej. GT-2026-0089")

                with col_sub_t2:
                    st.markdown(
                        f"""
                        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px;">
                            <strong>Detalle del Despacho:</strong><br>
                            • <strong>Insumo:</strong> {fila_traslado_sel['producto']}<br>
                            • <strong>Lote Proveedor:</strong> <code>{fila_traslado_sel['codigo_lote_proveedor']}</code><br>
                            • <strong>Vencimiento:</strong> {fila_traslado_sel['fecha_vencimiento']}<br>
                            • <strong>Disponible actual:</strong> <code>{max_traslado:.3f} {unidad_traslado}</code>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    obs_traslado = st.text_area("Condiciones de transporte:", placeholder="Cadena de frío en hielera sellada...", height=60)

                st.markdown("---")
                btn_traslado = st.form_submit_button("🚚 Ejecutar Traslado entre Sucursales", type="primary", use_container_width=True)

        if btn_traslado:
            try:
                res_tr = db.registrar_traslado_local(
                    id_local_origen=int(local_traslado_origen_id),
                    id_local_destino=int(local_traslado_destino_id),
                    id_lote=int(lote_traslado_sel),
                    cantidad=float(cant_traslado),
                    referencia=ref_traslado.strip() or "Traslado interno",
                    observaciones=obs_traslado.strip() or None,
                )
                nombre_origen_str = opciones_locales.get(str(local_traslado_origen_id), "Origen").replace("📍 ", "")
                nombre_destino_str = opciones_destino.get(local_traslado_destino_id, "Destino")
                st.session_state["voucher_traslado"] = {
                    "id_movimiento": res_tr["id_movimiento"],
                    "origen": nombre_origen_str,
                    "destino": nombre_destino_str,
                    "cantidad": res_tr["cantidad"],
                    "unidad": unidad_traslado,
                    "nuevo_origen": res_tr["nuevo_stock_origen"],
                    "nuevo_destino": res_tr["nuevo_stock_destino"],
                    "producto": fila_traslado_sel["producto"],
                    "lote": fila_traslado_sel["codigo_lote_proveedor"],
                }
                st.rerun()
            except Exception as e:
                st.error(f"Error al registrar el traslado: {e}")

    # Visualización en vivo de los últimos traslados en esta misma pestaña
    st.markdown("---")
    st.markdown("#### 📋 Historial de Traslados entre Sucursales")
    st.caption("Verificación de las transferencias registradas en la base de datos.")
    hist_traslados = db.load_historial_movimientos(id_local=None, limit=20)
    hist_traslados = hist_traslados[hist_traslados["tipo"].str.contains("Traslado", na=False)]
    if hist_traslados.empty:
        st.info("Aún no se han ejecutado traslados entre sucursales.")
    else:
        st.dataframe(
            hist_traslados[[
                "id_movimiento", "fecha_movimiento", "local_origen", "local_destino",
                "producto", "codigo_lote_proveedor", "cantidad", "unidad_medida", "referencia", "observaciones"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id_movimiento": "N° Guía",
                "fecha_movimiento": st.column_config.DatetimeColumn("Fecha y Hora", format="YYYY-MM-DD HH:mm"),
                "local_origen": "Local Origen (Desde)",
                "local_destino": "Local Destino (Hacia)",
                "producto": "Materia Prima",
                "codigo_lote_proveedor": "Lote Prov.",
                "cantidad": st.column_config.NumberColumn("Cantidad", format="%.3f"),
                "unidad_medida": "Unidad",
                "referencia": "Referencia",
                "observaciones": "Observaciones",
            },
        )

# ==============================================================================
# TAB 5: CONTROL DE MERMAS Y BAJAS (CONTROL DE COSTOS INACAP 4.5%)
# ==============================================================================
with tab_mermas:
    st.markdown("### 🗑️ Gestión y Control de Mermas de Materias Primas")
    st.caption(
        "Protocolo formal de baja y descarte para erradicar pérdidas no controladas (4,5% de costos "
        "según diagnóstico INACAP, pág. 17) y garantizar la inocuidad alimentaria."
    )

    if "voucher_merma" in st.session_state:
        v_m = st.session_state.pop("voucher_merma")
        st.success("✅ Baja por merma procesada y descontada de inventario.")
        st.markdown(
            f"""
            <div class="voucher-card" style="border-left: 5px solid #e63946; background: #fff5f5;">
                <h4 style="margin:0 0 8px 0; color:#b91c1c;">🗑️ Acta de Baja por Merma #{v_m['id_movimiento']}</h4>
                • <strong>Materia Prima:</strong> {v_m['producto']} (Lote: <code>{v_m['lote']}</code>)<br>
                • <strong>Motivo de la Baja:</strong> <code>{v_m['motivo']}</code><br>
                • <strong>Cantidad descartada:</strong> <code>{v_m['cantidad']:.3f} {v_m['unidad']}</code><br>
                • <strong>Costo Unitario:</strong> ${v_m['costo_unitario']:,.2f} / {v_m['unidad']}<br>
                • <strong>Pérdida Financiera Cuantificada:</strong> <strong style="color:#b91c1c;">${v_m['costo_total_perdida']:,.0f} CLP</strong><br>
                • <strong>Saldo remanente del lote en sucursal:</strong> <code>{v_m['nuevo_stock']:.3f} {v_m['unidad']}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

    resumen_mermas = db.load_resumen_mermas(id_local=id_local_activo)

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.markdown(
            f"""
            <div class="kpi-card" style="background:#fff5f5; border-left:5px solid #e63946;">
                <div class="kpi-label" style="color:#e63946;">Pérdida Monetaria en Mermas</div>
                <div class="kpi-num" style="color:#e63946;">${resumen_mermas['total_costo_merma']:,.0f} <span style="font-size:0.8rem; font-weight:500;">CLP</span></div>
                <div class="kpi-desc">Impacto directo acumulado en Costo de Ventas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_m2:
        st.markdown(
            f"""
            <div class="kpi-card" style="background:#fffaf0; border-left:5px solid #f77f00;">
                <div class="kpi-label" style="color:#f77f00;">Volumen Descartado</div>
                <div class="kpi-num" style="color:#f77f00;">{resumen_mermas['total_kilos']:,.3f} <span style="font-size:0.8rem; font-weight:500;">kg</span></div>
                <div class="kpi-desc">Kilos dados de baja por inocuidad o rotura</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_m3:
        st.markdown(
            f"""
            <div class="kpi-card" style="background:#f8fafc; border-left:5px solid #0d2b45;">
                <div class="kpi-label" style="color:#0d2b45;">Eventos Declarados</div>
                <div class="kpi-num" style="color:#0d2b45;">{resumen_mermas['total_eventos']} <span style="font-size:0.8rem; font-weight:500;">actas</span></div>
                <div class="kpi-desc">Total de bajas registradas y auditadas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if id_local_activo:
        local_merma_id = id_local_activo
        st.info(f"📍 Registrando baja por merma para: **{nombre_local_activo}**")
    else:
        opciones_locales_merma = {row["id_local"]: row["nombre"] for _, row in locales_df.iterrows()}
        local_merma_id = st.selectbox(
            "Seleccionar Local donde ocurrió la merma:*",
            options=list(opciones_locales_merma.keys()),
            format_func=lambda k: opciones_locales_merma[k],
            key="sel_local_merma",
        )

    stock_disp_merma = db.load_stock_disponible_local(int(local_merma_id))

    if stock_disp_merma.empty:
        st.warning("No hay lotes con existencias activas en este local para declarar mermas.")
    else:
        dict_lotes_merma = {
            int(row["id_lote"]): row["display_label"]
            for _, row in stock_disp_merma.iterrows()
        }

        with st.container(border=True):
            st.markdown("##### 📝 Declaración y Acta de Merma")
            with st.form("form_declarar_merma", clear_on_submit=False):
                lote_merma_sel = st.selectbox(
                    "Selecciona el lote afectado:*",
                    options=list(dict_lotes_merma.keys()),
                    format_func=lambda k: dict_lotes_merma[k],
                    key="sel_lote_merma_form",
                )

                fila_merma_sel = stock_disp_merma[stock_disp_merma["id_lote"] == lote_merma_sel].iloc[0]
                max_merma = float(fila_merma_sel["stock_disponible"])
                unidad_merma = fila_merma_sel["unidad_medida"]
                costo_unid_merma = float(fila_merma_sel.get("costo_unitario", 0.0))

                col_m_f1, col_m_f2 = st.columns(2)

                with col_m_f1:
                    motivos_merma = [
                        "❄️ Pérdida de cadena de frío (> 5°C - Riesgo Sanitario)",
                        "🔴 Vencimiento cumplido (Fecha expirada)",
                        "⚠️ Deterioro físico / Contaminación cruzada",
                        "🔪 Merma excesiva en preparación o porcionamiento",
                    ]
                    motivo_sel = st.selectbox("Causa / Motivo de la Merma:*", motivos_merma)

                    cant_merma = st.number_input(
                        f"Cantidad a dar de baja ({unidad_merma}):*",
                        min_value=0.001,
                        max_value=max_merma,
                        value=min(1.0, max_merma),
                        step=0.5,
                        format="%.3f",
                        help=f"Máximo disponible para dar de baja: {max_merma:.3f} {unidad_merma}",
                    )

                with col_m_f2:
                    costo_perdida_estimada = cant_merma * costo_unid_merma
                    st.markdown(
                        f"""
                        <div style="background:#fff5f5; border:1px solid #fecaca; border-radius:8px; padding:12px;">
                            <strong>Impacto Financiero de la Merma:</strong><br>
                            • <strong>Insumo:</strong> {fila_merma_sel['producto']}<br>
                            • <strong>Costo Unitario de Compra:</strong> ${costo_unid_merma:,.2f} / {unidad_merma}<br>
                            • <strong>Pérdida en Costos Estimada:</strong> <strong style="color:#b91c1c; font-size:1.1rem;">${costo_perdida_estimada:,.0f} CLP</strong><br>
                            • <strong>Stock disponible en local:</strong> <code>{max_merma:.3f} {unidad_merma}</code>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    obs_merma = st.text_area("Observaciones y causa raíz (Auditoría sanitaria):", placeholder="Ej. Falla de termostato en cámara 2 durante la noche...", height=60)

                st.markdown("---")
                btn_declarar_merma = st.form_submit_button("🗑️ Confirmar y Procesar Baja por Merma", type="primary", use_container_width=True)

            if btn_declarar_merma:
                try:
                    res_m = db.registrar_merma(
                        id_local=int(local_merma_id),
                        id_lote=int(lote_merma_sel),
                        cantidad=float(cant_merma),
                        motivo=motivo_sel,
                        observaciones=obs_merma.strip() or None,
                    )
                    st.session_state["voucher_merma"] = {
                        "id_movimiento": res_m["id_movimiento"],
                        "producto": res_m["producto"],
                        "lote": res_m["codigo_lote_proveedor"],
                        "motivo": res_m["motivo"],
                        "cantidad": res_m["cantidad"],
                        "unidad": res_m["unidad_medida"],
                        "costo_unitario": res_m["costo_unitario"],
                        "costo_total_perdida": res_m["costo_total_perdida"],
                        "nuevo_stock": res_m["nuevo_stock"],
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al procesar la merma: {e}")

    # Historial de Mermas
    st.markdown("---")
    st.markdown("#### 📋 Libro de Actas de Merma y Desecho")
    st.caption("Registro forense de todas las bajas efectuadas para el control de pérdidas del negocio.")

    hist_mermas = db.load_historial_mermas(id_local=id_local_activo, limit=50)

    if hist_mermas.empty:
        st.info("No se registran actas de merma para el filtro seleccionado.")
    else:
        st.dataframe(
            hist_mermas[[
                "id_movimiento", "fecha_movimiento", "local", "producto",
                "codigo_lote_proveedor", "motivo_merma", "cantidad", "unidad_medida",
                "costo_unitario", "costo_total_merma", "observaciones"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id_movimiento": "N° Acta",
                "fecha_movimiento": st.column_config.DatetimeColumn("Fecha y Hora", format="YYYY-MM-DD HH:mm"),
                "local": "Sucursal",
                "producto": "Materia Prima",
                "codigo_lote_proveedor": "Lote Prov.",
                "motivo_merma": "Causa de la Merma",
                "cantidad": st.column_config.NumberColumn("Kilos Descartados", format="%.3f"),
                "unidad_medida": "Unidad",
                "costo_unitario": st.column_config.NumberColumn("Costo/kg ($)", format="$%d"),
                "costo_total_merma": st.column_config.NumberColumn("Pérdida Total ($)", format="$%d"),
                "observaciones": "Causa Raíz / Detalle",
            },
        )

# ==============================================================================
# TAB 6: TRAZABILIDAD POR LOTE CON LÍNEA DE TIEMPO VISUAL
# ==============================================================================
with tab_trazabilidad:
    st.markdown("### 🔍 Expediente de Trazabilidad y Auditoría")
    st.caption(
        "Auditoría integral del ciclo de vida de cada lote: desde la compra al proveedor, "
        "su ingreso físico, hasta su dispersión en sucursales y consumos en cocina."
    )

    subtab_expediente, subtab_historial = st.tabs(["📦 Ficha de Trazabilidad por Lote", "📋 Registro Global de Movimientos"])

    with subtab_expediente:
        lotes_disponibles = db.load_lotes_selector()
        if lotes_disponibles.empty:
            st.info("No existen lotes registrados en la base de datos.")
        else:
            opciones_lotes = {
                int(row["id_lote"]): row["display_label"]
                for _, row in lotes_disponibles.iterrows()
            }

            col_sel_lote, _ = st.columns([2.5, 1])
            with col_sel_lote:
                lote_id_sel = st.selectbox(
                    "Selecciona el lote para auditar su ciclo de vida:",
                    options=list(opciones_lotes.keys()),
                    format_func=lambda k: opciones_lotes[k],
                )

            if lote_id_sel:
                trazabilidad = db.load_trazabilidad_lote(lote_id_sel)
                if not trazabilidad:
                    st.warning("No se pudo cargar la información del lote seleccionado.")
                else:
                    info = trazabilidad["info"]
                    dias_restantes = info["dias_para_vencer"]

                    if dias_restantes < 0:
                        badge_color = "#e63946"
                        badge_txt = "🔴 VENCIDO"
                    elif dias_restantes <= 7:
                        badge_color = "#f77f00"
                        badge_txt = "🟠 CRÍTICO (≤ 7 días)"
                    elif dias_restantes <= 30:
                        badge_color = "#e0a912"
                        badge_txt = "🟡 PREVENTIVO (8-30 días)"
                    else:
                        badge_color = "#2a9d8f"
                        badge_txt = "🟢 ÓPTIMO (> 30 días)"

                    # Encabezado visual del lote
                    st.markdown(
                        f"""
                        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:18px; margin: 15px 0;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <h3 style="margin:0; color:#0d2b45;">Lote Interno #{info['id_lote']} — {info['producto']}</h3>
                                    <span style="color:#64748b; font-size:0.9rem;">Código Proveedor: <code>{info['codigo_lote_proveedor']}</code></span>
                                </div>
                                <span style="background:{badge_color}; color:#fff; padding:6px 14px; border-radius:20px; font-weight:700; font-size:0.85rem;">
                                    {badge_txt}
                                </span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Timeline Stepper Visual (Línea de Vida del Lote)
                    st.markdown("##### 🧭 Línea de Vida del Lote (Trazabilidad Extremo a Extremo)")
                    costo_label = f"${info['costo_unitario']:,.2f}" if pd.notnull(info.get("costo_unitario")) else "No reg."

                    st.markdown(
                        f"""
                        <div class="timeline-wrapper">
                            <div class="timeline-step timeline-step-active">
                                <div class="timeline-header">1. 🏢 Origen / Compra</div>
                                <div class="timeline-body">
                                    • <strong>Proveedor:</strong> {info['proveedor']}<br>
                                    • <strong>RUT:</strong> {info['rut_proveedor']}<br>
                                    • <strong>Doc:</strong> {info['tipo_documento'].upper()} {info['documento_compra']}<br>
                                    • <strong>Fecha Emisión:</strong> {info['fecha_compra']}
                                </div>
                            </div>
                            <div class="timeline-step timeline-step-active">
                                <div class="timeline-header">2. 📥 Recepción Física</div>
                                <div class="timeline-body">
                                    • <strong>Local Ingreso:</strong> {info['local_receptor_original']}<br>
                                    • <strong>Fecha Recepción:</strong> {info['fecha_recepcion']}<br>
                                    • <strong>Volumen Inicial:</strong> {info['cantidad_inicial']:.3f} {info['unidad_medida']}<br>
                                    • <strong>Costo Unitario:</strong> {costo_label}<br>
                                    • <strong>Temp. Ingreso:</strong> {float(info.get('temperatura_recepcion', 2.0)):.1f} °C (Cadena de Frío)
                                </div>
                            </div>
                            <div class="timeline-step timeline-step-active">
                                <div class="timeline-header">3. ⏳ Estado Caducidad</div>
                                <div class="timeline-body">
                                    • <strong>Vencimiento:</strong> {info['fecha_vencimiento']}<br>
                                    • <strong>Días Restantes:</strong> {dias_restantes} días<br>
                                    • <strong>Estado:</strong> {badge_txt}<br>
                                    • <strong>Obs:</strong> {info.get('obs_compra') or 'Sin novedades'}
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Existencias y Movimientos
                    col_dist, col_mov = st.columns([1, 1.3])

                    with col_dist:
                        with st.container(border=True):
                            st.markdown("#### 📊 Stock Actual por Sucursal")
                            stock_locales_df = trazabilidad["stock_locales"]
                            if stock_locales_df.empty:
                                st.info("Este lote ya no tiene existencias físicas disponibles (consumido al 100%).")
                            else:
                                st.dataframe(
                                    stock_locales_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "local": "Sucursal",
                                        "cantidad": st.column_config.NumberColumn(
                                            f"Stock ({info['unidad_medida']})", format="%.3f"
                                        ),
                                        "actualizado_en": st.column_config.DatetimeColumn("Última actualización", format="YYYY-MM-DD HH:mm"),
                                    },
                                )

                    with col_mov:
                        with st.container(border=True):
                            st.markdown("#### 🔄 Historial de Movimientos del Lote")
                            mov_df = trazabilidad["movimientos"]
                            if mov_df.empty:
                                st.info("Aún no registra movimientos (salidas a cocina o traslados).")
                            else:
                                st.dataframe(
                                    mov_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "id_movimiento": "ID",
                                        "tipo_movimiento": "Operación",
                                        "fecha_movimiento": st.column_config.DatetimeColumn("Fecha", format="YYYY-MM-DD HH:mm"),
                                        "local_origen": "Origen",
                                        "destino": "Destino",
                                        "cantidad": st.column_config.NumberColumn("Cantidad", format="%.3f"),
                                        "referencia": "Ref.",
                                    },
                                )

    with subtab_historial:
        st.markdown("#### 📋 Libro de Movimientos de Inventario (Últimas Operaciones)")
        st.caption("Bitácora cronológica de traslados entre sucursales y despachos para consumo en cocina.")

        historial_df = db.load_historial_movimientos(id_local=id_local_activo, limit=50)

        if historial_df.empty:
            st.info("No se han registrado movimientos todavía en la base de datos.")
        else:
            st.dataframe(
                historial_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id_movimiento": "N°",
                    "tipo": "Operación",
                    "fecha_movimiento": st.column_config.DatetimeColumn("Fecha y Hora", format="YYYY-MM-DD HH:mm"),
                    "local_origen": "Origen",
                    "local_destino": "Destino",
                    "producto": "Materia Prima",
                    "id_lote": "Lote #",
                    "codigo_lote_proveedor": "Lote Prov.",
                    "cantidad": st.column_config.NumberColumn("Cantidad", format="%.3f"),
                    "unidad_medida": "Unidad",
                    "referencia": "Referencia / Guía",
                    "observaciones": "Observaciones",
                    "estado": "Estado",
                },
            )

# ==============================================================================
# TAB 7: MANTENEDORES (CATÁLOGOS MAESTROS DE PROVEEDORES Y PRODUCTOS)
# ==============================================================================
with tab_maestros:
    st.markdown("### ⚙️ Administración de Catálogos Maestros")
    st.caption(
        "Mantenimiento centralizado de proveedores y materias primas. "
        "Las altas y modificaciones se sincronizan de inmediato con los formularios de recepción e inventario."
    )

    subtab_m_prov, subtab_m_prod = st.tabs(
        ["🏢 Catálogo de Proveedores", "🥩 Catálogo de Materias Primas"]
    )

    # --------------------------------------------------------------------------
    # SUBTAB: PROVEEDORES
    # --------------------------------------------------------------------------
    with subtab_m_prov:
        todos_prov_df = db.load_proveedores(solo_activos=False)

        col_p_tbl, col_p_act = st.columns([1.5, 1])

        with col_p_tbl:
            st.markdown("##### 📋 Proveedores Registrados")
            if todos_prov_df.empty:
                st.info("No hay proveedores dados de alta.")
            else:
                st.dataframe(
                    todos_prov_df[[
                        "id_proveedor", "nombre", "rut", "telefono", "correo", "activo"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id_proveedor": st.column_config.NumberColumn("ID", width="small"),
                        "nombre": "Razón Social / Nombre",
                        "rut": "RUT / Identificador",
                        "telefono": "Teléfono",
                        "correo": "Correo Electrónico",
                        "activo": st.column_config.CheckboxColumn("Activo", width="small"),
                    },
                )

        with col_p_act:
            st.markdown("##### 🛠️ Acciones")
            accion_prov = st.radio(
                "Operación:",
                ["➕ Registrar Nuevo", "✏️ Modificar Existente"],
                horizontal=True,
                key="radio_accion_prov",
            )

            if accion_prov == "➕ Registrar Nuevo":
                with st.container(border=True):
                    st.markdown("###### Alta de Proveedor")
                    with st.form("form_alta_prov", clear_on_submit=True):
                        p_nom = st.text_input("Nombre / Razón Social:*", placeholder="Ej. Frigorífico del Sur")
                        p_rut = st.text_input("RUT / Identificador fiscal:", placeholder="Ej. 76.123.456-7")
                        p_tel = st.text_input("Teléfono:", placeholder="+56 9 1234 5678")
                        p_mail = st.text_input("Correo electrónico:", placeholder="contacto@frigorifico.cl")
                        p_dir = st.text_input("Dirección comercial:", placeholder="Av. Los Aromos 450")
                        p_act = st.checkbox("Proveedor Habilitado (Activo)", value=True)

                        btn_crear_prov = st.form_submit_button("💾 Guardar Proveedor", type="primary", use_container_width=True)

                    if btn_crear_prov:
                        if not p_nom.strip():
                            st.error("El nombre del proveedor es obligatorio.")
                        else:
                            try:
                                nuevo_id_prov = db.crear_proveedor(
                                    nombre=p_nom,
                                    rut=p_rut,
                                    telefono=p_tel,
                                    correo=p_mail,
                                    direccion=p_dir,
                                    activo=p_act,
                                )
                                st.success(f"✅ Proveedor creado con éxito con ID #{nuevo_id_prov}.")
                                st.rerun()
                            except Exception as err:
                                st.error(f"Error al registrar proveedor: {err}")

            else:
                with st.container(border=True):
                    st.markdown("###### Edición de Proveedor")
                    if todos_prov_df.empty:
                        st.warning("No hay proveedores para editar.")
                    else:
                        dict_opc_prov = {
                            int(row["id_proveedor"]): f"{row['nombre']} ({row['rut'] or 'Sin RUT'})"
                            for _, row in todos_prov_df.iterrows()
                        }
                        prov_id_edit = st.selectbox(
                            "Selecciona el proveedor a modificar:",
                            options=list(dict_opc_prov.keys()),
                            format_func=lambda k: dict_opc_prov[k],
                            key="sel_edit_prov",
                        )

                        fila_edit_p = todos_prov_df[todos_prov_df["id_proveedor"] == prov_id_edit].iloc[0]

                        with st.form("form_edit_prov"):
                            ed_nom = st.text_input("Nombre / Razón Social:*", value=str(fila_edit_p["nombre"]))
                            ed_rut = st.text_input("RUT / Identificador:", value=str(fila_edit_p["rut"] or ""))
                            ed_tel = st.text_input("Teléfono:", value=str(fila_edit_p["telefono"] or ""))
                            ed_mail = st.text_input("Correo electrónico:", value=str(fila_edit_p["correo"] or ""))
                            ed_dir = st.text_input("Dirección:", value=str(fila_edit_p["direccion"] or ""))
                            ed_act = st.checkbox("Proveedor Habilitado (Activo)", value=bool(fila_edit_p["activo"]))

                            btn_update_prov = st.form_submit_button("🔄 Actualizar Proveedor", type="primary", use_container_width=True)

                        if btn_update_prov:
                            if not ed_nom.strip():
                                st.error("El nombre del proveedor es obligatorio.")
                            else:
                                try:
                                    db.actualizar_proveedor(
                                        id_proveedor=int(prov_id_edit),
                                        nombre=ed_nom,
                                        rut=ed_rut,
                                        telefono=ed_tel,
                                        correo=ed_mail,
                                        direccion=ed_dir,
                                        activo=ed_act,
                                    )
                                    st.success(f"✅ Proveedor #{prov_id_edit} actualizado con éxito.")
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"Error al actualizar proveedor: {err}")

    # --------------------------------------------------------------------------
    # SUBTAB: PRODUCTOS
    # --------------------------------------------------------------------------
    with subtab_m_prod:
        todos_prod_df = db.load_productos(solo_activos=False)

        col_pr_tbl, col_pr_act = st.columns([1.5, 1])

        with col_pr_tbl:
            st.markdown("##### 📋 Catálogo de Materias Primas")
            if todos_prod_df.empty:
                st.info("No hay productos registrados en la base de datos.")
            else:
                st.dataframe(
                    todos_prod_df[[
                        "id_producto", "nombre", "unidad_medida", "descripcion", "activo"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id_producto": st.column_config.NumberColumn("ID", width="small"),
                        "nombre": "Materia Prima",
                        "unidad_medida": "Unidad de Medida",
                        "descripcion": "Descripción / Ficha",
                        "activo": st.column_config.CheckboxColumn("Activo", width="small"),
                    },
                )

        with col_pr_act:
            st.markdown("##### 🛠️ Acciones")
            accion_prod = st.radio(
                "Operación:",
                ["➕ Registrar Nuevo", "✏️ Modificar Existente"],
                horizontal=True,
                key="radio_accion_prod",
            )

            unidades_disponibles = ["kg", "g", "l", "ml", "unidad"]

            if accion_prod == "➕ Registrar Nuevo":
                with st.container(border=True):
                    st.markdown("###### Alta de Materia Prima")
                    with st.form("form_alta_prod", clear_on_submit=True):
                        pr_nom = st.text_input("Nombre de la materia prima:*", placeholder="Ej. Salmón del Atlántico")
                        pr_unid = st.selectbox("Unidad de Medida:*", unidades_disponibles, index=0)
                        pr_desc = st.text_area("Descripción / Especificaciones:", placeholder="Corte fresco, grado sushi...", height=75)
                        pr_act = st.checkbox("Materia Prima Habilitada (Activa)", value=True)

                        btn_crear_prod = st.form_submit_button("💾 Guardar Producto", type="primary", use_container_width=True)

                    if btn_crear_prod:
                        if not pr_nom.strip():
                            st.error("El nombre del producto es obligatorio.")
                        else:
                            try:
                                nuevo_id_prod = db.crear_producto(
                                    nombre=pr_nom,
                                    unidad_medida=pr_unid,
                                    descripcion=pr_desc,
                                    activo=pr_act,
                                )
                                st.success(f"✅ Producto creado con éxito con ID #{nuevo_id_prod}.")
                                st.rerun()
                            except Exception as err:
                                st.error(f"Error al registrar producto: {err}")

            else:
                with st.container(border=True):
                    st.markdown("###### Edición de Materia Prima")
                    if todos_prod_df.empty:
                        st.warning("No hay productos disponibles para editar.")
                    else:
                        dict_opc_prod = {
                            int(row["id_producto"]): f"{row['nombre']} ({row['unidad_medida']})"
                            for _, row in todos_prod_df.iterrows()
                        }
                        prod_id_edit = st.selectbox(
                            "Selecciona la materia prima a modificar:",
                            options=list(dict_opc_prod.keys()),
                            format_func=lambda k: dict_opc_prod[k],
                            key="sel_edit_prod",
                        )

                        fila_edit_pr = todos_prod_df[todos_prod_df["id_producto"] == prod_id_edit].iloc[0]
                        idx_unidad = unidades_disponibles.index(fila_edit_pr["unidad_medida"]) if fila_edit_pr["unidad_medida"] in unidades_disponibles else 0

                        with st.form("form_edit_prod"):
                            ed_pr_nom = st.text_input("Nombre:*", value=str(fila_edit_pr["nombre"]))
                            ed_pr_unid = st.selectbox("Unidad de Medida:*", unidades_disponibles, index=idx_unidad)
                            ed_pr_desc = st.text_area("Descripción:", value=str(fila_edit_pr["descripcion"] or ""), height=75)
                            ed_pr_act = st.checkbox("Materia Prima Habilitada (Activa)", value=bool(fila_edit_pr["activo"]))

                            btn_update_prod = st.form_submit_button("🔄 Actualizar Producto", type="primary", use_container_width=True)

                        if btn_update_prod:
                            if not ed_pr_nom.strip():
                                st.error("El nombre del producto es obligatorio.")
                            else:
                                try:
                                    db.actualizar_producto(
                                        id_producto=int(prod_id_edit),
                                        nombre=ed_pr_nom,
                                        unidad_medida=ed_pr_unid,
                                        descripcion=ed_pr_desc,
                                        activo=ed_pr_act,
                                    )
                                    st.success(f"✅ Producto #{prod_id_edit} actualizado con éxito.")
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"Error al actualizar producto: {err}")
