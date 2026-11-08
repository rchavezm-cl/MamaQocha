"""
Script para auditar estructura, dependencias e índices,
limpiar y cargar el nuevo dataset (1500 registros) en:
1. Base de datos LOCAL (PostgreSQL 18 mama_qocha)
2. Base de datos REMOTA (Neon PostgreSQL 18)
y generar métricas de verificación completas.
"""

import os
import sys

# Forzar salida en utf-8 para evitar errores de charmap en Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(override=True)

# URLs de conexión
local_url = "postgresql+psycopg://postgres:alpha.Prime@localhost:5432/mama_qocha"
neon_url = os.getenv("DATABASE_URL_UNPOOLED") or os.getenv("DATABASE_URL")
if neon_url and neon_url.startswith("postgresql://"):
    neon_url = neon_url.replace("postgresql://", "postgresql+psycopg://", 1)

def auditar_esquema(conn, nombre_db: str):
    print(f"\n--- [AUDITORÍA DE {nombre_db}] ---")
    
    # 1. Tablas
    tablas = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)).fetchall()
    print(f"Tablas encontradas ({len(tablas)}): {[t[0] for t in tablas]}")

    # 2. Claves foráneas (Foreign Keys)
    fks = conn.execute(text("""
        SELECT
            tc.table_name, kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name;
    """)).fetchall()
    print(f"Total Foreign Keys: {len(fks)}")
    for fk in fks:
        print(f"  FK: {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")

    # 3. Restricciones Check y Unique
    checks = conn.execute(text("""
        SELECT tc.table_name, tc.constraint_name, tc.constraint_type
        FROM information_schema.table_constraints tc
        WHERE tc.table_schema = 'public' AND tc.constraint_type IN ('CHECK', 'UNIQUE')
        ORDER BY tc.table_name, tc.constraint_name;
    """)).fetchall()
    print(f"Total restricciones CHECK/UNIQUE: {len(checks)}")
    for chk in checks:
        print(f"  {chk[2]}: {chk[0]} ({chk[1]})")

    # 4. Índices
    indices = conn.execute(text("""
        SELECT tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname;
    """)).fetchall()
    print(f"Total índices existentes: {len(indices)}")
    for idx in indices:
        print(f"  IDX: {idx[0]}.{idx[1]} -> {idx[2]}")

    return {
        "tablas": [t[0] for t in tablas],
        "fks": len(fks),
        "checks": len(checks),
        "indices": len(indices)
    }

def ejecutar_sql_file(conn, sql_file_path: str):
    with open(sql_file_path, "r", encoding="utf-8") as f:
        sql = f.read()
    raw = conn.connection.dbapi_connection
    cursor = raw.cursor()
    cursor.execute(sql)
    cursor.close()

def verificar_metricas(conn, nombre_db: str):
    print(f"\n--- [VERIFICACIÓN DE MÉTRICAS EN {nombre_db}] ---")
    
    # Conteos
    counts = conn.execute(text("""
        SELECT 
            (SELECT COUNT(*) FROM locales) AS locales,
            (SELECT COUNT(*) FROM productos) AS productos,
            (SELECT COUNT(*) FROM proveedores) AS proveedores,
            (SELECT COUNT(*) FROM compras) AS compras,
            (SELECT COUNT(*) FROM detalle_compra) AS detalle_compra,
            (SELECT COUNT(*) FROM lotes) AS lotes,
            (SELECT COUNT(*) FROM movimientos WHERE tipo_movimiento = 'traslado') AS traslados,
            (SELECT COUNT(*) FROM movimientos WHERE tipo_movimiento = 'salida_cocina' AND referencia NOT LIKE 'MERMA%') AS salidas_cocina,
            (SELECT COUNT(*) FROM movimientos WHERE referencia LIKE 'MERMA%') AS mermas,
            (SELECT COUNT(*) FROM movimientos) AS total_movimientos,
            (SELECT COUNT(*) FROM stock_lote_local WHERE cantidad > 0) AS registros_stock_activo,
            (SELECT ROUND(SUM(cantidad), 2) FROM stock_lote_local WHERE cantidad > 0) AS total_kg_stock
    """)).mappings().first()
    
    for k, v in counts.items():
        print(f"  {k}: {v}")

    # Lotes críticos semana 9.11 a 14.11
    criticos = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT l.id_lote) AS lotes_criticos_unicos,
            ROUND(SUM(s.cantidad), 2) AS kg_criticos_disponibles,
            MIN(l.fecha_vencimiento) AS min_venc,
            MAX(l.fecha_vencimiento) AS max_venc
        FROM lotes l
        JOIN stock_lote_local s ON s.id_lote = l.id_lote
        WHERE l.fecha_vencimiento BETWEEN DATE '2026-11-09' AND DATE '2026-11-14';
    """)).mappings().first()
    print(f"  Lotes Críticos (09-14 Nov): {criticos['lotes_criticos_unicos']} lotes únicos ({criticos['kg_criticos_disponibles']} kg)")

    # Distribución por local
    por_local = conn.execute(text("""
        SELECT loc.nombre,
               COUNT(DISTINCT c.id_compra) as compras,
               COUNT(DISTINCT l.id_lote) as lotes,
               COUNT(DISTINCT CASE WHEN m.tipo_movimiento = 'traslado' AND m.id_local_origen = loc.id_local THEN m.id_movimiento END) as traslados,
               COUNT(DISTINCT CASE WHEN m.tipo_movimiento = 'salida_cocina' AND m.id_local_origen = loc.id_local THEN m.id_movimiento END) as salidas
        FROM locales loc
        LEFT JOIN compras c ON c.id_local_receptor = loc.id_local
        LEFT JOIN detalle_compra dc ON dc.id_compra = c.id_compra
        LEFT JOIN lotes l ON l.id_detalle_compra = dc.id_detalle_compra
        LEFT JOIN movimientos m ON m.id_local_origen = loc.id_local
        GROUP BY loc.id_local, loc.nombre
        ORDER BY loc.id_local;
    """)).mappings().fetchall()
    print("  Distribución por local:")
    for row in por_local:
        total_ops = row['compras'] + row['traslados'] + row['salidas']
        print(f"    {row['nombre']}: {row['compras']} compras/lotes, {row['traslados']} traslados, {row['salidas']} salidas -> TOTAL: {total_ops}")

    # Semáforo de inventario
    alertas = conn.execute(text("""
        SELECT 
            CASE
                WHEN (l.fecha_vencimiento < CURRENT_DATE) THEN 'Vencido'
                WHEN (l.fecha_vencimiento - CURRENT_DATE <= 7) THEN 'Critico (<= 7 dias)'
                WHEN (l.fecha_vencimiento - CURRENT_DATE <= 30) THEN 'Preventivo (8-30 dias)'
                ELSE 'Optimo (> 30 dias)'
            END AS estado_alerta,
            COUNT(*) AS total_posiciones,
            ROUND(SUM(s.cantidad), 2) AS total_kg
        FROM stock_lote_local s
        JOIN lotes l ON l.id_lote = s.id_lote
        WHERE s.cantidad > 0
        GROUP BY 1
        ORDER BY 2 DESC;
    """)).fetchall()
    print("  Semáforo de inventario:")
    for a in alertas:
        print(f"    [{a[0]}]: {a[1]} posiciones ({a[2]} kg)")

    return counts

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, "dataset_1500.sql")
    schema_path = os.path.join(base_dir, "schema.sql")

    print("==============================================================")
    print("  MAMA QOCHA - APLICACIÓN DE DATASET EN LOCAL Y REMOTO (NEON)")
    print("==============================================================")

    # 1. Base Local
    print("\n>>> PROCESANDO BASE LOCAL (mama_qocha) <<<")
    eng_local = create_engine(local_url)
    with eng_local.begin() as conn:
        # Asegurar esquema e indices en local
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.connection.dbapi_connection.cursor().execute(f.read())
        auditar_esquema(conn, "LOCAL")
        print("\nEjecutando limpieza y carga de dataset_1500.sql en LOCAL...")
        ejecutar_sql_file(conn, sql_path)
        verificar_metricas(conn, "LOCAL")

    # 2. Base Remota (Neon)
    print("\n>>> PROCESANDO BASE REMOTA (NEON) <<<")
    eng_neon = create_engine(neon_url)
    with eng_neon.begin() as conn:
        # Asegurar esquema e indices en Neon
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.connection.dbapi_connection.cursor().execute(f.read())
        auditar_esquema(conn, "REMOTA (NEON)")
        print("\nEjecutando limpieza y carga de dataset_1500.sql en REMOTA...")
        ejecutar_sql_file(conn, sql_path)
        verificar_metricas(conn, "REMOTA (NEON)")

    print("\n==============================================================")
    print("¡PROCESO COMPLETADO EXITOSAMENTE EN AMBAS BASES DE DATOS!")
    print("==============================================================")

if __name__ == "__main__":
    main()
