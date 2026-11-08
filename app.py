import os
import json
from datetime import date, timedelta
from typing import Optional

import pandas as pd
import streamlit.components.v1 as components

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

def render_echarts(options: dict, height: int = 280, key: str = "chart"):
    """Renderiza gráficos Apache ECharts nativos con soporte responsivo y animación fluida."""
    chart_id = f"echart_{key}"
    json_options = json.dumps(options, ensure_ascii=False)
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }}
            #{chart_id} {{
                width: 100%;
                height: {height}px;
            }}
        </style>
    </head>
    <body>
        <div id="{chart_id}"></div>
        <script>
            (function() {{
                var chartDom = document.getElementById('{chart_id}');
                var myChart = echarts.init(chartDom, null, {{ renderer: 'canvas' }});
                var option = {json_options};
                myChart.setOption(option);
                window.addEventListener('resize', function() {{
                    myChart.resize();
                }});
                window.addEventListener('orientationchange', function() {{
                    setTimeout(function() {{ myChart.resize(); }}, 150);
                }});
            }})();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=height + 8)

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
        background:
            radial-gradient(circle at 88% 18%, rgba(56, 189, 248, 0.18), transparent 42%),
            radial-gradient(circle at 12% 85%, rgba(245, 158, 11, 0.14), transparent 38%),
            linear-gradient(135deg, #09192f 0%, #112d4e 55%, #163e6c 100%);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-top: 4px solid #f59e0b;
        border-radius: 16px;
        padding: 20px 26px;
        color: #ffffff;
        margin-bottom: 14px;
        box-shadow: 0 10px 28px -6px rgba(9, 25, 47, 0.32);
        position: relative;
        overflow: hidden;
    }
    .hero-flex-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 20px;
        flex-wrap: wrap;
        margin-bottom: 14px;
    }
    .hero-brand-group {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .hero-icon-box {
        width: 56px;
        height: 56px;
        border-radius: 14px;
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(56, 189, 248, 0.15) 100%);
        border: 1.5px solid rgba(245, 158, 11, 0.55);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 4px 16px rgba(245, 158, 11, 0.2);
    }
    .hero-title-text {
        font-size: 1.85rem;
        font-weight: 800;
        margin: 0;
        color: #ffffff;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .hero-version-pill {
        font-size: 0.7rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
        color: #451a03;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        box-shadow: 0 2px 6px rgba(245, 158, 11, 0.3);
    }
    .hero-subtitle {
        font-size: 0.9rem;
        color: #cbd5e1;
        margin-top: 3px;
        line-height: 1.35;
    }
    .hero-pulse-hud {
        background: rgba(15, 23, 42, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 12px;
        padding: 10px 16px;
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        gap: 16px;
        flex-wrap: wrap;
    }
    .hero-pulse-item {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .hero-pulse-divider {
        width: 1px;
        height: 30px;
        background: rgba(255, 255, 255, 0.16);
    }
    .hero-pulse-label {
        font-size: 0.68rem;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .hero-pulse-val {
        font-size: 0.88rem;
        font-weight: 700;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .hero-badge-container {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        padding-top: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-badge {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.76rem;
        font-weight: 600;
        color: #f1f5f9;
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

    /* Pestañas modernas tipo Segmented Control / Pills (React Aria + BaseWeb) */
    div[data-testid="stTabs"] [role="tablist"],
    div[data-testid="stTabs"] [data-baseweb="tab-list"],
    .stTabs [role="tablist"],
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background-color: #f1f5f9 !important;
        padding: 6px !important;
        border-radius: 12px !important;
        border: 1.5px solid #cbd5e1 !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        scrollbar-width: none !important;
        -webkit-overflow-scrolling: touch !important;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.05) !important;
    }
    div[data-testid="stTabs"] [role="tablist"]::after,
    .stTabs [role="tablist"]::after,
    div[data-testid="stTab"] .react-aria-SelectionIndicator,
    div[data-testid="stTabs"] [data-baseweb="tab-border"],
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"],
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    div[data-testid="stTab"],
    div[data-testid="stTabs"] [role="tab"],
    div[data-testid="stTabs"] button[data-baseweb="tab"],
    .stTabs [role="tab"],
    .stTabs button[data-baseweb="tab"] {
        height: 40px !important;
        padding: 0 16px !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-size: 0.86rem !important;
        color: #475569 !important;
        border: 1px solid transparent !important;
        background-color: transparent !important;
        transition: all 0.2s ease-in-out !important;
        white-space: nowrap !important;
    }
    div[data-testid="stTab"]:hover,
    div[data-testid="stTab"][data-hovered],
    div[data-testid="stTabs"] [role="tab"]:hover,
    div[data-testid="stTabs"] button[data-baseweb="tab"]:hover,
    .stTabs [role="tab"]:hover {
        color: #0d2b45 !important;
        background-color: #ffffff !important;
        border-color: #e2e8f0 !important;
    }
    div[data-testid="stTab"][aria-selected="true"],
    div[data-testid="stTab"][data-selected],
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"],
    .stTabs [role="tab"][aria-selected="true"],
    .stTabs button[aria-selected="true"] {
        background: linear-gradient(135deg, #0d2b45 0%, #163863 100%) !important;
        color: #ffffff !important;
        border: 1px solid #f59e0b !important;
        box-shadow: 0 3px 10px rgba(13, 43, 69, 0.25) !important;
        font-weight: 700 !important;
    }
    div[data-testid="stTab"][aria-selected="true"] *,
    div[data-testid="stTab"][data-selected] *,
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
    .stTabs [role="tab"][aria-selected="true"] *,
    .stTabs button[aria-selected="true"] * {
        color: #ffffff !important;
    }

    /* Botones interactivos y amigables al tacto */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        transition: all 0.2s ease;
        min-height: 40px;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(13, 43, 69, 0.12);
    }
    div.stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 40px;
        transition: all 0.2s ease;
    }

    /* Contenedores con borde y tarjetas (Clean SaaS look) */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        background: #ffffff;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
    }

    /* Tarjetas de métricas nativas */
    [data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    [data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #64748b;
        font-size: 0.8rem;
    }
    [data-testid="stMetricValue"] {
        font-weight: 700;
        color: #0d2b45;
    }

    /* Métricas en la barra lateral: tamaño adaptado para evitar truncamiento (...) */
    [data-testid="stSidebar"] [data-testid="stMetric"] {
        padding: 8px 10px;
        background: #ffffff;
    }
    [data-testid="stSidebar"] [data-testid="stMetricValue"],
    [data-testid="stSidebar"] [data-testid="stMetricValue"] * {
        font-size: 1.15rem !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }

    /* =========================================================================
       HERO FINANCIERO Y DISTRIBUCIÓN DE RIESGO
       ========================================================================= */
    .hero-fin-card {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
        margin-bottom: 16px;
    }
    .hero-fin-grid {
        display: grid;
        grid-template-columns: 1.2fr 1fr;
        gap: 24px;
        align-items: center;
    }
    @media (max-width: 768px) {
        .hero-fin-grid {
            grid-template-columns: 1fr;
            gap: 16px;
        }
    }
    .hero-fin-col {
        display: flex;
        flex-direction: column;
    }
    .hero-fin-title {
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 4px;
    }
    .hero-fin-val-blue {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0d2b45;
        line-height: 1.2;
    }
    .hero-fin-val-red {
        font-size: 1.85rem;
        font-weight: 800;
        color: #e63946;
        line-height: 1.2;
    }
    .hero-fin-badge-crit {
        background: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-top: 5px;
        width: fit-content;
    }
    .risk-bar-container {
        margin-top: 16px;
        padding-top: 14px;
        border-top: 1px dashed #e2e8f0;
    }
    .risk-bar {
        display: flex;
        height: 10px;
        border-radius: 6px;
        overflow: hidden;
        background: #f1f5f9;
        margin-bottom: 8px;
    }
    .risk-bar-seg {
        height: 100%;
        transition: width 0.3s ease;
    }
    .risk-legend-row {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
        font-size: 0.74rem;
        color: #475569;
    }

    /* =========================================================================
       TARJETAS DEL SEMÁFORO MODULAR
       ========================================================================= */
    .semaforo-card {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
        transition: all 0.2s ease-in-out;
        margin-bottom: 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .semaforo-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.12);
        border-color: #0d2b45;
    }
    .semaforo-header {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 6px;
    }
    .semaforo-num-flex {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 4px;
    }
    .semaforo-num {
        font-size: 1.85rem;
        font-weight: 800;
        line-height: 1;
    }
    .semaforo-monto-pill {
        font-size: 0.78rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        white-space: nowrap;
    }
    .semaforo-sub {
        font-size: 0.73rem;
        color: #64748b;
        margin-top: 4px;
    }

    /* =========================================================================
       TARJETAS OPERATIVAS (KPIS DE GESTIÓN)
       ========================================================================= */
    .op-kpi-card {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
        transition: all 0.2s ease-in-out;
        margin-bottom: 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    .op-kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.12);
        border-color: #0d2b45;
    }
    .op-kpi-head {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .op-kpi-icon-box {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.15rem;
        flex-shrink: 0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    .op-kpi-title {
        font-size: 0.76rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        line-height: 1.25;
    }
    .op-kpi-val {
        font-size: 1.55rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.15;
        margin-bottom: 6px;
    }
    .op-kpi-tag {
        font-size: 0.73rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
        display: inline-block;
        width: fit-content;
    }

    /* =========================================================================
       TARJETAS DE RECETA RECOMENDADA VIBRANTES (PLAN DE CHOQUE)
       ========================================================================= */
    .recipe-card {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
        transition: all 0.25s ease-in-out;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 12px;
        position: relative;
    }
    .recipe-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 14px 28px rgba(15, 23, 42, 0.14);
        border-color: #0d2b45;
    }
    .recipe-card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .recipe-cat-badge {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #475569;
        background: #f1f5f9;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .recipe-urg-critico {
        background: #fee2e2;
        color: #b91c1c;
        font-size: 0.73rem;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 12px;
        border: 1px solid #fecaca;
    }
    .recipe-urg-alta {
        background: #ffedd5;
        color: #c2410c;
        font-size: 0.73rem;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 12px;
        border: 1px solid #fed7aa;
    }
    .recipe-header-flex {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 14px;
    }
    .recipe-avatar {
        width: 44px;
        height: 44px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
        flex-shrink: 0;
    }
    .recipe-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.25;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .recipe-carta {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 2px;
    }
    .recipe-kpi-banner {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #bbf7d0;
        border-radius: 10px;
        padding: 12px 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .recipe-kpi-num {
        font-size: 1.55rem;
        font-weight: 800;
        color: #14532d;
        line-height: 1;
    }
    .recipe-kpi-gain {
        font-size: 1.15rem;
        font-weight: 800;
        color: #15803d;
        line-height: 1;
    }
    .recipe-kpi-sub {
        font-size: 0.72rem;
        font-weight: 600;
        color: #166534;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-top: 3px;
    }
    .recipe-meta-list {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 12px;
        font-size: 0.8rem;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    .recipe-meta-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 6px;
    }
    .recipe-footer-callout {
        background: #f0f9ff;
        border-left: 3px solid #0284c7;
        border-radius: 0 6px 6px 0;
        padding: 7px 10px;
        font-size: 0.76rem;
        color: #0369a1;
        line-height: 1.35;
    }

    /* =========================================================================
       RESPONSIVE DESIGN Y COMPATIBILIDAD MÓVIL
       ========================================================================= */
    @media (max-width: 768px) {
        /* Espaciado del lienzo en teléfonos */
        .main .block-container {
            padding-top: 1.5rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-bottom: 2rem !important;
        }
        /* Hero Banner compacto para celular */
        .hero-container {
            padding: 16px 14px !important;
            margin-bottom: 14px !important;
            border-radius: 12px !important;
        }
        .hero-title-text {
            font-size: 1.4rem !important;
            line-height: 1.25 !important;
        }
        .hero-subtitle {
            font-size: 0.82rem !important;
            margin-bottom: 6px !important;
        }
        .hero-pulse-hud {
            width: 100% !important;
            justify-content: space-between !important;
            padding: 8px 12px !important;
            gap: 10px !important;
        }
        .hero-pulse-divider {
            display: none !important;
        }
        .hero-badge-container {
            gap: 6px !important;
        }
        .hero-badge {
            font-size: 0.72rem !important;
            padding: 2px 8px !important;
        }
        /* Ajustar tarjetas de KPIs en pantallas pequeñas */
        .kpi-card {
            padding: 12px 14px !important;
            margin-bottom: 8px !important;
        }
        .kpi-num {
            font-size: 1.4rem !important;
        }
        /* Línea de tiempo colapsada verticalmente en móvil */
        .timeline-wrapper {
            flex-direction: column !important;
            gap: 8px !important;
            margin: 12px 0 16px 0 !important;
        }
        .timeline-step {
            margin: 0 !important;
            border-left: 4px solid #1a4d6f !important;
            border-top: 1px solid #e2e8f0 !important;
            border-radius: 6px !important;
            padding: 10px 12px !important;
        }
        /* Pestañas con deslizamiento táctil horizontal */
        div[data-testid="stTabs"] [role="tablist"],
        .stTabs [data-baseweb="tab-list"] {
            padding: 4px !important;
            gap: 4px !important;
        }
        div[data-testid="stTab"],
        .stTabs [data-baseweb="tab"] {
            height: 35px !important;
            padding: 0 10px !important;
            font-size: 0.78rem !important;
        }
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
val_tot = metricas["total_valor"]
val_rsk = metricas["valor_en_riesgo"]
txt_tot = f"${val_tot / 1_000_000:.1f}M" if val_tot >= 1_000_000 else f"${val_tot / 1000:,.0f}k"
txt_rsk = f"${val_rsk / 1_000_000:.1f}M" if val_rsk >= 1_000_000 else f"${val_rsk / 1000:,.0f}k"
col_s3.metric("Valor Total", txt_tot)
col_s4.metric("En Riesgo", txt_rsk)

st.sidebar.caption("Base de datos: **PostgreSQL 18**")
st.sidebar.caption("Lógica de Despacho: **FEFO / FIFO**")
st.sidebar.markdown("---")

manual_pdf_path = os.path.join(os.path.dirname(__file__), "Manual_de_Usuario_MamaQocha.pdf")
if os.path.exists(manual_pdf_path):
    with open(manual_pdf_path, "rb") as f_pdf:
        st.sidebar.download_button(
            label="📄 Descargar Manual (PDF)",
            data=f_pdf.read(),
            file_name="Manual_de_Usuario_MamaQocha.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.sidebar.caption("Proyecto Académico Demo Funcional")

# ==============================================================================
# HERO HEADER BANNER
# ==============================================================================
modo_badge = f"📍 {nombre_local_activo}" if id_local_activo else "🌐 Consolidado (5 Locales)"
lotes_urg_hero = int(metricas["vencidos"] + metricas["criticos"])
color_urg_hero = "#f87171" if lotes_urg_hero > 0 else "#4ade80"
icono_urg_hero = "🚨" if lotes_urg_hero > 0 else "✅"

st.markdown(
    f"""
    <div class="hero-container">
        <div class="hero-flex-top">
            <div class="hero-brand-group">
                <div class="hero-icon-box">
                    <svg width="34" height="34" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="18" cy="13" r="6" fill="url(#sunGrad)" />
                        <path d="M4 24C7.5 21 11 21 14.5 24C18 27 21.5 27 25 24C28.5 21 30.5 22 32 23.5" stroke="#38bdf8" stroke-width="2.6" stroke-linecap="round"/>
                        <path d="M6 29.5C9.5 26.5 13 26.5 16.5 29.5C20 32.5 23.5 32.5 27 29.5C29 27.8 30.5 28 31.5 29" stroke="#f59e0b" stroke-width="2.2" stroke-linecap="round"/>
                        <path d="M18 3V5M9.5 6.5L11 8M26.5 6.5L25 8" stroke="#fbbf24" stroke-width="2" stroke-linecap="round"/>
                        <defs>
                            <linearGradient id="sunGrad" x1="12" y1="7" x2="24" y2="19" gradientUnits="userSpaceOnUse">
                                <stop stop-color="#fde047"/>
                                <stop offset="1" stop-color="#f59e0b"/>
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
                <div>
                    <h1 class="hero-title-text">
                        Mamá Qocha
                        <span class="hero-version-pill">v2.4 Enterprise</span>
                    </h1>
                    <div class="hero-subtitle">
                        Control Gastronómico de Trazabilidad, Rotación FEFO y Rescate de Insumos Críticos
                    </div>
                </div>
            </div>
            <div class="hero-pulse-hud">
                <div class="hero-pulse-item">
                    <span class="hero-pulse-label">Vista Operativa</span>
                    <span class="hero-pulse-val" style="color:#38bdf8;">{modo_badge}</span>
                </div>
                <div class="hero-pulse-divider"></div>
                <div class="hero-pulse-item">
                    <span class="hero-pulse-label">Stock Físico</span>
                    <span class="hero-pulse-val">{metricas['total_cantidad']:,.1f} kg <span style="font-size:0.75rem; color:#94a3b8; font-weight:500;">({metricas['total_lotes']} lotes)</span></span>
                </div>
                <div class="hero-pulse-divider"></div>
                <div class="hero-pulse-item">
                    <span class="hero-pulse-label">Alerta FEFO</span>
                    <span class="hero-pulse-val" style="color:{color_urg_hero};">{icono_urg_hero} {lotes_urg_hero} lotes críticos</span>
                </div>
            </div>
        </div>
        <div class="hero-badge-container">
            <span class="hero-badge">🟢 Motor PostgreSQL 18 (Neon Cloud)</span>
            <span class="hero-badge">⚖️ Despacho FEFO / FIFO Automatizado</span>
            <span class="hero-badge">🛡️ Control Sanitario HACCP (≤ 4°C)</span>
            <span class="hero-badge">📅 Operación: {date.today().strftime('%d-%m-%Y')}</span>
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

    # Tarjeta Ejecutiva Financiera Unificada con Barra de Riesgo
    tot_val = metricas['total_valor'] if metricas['total_valor'] > 0 else 1.0
    pct_venc = (metricas['valor_vencidos'] / tot_val) * 100
    pct_crit = (metricas['valor_criticos'] / tot_val) * 100
    pct_prev = (metricas['valor_preventivos'] / tot_val) * 100
    pct_opt = max(0.0, 100.0 - pct_venc - pct_crit - pct_prev)

    st.markdown(
        f"""
        <div class="hero-fin-card">
            <div class="hero-fin-grid">
                <div class="hero-fin-col">
                    <span class="hero-fin-title">💼 Valorización del Inventario Activo</span>
                    <div class="hero-fin-val-blue">${metricas['total_valor']:,.0f} CLP</div>
                    <span style="font-size:0.8rem; color:#64748b; margin-top:4px;">
                        Calculado según costo unitario real en facturas de compra ({metricas['total_lotes']} lotes activos).
                    </span>
                </div>
                <div class="hero-fin-col">
                    <span class="hero-fin-title">⚠️ Capital en Riesgo de Vencimiento</span>
                    <div class="hero-fin-val-red">${metricas['valor_en_riesgo']:,.0f} CLP</div>
                    <div>
                        <span class="hero-fin-badge-crit">
                            🚨 <strong>{metricas['pct_en_riesgo']:.1f}%</strong> del Capital en Riesgo (≤ 7 días / vencido)
                        </span>
                    </div>
                </div>
            </div>
            <div class="risk-bar-container">
                <div style="display:flex; justify-content:space-between; font-size:0.75rem; font-weight:700; color:#475569; margin-bottom:6px;">
                    <span>DISTRIBUCIÓN DEL CAPITAL POR NIVEL DE RIESGO:</span>
                    <span>100% AUDITADO</span>
                </div>
                <div class="risk-bar">
                    <div class="risk-bar-seg" style="width:{pct_venc:.1f}%; background:#e63946;" title="Vencidos: {pct_venc:.1f}%"></div>
                    <div class="risk-bar-seg" style="width:{pct_crit:.1f}%; background:#f77f00;" title="Críticos: {pct_crit:.1f}%"></div>
                    <div class="risk-bar-seg" style="width:{pct_prev:.1f}%; background:#fcbf49;" title="Preventivos: {pct_prev:.1f}%"></div>
                    <div class="risk-bar-seg" style="width:{pct_opt:.1f}%; background:#2a9d8f;" title="Óptimos: {pct_opt:.1f}%"></div>
                </div>
                <div class="risk-legend-row">
                    <span><strong style="color:#e63946;">🔴 Vencido:</strong> {pct_venc:.1f}% (${metricas['valor_vencidos']:,.0f})</span>
                    <span><strong style="color:#f77f00;">🟠 Crítico:</strong> {pct_crit:.1f}% (${metricas['valor_criticos']:,.0f})</span>
                    <span><strong style="color:#b38600;">🟡 Preventivo:</strong> {pct_prev:.1f}% (${metricas['valor_preventivos']:,.0f})</span>
                    <span><strong style="color:#2a9d8f;">🟢 Óptimo:</strong> {pct_opt:.1f}% (${metricas['valor_optimos']:,.0f})</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tarjetas Modulares del Semáforo
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown(
            f"""
            <div class="semaforo-card" style="border-top: 5px solid #e63946;">
                <div class="semaforo-header" style="color: #e63946;">🔴 Vencidos</div>
                <div class="semaforo-num-flex">
                    <span class="semaforo-num" style="color: #e63946;">{metricas['vencidos']} <span style="font-size:0.85rem; font-weight:600; color:#64748b;">lotes</span></span>
                    <span class="semaforo-monto-pill" style="background:#fee2e2; color:#b91c1c;">${metricas['valor_vencidos']:,.0f}</span>
                </div>
                <div class="semaforo-sub">Caducados (Acción inmediata)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col2:
        st.markdown(
            f"""
            <div class="semaforo-card" style="border-top: 5px solid #f77f00;">
                <div class="semaforo-header" style="color: #c2410c;">🟠 Crítico (≤ 7 d)</div>
                <div class="semaforo-num-flex">
                    <span class="semaforo-num" style="color: #f77f00;">{metricas['criticos']} <span style="font-size:0.85rem; font-weight:600; color:#64748b;">lotes</span></span>
                    <span class="semaforo-monto-pill" style="background:#ffedd5; color:#c2410c;">${metricas['valor_criticos']:,.0f}</span>
                </div>
                <div class="semaforo-sub">Prioridad máxima en cocina</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col3:
        st.markdown(
            f"""
            <div class="semaforo-card" style="border-top: 5px solid #e0a912;">
                <div class="semaforo-header" style="color: #a16207;">🟡 Preventivo (8-30 d)</div>
                <div class="semaforo-num-flex">
                    <span class="semaforo-num" style="color: #d97706;">{metricas['preventivos']} <span style="font-size:0.85rem; font-weight:600; color:#64748b;">lotes</span></span>
                    <span class="semaforo-monto-pill" style="background:#fef3c7; color:#92400e;">${metricas['valor_preventivos']:,.0f}</span>
                </div>
                <div class="semaforo-sub">En observación y rotación regular</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col4:
        st.markdown(
            f"""
            <div class="semaforo-card" style="border-top: 5px solid #2a9d8f;">
                <div class="semaforo-header" style="color: #15803d;">🟢 Óptimo (> 30 d)</div>
                <div class="semaforo-num-flex">
                    <span class="semaforo-num" style="color: #2a9d8f;">{metricas['optimos']} <span style="font-size:0.85rem; font-weight:600; color:#64748b;">lotes</span></span>
                    <span class="semaforo-monto-pill" style="background:#dcfce7; color:#15803d;">${metricas['valor_optimos']:,.0f}</span>
                </div>
                <div class="semaforo-sub">Vida útil segura y holgada</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    inventario_df = db.load_inventario_alertas(id_local=id_local_activo)

    # --------------------------------------------------------------------------
    # NUEVA FILA: KPIS DE GESTIÓN Y CONTROL EJECUTIVO (ESTILIZADOS)
    # --------------------------------------------------------------------------
    total_val_inv = float(inventario_df["valor_inventario"].sum()) if not inventario_df.empty else 0.0
    potencial_facturacion = total_val_inv * 3.2
    lotes_haccp_ok = len(inventario_df[inventario_df["temperatura_recepcion"] <= 4.0]) if not inventario_df.empty else 0
    total_lotes_inv = len(inventario_df) if not inventario_df.empty else 1
    pct_haccp = (lotes_haccp_ok / total_lotes_inv * 100)
    dias_vida_pond = (
        float((inventario_df["dias_para_vencer"] * inventario_df["valor_inventario"]).sum() / total_val_inv)
        if total_val_inv > 0
        else 0.0
    )
    total_kg_stock = float(inventario_df["cantidad"].sum()) if not inventario_df.empty else 0.0
    porciones_totales_estimadas = int(total_kg_stock / 0.220) if total_kg_stock > 0 else 0

    col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)

    with col_ex1:
        st.markdown(
            f"""
            <div class="op-kpi-card">
                <div class="op-kpi-head">
                    <div class="op-kpi-icon-box" style="background:linear-gradient(135deg, #10b981 0%, #059669 100%); color:#ffffff;">💵</div>
                    <span class="op-kpi-title">Potencial Facturación Carta</span>
                </div>
                <div class="op-kpi-val">${potencial_facturacion:,.0f} <span style="font-size:0.82rem; font-weight:600; color:#64748b;">CLP</span></div>
                <div>
                    <span class="op-kpi-tag" style="background:#ecfdf5; color:#047857; border:1px solid #a7f3d0;">
                        ↑ Factor 3.2× Costo (Gastro)
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_ex2:
        st.markdown(
            f"""
            <div class="op-kpi-card">
                <div class="op-kpi-head">
                    <div class="op-kpi-icon-box" style="background:linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color:#ffffff;">🛡️</div>
                    <span class="op-kpi-title">Inocuidad HACCP (≤ 4°C)</span>
                </div>
                <div class="op-kpi-val">{pct_haccp:.1f}%</div>
                <div>
                    <span class="op-kpi-tag" style="background:#f0f9ff; color:#0369a1; border:1px solid #bae6fd;">
                        ↑ {lotes_haccp_ok}/{total_lotes_inv} lotes seguros
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_ex3:
        st.markdown(
            f"""
            <div class="op-kpi-card">
                <div class="op-kpi-head">
                    <div class="op-kpi-icon-box" style="background:linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color:#ffffff;">⏳</div>
                    <span class="op-kpi-title">Vida Útil Ponderada</span>
                </div>
                <div class="op-kpi-val">{dias_vida_pond:.1f} <span style="font-size:0.82rem; font-weight:600; color:#64748b;">días</span></div>
                <div>
                    <span class="op-kpi-tag" style="background:#fefce8; color:#a16207; border:1px solid #fef08a;">
                        Ponderado por capital
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_ex4:
        st.markdown(
            f"""
            <div class="op-kpi-card">
                <div class="op-kpi-head">
                    <div class="op-kpi-icon-box" style="background:linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color:#ffffff;">🍽️</div>
                    <span class="op-kpi-title">Capacidad de Comandas</span>
                </div>
                <div class="op-kpi-val">{porciones_totales_estimadas:,} <span style="font-size:0.82rem; font-weight:600; color:#64748b;">platos</span></div>
                <div>
                    <span class="op-kpi-tag" style="background:#eef2ff; color:#4338ca; border:1px solid #c7d2fe;">
                        ↑ {total_kg_stock:.1f} kg activos
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if inventario_df.empty:
        st.info("ℹ️ No hay existencias registradas para el local seleccionado.")
    else:
        # --------------------------------------------------------------------------
        # TOP PREPARACIONES SUGERIDAS (RESCATE DE MATERIA PRIMA CRÍTICA EN CARTA)
        # --------------------------------------------------------------------------
        st.markdown("---")
        st.markdown("#### 🍲 Top Preparaciones Recomendadas para la Carta del Día (Rescate de Insumos)")
        st.caption(
            "Cruce algorítmico entre materias primas en zona crítica y las fichas técnicas de Mamá Qocha. "
            "Permite al chef y al administrador activar 'Sugerencias del Día' para monetizar el stock antes de que venza."
        )

        recetas_activas_df = db.load_recetas(solo_activas=True)
        lotes_urgentes = inventario_df[(inventario_df["dias_para_vencer"] >= 0) & (inventario_df["dias_para_vencer"] <= 7)]

        if lotes_urgentes.empty:
            st.success("✅ **Excelente estado operativo:** No se detectan insumos en riesgo crítico (≤ 7 días). Todo el inventario se encuentra en rango preventivo u óptimo.")
        elif recetas_activas_df.empty:
            st.info("No hay recetas activas registradas en el catálogo maestro.")
        else:
            insumos_urg_resumen = (
                lotes_urgentes.groupby(["id_producto", "producto"])
                .agg(
                    kg_urgentes=("cantidad", "sum"),
                    min_dias=("dias_para_vencer", "min"),
                    locales=("local", lambda x: ", ".join(sorted(x.unique()))),
                    valor_riesgo=("valor_inventario", "sum"),
                )
                .reset_index()
            )

            platos_sugeridos = []
            for _, ins_row in insumos_urg_resumen.iterrows():
                id_prod = ins_row["id_producto"]
                nom_prod = ins_row["producto"]
                kg_disp = float(ins_row["kg_urgentes"])
                min_d = int(ins_row["min_dias"])
                locs_str = ins_row["locales"]
                val_rsk = float(ins_row["valor_riesgo"])

                recetas_asoc = recetas_activas_df[recetas_activas_df["id_producto"] == id_prod]
                for _, rec_row in recetas_asoc.iterrows():
                    kg_por_plato = float(rec_row["cantidad_kg"])
                    if kg_por_plato > 0:
                        platos_posibles = int(kg_disp / kg_por_plato)
                        if platos_posibles > 0:
                            precio_vta = float(rec_row["precio_venta"])
                            venta_recup = platos_posibles * precio_vta
                            platos_sugeridos.append({
                                "receta": rec_row["receta"],
                                "categoria": rec_row["categoria"],
                                "insumo_critico": nom_prod,
                                "kg_en_riesgo": kg_disp,
                                "porciones": platos_posibles,
                                "precio_carta": precio_vta,
                                "venta_recuperable": venta_recup,
                                "dias_restantes": min_d,
                                "locales": locs_str,
                                "costo_riesgo": val_rsk,
                            })

            df_sugeridos = pd.DataFrame(platos_sugeridos)
            if df_sugeridos.empty:
                st.warning("Hay materias primas críticas pero no están vinculadas a recetas activas.")
            else:
                df_sugeridos = df_sugeridos.sort_values(by=["dias_restantes", "venta_recuperable"], ascending=[True, False])
                venta_total_rescatable = df_sugeridos["venta_recuperable"].sum()

                st.markdown(
                    f"""
                    <div style="background: linear-gradient(90deg, #fffbeb 0%, #fef3c7 100%); border: 1px solid #fde68a; border-left: 6px solid #f59e0b; border-radius: 8px; padding: 12px 18px; margin-bottom: 16px;">
                        <strong style="color: #92400e; font-size: 1.05rem;">🎯 Oportunidad Comercial: Plan de Choque en Cocina</strong><br>
                        <span style="color: #78350f; font-size: 0.9rem;">
                            Se detectaron <strong>{len(insumos_urg_resumen)} materias primas críticas</strong> próximas a vencer. Al priorizar estos platos en la carta o menú de turno, 
                            la cadena puede transformar hasta <strong style="color: #b45309; font-size: 1.05rem;">${venta_total_rescatable:,.0f} CLP</strong> en ventas efectivas, evitando mermas operativas.
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                top_platos = df_sugeridos.head(3)
                cols_top = st.columns(len(top_platos))
                for idx, (_, p_fila) in enumerate(top_platos.iterrows()):
                    with cols_top[idx]:
                        receta = p_fila["receta"]
                        receta_lower = receta.lower()
                        if any(k in receta_lower for k in ["lomo", "carne", "res"]):
                            icono = "🥩"
                            color_grad = "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)"
                        elif any(k in receta_lower for k in ["gallina", "pollo", "ave"]):
                            icono = "🍗"
                            color_grad = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
                        elif any(k in receta_lower for k in ["ceviche", "pescado", "reineta", "salmon", "marisco", "pulpo"]):
                            icono = "🐟"
                            color_grad = "linear-gradient(135deg, #06b6d4 0%, #0284c7 100%)"
                        elif any(k in receta_lower for k in ["arroz", "chaufa"]):
                            icono = "🍚"
                            color_grad = "linear-gradient(135deg, #10b981 0%, #059669 100%)"
                        else:
                            icono = "🍽️"
                            color_grad = "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)"

                        dias = int(p_fila["dias_restantes"])
                        if dias <= 0:
                            badge_html = '<span class="recipe-urg-critico">🔴 Vence Hoy</span>'
                            color_borde_top = "#ef4444"
                        elif dias <= 2:
                            badge_html = f'<span class="recipe-urg-critico">🔴 Urgente ({dias}d)</span>'
                            color_borde_top = "#ef4444"
                        else:
                            badge_html = f'<span class="recipe-urg-alta">🟠 Prioridad ({dias}d)</span>'
                            color_borde_top = "#f59e0b"

                        card_html = f"""
                        <div class="recipe-card" style="border-top: 5px solid {color_borde_top};">
                            <div class="recipe-card-top">
                                <span class="recipe-cat-badge">{p_fila['categoria']}</span>
                                {badge_html}
                            </div>
                            <div class="recipe-header-flex">
                                <div class="recipe-avatar" style="background: {color_grad};">{icono}</div>
                                <div style="flex: 1; min-width: 0;">
                                    <div class="recipe-title" title="{receta}">{receta}</div>
                                    <div class="recipe-carta">Carta: <strong>${p_fila['precio_carta']:,.0f}</strong></div>
                                </div>
                            </div>
                            <div class="recipe-kpi-banner">
                                <div>
                                    <div class="recipe-kpi-num">{int(p_fila['porciones'])} <span style="font-size:0.85rem; font-weight:600;">platos</span></div>
                                    <div class="recipe-kpi-sub">Porciones Sugeridas</div>
                                </div>
                                <div style="text-align: right;">
                                    <div class="recipe-kpi-gain">+${p_fila['venta_recuperable']:,.0f}</div>
                                    <div class="recipe-kpi-sub">Venta Recuperable</div>
                                </div>
                            </div>
                            <div class="recipe-meta-list">
                                <div class="recipe-meta-item">
                                    <span style="color:#64748b;">⚠️ Insumo Crítico:</span>
                                    <strong>{p_fila['kg_en_riesgo']:.1f} kg {p_fila['insumo_critico']}</strong>
                                </div>
                                <div class="recipe-meta-item">
                                    <span style="color:#64748b;">📍 Sucursales:</span>
                                    <span style="font-weight:600; font-size:0.76rem;">{p_fila['locales']}</span>
                                </div>
                            </div>
                            <div class="recipe-footer-callout">
                                💡 <strong>Sugerencia Chef:</strong> Ofrecer como especial de turno o promo 2×1.
                            </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)

                with st.expander("🔍 Ver todas las recetas recomendadas para rescate de stock"):
                    st.dataframe(
                        df_sugeridos[[
                            "receta", "categoria", "insumo_critico", "kg_en_riesgo", "porciones", "precio_carta", "venta_recuperable", "dias_restantes", "locales"
                        ]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "receta": "Plato Recomendado",
                            "categoria": "Categoría",
                            "insumo_critico": "Insumo Crítico",
                            "kg_en_riesgo": st.column_config.NumberColumn("Kg en Riesgo", format="%.2f kg"),
                            "porciones": st.column_config.NumberColumn("Platos a Elaborar", format="%d u."),
                            "precio_carta": st.column_config.NumberColumn("Precio Carta", format="$%d"),
                            "venta_recuperable": st.column_config.NumberColumn("Venta Potencial", format="$%d CLP"),
                            "dias_restantes": st.column_config.NumberColumn("Días Restantes", format="%d d."),
                            "locales": "Sucursales Afectadas",
                        },
                    )

        st.markdown("---")
        # Gráficos interactivos
        col_g1, col_g2 = st.columns([1, 1.4])

        with col_g1:
            with st.container(border=True):
                st.markdown("##### 🥧 Distribución del Semáforo")
                resumen_alertas = inventario_df["estado_alerta"].value_counts().reset_index()
                resumen_alertas.columns = ["Estado", "Cantidad de Lotes"]

                colores_map = {
                    "🔴 Vencido": "#e63946",
                    "🟠 Crítico (≤ 7 días)": "#f77f00",
                    "🟡 Preventivo (8-30 días)": "#fcbf49",
                    "🟢 Óptimo (> 30 días)": "#2a9d8f",
                }

                donut_data = [
                    {
                        "name": str(row["Estado"]),
                        "value": int(row["Cantidad de Lotes"]),
                        "itemStyle": {"color": colores_map.get(str(row["Estado"]), "#8da9c4")},
                    }
                    for _, row in resumen_alertas.iterrows()
                ]

                option_donut = {
                    "tooltip": {
                        "trigger": "item",
                        "formatter": "{b}<br/><b>{c} lotes</b> ({d}%)",
                    },
                    "legend": {
                        "bottom": "0%",
                        "left": "center",
                        "icon": "circle",
                        "textStyle": {"fontSize": 11, "color": "#475569"},
                    },
                    "series": [
                        {
                            "name": "Semáforo",
                            "type": "pie",
                            "radius": ["48%", "72%"],
                            "center": ["50%", "45%"],
                            "avoidLabelOverlap": False,
                            "itemStyle": {
                                "borderRadius": 6,
                                "borderColor": "#ffffff",
                                "borderWidth": 2,
                            },
                            "label": {"show": False},
                            "emphasis": {
                                "scale": True,
                                "scaleSize": 5,
                                "label": {
                                    "show": True,
                                    "fontSize": 14,
                                    "fontWeight": "bold",
                                    "formatter": "{d}%",
                                },
                            },
                            "data": donut_data,
                        }
                    ],
                }
                render_echarts(option_donut, height=270, key="donut_semaforo")

        with col_g2:
            with st.container(border=True):
                st.markdown("##### 🥩 Stock Total por Producto (kg)")
                stock_producto = (
                    inventario_df.groupby("producto")["cantidad"]
                    .sum()
                    .reset_index()
                    .sort_values(by="cantidad", ascending=True)
                )

                option_bar = {
                    "tooltip": {
                        "trigger": "axis",
                        "axisPointer": {"type": "shadow"},
                        "formatter": "{b}: <b>{c} kg</b>",
                    },
                    "grid": {
                        "left": "3%",
                        "right": "12%",
                        "bottom": "3%",
                        "top": "5%",
                        "containLabel": True,
                    },
                    "xAxis": {
                        "type": "value",
                        "axisLabel": {"formatter": "{value} kg"},
                        "splitLine": {"lineStyle": {"type": "dashed", "color": "#e2e8f0"}},
                    },
                    "yAxis": {
                        "type": "category",
                        "data": [str(p) for p in stock_producto["producto"].tolist()],
                        "axisLine": {"lineStyle": {"color": "#94a3b8"}},
                        "axisLabel": {"color": "#334155", "fontSize": 11},
                    },
                    "series": [
                        {
                            "name": "Stock Total",
                            "type": "bar",
                            "data": [round(float(c), 1) for c in stock_producto["cantidad"].tolist()],
                            "itemStyle": {
                                "borderRadius": [0, 6, 6, 0],
                                "color": {
                                    "type": "linear",
                                    "x": 0,
                                    "y": 0,
                                    "x2": 1,
                                    "y2": 0,
                                    "colorStops": [
                                        {"offset": 0, "color": "#0d2b45"},
                                        {"offset": 1, "color": "#00b4d8"},
                                    ],
                                },
                            },
                            "label": {
                                "show": True,
                                "position": "right",
                                "formatter": "{c} kg",
                                "color": "#0f172a",
                                "fontWeight": "bold",
                                "fontSize": 11,
                            },
                        }
                    ],
                }
                render_echarts(option_bar, height=270, key="bar_stock")

        # Matriz de Dispersión Riesgo vs Capital
        with st.container(border=True):
            st.markdown("##### 🎯 Matriz de Dispersión: Riesgo Temporal vs Capital Inmovilizado por Lote")
            st.caption(
                "Mapeo forense de cada lote físico en inventario. Las partidas ubicadas en el **cuadrante superior izquierdo** "
                "(alta valorización monetaria y pocos días de vida útil) representan el foco de alerta inmediata para la dirección."
            )
            if HAS_PLOTLY:
                fig_scatter = px.scatter(
                    inventario_df,
                    x="dias_para_vencer",
                    y="valor_inventario",
                    size="cantidad",
                    color="estado_alerta",
                    hover_name="producto",
                    hover_data={
                        "local": True,
                        "codigo_lote_proveedor": True,
                        "fecha_vencimiento": True,
                        "cantidad": ":.2f",
                        "costo_unitario": ":$,.0f",
                        "valor_inventario": ":$,.0f",
                        "dias_para_vencer": True,
                        "estado_alerta": False,
                    },
                    color_discrete_map={
                        "🔴 Vencido": "#e63946",
                        "🟠 Crítico (≤ 7 días)": "#f77f00",
                        "🟡 Preventivo (8-30 días)": "#fcbf49",
                        "🟢 Óptimo (> 30 días)": "#2a9d8f",
                    },
                    labels={
                        "dias_para_vencer": "Días Restantes de Vida Útil",
                        "valor_inventario": "Capital Inmovilizado ($CLP)",
                        "estado_alerta": "Nivel de Alerta",
                        "cantidad": "Kilos en Lote",
                    },
                )
                fig_scatter.add_vline(
                    x=7,
                    line_width=2,
                    line_dash="dash",
                    line_color="#e63946",
                    annotation_text="Límite Crítico (≤ 7 días)",
                    annotation_position="top left",
                )
                fig_scatter.update_layout(
                    margin=dict(t=25, b=10, l=10, r=10),
                    height=330,
                    yaxis=dict(tickformat="$,.0f"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.dataframe(inventario_df[["producto", "local", "dias_para_vencer", "valor_inventario"]])

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
                df_chart_loc = (
                    df_todas_sucursales.groupby(["local", "estado_alerta", "severidad_alerta"])[
                        "valor_inventario"
                    ]
                    .sum()
                    .reset_index()
                )
                df_chart_loc = df_chart_loc.sort_values(by="severidad_alerta")

                locales_unicos = df_todas_sucursales["local"].unique().tolist()
                estados_orden = [
                    "🔴 Vencido",
                    "🟠 Crítico (≤ 7 días)",
                    "🟡 Preventivo (8-30 días)",
                    "🟢 Óptimo (> 30 días)",
                ]

                colores_riesgo = {
                    "🔴 Vencido": "#e63946",
                    "🟠 Crítico (≤ 7 días)": "#f77f00",
                    "🟡 Preventivo (8-30 días)": "#fcbf49",
                    "🟢 Óptimo (> 30 días)": "#2a9d8f",
                }

                series_list = []
                for est in estados_orden:
                    sub = df_chart_loc[df_chart_loc["estado_alerta"] == est]
                    mapa_monto = dict(zip(sub["local"], sub["valor_inventario"]))
                    data_vals = [float(mapa_monto.get(loc, 0)) for loc in locales_unicos]
                    series_list.append({
                        "name": est,
                        "type": "bar",
                        "stack": "riesgo",
                        "data": data_vals,
                        "itemStyle": {"color": colores_riesgo.get(est, "#94a3b8")},
                    })

                option_sucursales = {
                    "tooltip": {
                        "trigger": "axis",
                        "axisPointer": {"type": "shadow"},
                    },
                    "legend": {
                        "top": "0%",
                        "left": "center",
                        "icon": "circle",
                        "textStyle": {"fontSize": 11, "color": "#475569"},
                    },
                    "grid": {
                        "left": "3%",
                        "right": "4%",
                        "bottom": "5%",
                        "top": "16%",
                        "containLabel": True,
                    },
                    "xAxis": {
                        "type": "category",
                        "data": locales_unicos,
                        "axisLabel": {"interval": 0, "rotate": 10, "color": "#334155", "fontSize": 11},
                    },
                    "yAxis": {
                        "type": "value",
                        "axisLabel": {
                            "formatter": "${value}",
                        },
                        "splitLine": {"lineStyle": {"type": "dashed", "color": "#e2e8f0"}},
                    },
                    "series": series_list,
                }
                render_echarts(option_sucursales, height=290, key="sucursales_riesgo")

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

        # Módulo de Traspasos Preventivos Sugeridos (Rebalanceo Logístico)
        if id_local_activo is None:
            with st.container(border=True):
                st.markdown("##### 🚚 Oportunidades de Rebalanceo Logístico (Traspasos Preventivos Sugeridos)")
                st.caption(
                    "Detección proactiva de asimetrías de abastecimiento: sucursales con materias primas críticas que pueden "
                    "ser transferidas hacia locales con existencias en cero para acelerar su rotación y evitar pérdidas."
                )
                prods_crit_unicos = df_todas_sucursales[df_todas_sucursales["dias_para_vencer"] <= 7]["producto"].unique()
                sugerencias_traspaso = []
                todos_nombres_locales = sorted(df_todas_sucursales["local"].unique())

                for p_nom in prods_crit_unicos:
                    sub_p = df_todas_sucursales[df_todas_sucursales["producto"] == p_nom]
                    stock_por_loc = sub_p.groupby("local")["cantidad"].sum().to_dict()
                    locs_con_critico = sub_p[sub_p["dias_para_vencer"] <= 7].groupby("local")["cantidad"].sum()

                    for loc_origen, cant_critica in locs_con_critico.items():
                        for loc_destino in todos_nombres_locales:
                            if loc_destino != loc_origen and stock_por_loc.get(loc_destino, 0.0) == 0.0:
                                dias_min_prod = int(sub_p[sub_p["local"] == loc_origen]["dias_para_vencer"].min())
                                cant_sug = round(cant_critica / 2.0, 1) if cant_critica > 2.0 else round(cant_critica, 1)
                                sugerencias_traspaso.append({
                                    "insumo": p_nom,
                                    "origen": loc_origen,
                                    "destino": loc_destino,
                                    "cantidad": cant_sug,
                                    "dias": dias_min_prod,
                                })

                if sugerencias_traspaso:
                    col_trasp1, col_trasp2 = st.columns(2)
                    for idx_t, sug in enumerate(sugerencias_traspaso[:4]):
                        col_t_act = col_trasp1 if idx_t % 2 == 0 else col_trasp2
                        with col_t_act:
                            st.markdown(
                                f"""
                                <div style="background:#eff6ff; border:1px solid #bfdbfe; border-left:4px solid #3b82f6; border-radius:6px; padding:8px 12px; margin-bottom:8px;">
                                    <strong>💡 Sugerencia #{idx_t+1}:</strong> {sug['insumo']}<br>
                                    • De <strong>{sug['origen']}</strong> $\\rightarrow$ hacia <strong>{sug['destino']}</strong> (Sin stock)<br>
                                    • Traspaso recomendado: <code>{sug['cantidad']} kg</code> (Vence en {sug['dias']} días)
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                else:
                    st.info("✅ No se detectan desequilibrios críticos de inventario entre sucursales.")

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
# TAB 3: SALIDAS POR CONSUMO EN COCINA (FEFO Y RECETAS)
# ==============================================================================
with tab_cocina:
    st.markdown("### 🍳 Salidas a Cocina y Producción Culinaria")
    st.caption(
        "Control de consumos gastronómicos bajo criterio **FEFO** (First Expired, First Out). "
        "Permite registrar producción por recetas estandarizadas (comandas por turno) o consumos directos por lote individual."
    )

    if id_local_activo:
        local_cocina_id = id_local_activo
        st.info(f"📍 Operando en la cocina del: **{nombre_local_activo}**")
    else:
        opciones_locales_cocina = {row["id_local"]: row["nombre"] for _, row in locales_df.iterrows()}
        local_cocina_id = st.selectbox(
            "Seleccionar Local donde opera la cocina:",
            options=list(opciones_locales_cocina.keys()),
            format_func=lambda k: opciones_locales_cocina[k],
            key="sel_local_cocina",
        )

    subtab_recetas, subtab_lote_manual = st.tabs(
        ["📋 Producción por Recetas (Comanda / Turno)", "📦 Salida Manual por Lote Individual"]
    )

    # --------------------------------------------------------------------------
    # SUBTAB: PRODUCCIÓN POR RECETAS ESTANDARIZADAS
    # --------------------------------------------------------------------------
    with subtab_recetas:
        st.markdown("#### 🍽️ Elaboración de Recetas y Descuento Automático FEFO")
        st.caption(
            "Configura las comandas del turno (ej. 10 Ceviches, 5 Lomo Saltado). El motor calcula el escandallo, "
            "comprueba las existencias del local y descuenta automáticamente los lotes más próximos a vencer."
        )

        if "voucher_produccion" in st.session_state:
            v_prod = st.session_state.pop("voucher_produccion")
            st.success(f"✅ ¡Producción registrada exitosamente! Vale #{v_prod['id_movimiento']} generado y auditado.")

            with st.container(border=True):
                col_vm1, col_vm2, col_vm3, col_vm4 = st.columns(4)
                col_vm1.metric("Platos Elaborados", f"{v_prod['platos_totales']} u.")
                col_vm2.metric("Venta Bruta Menú", f"${v_prod['venta_total']:,.0f}")
                col_vm3.metric("Costo Insumos (FEFO)", f"${v_prod['costo_total_insumos']:,.0f}")
                col_vm4.metric("Margen Bruto", f"${v_prod['margen_bruto']:,.0f}", f"{v_prod['pct_margen']:.1f}%")

                st.markdown(f"**Turno:** `{v_prod['turno']}` | **Movimiento de Inventario:** `#{v_prod['id_movimiento']}`")

                col_vp_left, col_vp_right = st.columns(2)
                with col_vp_left:
                    st.markdown("##### 🍲 Platos Preparados")
                    for p_item in v_prod["detalle_platos"]:
                        st.markdown(
                            f"- **{p_item['cantidad_platos']}x** {p_item['receta']} — `${p_item['subtotal_venta']:,.0f}` "
                            f"(Precio carta: ${p_item['precio_venta']:,.0f})"
                        )

                with col_vp_right:
                    st.markdown("##### 🥩 Insumos Descontados por FEFO")
                    for ins_item in v_prod["desglose_insumos"]:
                        st.markdown(
                            f"- **{ins_item['producto']}**: `{ins_item['cantidad_consumida']:.3f} {ins_item['unidad']}` "
                            f"(Lote: <code>{ins_item['codigo_lote_proveedor']}</code> | Stock restante: {ins_item['nuevo_stock']:.3f} {ins_item['unidad']})",
                            unsafe_allow_html=True,
                        )

        recetas_raw_df = db.load_recetas(solo_activas=True)
        if recetas_raw_df.empty:
            st.warning("⚠️ No hay recetas activas configuradas en la base de datos.")
        else:
            recetas_catalogo = (
                recetas_raw_df[["id_receta", "receta", "categoria", "precio_venta", "tiempo_preparacion_min"]]
                .drop_duplicates()
                .sort_values(by=["categoria", "receta"])
            )

            col_cf1, col_cf2 = st.columns([1, 2])
            with col_cf1:
                turno_prod = st.selectbox(
                    "Turno de Cocina / Servicio:*",
                    ["Almuerzo (12:00 - 16:00)", "Tarde (16:00 - 20:00)", "Cena (20:00 - 00:00)", "Evento Especial"],
                    key="sel_turno_produccion",
                )
            with col_cf2:
                obs_prod = st.text_input(
                    "Referencia de la comanda u observaciones:",
                    placeholder="Ej. Comanda salón principal y pedidos delivery",
                    key="txt_obs_produccion",
                )

            recetas_opciones = {
                int(row["id_receta"]): f"{row['receta']} ({row['categoria']}) — ${row['precio_venta']:,.0f}"
                for _, row in recetas_catalogo.iterrows()
            }

            recetas_seleccionadas = st.multiselect(
                "Selecciona los platos a elaborar en este turno:*",
                options=list(recetas_opciones.keys()),
                default=[1, 3] if (1 in recetas_opciones and 3 in recetas_opciones) else list(recetas_opciones.keys())[:2],
                format_func=lambda k: recetas_opciones[k],
                key="multisel_recetas_cocina",
            )

            if not recetas_seleccionadas:
                st.info("Selecciona al menos una receta para configurar las porciones del turno.")
            else:
                st.markdown("##### 🔢 Cantidad de Porciones por Plato")
                orden_platos = {}
                cols_porciones = st.columns(min(len(recetas_seleccionadas), 4))
                for idx, r_id in enumerate(recetas_seleccionadas):
                    col_act = cols_porciones[idx % len(cols_porciones)]
                    nom_r = recetas_catalogo.loc[recetas_catalogo["id_receta"] == r_id, "receta"].values[0]
                    with col_act:
                        cant = st.number_input(
                            f"{nom_r}:",
                            min_value=1,
                            max_value=200,
                            value=5,
                            step=1,
                            key=f"cant_receta_input_{r_id}",
                        )
                        orden_platos[r_id] = cant

                # Cálculo de requerimientos y stock disponible
                stock_local_df = db.load_stock_disponible_local(int(local_cocina_id))
                stock_por_prod = (
                    stock_local_df.groupby("id_producto")["stock_disponible"].sum().to_dict()
                    if not stock_local_df.empty
                    else {}
                )

                req_totales = {}
                venta_estimada = 0
                for r_id, cant in orden_platos.items():
                    sub_df = recetas_raw_df[recetas_raw_df["id_receta"] == r_id]
                    p_vta = float(sub_df.iloc[0]["precio_venta"])
                    venta_estimada += p_vta * cant

                    for _, ing in sub_df.iterrows():
                        p_id = int(ing["id_producto"])
                        kg_req = float(ing["cantidad_kg"]) * cant
                        if p_id not in req_totales:
                            req_totales[p_id] = {
                                "nombre": ing["ingrediente"],
                                "unidad": ing["unidad_medida"],
                                "total_req": 0.0,
                            }
                        req_totales[p_id]["total_req"] += kg_req

                st.markdown("##### 📊 Simulación de Consumo vs Stock Disponible en Sucursal")
                filas_simulacion = []
                hay_faltante = False

                for p_id, datos in req_totales.items():
                    disp = float(stock_por_prod.get(p_id, 0.0))
                    req = datos["total_req"]
                    estado_str = "✅ Suficiente" if disp >= req else f"❌ Faltan {(req - disp):.3f} {datos['unidad']}"
                    if disp < req:
                        hay_faltante = True

                    filas_simulacion.append({
                        "Insumo": datos["nombre"],
                        "Requerido (Comanda)": f"{req:.3f} {datos['unidad']}",
                        "Stock en Local": f"{disp:.3f} {datos['unidad']}",
                        "Saldo Proyectado": f"{(disp - req):.3f} {datos['unidad']}",
                        "Factibilidad": estado_str,
                    })

                simulacion_df = pd.DataFrame(filas_simulacion)
                st.dataframe(simulacion_df, use_container_width=True, hide_index=True)

                col_res1, col_res2, col_res3 = st.columns([1, 1, 1.5])
                col_res1.metric("Total Platos a Elaborar", f"{sum(orden_platos.values())} u.")
                col_res2.metric("Venta Bruta Proyectada", f"${venta_estimada:,.0f} CLP")

                with col_res3:
                    if hay_faltante:
                        st.error("⚠️ Stock insuficiente en esta sucursal para completar la comanda. Ajuste las cantidades o solicite un traspaso desde otra sucursal.")
                    else:
                        st.success("✨ ¡Stock suficiente! Todos los insumos se descontarán automáticamente bajo FEFO.")

                btn_confirmar_recetas = st.button(
                    "🍳 Confirmar y Descontar Producción por FEFO",
                    type="primary",
                    disabled=hay_faltante,
                    use_container_width=True,
                    key="btn_exec_produccion_recetas",
                )

                if btn_confirmar_recetas:
                    try:
                        res_prod = db.consumir_produccion_recetas(
                            id_local=int(local_cocina_id),
                            orden_platos=orden_platos,
                            turno=turno_prod,
                            observaciones=obs_prod.strip() or f"Producción comanda {turno_prod}",
                        )
                        st.session_state["voucher_produccion"] = res_prod
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al registrar producción: {err}")

    # --------------------------------------------------------------------------
    # SUBTAB: SALIDA MANUAL POR LOTE INDIVIDUAL
    # --------------------------------------------------------------------------
    with subtab_lote_manual:
        st.markdown("#### 📦 Salida Manual por Lote Específico")
        st.caption(
            "Permite dar salida puntual a un lote específico para consumo directo, pruebas de sabor o calibración de partidas."
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

    # Control de Vouchers de Despacho
    if "voucher_traslado_consolidado" in st.session_state:
        v_cons = st.session_state.pop("voucher_traslado_consolidado")
        st.success("✅ ¡Despacho consolidado y guías emitidas exitosamente en base de datos!")
        col_v1, col_v2 = st.columns(2)
        if v_cons.get("ida"):
            with col_v1:
                v_ida = v_cons["ida"]
                st.markdown(
                    f"""
                    <div class="voucher-card" style="border-left: 5px solid #2a9d8f; background: #f0fdf4;">
                        <h4 style="margin:0 0 8px 0; color:#0d2b45;">🔴 Guía de Despacho IDA #{v_ida['id_movimiento']}</h4>
                        • <strong>Referencia:</strong> <code>{v_ida['referencia']}</code><br>
                        • <strong>Ruta:</strong> <strong>{v_cons['origen']}</strong> ➡️ <strong>{v_cons['destino']}</strong><br>
                        • <strong>Partidas emitidas:</strong> <code>{v_ida['total_partidas']} lotes</code> (<code>{v_ida['total_kg']:.3f} kg</code>)<br>
                        • <strong>Trazabilidad:</strong> Códigos de lote preservados con éxito.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if v_cons.get("retorno"):
            with col_v2:
                v_ret = v_cons["retorno"]
                st.markdown(
                    f"""
                    <div class="voucher-card" style="border-left: 5px solid #0284c7; background: #f0f9ff;">
                        <h4 style="margin:0 0 8px 0; color:#0d2b45;">🔄 Guía de RETORNO #{v_ret['id_movimiento']}</h4>
                        • <strong>Referencia:</strong> <code>{v_ret['referencia']}</code><br>
                        • <strong>Ruta:</strong> <strong>{v_cons['destino']}</strong> ➡️ <strong>{v_cons['origen']}</strong><br>
                        • <strong>Partidas retornadas:</strong> <code>{v_ret['total_partidas']} lotes</code> (<code>{v_ret['total_kg']:.3f} kg</code>)<br>
                        • <strong>Logística de Retorno:</strong> Backhaul completado al 100%.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    if "voucher_traslado" in st.session_state:
        v_tr = st.session_state.pop("voucher_traslado")
        st.success("✅ ¡Traslado individual completado en base de datos!")
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
                # Permitir sobreescribir origen si se pinchó un flete de retorno
                default_origen = st.session_state.pop("traslado_intercambiar_origen", None)
                if default_origen and default_origen in opciones_locales_traslado:
                    idx_orig = list(opciones_locales_traslado.keys()).index(default_origen)
                else:
                    idx_orig = 0

                local_traslado_origen_id = st.selectbox(
                    "Local de Origen (Emisor):*",
                    options=list(opciones_locales_traslado.keys()),
                    index=idx_orig,
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
            default_destino = st.session_state.pop("traslado_intercambiar_destino", None)
            if default_destino and default_destino in opciones_destino:
                idx_dest = list(opciones_destino.keys()).index(default_destino)
            else:
                idx_dest = 0

            local_traslado_destino_id = st.selectbox(
                "Local de Destino (Receptor):*",
                options=list(opciones_destino.keys()),
                index=idx_dest,
                format_func=lambda k: opciones_destino[k],
                key="sel_local_traslado_destino",
            )

    # Cargar datos de riesgo FEFO para ambos locales (Ida y Retorno)
    stock_disp_traslado = db.load_stock_disponible_local(int(local_traslado_origen_id))
    df_top_origen = db.load_top_riesgo_traslado(int(local_traslado_origen_id), limit=7)
    df_top_destino = db.load_top_riesgo_traslado(int(local_traslado_destino_id), limit=7)

    # ==========================================================================
    # TABLAS DE TRASLADO: TOP 7 CRÍTICOS + OPTIMIZACIÓN DE FLETE DE RETORNO
    # ==========================================================================
    st.markdown("#### ⚖️ Tablas de Decisión Logística y Optimización de Flete (Backhaul)")
    st.caption(
        "Monitoreo bilateral de riesgo FEFO. Pincha un producto para transferirlo o aprovecha "
        "el flete de regreso para rescatar insumos críticos del local destino."
    )

    col_panel_ida, col_panel_vuelta = st.columns(2)

    # PANEL 1: FLETE DE IDA (ORIGEN -> DESTINO)
    with col_panel_ida:
        with st.container(border=True):
            nombre_orig_simple = opciones_locales.get(str(local_traslado_origen_id), "Origen").replace("📍 ", "")
            nombre_dest_simple = opciones_destino.get(local_traslado_destino_id, "Destino")
            
            val_riesgo_orig = df_top_origen["valor_en_riesgo"].sum() if not df_top_origen.empty else 0
            kg_riesgo_orig = df_top_origen["stock_disponible"].sum() if not df_top_origen.empty else 0

            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div>
                        <strong style="color:#e63946; font-size:1.05rem;">🔴 Flete de Ida: Top 7 en Riesgo</strong><br>
                        <span style="font-size:0.8rem; color:#64748b;">Desde: <b>{nombre_orig_simple}</b> ➡️ Hacia: <b>{nombre_dest_simple}</b></span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:0.75rem; color:#64748b;">Capital en Riesgo:</span><br>
                        <strong style="color:#e63946; font-size:1rem;">${val_riesgo_orig:,.0f} CLP</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if df_top_origen.empty:
                st.info("No hay insumos disponibles en el local de origen.")
            else:
                # Tabla interactiva con dataframe
                st.dataframe(
                    df_top_origen[[
                        "id_lote", "producto", "dias_para_vencer", "estado_alerta",
                        "stock_disponible", "valor_en_riesgo", "codigo_lote_proveedor"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    height=240,
                    column_config={
                        "id_lote": st.column_config.NumberColumn("Lote", format="#%d"),
                        "producto": "Materia Prima",
                        "dias_para_vencer": st.column_config.NumberColumn("Vence", format="%d d"),
                        "estado_alerta": "Semáforo",
                        "stock_disponible": st.column_config.NumberColumn("Disp.", format="%.2f kg"),
                        "valor_en_riesgo": st.column_config.NumberColumn("Valor Riesgo", format="$%d"),
                        "codigo_lote_proveedor": "Ref.",
                    }
                )

                # Selector rápido / Cargar a Guía de Ida
                lotes_ida_dict = {
                    int(r["id_lote"]): f"#{r['id_lote']} {r['producto']} (Vence: {r['dias_para_vencer']}d | Disp: {r['stock_disponible']:.2f} {r['unidad_medida']} | ${r['valor_en_riesgo']:,.0f})"
                    for _, r in df_top_origen.iterrows()
                }
                
                col_pin_sel, col_pin_btn1, col_pin_btn2 = st.columns([3, 1.2, 1.2])
                with col_pin_sel:
                    lote_pin_ida = st.selectbox(
                        "Seleccionar insumo de origen:*",
                        options=list(lotes_ida_dict.keys()),
                        format_func=lambda k: lotes_ida_dict[k],
                        key="sel_pin_ida",
                        label_visibility="collapsed",
                    )
                with col_pin_btn1:
                    if st.button("➕ Cargar", key="btn_add_ida", use_container_width=True, help="Agrega esta partida a la vista previa de la Guía de Ida."):
                        row_ida = df_top_origen[df_top_origen["id_lote"] == lote_pin_ida].iloc[0]
                        if "carro_ida_items" not in st.session_state:
                            st.session_state["carro_ida_items"] = []
                        if not any(it["id_lote"] == lote_pin_ida for it in st.session_state["carro_ida_items"]):
                            st.session_state["carro_ida_items"].append({
                                "id_lote": int(row_ida["id_lote"]),
                                "producto": str(row_ida["producto"]),
                                "codigo_lote_proveedor": str(row_ida["codigo_lote_proveedor"]),
                                "dias_para_vencer": int(row_ida["dias_para_vencer"]),
                                "stock_disponible": float(row_ida["stock_disponible"]),
                                "cantidad": float(row_ida["stock_disponible"]),
                                "costo_unitario": float(row_ida["costo_unitario"]),
                                "subtotal_valor": float(row_ida["valor_en_riesgo"]),
                                "unidad_medida": str(row_ida["unidad_medida"]),
                            })
                            st.toast(f"✅ #{lote_pin_ida} {row_ida['producto']} agregado a Guía de Ida.", icon="📦")
                            st.rerun()
                        else:
                            st.info("Esta partida ya se encuentra cargada en la Guía de Ida.")
                with col_pin_btn2:
                    if st.button("⚡ Cargar 7", key="btn_add_all_ida", use_container_width=True, help="Agrega las 7 partidas críticas a la Guía de Ida de una sola vez."):
                        if "carro_ida_items" not in st.session_state:
                            st.session_state["carro_ida_items"] = []
                        agregados = 0
                        for _, row_ida in df_top_origen.iterrows():
                            lid = int(row_ida["id_lote"])
                            if not any(it["id_lote"] == lid for it in st.session_state["carro_ida_items"]):
                                st.session_state["carro_ida_items"].append({
                                    "id_lote": lid,
                                    "producto": str(row_ida["producto"]),
                                    "codigo_lote_proveedor": str(row_ida["codigo_lote_proveedor"]),
                                    "dias_para_vencer": int(row_ida["dias_para_vencer"]),
                                    "stock_disponible": float(row_ida["stock_disponible"]),
                                    "cantidad": float(row_ida["stock_disponible"]),
                                    "costo_unitario": float(row_ida["costo_unitario"]),
                                    "subtotal_valor": float(row_ida["valor_en_riesgo"]),
                                    "unidad_medida": str(row_ida["unidad_medida"]),
                                })
                                agregados += 1
                        if agregados > 0:
                            st.toast(f"✅ Se cargaron {agregados} partidas críticas a la Guía de Ida.", icon="🚀")
                            st.rerun()

    # PANEL 2: OPTIMIZACIÓN DE RETORNO / BACKHAUL (DESTINO -> ORIGEN)
    with col_panel_vuelta:
        with st.container(border=True):
            val_riesgo_dest = df_top_destino["valor_en_riesgo"].sum() if not df_top_destino.empty else 0
            kg_riesgo_dest = df_top_destino["stock_disponible"].sum() if not df_top_destino.empty else 0

            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div>
                        <strong style="color:#0284c7; font-size:1.05rem;">🔄 Retorno Oportuno: Top 7 en Destino</strong><br>
                        <span style="font-size:0.8rem; color:#64748b;">Aprovechar vuelta desde: <b>{nombre_dest_simple}</b> ➡️ <b>{nombre_orig_simple}</b></span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:0.75rem; color:#64748b;">Rescatable en Retorno:</span><br>
                        <strong style="color:#0284c7; font-size:1rem;">${val_riesgo_dest:,.0f} CLP</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if df_top_destino.empty:
                st.info("El local destino no registra partidas críticas para flete de retorno.")
            else:
                st.dataframe(
                    df_top_destino[[
                        "id_lote", "producto", "dias_para_vencer", "estado_alerta",
                        "stock_disponible", "valor_en_riesgo", "codigo_lote_proveedor"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    height=240,
                    column_config={
                        "id_lote": st.column_config.NumberColumn("Lote", format="#%d"),
                        "producto": "Materia Prima",
                        "dias_para_vencer": st.column_config.NumberColumn("Vence", format="%d d"),
                        "estado_alerta": "Semáforo",
                        "stock_disponible": st.column_config.NumberColumn("Disp.", format="%.2f kg"),
                        "valor_en_riesgo": st.column_config.NumberColumn("Valor Riesgo", format="$%d"),
                        "codigo_lote_proveedor": "Ref.",
                    }
                )

                lotes_vuelta_dict = {
                    int(r["id_lote"]): f"#{r['id_lote']} {r['producto']} (Vence: {r['dias_para_vencer']}d | Disp: {r['stock_disponible']:.2f} {r['unidad_medida']} | ${r['valor_en_riesgo']:,.0f})"
                    for _, r in df_top_destino.iterrows()
                }

                col_ret_sel, col_ret_btn1, col_ret_btn2 = st.columns([2.6, 1.2, 1.2])
                with col_ret_sel:
                    lote_ret_sel = st.selectbox(
                        "Seleccionar insumo de retorno:*",
                        options=list(lotes_vuelta_dict.keys()),
                        format_func=lambda k: lotes_vuelta_dict[k],
                        key="sel_ret_dest",
                        label_visibility="collapsed",
                    )
                with col_ret_btn1:
                    if st.button("➕ Retorno", key="btn_add_ret", use_container_width=True, help="Agrega esta partida a la vista previa de la Guía de Retorno."):
                        row_ret = df_top_destino[df_top_destino["id_lote"] == lote_ret_sel].iloc[0]
                        if "carro_retorno_items" not in st.session_state:
                            st.session_state["carro_retorno_items"] = []
                        if not any(it["id_lote"] == lote_ret_sel for it in st.session_state["carro_retorno_items"]):
                            st.session_state["carro_retorno_items"].append({
                                "id_lote": int(row_ret["id_lote"]),
                                "producto": str(row_ret["producto"]),
                                "codigo_lote_proveedor": str(row_ret["codigo_lote_proveedor"]),
                                "dias_para_vencer": int(row_ret["dias_para_vencer"]),
                                "stock_disponible": float(row_ret["stock_disponible"]),
                                "cantidad": float(row_ret["stock_disponible"]),
                                "costo_unitario": float(row_ret["costo_unitario"]),
                                "subtotal_valor": float(row_ret["valor_en_riesgo"]),
                                "unidad_medida": str(row_ret["unidad_medida"]),
                            })
                            st.toast(f"🔄 #{lote_ret_sel} {row_ret['producto']} agregado a Guía de Retorno.", icon="🚚")
                            st.rerun()
                        else:
                            st.info("Esta partida ya se encuentra cargada en la Guía de Retorno.")
                with col_ret_btn2:
                    if st.button("⚡ Cargar 7", key="btn_add_all_ret", use_container_width=True, help="Agrega las 7 partidas críticas de destino a la Guía de Retorno."):
                        if "carro_retorno_items" not in st.session_state:
                            st.session_state["carro_retorno_items"] = []
                        agregados_ret = 0
                        for _, row_ret in df_top_destino.iterrows():
                            lid = int(row_ret["id_lote"])
                            if not any(it["id_lote"] == lid for it in st.session_state["carro_retorno_items"]):
                                st.session_state["carro_retorno_items"].append({
                                    "id_lote": lid,
                                    "producto": str(row_ret["producto"]),
                                    "codigo_lote_proveedor": str(row_ret["codigo_lote_proveedor"]),
                                    "dias_para_vencer": int(row_ret["dias_para_vencer"]),
                                    "stock_disponible": float(row_ret["stock_disponible"]),
                                    "cantidad": float(row_ret["stock_disponible"]),
                                    "costo_unitario": float(row_ret["costo_unitario"]),
                                    "subtotal_valor": float(row_ret["valor_en_riesgo"]),
                                    "unidad_medida": str(row_ret["unidad_medida"]),
                                })
                                agregados_ret += 1
                        if agregados_ret > 0:
                            st.toast(f"🔄 Se cargaron {agregados_ret} partidas a la Guía de Retorno.", icon="🚀")
                            st.rerun()

    # ==========================================================================
    # SECCIÓN: VISTA PREVIA Y MANIFIESTO DE GUÍAS DE DESPACHO (DOS TABLAS)
    # ==========================================================================
    st.markdown("---")
    st.markdown("#### 📋 Vista Previa de las Guías de Despacho (Manifiesto de Carga)")
    st.caption(
        "Detalle consolidado de los movimientos seleccionados para el flete de ida y el retorno optimizado. "
        "Ajusta cantidades o remueve partidas antes de emitir formalmente las guías."
    )

    if "carro_ida_items" not in st.session_state:
        st.session_state["carro_ida_items"] = []
    if "carro_retorno_items" not in st.session_state:
        st.session_state["carro_retorno_items"] = []

    col_preview_ida, col_preview_retorno = st.columns(2)

    # PREVIEW TABLA 1: GUÍA DE DESPACHO - IDA
    with col_preview_ida:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="background:#fee2e2; border-left:4px solid #e63946; padding:8px 12px; border-radius:4px; margin-bottom:12px;">
                    <strong style="color:#991b1b; font-size:1rem;">🔴 Guía de Despacho - IDA</strong><br>
                    <span style="font-size:0.8rem; color:#7f1d1d;">Ruta: <b>{nombre_orig_simple}</b> ➡️ <b>{nombre_dest_simple}</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            ref_def_ida = f"GT-IDA-{local_traslado_origen_id}{local_traslado_destino_id}-{pd.Timestamp.now().strftime('%Y%m%d%H%M')}"
            ref_guia_ida = st.text_input("N° Guía / Referencia de Ida:*", value=ref_def_ida, key="ref_despacho_ida")

            items_ida = st.session_state["carro_ida_items"]
            if not items_ida:
                st.info("No hay partidas cargadas en la Guía de Ida. Selecciona y presiona **➕ Cargar** en el panel superior izquierdo.")
                tot_kg_ida = 0.0
                tot_val_ida = 0.0
            else:
                df_editor_ida = pd.DataFrame(items_ida)
                edited_ida = st.data_editor(
                    df_editor_ida[[
                        "id_lote", "producto", "dias_para_vencer",
                        "stock_disponible", "cantidad", "subtotal_valor"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    key="editor_guia_ida",
                    column_config={
                        "id_lote": st.column_config.NumberColumn("Lote", disabled=True, format="#%d"),
                        "producto": st.column_config.TextColumn("Insumo", disabled=True),
                        "dias_para_vencer": st.column_config.NumberColumn("Vence", disabled=True, format="%d d"),
                        "stock_disponible": st.column_config.NumberColumn("Disp.", disabled=True, format="%.2f kg"),
                        "cantidad": st.column_config.NumberColumn("A Enviar (kg)", min_value=0.001, format="%.3f", required=True),
                        "subtotal_valor": st.column_config.NumberColumn("Valor Riesgo", disabled=True, format="$%d"),
                    }
                )
                nuevos_items_ida = []
                for _, r_ed in edited_ida.iterrows():
                    match_orig = next((x for x in items_ida if x["id_lote"] == r_ed["id_lote"]), None)
                    if match_orig:
                        cant_real = min(float(r_ed["cantidad"]), float(match_orig["stock_disponible"]))
                        match_orig["cantidad"] = cant_real
                        match_orig["subtotal_valor"] = cant_real * match_orig["costo_unitario"]
                        nuevos_items_ida.append(match_orig)
                st.session_state["carro_ida_items"] = nuevos_items_ida

                tot_kg_ida = sum(it["cantidad"] for it in nuevos_items_ida)
                tot_val_ida = sum(it["subtotal_valor"] for it in nuevos_items_ida)

                col_tot_i1, col_tot_i2 = st.columns(2)
                with col_tot_i1:
                    st.metric("Total Kilos Ida", f"{tot_kg_ida:.2f} kg")
                with col_tot_i2:
                    st.metric("Capital Rescatado", f"${tot_val_ida:,.0f} CLP")

                if st.button("🗑️ Vaciar Guía de Ida", key="btn_clear_ida"):
                    st.session_state["carro_ida_items"] = []
                    st.rerun()

    # PREVIEW TABLA 2: GUÍA DE DESPACHO - RETORNO (BACKHAUL)
    with col_preview_retorno:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="background:#e0f2fe; border-left:4px solid #0284c7; padding:8px 12px; border-radius:4px; margin-bottom:12px;">
                    <strong style="color:#0369a1; font-size:1rem;">🔄 Guía de Despacho - RETORNO</strong><br>
                    <span style="font-size:0.8rem; color:#0c4a6e;">Ruta: <b>{nombre_dest_simple}</b> ➡️ <b>{nombre_orig_simple}</b> (Aprovechamiento de flete)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            ref_def_ret = f"GT-RET-{local_traslado_destino_id}{local_traslado_origen_id}-{pd.Timestamp.now().strftime('%Y%m%d%H%M')}"
            ref_guia_ret = st.text_input("N° Guía / Referencia de Retorno:*", value=ref_def_ret, key="ref_despacho_ret")

            items_ret = st.session_state["carro_retorno_items"]
            if not items_ret:
                st.info("No hay partidas cargadas en la Guía de Retorno. Selecciona y presiona **➕ Retorno** en el panel superior derecho.")
                tot_kg_ret = 0.0
                tot_val_ret = 0.0
            else:
                df_editor_ret = pd.DataFrame(items_ret)
                edited_ret = st.data_editor(
                    df_editor_ret[[
                        "id_lote", "producto", "dias_para_vencer",
                        "stock_disponible", "cantidad", "subtotal_valor"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    key="editor_guia_retorno",
                    column_config={
                        "id_lote": st.column_config.NumberColumn("Lote", disabled=True, format="#%d"),
                        "producto": st.column_config.TextColumn("Insumo", disabled=True),
                        "dias_para_vencer": st.column_config.NumberColumn("Vence", disabled=True, format="%d d"),
                        "stock_disponible": st.column_config.NumberColumn("Disp.", disabled=True, format="%.2f kg"),
                        "cantidad": st.column_config.NumberColumn("A Retornar (kg)", min_value=0.001, format="%.3f", required=True),
                        "subtotal_valor": st.column_config.NumberColumn("Valor Riesgo", disabled=True, format="$%d"),
                    }
                )
                nuevos_items_ret = []
                for _, r_ed in edited_ret.iterrows():
                    match_orig = next((x for x in items_ret if x["id_lote"] == r_ed["id_lote"]), None)
                    if match_orig:
                        cant_real = min(float(r_ed["cantidad"]), float(match_orig["stock_disponible"]))
                        match_orig["cantidad"] = cant_real
                        match_orig["subtotal_valor"] = cant_real * match_orig["costo_unitario"]
                        nuevos_items_ret.append(match_orig)
                st.session_state["carro_retorno_items"] = nuevos_items_ret

                tot_kg_ret = sum(it["cantidad"] for it in nuevos_items_ret)
                tot_val_ret = sum(it["subtotal_valor"] for it in nuevos_items_ret)

                col_tot_r1, col_tot_r2 = st.columns(2)
                with col_tot_r1:
                    st.metric("Total Kilos Retorno", f"{tot_kg_ret:.2f} kg")
                with col_tot_r2:
                    st.metric("Capital Rescatado", f"${tot_val_ret:,.0f} CLP")

                if st.button("🗑️ Vaciar Guía de Retorno", key="btn_clear_ret"):
                    st.session_state["carro_retorno_items"] = []
                    st.rerun()

    # PANEL HORIZONTAL: BALANCE LOGÍSTICO Y EMISIÓN CONSOLIDADA
    hay_ida = len(st.session_state["carro_ida_items"]) > 0
    hay_ret = len(st.session_state["carro_retorno_items"]) > 0

    if hay_ida or hay_ret:
        peso_total_flete = tot_kg_ida + tot_kg_ret
        valor_total_flete = tot_val_ida + tot_val_ret
        pct_aprovechamiento = 100 if (hay_ida and hay_ret) else 50
        color_eficiencia = "#16a34a" if pct_aprovechamiento == 100 else "#ea580c"

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:12px;">
                    <div>
                        <span style="font-size:0.85rem; color:#64748b; font-weight:600;">RESUMEN LOGÍSTICO DEL VIAJE REDONDO:</span><br>
                        <strong style="font-size:1.15rem; color:#0f172a;">🚚 Carga Total Movilizada: {peso_total_flete:.2f} kg</strong>
                    </div>
                    <div>
                        <span style="font-size:0.85rem; color:#64748b; font-weight:600;">CAPITAL TOTAL RESCATADO:</span><br>
                        <strong style="font-size:1.15rem; color:#0284c7;">💰 ${valor_total_flete:,.0f} CLP</strong>
                    </div>
                    <div>
                        <span style="font-size:0.85rem; color:#64748b; font-weight:600;">APROVECHAMIENTO FLETE:</span><br>
                        <strong style="font-size:1.15rem; color:{color_eficiencia};">⚖️ {pct_aprovechamiento}% ({'Ida + Retorno Completo' if pct_aprovechamiento == 100 else 'Solo un sentido'})</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            obs_despacho_consolidado = st.text_area(
                "Protocolo y Condiciones de Transporte (Inocuidad y Cadena de Frío):*",
                value="Cadena de frío controlada con termómetro digital en hieleras selladas. Transporte directo sin aperturas intermedias.",
                height=55,
                key="obs_transporte_cons"
            )

            col_btn_emision1, col_btn_emision2 = st.columns([2, 1])
            with col_btn_emision1:
                if hay_ida and hay_ret:
                    btn_emitir_global = st.button(
                        f"🚚 Confirmar y Emitir Ambas Guías ({len(st.session_state['carro_ida_items'])} Ida + {len(st.session_state['carro_retorno_items'])} Retorno)",
                        type="primary",
                        use_container_width=True,
                        key="btn_emitir_ambas"
                    )
                elif hay_ida:
                    btn_emitir_global = st.button(
                        f"🚚 Confirmar y Emitir Guía de Despacho de IDA ({len(st.session_state['carro_ida_items'])} partidas | {tot_kg_ida:.2f} kg)",
                        type="primary",
                        use_container_width=True,
                        key="btn_emitir_ida_solo"
                    )
                else:
                    btn_emitir_global = st.button(
                        f"🔄 Confirmar y Emitir Guía de RETORNO ({len(st.session_state['carro_retorno_items'])} partidas | {tot_kg_ret:.2f} kg)",
                        type="primary",
                        use_container_width=True,
                        key="btn_emitir_ret_solo"
                    )

            with col_btn_emision2:
                if st.button("🗑️ Vaciar Todo el Manifiesto", use_container_width=True, key="btn_vaciar_todo"):
                    st.session_state["carro_ida_items"] = []
                    st.session_state["carro_retorno_items"] = []
                    st.rerun()

            if btn_emitir_global:
                try:
                    res_ida_dict = None
                    res_ret_dict = None

                    # Emitir Ida si hay ítems
                    if hay_ida:
                        res_ida_dict = db.registrar_traslado_consolidado(
                            id_local_origen=int(local_traslado_origen_id),
                            id_local_destino=int(local_traslado_destino_id),
                            partidas=st.session_state["carro_ida_items"],
                            referencia=ref_guia_ida.strip() or "Guía de Ida",
                            observaciones=obs_despacho_consolidado.strip() or None,
                        )

                    # Emitir Retorno si hay ítems
                    if hay_ret:
                        res_ret_dict = db.registrar_traslado_consolidado(
                            id_local_origen=int(local_traslado_destino_id),
                            id_local_destino=int(local_traslado_origen_id),
                            partidas=st.session_state["carro_retorno_items"],
                            referencia=ref_guia_ret.strip() or "Guía de Retorno",
                            observaciones=obs_despacho_consolidado.strip() or None,
                        )

                    # Limpiar carritos
                    st.session_state["carro_ida_items"] = []
                    st.session_state["carro_retorno_items"] = []

                    st.session_state["voucher_traslado_consolidado"] = {
                        "ida": res_ida_dict,
                        "retorno": res_ret_dict,
                        "origen": nombre_orig_simple,
                        "destino": nombre_dest_simple,
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al emitir el manifiesto consolidado de despacho: {e}")

    # ==========================================================================
    # MODALIDAD DE TRASLADO INDIVIDUAL DE RESPALDO (MANUAL)
    # ==========================================================================
    with st.expander("➕ Registro de Traslado Individual Manual (1 solo lote)", expanded=False):
        if stock_disp_traslado.empty:
            st.warning("El local de origen seleccionado no cuenta con insumos disponibles para traspasar.")
        else:
            dict_lotes_traslado = {
                int(row["id_lote"]): row["display_label"]
                for _, row in stock_disp_traslado.iterrows()
            }

            lote_preseleccionado = st.session_state.get("lote_traslado_seleccionado")
            if lote_preseleccionado not in dict_lotes_traslado:
                lote_preseleccionado = list(dict_lotes_traslado.keys())[0]

            idx_default_lote = list(dict_lotes_traslado.keys()).index(lote_preseleccionado)

            with st.form("form_traslado_lotes_manual", clear_on_submit=False):
                lote_traslado_sel = st.selectbox(
                    "Lote a transferir hacia la otra sucursal:*",
                    options=list(dict_lotes_traslado.keys()),
                    index=idx_default_lote,
                    format_func=lambda k: dict_lotes_traslado[k],
                )

                fila_traslado_sel = stock_disp_traslado[stock_disp_traslado["id_lote"] == lote_traslado_sel].iloc[0]
                max_traslado = float(fila_traslado_sel["stock_disponible"])
                unidad_traslado = fila_traslado_sel["unidad_medida"]
                costo_unit_lote = float(fila_traslado_sel["costo_unitario"])

                col_sub_t1, col_sub_t2 = st.columns(2)
                with col_sub_t1:
                    cant_traslado = st.number_input(
                        f"Cantidad a trasladar ({unidad_traslado}):*",
                        min_value=0.001,
                        max_value=max_traslado,
                        value=float(max_traslado),
                        step=0.5,
                        format="%.3f",
                    )
                    ref_traslado = st.text_input(
                        "N° de Guía o Referencia de Traslado:*",
                        value=f"GT-{local_traslado_origen_id}{local_traslado_destino_id}-{fila_traslado_sel['codigo_lote_proveedor'][-6:] if len(fila_traslado_sel['codigo_lote_proveedor']) >= 6 else '001'}",
                    )

                with col_sub_t2:
                    valor_transferido_clp = cant_traslado * costo_unit_lote
                    dias_venc = int(fila_traslado_sel['dias_para_vencer'])
                    color_dias = "#e63946" if dias_venc <= 2 else ("#f77f00" if dias_venc <= 5 else "#2a9d8f")

                    st.markdown(
                        f"""
                        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px;">
                            <strong>Detalle del Despacho Individual:</strong><br>
                            • <strong>Insumo:</strong> {fila_traslado_sel['producto']} (Lote: <code>{fila_traslado_sel['codigo_lote_proveedor']}</code>)<br>
                            • <strong>Caducidad FEFO:</strong> {fila_traslado_sel['fecha_vencimiento']} (<strong style="color:{color_dias};">{dias_venc} días restantes</strong>)<br>
                            • <strong>Capital:</strong> <code>${valor_transferido_clp:,.0f} CLP</code><br>
                            • <strong>Stock Disponible:</strong> <code>{max_traslado:.3f} {unidad_traslado}</code>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    obs_traslado = st.text_area(
                        "Condiciones de Transporte:*",
                        value="Cadena de frío verificada con termómetro en hielera sellada.",
                        height=55,
                    )

                btn_traslado_manual = st.form_submit_button("🚚 Ejecutar Traslado Individual", type="primary", use_container_width=True)

            if btn_traslado_manual:
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
                    st.error(f"Error al registrar el traslado manual: {e}")

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
                    iconos_causa = {
                        "Ruptura de cadena de frío en cocina": "❄️ Ruptura de cadena de frío en cocina",
                        "Vencimiento de fecha límite FEFO": "🔴 Vencimiento de fecha límite FEFO",
                        "Deterioro organoléptico en recepción": "⚠️ Deterioro organoléptico en recepción",
                        "Manipulación / Error de porcionado": "🔪 Manipulación / Error de porcionado",
                    }
                    motivo_sel = st.selectbox(
                        "Tipificación Obligatoria de Causa Raíz:*",
                        options=list(db.CAUSAS_RAIZ_MERMA),
                        format_func=lambda k: iconos_causa.get(k, k),
                        help="Protocolo estandarizado de clasificación de pérdidas para auditoría e informes (Etapa 2 [19, 24])."
                    )

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
                    obs_merma = st.text_area(
                        "Justificación sanitaria / Causa Raíz detallada:*",
                        placeholder="Ej. Registro de temperatura superó los 7°C por corte eléctrico de 3 horas...",
                        height=60,
                        help="Obligatorio para mantener el expediente forense de control de pérdidas."
                    )

                st.markdown("---")
                btn_declarar_merma = st.form_submit_button("🗑️ Confirmar y Procesar Baja por Merma", type="primary", use_container_width=True)

            if btn_declarar_merma:
                if not obs_merma.strip():
                    st.warning("⚠️ Debe ingresar una justificación o detalle de causa raíz antes de confirmar el acta.")
                else:
                    try:
                        res_m = db.registrar_merma(
                            id_local=int(local_merma_id),
                            id_lote=int(lote_merma_sel),
                            cantidad=float(cant_merma),
                            motivo=motivo_sel,
                            observaciones=obs_merma.strip(),
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

    # ==============================================================================
    # REPORTE ESTADÍSTICO DE CAUSAS RAÍZ (ETAPA 2 INACAP [19, 24])
    # ==============================================================================
    st.markdown("---")
    st.markdown("#### 📊 Reporte Estadístico de Causas de Merma (Etapa 2 - INACAP [19, 24])")
    st.caption(
        "Distribución analítica y costo de pérdidas por causa raíz tipificada. "
        "Permite priorizar intervenciones operativas (mantención de frío, compras FEFO o capacitación en porcionado)."
    )

    df_est_causas = db.load_estadisticas_mermas_causa(id_local=id_local_activo)

    if not df_est_causas.empty and df_est_causas["costo_total_perdida"].sum() > 0:
        col_graf_m, col_tbl_m = st.columns([1.2, 1.3])

        with col_graf_m:
            with st.container(border=True):
                st.markdown("##### 🍩 Distribución de Costos por Causa ($ CLP)")
                colores_causas = {
                    "Ruptura de cadena de frío en cocina": "#0284c7",   # Azul frío
                    "Vencimiento de fecha límite FEFO": "#ef4444",      # Rojo alerta
                    "Deterioro organoléptico en recepción": "#f59e0b",  # Ámbar advertencia
                    "Manipulación / Error de porcionado": "#8b5cf6",    # Morado operativo
                }
                donut_merma_data = []
                for _, r_c in df_est_causas.iterrows():
                    causa_name = r_c["causa_raiz"]
                    val_costo = float(r_c["costo_total_perdida"])
                    color_item = colores_causas.get(causa_name, "#64748b")
                    donut_merma_data.append({
                        "value": val_costo,
                        "name": causa_name,
                        "itemStyle": {"color": color_item}
                    })

                option_donut_merma = {
                    "tooltip": {
                        "trigger": "item",
                        "formatter": "{b}: <br/><b>${c:,.0f} CLP</b> ({d}%)"
                    },
                    "legend": {
                        "bottom": "0%",
                        "left": "center",
                        "textStyle": {"fontSize": 11, "color": "#475569"}
                    },
                    "series": [
                        {
                            "name": "Causa Raíz",
                            "type": "pie",
                            "radius": ["45%", "70%"],
                            "center": ["50%", "42%"],
                            "avoidLabelOverlap": False,
                            "itemStyle": {
                                "borderRadius": 6,
                                "borderColor": "#ffffff",
                                "borderWidth": 2
                            },
                            "label": {"show": False},
                            "emphasis": {
                                "label": {
                                    "show": True,
                                    "fontSize": 13,
                                    "fontWeight": "bold",
                                    "formatter": "{d}%"
                                }
                            },
                            "data": donut_merma_data
                        }
                    ]
                }
                render_echarts(option_donut_merma, height=270, key="donut_causas_merma")

        with col_tbl_m:
            with st.container(border=True):
                st.markdown("##### 📋 Matriz Cuantitativa de Pérdidas")
                st.dataframe(
                    df_est_causas,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "causa_raiz": "Causa Raíz Tipificada",
                        "total_eventos": st.column_config.NumberColumn("Actas", format="%d"),
                        "total_kg": st.column_config.NumberColumn("Total Kilos", format="%.2f kg"),
                        "costo_total_perdida": st.column_config.NumberColumn("Pérdida Económica", format="$%d CLP"),
                        "pct_costo": st.column_config.ProgressColumn(
                            "% Impacto",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100
                        ),
                    }
                )

                # Exportar para el informe de la Etapa 2
                csv_causas = df_est_causas.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Exportar Resumen Estadístico (CSV para Informe)",
                    data=csv_causas,
                    file_name="reporte_causas_merma_etapa2.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
    else:
        st.info("No hay suficientes registros de merma para generar el reporte estadístico.")

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

    subtab_m_prov, subtab_m_prod, subtab_m_recetas = st.tabs(
        ["🏢 Catálogo de Proveedores", "🥩 Catálogo de Materias Primas", "🍽️ Fichas Técnicas de Recetas"]
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

    # --------------------------------------------------------------------------
    # SUBTAB: FICHAS TÉCNICAS DE RECETAS (ESCANDALLO)
    # --------------------------------------------------------------------------
    with subtab_m_recetas:
        st.markdown("##### 🍽️ Fichas Técnicas y Escandallo de Recetas")
        st.caption(
            "Estandarización de porciones, gramajes e insumos cárnicos/marinos para cada plato del menú de Mamá Qocha. "
            "Garantiza el control de costos culinarios, la trazabilidad higiénica y la consistencia en todos los locales."
        )

        recetas_cat_df = db.load_recetas_catalogo(solo_activas=False)
        recetas_det_df = db.load_recetas(solo_activas=False)

        if recetas_cat_df.empty:
            st.info("No hay recetas registradas en el catálogo maestro.")
        else:
            col_mr1, col_mr2, col_mr3 = st.columns(3)
            col_mr1.metric("Recetas Estandarizadas", f"{len(recetas_cat_df)} platos")
            col_mr2.metric("Categorías de Menú", f"{recetas_cat_df['categoria'].nunique()}")
            col_mr3.metric("Ticket Promedio Carta", f"${recetas_cat_df['precio_venta'].mean():,.0f} CLP")

            st.dataframe(
                recetas_cat_df[[
                    "id_receta", "receta", "categoria", "precio_venta", "tiempo_preparacion_min", "escandallo_ingredientes", "activo"
                ]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id_receta": st.column_config.NumberColumn("ID", width="small"),
                    "receta": "Nombre del Plato",
                    "categoria": "Categoría",
                    "precio_venta": st.column_config.NumberColumn("Precio Venta", format="$%d CLP"),
                    "tiempo_preparacion_min": st.column_config.NumberColumn("Tiempo (min)", width="small"),
                    "escandallo_ingredientes": "Escandallo / Gramaje Estándar por Porción",
                    "activo": st.column_config.CheckboxColumn("Activo", width="small"),
                },
            )

            with st.expander("🔍 Ver Detalle de Gramajes por Plato (Ficha Técnica Desglosada)"):
                st.dataframe(
                    recetas_det_df[[
                        "receta", "categoria", "ingrediente", "cantidad_kg", "unidad_medida", "precio_venta"
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "receta": "Plato",
                        "categoria": "Categoría",
                        "ingrediente": "Materia Prima",
                        "cantidad_kg": st.column_config.NumberColumn("Gramaje Requerido (kg)", format="%.3f kg"),
                        "unidad_medida": "Unidad",
                        "precio_venta": st.column_config.NumberColumn("Precio Venta", format="$%d CLP"),
                    },
                )

