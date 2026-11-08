import sys
sys.stdout.reconfigure(encoding='utf-8')
import db
import pandas as pd
from sqlalchemy import text

with db.engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT 
            loc.nombre AS local,
            COUNT(s.id_lote) AS lotes_activos,
            ROUND(SUM(s.cantidad), 2) AS total_kg,
            ROUND(SUM(s.cantidad * COALESCE(dc.costo_unitario, 0)), 0) AS valor_inventario_clp,
            ROUND(SUM(s.cantidad) / 65.0, 1) AS dias_cobertura_doh
        FROM stock_lote_local s
        JOIN locales loc ON loc.id_local = s.id_local
        JOIN lotes l ON l.id_lote = s.id_lote
        JOIN detalle_compra dc ON dc.id_detalle_compra = l.id_detalle_compra
        WHERE s.cantidad > 0
        GROUP BY loc.id_local, loc.nombre
        ORDER BY loc.id_local;
    """), conn)
    print("=== MÉTRICAS LEAN DOH (11-12 DÍAS) POR LOCAL ===")
    print(df.to_string(index=False))

    total_valor = df['valor_inventario_clp'].sum()
    total_kg = df['total_kg'].sum()
    doh_cadena = total_kg / 325.0
    print(f"\nTOTAL CONSOLIDADO: {total_kg:.2f} kg | ${total_valor:,.0f} CLP | DOH Cadena: {doh_cadena:.1f} días")

resumen = db.load_resumen_metricas()
print("\n=== HERO FINANCIERO OPTIMIZADO ===")
print(f"Valorización inventario: ${resumen['total_valor']:,.0f} CLP")
print(f"Capital en riesgo: ${resumen['valor_en_riesgo']:,.0f} CLP ({resumen['pct_en_riesgo']:.1f}%)")
print(f"Lotes críticos: {resumen['criticos']} partidas (${resumen['valor_criticos']:,.0f} CLP)")
print(f"Lotes preventivos: {resumen['preventivos']} partidas (${resumen['valor_preventivos']:,.0f} CLP)")
print(f"Lotes óptimos: {resumen['optimos']} partidas (${resumen['valor_optimos']:,.0f} CLP)")

df_causas = db.load_estadisticas_mermas_causa()
print("\n=== MERMAS POR CAUSA RAÍZ (ETAPA 2) ===")
print(df_causas.to_string(index=False))
