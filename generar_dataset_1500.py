"""
Script de generacion e inyeccion de dataset transaccional (~1500 registros)
para Mama Qocha.
- Limpia tablas operativas previas (TRUNCATE CASCADE).
- Preserva datos maestros (locales, productos, proveedores, usuarios, recetas).
- 500 lotes (100 por local, con 5% = 25 lotes con vencimiento 09.11 a 14.11.2026).
- 350 traslados entre locales.
- 650 salidas de cocina y mermas.
- Genera archivo SQL de respaldo y aplica en base de datos.
"""

import os
import random
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import text
import db

def run():
    print("Iniciando preparacion de dataset...")
    random.seed(42)

    # Fecha base del sistema: 8 de noviembre de 2026
    FECHA_BASE = date(2026, 11, 8)

    with db.engine.begin() as conn:
        print("1. Limpiando datos transaccionales previos...")
        conn.execute(text("""
            TRUNCATE TABLE 
                detalle_movimiento, 
                movimientos, 
                stock_lote_local, 
                lotes, 
                detalle_compra, 
                compras 
            RESTART IDENTITY CASCADE;
        """))
        print("   [OK] Tablas transaccionales limpiadas con éxito.")

        # Obtener entidades maestras
        locales = conn.execute(text("SELECT id_local, nombre FROM locales WHERE activo = TRUE ORDER BY id_local")).fetchall()
        proveedores = conn.execute(text("SELECT id_proveedor, nombre, rut FROM proveedores WHERE activo = TRUE ORDER BY id_proveedor")).fetchall()
        productos = conn.execute(text("SELECT id_producto, nombre, unidad_medida FROM productos WHERE activo = TRUE ORDER BY id_producto")).fetchall()
        usuarios = conn.execute(text("SELECT id_usuario FROM usuarios WHERE activo = TRUE")).fetchall()

        id_usuario_default = usuarios[0][0] if usuarios else None

        locales_ids = [l[0] for l in locales]
        proveedores_ids = [p[0] for p in proveedores]
        productos_info = {p[0]: {"nombre": p[1], "unidad": p[2]} for p in productos}
        productos_ids = list(productos_info.keys())

        print(f"   Locales: {len(locales_ids)}, Proveedores: {len(proveedores_ids)}, Productos: {len(productos_ids)}")

        # Costos de referencia por producto
        costos_ref = {
            "Lomo vetado": 9200.0,
            "Sobrecostilla": 7800.0,
            "Posta rosada": 7400.0,
            "Pulpa de cerdo": 6200.0,
            "Pechuga de pollo": 4300.0,
            "Trutro de pollo": 3950.0,
            "Atún": 5400.0,
            "Camarón": 8200.0,
            "Reineta": 5100.0,
            "Merluza Austral Premium": 6700.0
        }

        # -------------------------------------------------------------
        # 2. GENERACIÓN DE COMPRAS Y LOTES (500 lotes en total)
        # 100 lotes por local receptor.
        # Por cada local: 5 lotes vencen entre 09.11 y 14.11 (Total = 25 lotes = 5%).
        # El resto (95 lotes por local = 475 lotes) vencen entre 15.11 y 23.12 (hasta 45 días).
        # -------------------------------------------------------------
        print("2. Generando 500 compras y lotes...")
        
        # Estructura en memoria para seguimiento de stock:
        # stock_local[id_local][id_lote] = cantidad
        stock_local: Dict[int, Dict[int, float]] = {l_id: {} for l_id in locales_ids}
        lotes_info: Dict[int, Dict[str, Any]] = {}

        id_compra_counter = 1
        id_detalle_counter = 1
        id_lote_counter = 1

        # Fechas de vencimiento crítico: semana del 9 al 14 de noviembre de 2026
        dias_criticos = [
            date(2026, 11, 9),
            date(2026, 11, 10),
            date(2026, 11, 11),
            date(2026, 11, 12),
            date(2026, 11, 13),
            date(2026, 11, 14)
        ]

        compras_rows = []
        detalles_rows = []
        lotes_rows = []

        factura_num = 1000

        for id_local in locales_ids:
            # 100 lotes para este local
            # Determinamos cuáles 5 serán críticos
            indices_criticos = set(range(5)) # primeros 5 del local

            for i in range(100):
                factura_num += 1
                id_prov = random.choice(proveedores_ids)
                id_prod = random.choice(productos_ids)
                nombre_prod = productos_info[id_prod]["nombre"]
                costo_base = costos_ref.get(nombre_prod, 5000.0)
                costo_u = round(costo_base * random.uniform(0.95, 1.05), 2)

                # Fecha de compra y recepción
                dias_atras = random.randint(3, 14)
                fecha_compra = FECHA_BASE - timedelta(days=dias_atras)
                fecha_recep = fecha_compra + timedelta(days=random.choice([0, 1]))

                num_doc = f"FAC-2026-{factura_num}"

                # Inserción compra
                compras_rows.append({
                    "id_compra": id_compra_counter,
                    "id_proveedor": id_prov,
                    "id_local_receptor": id_local,
                    "tipo_documento": "factura",
                    "numero_documento": num_doc,
                    "fecha_compra": fecha_compra,
                    "fecha_recepcion": fecha_recep,
                    "observaciones": f"Recepción programada de abastecimiento - Local {id_local}"
                })

                # Cantidad de compra calibrada para DOH de 12 días (reposición semanal: 7.0 a 13.5 kg por lote)
                cantidad_lote = round(random.uniform(7.0, 13.5), 2)

                detalles_rows.append({
                    "id_detalle_compra": id_detalle_counter,
                    "id_compra": id_compra_counter,
                    "id_producto": id_prod,
                    "cantidad_recibida": cantidad_lote,
                    "costo_unitario": costo_u,
                    "observaciones": f"Entrada estándar {nombre_prod}"
                })

                # Fecha de vencimiento
                if i in indices_criticos:
                    # Crítico: 9.11 al 14.11
                    fecha_venc = dias_criticos[i % len(dias_criticos)]
                else:
                    # Entre 7 y 45 días a partir del 8.11 (es decir, entre 15.11 y 23.12)
                    dias_futuros = random.randint(7, 45)
                    fecha_venc = FECHA_BASE + timedelta(days=dias_futuros)

                temp_recep = round(random.uniform(1.2, 3.8), 1)
                cod_lote = f"LT-{id_local}-{fecha_recep.strftime('%m%d')}-{id_lote_counter:04d}"

                lotes_rows.append({
                    "id_lote": id_lote_counter,
                    "id_detalle_compra": id_detalle_counter,
                    "codigo_lote_proveedor": cod_lote,
                    "cantidad_inicial": cantidad_lote,
                    "fecha_vencimiento": fecha_venc,
                    "fecha_recepcion": fecha_recep,
                    "temperatura_recepcion": temp_recep
                })

                # Registrar en stock en memoria
                stock_local[id_local][id_lote_counter] = cantidad_lote
                lotes_info[id_lote_counter] = {
                    "id_local_original": id_local,
                    "fecha_recep": fecha_recep,
                    "fecha_venc": fecha_venc,
                    "es_critico": (i in indices_criticos)
                }

                id_detalle_counter += 1
                id_compra_counter += 1
                id_lote_counter += 1

        # Insertar compras
        conn.execute(
            text("""
                INSERT INTO compras (id_compra, id_proveedor, id_local_receptor, tipo_documento, numero_documento, fecha_compra, fecha_recepcion, observaciones)
                VALUES (:id_compra, :id_proveedor, :id_local_receptor, :tipo_documento, :numero_documento, :fecha_compra, :fecha_recepcion, :observaciones)
            """),
            compras_rows
        )

        # Insertar detalle_compra
        conn.execute(
            text("""
                INSERT INTO detalle_compra (id_detalle_compra, id_compra, id_producto, cantidad_recibida, costo_unitario, observaciones)
                VALUES (:id_detalle_compra, :id_compra, :id_producto, :cantidad_recibida, :costo_unitario, :observaciones)
            """),
            detalles_rows
        )

        # Insertar lotes
        conn.execute(
            text("""
                INSERT INTO lotes (id_lote, id_detalle_compra, codigo_lote_proveedor, cantidad_inicial, fecha_vencimiento, fecha_recepcion, temperatura_recepcion)
                VALUES (:id_lote, :id_detalle_compra, :codigo_lote_proveedor, :cantidad_inicial, :fecha_vencimiento, :fecha_recepcion, :temperatura_recepcion)
            """),
            lotes_rows
        )

        print(f"   [OK] 500 compras y 500 lotes insertados.")

        # -------------------------------------------------------------
        # 3. GENERACIÓN DE MOVIMIENTOS: TRASLADOS ENTRE LOCALES (350 operaciones)
        # 70 traslados por local de origen
        # -------------------------------------------------------------
        print("3. Generando 350 traslados entre locales...")
        movimientos_rows = []
        detalles_mov_rows = []
        id_movimiento_counter = 1

        for id_local_orig in locales_ids:
            destinos_posibles = [lid for lid in locales_ids if lid != id_local_orig]
            # Seleccionar lotes con stock en este local
            lotes_disponibles = [lid for lid, cant in stock_local[id_local_orig].items() if cant > 3.0]

            for _ in range(70):
                if not lotes_disponibles:
                    break
                id_lote = random.choice(lotes_disponibles)
                cant_disp = stock_local[id_local_orig][id_lote]

                # Dejar margen seguro para no agotar el lote (especialmente si es crítico)
                max_mover = min(2.5, cant_disp * 0.3)
                if max_mover < 0.3:
                    continue
                cant_mover = round(random.uniform(0.3, max_mover), 2)

                id_local_dest = random.choice(destinos_posibles)
                f_recep = lotes_info[id_lote]["fecha_recep"]
                # Fecha movimiento entre f_recep y FECHA_BASE
                dias_delta = (FECHA_BASE - f_recep).days
                f_mov = f_recep + timedelta(days=random.randint(1, max(1, dias_delta)))
                f_mov_dt = datetime(f_mov.year, f_mov.month, f_mov.day, random.randint(8, 18), random.randint(0, 59))

                guia_num = f"GD-2026-{id_movimiento_counter:05d}"
                movimientos_rows.append({
                    "id_movimiento": id_movimiento_counter,
                    "tipo_movimiento": "traslado",
                    "fecha_movimiento": f_mov_dt,
                    "id_local_origen": id_local_orig,
                    "id_local_destino": id_local_dest,
                    "id_usuario": id_usuario_default,
                    "referencia": guia_num,
                    "observaciones": f"Rebalanceo de stock inter-local hacia Local {id_local_dest}",
                    "estado": "confirmado"
                })

                detalles_mov_rows.append({
                    "id_detalle_movimiento": id_movimiento_counter,
                    "id_movimiento": id_movimiento_counter,
                    "id_lote": id_lote,
                    "cantidad": cant_mover,
                    "observaciones": f"Traslado frigorífico {cant_mover} kg"
                })

                # Actualizar stock en memoria
                stock_local[id_local_orig][id_lote] -= cant_mover
                stock_local[id_local_dest][id_lote] = stock_local[id_local_dest].get(id_lote, 0.0) + cant_mover

                if stock_local[id_local_orig][id_lote] <= 3.0:
                    lotes_disponibles.remove(id_lote)

                id_movimiento_counter += 1

        print(f"   [OK] {len(movimientos_rows)} traslados generados.")

        # -------------------------------------------------------------
        # 4. GENERACIÓN DE SALIDAS (650 operaciones: 550 cocina + 100 mermas)
        # 130 salidas por local (110 de cocina + 20 de mermas)
        # -------------------------------------------------------------
        print("4. Generando 650 salidas operativas (550 cocina + 100 mermas)...")

        for id_local in locales_ids:
            # 110 salidas a cocina
            for _ in range(110):
                # Elegir lotes con stock disponible
                lotes_con_stock = [lid for lid, cant in stock_local[id_local].items() if cant > 1.0]
                if not lotes_con_stock:
                    continue
                id_lote = random.choice(lotes_con_stock)
                cant_disp = stock_local[id_local][id_lote]
                
                # Para lotes críticos, aseguramos que siempre quede stock positivo (>= 0.6 kg)
                min_remanente = 0.8 if lotes_info[id_lote]["es_critico"] else 0.3
                max_salida = max(0.2, cant_disp - min_remanente)
                cant_salida = round(random.uniform(0.6, min(4.0, max_salida)), 2)
                if cant_salida <= 0:
                    continue

                f_recep = lotes_info[id_lote]["fecha_recep"]
                dias_delta = (FECHA_BASE - f_recep).days
                f_mov = f_recep + timedelta(days=random.randint(1, max(1, dias_delta)))
                f_mov_dt = datetime(f_mov.year, f_mov.month, f_mov.day, random.randint(11, 23), random.randint(0, 59))

                turno = random.choice(["Turno AM - Apertura", "Turno PM - Cierre"])
                ref = f"Comanda Cocina - {turno}"

                movimientos_rows.append({
                    "id_movimiento": id_movimiento_counter,
                    "tipo_movimiento": "salida_cocina",
                    "fecha_movimiento": f_mov_dt,
                    "id_local_origen": id_local,
                    "id_local_destino": None,
                    "id_usuario": id_usuario_default,
                    "referencia": ref,
                    "observaciones": "Consumo para preparaciones del menú",
                    "estado": "confirmado"
                })

                detalles_mov_rows.append({
                    "id_detalle_movimiento": id_movimiento_counter,
                    "id_movimiento": id_movimiento_counter,
                    "id_lote": id_lote,
                    "cantidad": cant_salida,
                    "observaciones": f"Preparación de cocina ({cant_salida} kg)"
                })

                stock_local[id_local][id_lote] -= cant_salida
                id_movimiento_counter += 1

            # 20 mermas declaradas con tipificación obligatoria de causa raíz
            motivos_merma = [
                "MERMA: Ruptura de cadena de frío en cocina",
                "MERMA: Vencimiento de fecha límite FEFO",
                "MERMA: Deterioro organoléptico en recepción",
                "MERMA: Manipulación / Error de porcionado"
            ]
            pesos_merma = [0.35, 0.30, 0.15, 0.20]
            for _ in range(20):
                lotes_con_stock = [lid for lid, cant in stock_local[id_local].items() if cant > 0.8]
                if not lotes_con_stock:
                    continue
                id_lote = random.choice(lotes_con_stock)
                cant_disp = stock_local[id_local][id_lote]

                min_remanente = 0.8 if lotes_info[id_lote]["es_critico"] else 0.2
                max_merma = max(0.2, cant_disp - min_remanente)
                cant_merma = round(random.uniform(0.2, min(0.9, max_merma)), 2)
                if cant_merma <= 0:
                    continue

                f_recep = lotes_info[id_lote]["fecha_recep"]
                dias_delta = (FECHA_BASE - f_recep).days
                f_mov = f_recep + timedelta(days=random.randint(1, max(1, dias_delta)))
                f_mov_dt = datetime(f_mov.year, f_mov.month, f_mov.day, random.randint(9, 19), random.randint(0, 59))

                motivo = random.choices(motivos_merma, weights=pesos_merma, k=1)[0]
                obs_por_motivo = {
                    "MERMA: Ruptura de cadena de frío en cocina": "Alerta de temperatura > 5.5°C en cámara/mesón durante servicio.",
                    "MERMA: Vencimiento de fecha límite FEFO": "Cumplimiento estricto de fecha límite FEFO; lote retirado preventivamente.",
                    "MERMA: Deterioro organoléptico en recepción": "Textura/olor no conforme con estándar en control de recepción.",
                    "MERMA: Manipulación / Error de porcionado": "Error en proceso de fileteado/porcionamiento en línea de cocina."
                }
                obs_merma_txt = obs_por_motivo.get(motivo, "Baja formal de inventario auditada")

                movimientos_rows.append({
                    "id_movimiento": id_movimiento_counter,
                    "tipo_movimiento": "salida_cocina",
                    "fecha_movimiento": f_mov_dt,
                    "id_local_origen": id_local,
                    "id_local_destino": None,
                    "id_usuario": id_usuario_default,
                    "referencia": motivo,
                    "observaciones": obs_merma_txt,
                    "estado": "confirmado"
                })

                detalles_mov_rows.append({
                    "id_detalle_movimiento": id_movimiento_counter,
                    "id_movimiento": id_movimiento_counter,
                    "id_lote": id_lote,
                    "cantidad": cant_merma,
                    "observaciones": f"Baja por merma ({cant_merma} kg)"
                })

                stock_local[id_local][id_lote] -= cant_merma
                id_movimiento_counter += 1

        print(f"   [OK] Total movimientos a insertar: {len(movimientos_rows)}.")

        # Insertar movimientos
        conn.execute(
            text("""
                INSERT INTO movimientos (id_movimiento, tipo_movimiento, fecha_movimiento, id_local_origen, id_local_destino, id_usuario, referencia, observaciones, estado)
                VALUES (:id_movimiento, :tipo_movimiento, :fecha_movimiento, :id_local_origen, :id_local_destino, :id_usuario, :referencia, :observaciones, :estado)
            """),
            movimientos_rows
        )

        # Insertar detalle_movimiento
        conn.execute(
            text("""
                INSERT INTO detalle_movimiento (id_detalle_movimiento, id_movimiento, id_lote, cantidad, observaciones)
                VALUES (:id_detalle_movimiento, :id_movimiento, :id_lote, :cantidad, :observaciones)
            """),
            detalles_mov_rows
        )

        # -------------------------------------------------------------
        # 5. CONSOLIDACIÓN DE STOCK (stock_lote_local)
        # -------------------------------------------------------------
        print("5. Consolidando existencias en stock_lote_local...")
        stock_rows = []
        for id_local, lotes_dict in stock_local.items():
            for id_lote, cant in lotes_dict.items():
                cant_final = round(cant, 3)
                if cant_final > 0:
                    stock_rows.append({
                        "id_lote": id_lote,
                        "id_local": id_local,
                        "cantidad": cant_final
                    })

        conn.execute(
            text("""
                INSERT INTO stock_lote_local (id_lote, id_local, cantidad, actualizado_en)
                VALUES (:id_lote, :id_local, :cantidad, CURRENT_TIMESTAMP)
            """),
            stock_rows
        )
        print(f"   [OK] {len(stock_rows)} registros de stock consolidado insertados.")

        # Actualizar secuencias de Postgres usando pg_get_serial_sequence
        for t, col in [
            ('compras', 'id_compra'),
            ('detalle_compra', 'id_detalle_compra'),
            ('lotes', 'id_lote'),
            ('movimientos', 'id_movimiento'),
            ('detalle_movimiento', 'id_detalle_movimiento'),
            ('stock_lote_local', 'id_stock')
        ]:
            conn.execute(text(f"""
                SELECT setval(pg_get_serial_sequence('{t}', '{col}'), COALESCE((SELECT MAX({col}) FROM {t}), 1));
            """))

    print("\nExportando respaldo a dataset_1500.sql...")
    with open("dataset_1500.sql", "w", encoding="utf-8") as f:
        f.write("-- Mamá Qocha: Dataset 1500 registros transaccionales\n")
        f.write("BEGIN;\n\n")
        f.write("TRUNCATE TABLE detalle_movimiento, movimientos, stock_lote_local, lotes, detalle_compra, compras RESTART IDENTITY CASCADE;\n\n")
        
        f.write("-- 1. Compras\n")
        for r in compras_rows:
            f.write(f"INSERT INTO compras (id_compra, id_proveedor, id_local_receptor, tipo_documento, numero_documento, fecha_compra, fecha_recepcion, observaciones) VALUES ({r['id_compra']}, {r['id_proveedor']}, {r['id_local_receptor']}, '{r['tipo_documento']}', '{r['numero_documento']}', '{r['fecha_compra']}', '{r['fecha_recepcion']}', '{r['observaciones']}');\n")
        
        f.write("\n-- 2. Detalles de compra\n")
        for r in detalles_rows:
            f.write(f"INSERT INTO detalle_compra (id_detalle_compra, id_compra, id_producto, cantidad_recibida, costo_unitario, observaciones) VALUES ({r['id_detalle_compra']}, {r['id_compra']}, {r['id_producto']}, {r['cantidad_recibida']}, {r['costo_unitario']}, '{r['observaciones']}');\n")

        f.write("\n-- 3. Lotes\n")
        for r in lotes_rows:
            f.write(f"INSERT INTO lotes (id_lote, id_detalle_compra, codigo_lote_proveedor, cantidad_inicial, fecha_vencimiento, fecha_recepcion, temperatura_recepcion) VALUES ({r['id_lote']}, {r['id_detalle_compra']}, '{r['codigo_lote_proveedor']}', {r['cantidad_inicial']}, '{r['fecha_vencimiento']}', '{r['fecha_recepcion']}', {r['temperatura_recepcion']});\n")

        f.write("\n-- 4. Movimientos\n")
        for r in movimientos_rows:
            dest = r['id_local_destino'] if r['id_local_destino'] is not None else "NULL"
            usr = r['id_usuario'] if r['id_usuario'] is not None else "NULL"
            f.write(f"INSERT INTO movimientos (id_movimiento, tipo_movimiento, fecha_movimiento, id_local_origen, id_local_destino, id_usuario, referencia, observaciones, estado) VALUES ({r['id_movimiento']}, '{r['tipo_movimiento']}', '{r['fecha_movimiento'].isoformat()}', {r['id_local_origen']}, {dest}, {usr}, '{r['referencia']}', '{r['observaciones']}', '{r['estado']}');\n")

        f.write("\n-- 5. Detalles de movimiento\n")
        for r in detalles_mov_rows:
            f.write(f"INSERT INTO detalle_movimiento (id_detalle_movimiento, id_movimiento, id_lote, cantidad, observaciones) VALUES ({r['id_detalle_movimiento']}, {r['id_movimiento']}, {r['id_lote']}, {r['cantidad']}, '{r['observaciones']}');\n")

        f.write("\n-- 6. Stock consolidado\n")
        for r in stock_rows:
            f.write(f"INSERT INTO stock_lote_local (id_lote, id_local, cantidad, actualizado_en) VALUES ({r['id_lote']}, {r['id_local']}, {r['cantidad']}, CURRENT_TIMESTAMP);\n")

        f.write("\nCOMMIT;\n")

    print("[OK] Respaldo dataset_1500.sql generado con éxito.")
    print("\nDataset inyectado exitosamente en la base de datos.")

if __name__ == "__main__":
    run()
