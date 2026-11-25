"""
Script de generación e inyección del dataset Opción B (Escenario Defensa 310 platos/día)
para Mamá Qocha:
- Incorpora 5 nuevos platos en `recetas` y `receta_ingredientes` (total 15 platos).
- Limpia tablas transaccionales previas (TRUNCATE CASCADE).
- Preserva locales, productos, proveedores y usuarios.
- 500 compras y 500 lotes (100 por local, primer vencimiento 2026-12-10 equilibrado en los 5 locales).
- 300 traslados entre locales (60 por local de origen, repartidos equitativamente en round-robin).
- 500 salidas de cocina (100 por local en ventana uniforme de 14 días, calibradas a 310 platos/día).
- 0 mermas declaradas (para generar actas de merma in situ en la defensa del 15-16 de diciembre).
- DOH Global <= 13 días (~11.8 d) con variación controlada por sucursal (9.2 d a 14.8 d).
- Genera respaldo SQL en `dataset_310.sql` e inyecta en PostgreSQL.
"""

import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import text
import db


NUEVOS_PLATOS = [
    {
        "nombre": "Merluza Austral a la Mantequilla de Alcaparras",
        "categoria": "Pescados y Plancha",
        "tiempo_preparacion_min": 20,
        "precio_venta": 15900.00,
        "ingredientes": [("Merluza Austral Premium", 0.260)],
    },
    {
        "nombre": "Tiradito Nikkei de Atún y Reineta",
        "categoria": "Ceviches y Fríos",
        "tiempo_preparacion_min": 14,
        "precio_venta": 14500.00,
        "ingredientes": [("Atún", 0.130), ("Reineta", 0.120)],
    },
    {
        "nombre": "Chupe Cremoso de Camarones",
        "categoria": "Guisos y Fondos",
        "tiempo_preparacion_min": 22,
        "precio_venta": 13900.00,
        "ingredientes": [("Camarón", 0.220)],
    },
    {
        "nombre": "Costillar de Cerdo al Rocoto",
        "categoria": "Brasas y Parrillas",
        "tiempo_preparacion_min": 25,
        "precio_venta": 13200.00,
        "ingredientes": [("Pulpa de cerdo", 0.280)],
    },
    {
        "nombre": "Pollo a la Brasa con Anticucho",
        "categoria": "Brasas y Parrillas",
        "tiempo_preparacion_min": 24,
        "precio_venta": 12900.00,
        "ingredientes": [("Trutro de pollo", 0.240), ("Lomo vetado", 0.100)],
    },
]


# Perfil calibrado por local para 310 platos/día globales (68.20 kg/día) y DOH Global ~11.8 días
PERFIL_LOCALES = [
    # (consumo_diario_kg, doh_objetivo_dias)
    (15.40, 9.2),   # Local 1 - Centro (~70 platos/d)
    (13.64, 11.8),  # Local 2 - Norte (~62 platos/d)
    (14.52, 10.5),  # Local 3 - Sur (~66 platos/d)
    (12.10, 14.8),  # Local 4 - Oriente (~55 platos/d)
    (12.54, 13.4),  # Local 5 - Poniente (~57 platos/d)
]


def _sql_str(val: str) -> str:
    return val.replace("'", "''")


def run() -> None:
    print("Iniciando preparación de dataset Opción B (310 platos/día, DOH <= 13d, 0 mermas)...")
    random.seed(2026)

    FECHA_INICIO_VENTANA = date(2026, 11, 11)
    FECHA_FIN_VENTANA = date(2026, 11, 24)
    DIAS_VENTANA = (FECHA_FIN_VENTANA - FECHA_INICIO_VENTANA).days + 1  # 14 días exactos
    PRIMER_VENCIMIENTO = date(2026, 12, 10)

    with db.engine.begin() as conn:
        print("1. Incorporando 5 nuevos platos al catálogo de recetas...")
        productos_rows = conn.execute(
            text("SELECT id_producto, nombre FROM productos WHERE activo = TRUE ORDER BY id_producto")
        ).fetchall()
        prod_by_name = {r[1]: int(r[0]) for r in productos_rows}

        for plato in NUEVOS_PLATOS:
            row_rec = conn.execute(
                text("SELECT id_receta FROM recetas WHERE nombre = :nombre"),
                {"nombre": plato["nombre"]},
            ).fetchone()
            if row_rec is None:
                row_rec = conn.execute(
                    text(
                        """
                        INSERT INTO recetas (nombre, categoria, tiempo_preparacion_min, precio_venta, activo)
                        VALUES (:nombre, :categoria, :tiempo, :precio, TRUE)
                        RETURNING id_receta
                        """
                    ),
                    {
                        "nombre": plato["nombre"],
                        "categoria": plato["categoria"],
                        "tiempo": plato["tiempo_preparacion_min"],
                        "precio": plato["precio_venta"],
                    },
                ).fetchone()
            id_receta = int(row_rec[0])

            for prod_nombre, cant_kg in plato["ingredientes"]:
                id_prod = prod_by_name.get(prod_nombre)
                if id_prod is None:
                    raise ValueError(f"Producto no encontrado en BD: {prod_nombre}")
                conn.execute(
                    text(
                        """
                        INSERT INTO receta_ingredientes (id_receta, id_producto, cantidad_kg)
                        VALUES (:id_receta, :id_producto, :cantidad_kg)
                        ON CONFLICT (id_receta, id_producto)
                        DO UPDATE SET cantidad_kg = EXCLUDED.cantidad_kg
                        """
                    ),
                    {
                        "id_receta": id_receta,
                        "id_producto": id_prod,
                        "cantidad_kg": cant_kg,
                    },
                )

        recetas_activas = conn.execute(
            text("SELECT id_receta, nombre FROM recetas WHERE activo = TRUE ORDER BY id_receta")
        ).fetchall()
        nombres_recetas = [r[1] for r in recetas_activas]
        print(f"   [OK] Catálogo actualizado: {len(nombres_recetas)} recetas activas.")

        print("2. Limpiando datos transaccionales previos...")
        conn.execute(
            text(
                """
                TRUNCATE TABLE
                    detalle_movimiento,
                    movimientos,
                    stock_lote_local,
                    lotes,
                    detalle_compra,
                    compras
                RESTART IDENTITY CASCADE;
                """
            )
        )
        print("   [OK] Tablas transaccionales limpiadas.")

        locales = conn.execute(
            text("SELECT id_local, nombre FROM locales WHERE activo = TRUE ORDER BY id_local")
        ).fetchall()
        proveedores = conn.execute(
            text("SELECT id_proveedor, nombre FROM proveedores WHERE activo = TRUE ORDER BY id_proveedor")
        ).fetchall()
        productos = conn.execute(
            text("SELECT id_producto, nombre FROM productos WHERE activo = TRUE ORDER BY id_producto")
        ).fetchall()
        usuarios = conn.execute(
            text("SELECT id_usuario FROM usuarios WHERE activo = TRUE ORDER BY id_usuario")
        ).fetchall()

        id_usuario_default = int(usuarios[0][0]) if usuarios else None
        locales_ids = [int(l[0]) for l in locales]
        proveedores_ids = [int(p[0]) for p in proveedores]
        productos_info = {int(p[0]): p[1] for p in productos}
        productos_ids = list(productos_info.keys())

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
            "Merluza Austral Premium": 6700.0,
        }

        # -------------------------------------------------------------
        # 3. COMPRAS Y LOTES (100 lotes por local = 500 lotes)
        # -------------------------------------------------------------
        print("3. Generando 500 compras y 500 lotes calibrados para DOH <= 13d...")
        stock_local: Dict[int, Dict[int, float]] = {lid: {} for lid in locales_ids}
        lotes_info: Dict[int, Dict[str, Any]] = {}

        compras_rows: List[Dict[str, Any]] = []
        detalles_rows: List[Dict[str, Any]] = []
        lotes_rows: List[Dict[str, Any]] = []

        id_compra_counter = 1
        id_detalle_counter = 1
        id_lote_counter = 1
        factura_num = 2000

        for idx_loc, id_local in enumerate(locales_ids):
            consumo_diario_obj, doh_obj = PERFIL_LOCALES[idx_loc % len(PERFIL_LOCALES)]
            consumo_total_obj = round(consumo_diario_obj * DIAS_VENTANA, 2)
            stock_final_obj = round(consumo_diario_obj * doh_obj, 2)
            total_compra_local = round(consumo_total_obj + stock_final_obj, 2)

            # Pesos aleatorios suaves para 100 lotes que sumen exactamente total_compra_local
            pesos = [random.uniform(0.75, 1.25) for _ in range(100)]
            suma_pesos = sum(pesos)
            cantidades_lote = [round(total_compra_local * w / suma_pesos, 2) for w in pesos]
            diff = round(total_compra_local - sum(cantidades_lote), 2)
            cantidades_lote[0] = round(cantidades_lote[0] + diff, 2)

            for i in range(100):
                factura_num += 1
                id_prov = proveedores_ids[(i + idx_loc) % len(proveedores_ids)]
                id_prod = productos_ids[(i + idx_loc * 2) % len(productos_ids)]
                nombre_prod = productos_info[id_prod]
                costo_base = costos_ref.get(nombre_prod, 5000.0)
                costo_u = round(costo_base * random.uniform(0.96, 1.04), 2)

                # Compras recibidas entre 2026-11-08 y 2026-11-11 (antes/inicio ventana consumo)
                fecha_compra = date(2026, 11, 8) + timedelta(days=i % 3)
                fecha_recep = fecha_compra + timedelta(days=1 if i % 2 == 0 else 0)
                if fecha_recep > FECHA_INICIO_VENTANA:
                    fecha_recep = FECHA_INICIO_VENTANA

                num_doc = f"FAC-LEAN-{factura_num}"
                compras_rows.append(
                    {
                        "id_compra": id_compra_counter,
                        "id_proveedor": id_prov,
                        "id_local_receptor": id_local,
                        "tipo_documento": "factura",
                        "numero_documento": num_doc,
                        "fecha_compra": fecha_compra,
                        "fecha_recepcion": fecha_recep,
                        "observaciones": f"Abastecimiento Lean calibrado - Local {id_local}",
                    }
                )

                cant_lote = cantidades_lote[i]
                detalles_rows.append(
                    {
                        "id_detalle_compra": id_detalle_counter,
                        "id_compra": id_compra_counter,
                        "id_producto": id_prod,
                        "cantidad_recibida": cant_lote,
                        "costo_unitario": costo_u,
                        "observaciones": f"Ingreso estándar {nombre_prod}",
                    }
                )

                # Distribución equilibrada de vencimientos por local:
                # 0..3   (4 lotes): 2026-12-10 (primer vencimiento, vencidos el 15-16 dic para acta in situ)
                # 4..15  (12 lotes): 2026-12-17 a 2026-12-22 (críticos <= 7 d en defensa)
                # 16..59 (44 lotes): 2026-12-24 a 2027-01-12 (preventivos 8-30 d en defensa)
                # 60..99 (40 lotes): 2027-01-17 a 2027-02-15 (óptimos > 30 d en defensa)
                if i < 4:
                    fecha_venc = PRIMER_VENCIMIENTO
                    es_primer_venc = True
                elif i < 16:
                    fecha_venc = date(2026, 12, 17) + timedelta(days=(i - 4) % 6)
                    es_primer_venc = False
                elif i < 60:
                    fecha_venc = date(2026, 12, 24) + timedelta(days=random.randint(0, 19))
                    es_primer_venc = False
                else:
                    fecha_venc = date(2027, 1, 17) + timedelta(days=random.randint(0, 29))
                    es_primer_venc = False

                temp_recep = round(random.uniform(1.2, 3.6), 1)
                cod_lote = f"LT-{id_local}-{fecha_recep.strftime('%m%d')}-{id_lote_counter:04d}"

                lotes_rows.append(
                    {
                        "id_lote": id_lote_counter,
                        "id_detalle_compra": id_detalle_counter,
                        "codigo_lote_proveedor": cod_lote,
                        "cantidad_inicial": cant_lote,
                        "fecha_vencimiento": fecha_venc,
                        "fecha_recepcion": fecha_recep,
                        "temperatura_recepcion": temp_recep,
                    }
                )

                stock_local[id_local][id_lote_counter] = cant_lote
                lotes_info[id_lote_counter] = {
                    "id_local_original": id_local,
                    "fecha_recep": fecha_recep,
                    "fecha_venc": fecha_venc,
                    "es_primer_venc": es_primer_venc,
                }

                id_compra_counter += 1
                id_detalle_counter += 1
                id_lote_counter += 1

        conn.execute(
            text(
                """
                INSERT INTO compras (id_compra, id_proveedor, id_local_receptor, tipo_documento, numero_documento, fecha_compra, fecha_recepcion, observaciones)
                VALUES (:id_compra, :id_proveedor, :id_local_receptor, :tipo_documento, :numero_documento, :fecha_compra, :fecha_recepcion, :observaciones)
                """
            ),
            compras_rows,
        )
        conn.execute(
            text(
                """
                INSERT INTO detalle_compra (id_detalle_compra, id_compra, id_producto, cantidad_recibida, costo_unitario, observaciones)
                VALUES (:id_detalle_compra, :id_compra, :id_producto, :cantidad_recibida, :costo_unitario, :observaciones)
                """
            ),
            detalles_rows,
        )
        conn.execute(
            text(
                """
                INSERT INTO lotes (id_lote, id_detalle_compra, codigo_lote_proveedor, cantidad_inicial, fecha_vencimiento, fecha_recepcion, temperatura_recepcion)
                VALUES (:id_lote, :id_detalle_compra, :codigo_lote_proveedor, :cantidad_inicial, :fecha_vencimiento, :fecha_recepcion, :temperatura_recepcion)
                """
            ),
            lotes_rows,
        )
        print("   [OK] 500 compras y 500 lotes insertados.")

        # -------------------------------------------------------------
        # 4. TRASLADOS HOMOGÉNEOS (60 por local = 300 traslados)
        # Round-robin exacto hacia los otros 4 locales y cantidad fija net-zero (0.80 kg)
        # -------------------------------------------------------------
        print("4. Generando 300 traslados homogéneos entre locales...")
        movimientos_rows: List[Dict[str, Any]] = []
        detalles_mov_rows: List[Dict[str, Any]] = []
        id_movimiento_counter = 1

        for id_local_orig in locales_ids:
            destinos = [lid for lid in locales_ids if lid != id_local_orig]
            lotes_candidatos = [
                lid for lid, cant in stock_local[id_local_orig].items()
                if cant >= 2.0 and not lotes_info[lid]["es_primer_venc"]
            ]
            for j in range(60):
                id_lote = lotes_candidatos[j % len(lotes_candidatos)]
                if stock_local[id_local_orig][id_lote] < 1.2:
                    disponibles = [
                        lid for lid, cant in stock_local[id_local_orig].items()
                        if cant >= 1.5 and not lotes_info[lid]["es_primer_venc"]
                    ]
                    id_lote = random.choice(disponibles)

                cant_mover = 0.80
                id_local_dest = destinos[j % len(destinos)]
                f_mov = FECHA_INICIO_VENTANA + timedelta(days=j % DIAS_VENTANA)
                f_mov_dt = datetime(f_mov.year, f_mov.month, f_mov.day, 8 + (j % 10), (j * 7) % 60)

                movimientos_rows.append(
                    {
                        "id_movimiento": id_movimiento_counter,
                        "tipo_movimiento": "traslado",
                        "fecha_movimiento": f_mov_dt,
                        "id_local_origen": id_local_orig,
                        "id_local_destino": id_local_dest,
                        "id_usuario": id_usuario_default,
                        "referencia": f"GD-LEAN-{id_movimiento_counter:05d}",
                        "observaciones": f"Rebalanceo FEFO homogéneo hacia Local {id_local_dest}",
                        "estado": "confirmado",
                    }
                )
                detalles_mov_rows.append(
                    {
                        "id_detalle_movimiento": id_movimiento_counter,
                        "id_movimiento": id_movimiento_counter,
                        "id_lote": id_lote,
                        "cantidad": cant_mover,
                        "observaciones": f"Traslado refrigerado {cant_mover} kg",
                    }
                )
                stock_local[id_local_orig][id_lote] = round(stock_local[id_local_orig][id_lote] - cant_mover, 3)
                stock_local[id_local_dest][id_lote] = round(stock_local[id_local_dest].get(id_lote, 0.0) + cant_mover, 3)
                id_movimiento_counter += 1

        print(f"   [OK] {len(movimientos_rows)} traslados generados.")

        # -------------------------------------------------------------
        # 5. SALIDAS DE COCINA HOMOGÉNEAS (100 por local = 500 salidas, 0 MERMAS)
        # Calibradas exactamente al consumo_total_obj de cada local en 14 días
        # -------------------------------------------------------------
        print("5. Generando 500 salidas de cocina (0 mermas)...")
        for idx_loc, id_local in enumerate(locales_ids):
            consumo_diario_obj, _ = PERFIL_LOCALES[idx_loc % len(PERFIL_LOCALES)]
            consumo_total_obj = round(consumo_diario_obj * DIAS_VENTANA, 2)

            # 100 salidas repartidas uniformemente en los 14 días (garantizando día 0 y día 13)
            pesos_sal = [random.uniform(0.75, 1.25) for _ in range(100)]
            suma_ps = sum(pesos_sal)
            cantidades_sal = [round(consumo_total_obj * w / suma_ps, 2) for w in pesos_sal]
            diff_sal = round(consumo_total_obj - sum(cantidades_sal), 2)
            cantidades_sal[0] = round(cantidades_sal[0] + diff_sal, 2)
            # Procesar mayores salidas primero para evitar fragmentación al final
            cantidades_sal.sort(reverse=True)

            for k in range(100):
                cant_sal = cantidades_sal[k]
                if k == 0:
                    f_mov = FECHA_INICIO_VENTANA
                elif k == 99:
                    f_mov = FECHA_FIN_VENTANA
                else:
                    f_mov = FECHA_INICIO_VENTANA + timedelta(days=k % DIAS_VENTANA)

                f_mov_dt = datetime(f_mov.year, f_mov.month, f_mov.day, 12 + (k % 11), (k * 13) % 60)
                turno = "AM" if k % 2 == 0 else "PM"
                receta_ref = nombres_recetas[(k + idx_loc * 3) % len(nombres_recetas)]

                movimientos_rows.append(
                    {
                        "id_movimiento": id_movimiento_counter,
                        "tipo_movimiento": "salida_cocina",
                        "fecha_movimiento": f_mov_dt,
                        "id_local_origen": id_local,
                        "id_local_destino": None,
                        "id_usuario": id_usuario_default,
                        "referencia": f"PRODUCCIÓN {turno}: {receta_ref}"[:100],
                        "observaciones": f"Consumo operativo cocina - {receta_ref}",
                        "estado": "confirmado",
                    }
                )

                # Descontar de uno o más lotes disponibles (preservando los de 1er vencimiento 2026-12-10)
                restante = cant_sal
                lotes_ord = sorted(
                    [
                        lid for lid, cant in stock_local[id_local].items()
                        if cant > 0.05 and not lotes_info[lid]["es_primer_venc"]
                    ],
                    key=lambda lid: stock_local[id_local][lid],
                    reverse=True,
                )
                for lid in lotes_ord:
                    if restante <= 0.001:
                        break
                    disp = stock_local[id_local][lid]
                    tomar = round(min(restante, max(0.0, disp - 0.05)), 3)
                    if tomar <= 0:
                        continue
                    detalles_mov_rows.append(
                        {
                            "id_detalle_movimiento": len(detalles_mov_rows) + 1,
                            "id_movimiento": id_movimiento_counter,
                            "id_lote": lid,
                            "cantidad": tomar,
                            "observaciones": f"Despacho cocina ({tomar} kg)",
                        }
                    )
                    stock_local[id_local][lid] = round(disp - tomar, 3)
                    restante = round(restante - tomar, 3)

                id_movimiento_counter += 1

        conn.execute(
            text(
                """
                INSERT INTO movimientos (id_movimiento, tipo_movimiento, fecha_movimiento, id_local_origen, id_local_destino, id_usuario, referencia, observaciones, estado)
                VALUES (:id_movimiento, :tipo_movimiento, :fecha_movimiento, :id_local_origen, :id_local_destino, :id_usuario, :referencia, :observaciones, :estado)
                """
            ),
            movimientos_rows,
        )
        conn.execute(
            text(
                """
                INSERT INTO detalle_movimiento (id_detalle_movimiento, id_movimiento, id_lote, cantidad, observaciones)
                VALUES (:id_detalle_movimiento, :id_movimiento, :id_lote, :cantidad, :observaciones)
                """
            ),
            detalles_mov_rows,
        )
        print(f"   [OK] {len(movimientos_rows)} movimientos totales insertados (300 traslados + 500 salidas cocina, 0 mermas).")

        # -------------------------------------------------------------
        # 6. CONSOLIDACIÓN DE STOCK
        # -------------------------------------------------------------
        stock_rows = [
            {"id_lote": id_lote, "id_local": id_local, "cantidad": round(cant, 3)}
            for id_local, lotes_dict in stock_local.items()
            for id_lote, cant in lotes_dict.items()
            if round(cant, 3) > 0
        ]
        conn.execute(
            text(
                """
                INSERT INTO stock_lote_local (id_lote, id_local, cantidad, actualizado_en)
                VALUES (:id_lote, :id_local, :cantidad, CURRENT_TIMESTAMP)
                """
            ),
            stock_rows,
        )

        for t, col in [
            ("recetas", "id_receta"),
            ("receta_ingredientes", "id_receta_ingrediente"),
            ("compras", "id_compra"),
            ("detalle_compra", "id_detalle_compra"),
            ("lotes", "id_lote"),
            ("movimientos", "id_movimiento"),
            ("detalle_movimiento", "id_detalle_movimiento"),
            ("stock_lote_local", "id_stock"),
        ]:
            conn.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{t}', '{col}'), COALESCE((SELECT MAX({col}) FROM {t}), 1));"
                )
            )
        print(f"   [OK] {len(stock_rows)} registros en stock_lote_local.")

    print("7. Exportando respaldo a dataset_310.sql...")
    with open("dataset_310.sql", "w", encoding="utf-8") as f:
        f.write("-- Mamá Qocha: Dataset Opción B (310 platos/día, DOH <= 13d, 1er vencimiento 2026-12-10, 0 mermas)\n")
        f.write("BEGIN;\n\n")
        f.write("TRUNCATE TABLE detalle_movimiento, movimientos, stock_lote_local, lotes, detalle_compra, compras RESTART IDENTITY CASCADE;\n\n")
        for r in compras_rows:
            f.write(
                f"INSERT INTO compras (id_compra, id_proveedor, id_local_receptor, tipo_documento, numero_documento, fecha_compra, fecha_recepcion, observaciones) "
                f"VALUES ({r['id_compra']}, {r['id_proveedor']}, {r['id_local_receptor']}, '{_sql_str(r['tipo_documento'])}', '{_sql_str(r['numero_documento'])}', '{r['fecha_compra']}', '{r['fecha_recepcion']}', '{_sql_str(r['observaciones'])}');\n"
            )
        for r in detalles_rows:
            f.write(
                f"INSERT INTO detalle_compra (id_detalle_compra, id_compra, id_producto, cantidad_recibida, costo_unitario, observaciones) "
                f"VALUES ({r['id_detalle_compra']}, {r['id_compra']}, {r['id_producto']}, {r['cantidad_recibida']}, {r['costo_unitario']}, '{_sql_str(r['observaciones'])}');\n"
            )
        for r in lotes_rows:
            f.write(
                f"INSERT INTO lotes (id_lote, id_detalle_compra, codigo_lote_proveedor, cantidad_inicial, fecha_vencimiento, fecha_recepcion, temperatura_recepcion) "
                f"VALUES ({r['id_lote']}, {r['id_detalle_compra']}, '{_sql_str(r['codigo_lote_proveedor'])}', {r['cantidad_inicial']}, '{r['fecha_vencimiento']}', '{r['fecha_recepcion']}', {r['temperatura_recepcion']});\n"
            )
        for r in movimientos_rows:
            dest = r["id_local_destino"] if r["id_local_destino"] is not None else "NULL"
            usr = r["id_usuario"] if r["id_usuario"] is not None else "NULL"
            f.write(
                f"INSERT INTO movimientos (id_movimiento, tipo_movimiento, fecha_movimiento, id_local_origen, id_local_destino, id_usuario, referencia, observaciones, estado) "
                f"VALUES ({r['id_movimiento']}, '{r['tipo_movimiento']}', '{r['fecha_movimiento'].isoformat()}', {r['id_local_origen']}, {dest}, {usr}, '{_sql_str(r['referencia'])}', '{_sql_str(r['observaciones'])}', '{r['estado']}');\n"
            )
        for r in detalles_mov_rows:
            f.write(
                f"INSERT INTO detalle_movimiento (id_detalle_movimiento, id_movimiento, id_lote, cantidad, observaciones) "
                f"VALUES ({r['id_detalle_movimiento']}, {r['id_movimiento']}, {r['id_lote']}, {r['cantidad']}, '{_sql_str(r['observaciones'])}');\n"
            )
        for r in stock_rows:
            f.write(
                f"INSERT INTO stock_lote_local (id_lote, id_local, cantidad, actualizado_en) "
                f"VALUES ({r['id_lote']}, {r['id_local']}, {r['cantidad']}, CURRENT_TIMESTAMP);\n"
            )
        f.write("\nCOMMIT;\n")

    print("[OK] Dataset Opción B aplicado y respaldado en dataset_310.sql.")


if __name__ == "__main__":
    run()
