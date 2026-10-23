import os
from datetime import date
from typing import Any, Dict, Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Cargar las variables desde el archivo .env
load_dotenv(override=True)

# Soporte para DATABASE_URL directa (Nube: Neon, Supabase, Render) o variables individuales (.env local)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
            DATABASE_URL = st.secrets["DATABASE_URL"]
    except Exception:
        pass

if not DATABASE_URL:
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")
    pg_database = os.getenv("PG_DATABASE", "mama_qocha")
    pg_user = os.getenv("PG_USER", "postgres")
    pg_password = os.getenv("PG_PASSWORD", "")
    DATABASE_URL = f"postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+psycopg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Crear el motor de SQLAlchemy con soporte para reconexión automática en Postgres serverless
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)


def load_locales() -> pd.DataFrame:
    """Carga la lista de todos los locales ordenados por id."""
    query = text(
        """
        SELECT id_local, nombre, direccion, activo
        FROM locales
        ORDER BY id_local
        """
    )
    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def load_proveedores(solo_activos: bool = False) -> pd.DataFrame:
    """Carga los proveedores registrados con opción de filtrar solo activos."""
    filtro = "WHERE activo = TRUE" if solo_activos else ""
    query = text(
        f"""
        SELECT id_proveedor, nombre, rut, telefono, correo, direccion, activo, creado_en
        FROM proveedores
        {filtro}
        ORDER BY nombre
        """
    )
    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def crear_proveedor(
    nombre: str,
    rut: Optional[str] = None,
    telefono: Optional[str] = None,
    correo: Optional[str] = None,
    direccion: Optional[str] = None,
    activo: bool = True,
) -> int:
    """Crea un nuevo proveedor en la base de datos."""
    if not nombre.strip():
        raise ValueError("El nombre del proveedor es obligatorio.")
    query = text(
        """
        INSERT INTO proveedores (nombre, rut, telefono, correo, direccion, activo)
        VALUES (:nombre, :rut, :telefono, :correo, :direccion, :activo)
        RETURNING id_proveedor;
        """
    )
    with engine.begin() as conn:
        return conn.execute(
            query,
            {
                "nombre": nombre.strip(),
                "rut": rut.strip() if rut and rut.strip() else None,
                "telefono": telefono.strip() if telefono and telefono.strip() else None,
                "correo": correo.strip() if correo and correo.strip() else None,
                "direccion": direccion.strip() if direccion and direccion.strip() else None,
                "activo": activo,
            },
        ).scalar_one()


def actualizar_proveedor(
    id_proveedor: int,
    nombre: str,
    rut: Optional[str] = None,
    telefono: Optional[str] = None,
    correo: Optional[str] = None,
    direccion: Optional[str] = None,
    activo: bool = True,
) -> bool:
    """Actualiza la información de un proveedor existente."""
    if not nombre.strip():
        raise ValueError("El nombre del proveedor es obligatorio.")
    query = text(
        """
        UPDATE proveedores
        SET nombre = :nombre,
            rut = :rut,
            telefono = :telefono,
            correo = :correo,
            direccion = :direccion,
            activo = :activo
        WHERE id_proveedor = :id_proveedor;
        """
    )
    with engine.begin() as conn:
        result = conn.execute(
            query,
            {
                "id_proveedor": id_proveedor,
                "nombre": nombre.strip(),
                "rut": rut.strip() if rut and rut.strip() else None,
                "telefono": telefono.strip() if telefono and telefono.strip() else None,
                "correo": correo.strip() if correo and correo.strip() else None,
                "direccion": direccion.strip() if direccion and direccion.strip() else None,
                "activo": activo,
            },
        )
        return result.rowcount > 0


def load_productos(solo_activos: bool = False) -> pd.DataFrame:
    """Carga los productos o materias primas con opción de filtrar solo activos."""
    filtro = "WHERE activo = TRUE" if solo_activos else ""
    query = text(
        f"""
        SELECT id_producto, nombre, unidad_medida, descripcion, activo, creado_en
        FROM productos
        {filtro}
        ORDER BY nombre
        """
    )
    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def crear_producto(
    nombre: str,
    unidad_medida: str = "kg",
    descripcion: Optional[str] = None,
    activo: bool = True,
) -> int:
    """Crea un nuevo producto en el catálogo maestro."""
    if not nombre.strip():
        raise ValueError("El nombre del producto es obligatorio.")
    if unidad_medida not in ("kg", "g", "l", "ml", "unidad"):
        raise ValueError("Unidad de medida no permitida. Debe ser kg, g, l, ml o unidad.")
    query = text(
        """
        INSERT INTO productos (nombre, descripcion, unidad_medida, activo)
        VALUES (:nombre, :descripcion, :unidad_medida, :activo)
        RETURNING id_producto;
        """
    )
    with engine.begin() as conn:
        return conn.execute(
            query,
            {
                "nombre": nombre.strip(),
                "descripcion": descripcion.strip() if descripcion and descripcion.strip() else None,
                "unidad_medida": unidad_medida,
                "activo": activo,
            },
        ).scalar_one()


def actualizar_producto(
    id_producto: int,
    nombre: str,
    unidad_medida: str = "kg",
    descripcion: Optional[str] = None,
    activo: bool = True,
) -> bool:
    """Actualiza la información de un producto existente."""
    if not nombre.strip():
        raise ValueError("El nombre del producto es obligatorio.")
    if unidad_medida not in ("kg", "g", "l", "ml", "unidad"):
        raise ValueError("Unidad de medida no permitida. Debe ser kg, g, l, ml o unidad.")
    query = text(
        """
        UPDATE productos
        SET nombre = :nombre,
            descripcion = :descripcion,
            unidad_medida = :unidad_medida,
            activo = :activo
        WHERE id_producto = :id_producto;
        """
    )
    with engine.begin() as conn:
        result = conn.execute(
            query,
            {
                "id_producto": id_producto,
                "nombre": nombre.strip(),
                "descripcion": descripcion.strip() if descripcion and descripcion.strip() else None,
                "unidad_medida": unidad_medida,
                "activo": activo,
            },
        )
        return result.rowcount > 0


def load_inventario_alertas(id_local: Optional[int] = None) -> pd.DataFrame:
    """
    Carga el inventario por lote calculando los días restantes para el vencimiento
    y asignando el estado del semáforo. Opcionalmente filtra por id_local.
    """
    where_conditions = ["s.cantidad > 0"]
    if id_local:
        where_conditions.append("s.id_local = :id_local")
    where_clause = "WHERE " + " AND ".join(where_conditions)
    query = text(
        f"""
        SELECT
            s.id_stock,
            loc.id_local,
            loc.nombre AS local,
            p.id_producto,
            p.nombre AS producto,
            p.unidad_medida,
            l.id_lote,
            l.codigo_lote_proveedor,
            s.cantidad,
            l.fecha_vencimiento,
            (l.fecha_vencimiento - CURRENT_DATE) AS dias_para_vencer,
            CASE
                WHEN (l.fecha_vencimiento < CURRENT_DATE) THEN '🔴 Vencido'
                WHEN (l.fecha_vencimiento - CURRENT_DATE <= 7) THEN '🟠 Crítico (≤ 7 días)'
                WHEN (l.fecha_vencimiento - CURRENT_DATE <= 30) THEN '🟡 Preventivo (8-30 días)'
                ELSE '🟢 Óptimo (> 30 días)'
            END AS estado_alerta,
            CASE
                WHEN (l.fecha_vencimiento < CURRENT_DATE) THEN 1
                WHEN (l.fecha_vencimiento - CURRENT_DATE <= 7) THEN 2
                WHEN (l.fecha_vencimiento - CURRENT_DATE <= 30) THEN 3
                ELSE 4
            END AS severidad_alerta,
            COALESCE(dc.costo_unitario, 0) AS costo_unitario,
            ROUND(s.cantidad * COALESCE(dc.costo_unitario, 0), 2) AS valor_inventario,
            COALESCE(l.temperatura_recepcion, 2.0) AS temperatura_recepcion,
            prov.nombre AS proveedor,
            c.tipo_documento,
            c.numero_documento AS documento_compra,
            l.fecha_recepcion,
            s.actualizado_en
        FROM stock_lote_local AS s
        JOIN lotes AS l ON l.id_lote = s.id_lote
        JOIN detalle_compra AS dc ON dc.id_detalle_compra = l.id_detalle_compra
        JOIN productos AS p ON p.id_producto = dc.id_producto
        JOIN locales AS loc ON loc.id_local = s.id_local
        JOIN compras AS c ON c.id_compra = dc.id_compra
        JOIN proveedores AS prov ON prov.id_proveedor = c.id_proveedor
        {where_clause}
        ORDER BY severidad_alerta ASC, l.fecha_vencimiento ASC, loc.nombre, p.nombre
        """
    )
    with engine.connect() as connection:
        params = {"id_local": id_local} if id_local else {}
        return pd.read_sql(query, connection, params=params)


def load_resumen_metricas(id_local: Optional[int] = None) -> Dict[str, Any]:
    """Obtiene métricas cuantitativas y financieras de stock y alertas para el local o consolidado."""
    inv = load_inventario_alertas(id_local)
    if inv.empty:
        return {
            "total_lotes": 0,
            "total_cantidad": 0.0,
            "total_productos": 0,
            "total_valor": 0.0,
            "valor_en_riesgo": 0.0,
            "pct_en_riesgo": 0.0,
            "vencidos": 0,
            "valor_vencidos": 0.0,
            "criticos": 0,
            "valor_criticos": 0.0,
            "preventivos": 0,
            "valor_preventivos": 0.0,
            "optimos": 0,
            "valor_optimos": 0.0,
        }

    total_valor = float(inv["valor_inventario"].sum())
    valor_vencido = float(inv[inv["severidad_alerta"] == 1]["valor_inventario"].sum())
    valor_critico = float(inv[inv["severidad_alerta"] == 2]["valor_inventario"].sum())
    valor_preventivo = float(inv[inv["severidad_alerta"] == 3]["valor_inventario"].sum())
    valor_optimo = float(inv[inv["severidad_alerta"] == 4]["valor_inventario"].sum())
    valor_en_riesgo = valor_vencido + valor_critico
    pct_en_riesgo = (valor_en_riesgo / total_valor * 100) if total_valor > 0 else 0.0

    return {
        "total_lotes": len(inv),
        "total_cantidad": float(inv["cantidad"].sum()),
        "total_productos": int(inv["id_producto"].nunique()),
        "total_valor": total_valor,
        "valor_en_riesgo": valor_en_riesgo,
        "pct_en_riesgo": pct_en_riesgo,
        "vencidos": int((inv["severidad_alerta"] == 1).sum()),
        "valor_vencidos": valor_vencido,
        "criticos": int((inv["severidad_alerta"] == 2).sum()),
        "valor_criticos": valor_critico,
        "preventivos": int((inv["severidad_alerta"] == 3).sum()),
        "valor_preventivos": valor_preventivo,
        "optimos": int((inv["severidad_alerta"] == 4).sum()),
        "valor_optimos": valor_optimo,
    }


def load_lotes_selector() -> pd.DataFrame:
    """Devuelve listado de lotes para selector de trazabilidad."""
    query = text(
        """
        SELECT
            l.id_lote,
            l.codigo_lote_proveedor,
            p.nombre AS producto,
            prov.nombre AS proveedor,
            l.fecha_vencimiento,
            CONCAT('Lote #', l.id_lote, ' - ', p.nombre, ' (Ref: ', l.codigo_lote_proveedor, ')') AS display_label
        FROM lotes AS l
        JOIN detalle_compra AS dc ON dc.id_detalle_compra = l.id_detalle_compra
        JOIN productos AS p ON p.id_producto = dc.id_producto
        JOIN compras AS c ON c.id_compra = dc.id_compra
        JOIN proveedores AS prov ON prov.id_proveedor = c.id_proveedor
        ORDER BY l.id_lote DESC
        """
    )
    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def load_trazabilidad_lote(id_lote: int) -> Dict[str, Any]:
    """
    Obtiene la trazabilidad completa de un lote:
    - Cabecera del lote y compra origen
    - Existencia actual distribuida en cada local
    - Historial de movimientos (salidas/traslados)
    """
    # 1. Cabecera e información de compra/proveedor
    query_header = text(
        """
        SELECT
            l.id_lote,
            l.codigo_lote_proveedor,
            l.cantidad_inicial,
            l.fecha_vencimiento,
            (l.fecha_vencimiento - CURRENT_DATE) AS dias_para_vencer,
            l.fecha_recepcion,
            COALESCE(l.temperatura_recepcion, 2.0) AS temperatura_recepcion,
            COALESCE(dc.costo_unitario, 0) AS costo_unitario,
            l.creado_en AS fecha_registro_lote,
            p.nombre AS producto,
            p.unidad_medida,
            prov.nombre AS proveedor,
            prov.rut AS rut_proveedor,
            c.id_compra,
            c.tipo_documento,
            c.numero_documento AS documento_compra,
            c.fecha_compra,
            loc_rec.nombre AS local_receptor_original,
            dc.costo_unitario,
            dc.observaciones AS obs_detalle,
            c.observaciones AS obs_compra
        FROM lotes AS l
        JOIN detalle_compra AS dc ON dc.id_detalle_compra = l.id_detalle_compra
        JOIN productos AS p ON p.id_producto = dc.id_producto
        JOIN compras AS c ON c.id_compra = dc.id_compra
        JOIN proveedores AS prov ON prov.id_proveedor = c.id_proveedor
        JOIN locales AS loc_rec ON loc_rec.id_local = c.id_local_receptor
        WHERE l.id_lote = :id_lote
        """
    )

    # 2. Stock distribuido por locales
    query_stock = text(
        """
        SELECT
            loc.nombre AS local,
            s.cantidad,
            s.actualizado_en
        FROM stock_lote_local AS s
        JOIN locales AS loc ON loc.id_local = s.id_local
        WHERE s.id_lote = :id_lote AND s.cantidad > 0
        ORDER BY loc.nombre
        """
    )

    # 3. Historial de movimientos
    query_movimientos = text(
        """
        SELECT
            m.id_movimiento,
            m.tipo_movimiento,
            m.fecha_movimiento,
            loc_o.nombre AS local_origen,
            COALESCE(loc_d.nombre, 'Consumo en cocina') AS destino,
            dm.cantidad,
            m.referencia,
            m.observaciones,
            m.estado
        FROM detalle_movimiento AS dm
        JOIN movimientos AS m ON m.id_movimiento = dm.id_movimiento
        JOIN locales AS loc_o ON loc_o.id_local = m.id_local_origen
        LEFT JOIN locales AS loc_d ON loc_d.id_local = m.id_local_destino
        WHERE dm.id_lote = :id_lote
        ORDER BY m.fecha_movimiento DESC
        """
    )

    with engine.connect() as conn:
        header_df = pd.read_sql(query_header, conn, params={"id_lote": id_lote})
        if header_df.empty:
            return {}

        stock_df = pd.read_sql(query_stock, conn, params={"id_lote": id_lote})
        movimientos_df = pd.read_sql(query_movimientos, conn, params={"id_lote": id_lote})

        info = header_df.iloc[0].to_dict()
        return {
            "info": info,
            "stock_locales": stock_df,
            "movimientos": movimientos_df,
        }


def registrar_recepcion_compra(
    id_proveedor: int,
    id_local_receptor: int,
    tipo_documento: str,
    numero_documento: str,
    fecha_compra: date,
    fecha_recepcion: date,
    id_producto: int,
    cantidad: float,
    codigo_lote_proveedor: str,
    fecha_vencimiento: date,
    temperatura_recepcion: float = 2.0,
    costo_unitario: Optional[float] = None,
    observaciones: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Registra de manera atómica una compra, detalle, lote y actualiza el stock
    en el local receptor dentro de una única transacción.
    """
    if fecha_recepcion < fecha_compra:
        raise ValueError("La fecha de recepción no puede ser anterior a la fecha de compra.")
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a 0.")

    with engine.begin() as conn:
        # 1. Verificar si ya existe la compra por (id_proveedor, tipo_documento, numero_documento)
        q_find_compra = text(
            """
            SELECT id_compra
            FROM compras
            WHERE id_proveedor = :id_proveedor
              AND tipo_documento = :tipo_documento
              AND numero_documento = :numero_documento
            """
        )
        res_compra = conn.execute(
            q_find_compra,
            {
                "id_proveedor": id_proveedor,
                "tipo_documento": tipo_documento,
                "numero_documento": numero_documento,
            },
        ).first()

        if res_compra:
            id_compra = res_compra[0]
        else:
            q_insert_compra = text(
                """
                INSERT INTO compras (
                    id_proveedor, id_local_receptor, tipo_documento,
                    numero_documento, fecha_compra, fecha_recepcion, observaciones
                )
                VALUES (
                    :id_proveedor, :id_local_receptor, :tipo_documento,
                    :numero_documento, :fecha_compra, :fecha_recepcion, :observaciones
                )
                RETURNING id_compra;
                """
            )
            id_compra = conn.execute(
                q_insert_compra,
                {
                    "id_proveedor": id_proveedor,
                    "id_local_receptor": id_local_receptor,
                    "tipo_documento": tipo_documento,
                    "numero_documento": numero_documento,
                    "fecha_compra": fecha_compra,
                    "fecha_recepcion": fecha_recepcion,
                    "observaciones": observaciones,
                },
            ).scalar_one()

        # 2. Verificar o crear detalle_compra para este producto
        q_find_detalle = text(
            """
            SELECT id_detalle_compra
            FROM detalle_compra
            WHERE id_compra = :id_compra AND id_producto = :id_producto
            """
        )
        res_detalle = conn.execute(
            q_find_detalle, {"id_compra": id_compra, "id_producto": id_producto}
        ).first()

        if res_detalle:
            id_detalle_compra = res_detalle[0]
            # Actualizar la cantidad acumulada en el detalle
            q_update_detalle = text(
                """
                UPDATE detalle_compra
                SET cantidad_recibida = cantidad_recibida + :cantidad,
                    costo_unitario = COALESCE(:costo_unitario, costo_unitario)
                WHERE id_detalle_compra = :id_detalle_compra
                """
            )
            conn.execute(
                q_update_detalle,
                {
                    "cantidad": cantidad,
                    "costo_unitario": costo_unitario,
                    "id_detalle_compra": id_detalle_compra,
                },
            )
        else:
            q_insert_detalle = text(
                """
                INSERT INTO detalle_compra (
                    id_compra, id_producto, cantidad_recibida, costo_unitario, observaciones
                )
                VALUES (
                    :id_compra, :id_producto, :cantidad, :costo_unitario, :observaciones
                )
                RETURNING id_detalle_compra;
                """
            )
            id_detalle_compra = conn.execute(
                q_insert_detalle,
                {
                    "id_compra": id_compra,
                    "id_producto": id_producto,
                    "cantidad": cantidad,
                    "costo_unitario": costo_unitario,
                    "observaciones": observaciones,
                },
            ).scalar_one()

        # 3. Crear el lote con control de temperatura de ingreso
        q_insert_lote = text(
            """
            INSERT INTO lotes (
                id_detalle_compra, codigo_lote_proveedor, cantidad_inicial,
                fecha_vencimiento, fecha_recepcion, temperatura_recepcion
            )
            VALUES (
                :id_detalle_compra, :codigo_lote_proveedor, :cantidad,
                :fecha_vencimiento, :fecha_recepcion, :temperatura_recepcion
            )
            RETURNING id_lote;
            """
        )
        id_lote = conn.execute(
            q_insert_lote,
            {
                "id_detalle_compra": id_detalle_compra,
                "codigo_lote_proveedor": codigo_lote_proveedor,
                "cantidad": cantidad,
                "fecha_vencimiento": fecha_vencimiento,
                "fecha_recepcion": fecha_recepcion,
                "temperatura_recepcion": temperatura_recepcion,
            },
        ).scalar_one()

        # 4. Asignar el stock al local receptor
        q_upsert_stock = text(
            """
            INSERT INTO stock_lote_local (id_lote, id_local, cantidad, actualizado_en)
            VALUES (:id_lote, :id_local, :cantidad, CURRENT_TIMESTAMP)
            ON CONFLICT (id_lote, id_local) DO UPDATE
            SET cantidad = stock_lote_local.cantidad + EXCLUDED.cantidad,
                actualizado_en = CURRENT_TIMESTAMP;
            """
        )
        conn.execute(
            q_upsert_stock,
            {
                "id_lote": id_lote,
                "id_local": id_local_receptor,
                "cantidad": cantidad,
            },
        )

        return {
            "id_compra": id_compra,
            "id_detalle_compra": id_detalle_compra,
            "id_lote": id_lote,
        }


def load_stock_disponible_local(id_local: int) -> pd.DataFrame:
    """
    Carga todos los lotes con stock > 0 para un local específico,
    ordenados bajo criterio FEFO (vencimiento más cercano) y FIFO como desempate.
    """
    query = text(
        """
        SELECT
            s.id_stock,
            s.id_lote,
            s.id_local,
            p.id_producto,
            p.nombre AS producto,
            p.unidad_medida,
            l.codigo_lote_proveedor,
            s.cantidad AS stock_disponible,
            l.fecha_vencimiento,
            (l.fecha_vencimiento - CURRENT_DATE) AS dias_para_vencer,
            l.fecha_recepcion,
            COALESCE(l.temperatura_recepcion, 2.0) AS temperatura_recepcion,
            COALESCE(dc.costo_unitario, 0) AS costo_unitario,
            CONCAT(
                p.nombre,
                ' | Lote #', l.id_lote,
                ' (Ref: ', l.codigo_lote_proveedor, ')',
                ' | Disp: ', ROUND(s.cantidad, 3), ' ', p.unidad_medida,
                ' | Vence: ', l.fecha_vencimiento,
                ' (', (l.fecha_vencimiento - CURRENT_DATE), ' d)'
            ) AS display_label
        FROM stock_lote_local AS s
        JOIN lotes AS l ON l.id_lote = s.id_lote
        JOIN detalle_compra AS dc ON dc.id_detalle_compra = l.id_detalle_compra
        JOIN productos AS p ON p.id_producto = dc.id_producto
        WHERE s.id_local = :id_local AND s.cantidad > 0
        ORDER BY l.fecha_vencimiento ASC, l.fecha_recepcion ASC, l.id_lote ASC
        """
    )
    with engine.connect() as connection:
        return pd.read_sql(query, connection, params={"id_local": id_local})


def registrar_salida_cocina(
    id_local: int,
    id_lote: int,
    cantidad: float,
    referencia: Optional[str] = None,
    observaciones: Optional[str] = None,
    id_usuario: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Registra una salida de stock por consumo en cocina (destino NULL).
    Valida existencias suficientes y actualiza stock atómicamente.
    """
    if cantidad <= 0:
        raise ValueError("La cantidad a consumir debe ser mayor a 0.")

    with engine.begin() as conn:
        # 1. Validar y bloquear stock actual
        q_stock = text(
            """
            SELECT cantidad
            FROM stock_lote_local
            WHERE id_lote = :id_lote AND id_local = :id_local
            FOR UPDATE
            """
        )
        row = conn.execute(q_stock, {"id_lote": id_lote, "id_local": id_local}).first()
        if not row:
            raise ValueError("El lote seleccionado no tiene registro de stock en este local.")

        stock_actual = float(row[0])
        if stock_actual < cantidad:
            raise ValueError(
                f"Stock insuficiente: disponible {stock_actual:.3f}, solicitado {cantidad:.3f}."
            )

        # 2. Registrar movimiento
        q_insert_mov = text(
            """
            INSERT INTO movimientos (
                tipo_movimiento, id_local_origen, id_local_destino,
                id_usuario, referencia, observaciones, estado
            )
            VALUES (
                'salida_cocina', :id_local, NULL,
                :id_usuario, :referencia, :observaciones, 'confirmado'
            )
            RETURNING id_movimiento;
            """
        )
        id_movimiento = conn.execute(
            q_insert_mov,
            {
                "id_local": id_local,
                "id_usuario": id_usuario,
                "referencia": referencia or "Consumo cocina",
                "observaciones": observaciones,
            },
        ).scalar_one()

        # 3. Registrar detalle de movimiento
        q_insert_det = text(
            """
            INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad, observaciones)
            VALUES (:id_movimiento, :id_lote, :cantidad, :observaciones);
            """
        )
        conn.execute(
            q_insert_det,
            {
                "id_movimiento": id_movimiento,
                "id_lote": id_lote,
                "cantidad": cantidad,
                "observaciones": observaciones,
            },
        )

        # 4. Descontar stock
        nuevo_stock = stock_actual - cantidad
        q_update_stock = text(
            """
            UPDATE stock_lote_local
            SET cantidad = :nuevo_stock, actualizado_en = CURRENT_TIMESTAMP
            WHERE id_lote = :id_lote AND id_local = :id_local
            """
        )
        conn.execute(
            q_update_stock,
            {
                "nuevo_stock": nuevo_stock,
                "id_lote": id_lote,
                "id_local": id_local,
            },
        )

        return {
            "id_movimiento": id_movimiento,
            "tipo_movimiento": "salida_cocina",
            "cantidad": cantidad,
            "nuevo_stock": nuevo_stock,
        }


def registrar_merma(
    id_local: int,
    id_lote: int,
    cantidad: float,
    motivo: str,
    observaciones: Optional[str] = None,
    id_usuario: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Registra una baja formal por merma, vencimiento o pérdida de cadena de frío.
    Calcula el costo financiero de la pérdida y actualiza el inventario atómicamente.
    """
    if cantidad <= 0:
        raise ValueError("La cantidad de merma debe ser mayor a 0.")

    with engine.begin() as conn:
        # 1. Validar y bloquear stock actual obteniendo el costo unitario
        q_stock = text(
            """
            SELECT s.cantidad, dc.costo_unitario, p.nombre AS producto, p.unidad_medida, l.codigo_lote_proveedor
            FROM stock_lote_local AS s
            JOIN lotes AS l ON l.id_lote = s.id_lote
            JOIN detalle_compra AS dc ON dc.id_detalle_compra = l.id_detalle_compra
            JOIN productos AS p ON p.id_producto = dc.id_producto
            WHERE s.id_lote = :id_lote AND s.id_local = :id_local
            FOR UPDATE OF s
            """
        )
        row = conn.execute(q_stock, {"id_lote": id_lote, "id_local": id_local}).first()
        if not row:
            raise ValueError("El lote seleccionado no cuenta con existencias registradas en este local.")

        stock_actual = float(row[0])
        costo_unitario = float(row[1]) if row[1] is not None else 0.0
        producto = row[2]
        unidad_medida = row[3]
        codigo_lote_prov = row[4]

        if stock_actual < cantidad:
            raise ValueError(
                f"Stock insuficiente: disponible {stock_actual:.3f}, merma a declarar {cantidad:.3f}."
            )

        # 2. Registrar movimiento tipificado como MERMA
        referencia_merma = f"MERMA: {motivo}"
        q_insert_mov = text(
            """
            INSERT INTO movimientos (
                tipo_movimiento, id_local_origen, id_local_destino,
                id_usuario, referencia, observaciones, estado
            )
            VALUES (
                'salida_cocina', :id_local, NULL,
                :id_usuario, :referencia, :observaciones, 'confirmado'
            )
            RETURNING id_movimiento;
            """
        )
        id_movimiento = conn.execute(
            q_insert_mov,
            {
                "id_local": id_local,
                "id_usuario": id_usuario,
                "referencia": referencia_merma,
                "observaciones": observaciones,
            },
        ).scalar_one()

        # 3. Registrar detalle del movimiento
        q_insert_det = text(
            """
            INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad, observaciones)
            VALUES (:id_movimiento, :id_lote, :cantidad, :observaciones);
            """
        )
        conn.execute(
            q_insert_det,
            {
                "id_movimiento": id_movimiento,
                "id_lote": id_lote,
                "cantidad": cantidad,
                "observaciones": observaciones,
            },
        )

        # 4. Descontar existencias del stock
        nuevo_stock = stock_actual - cantidad
        q_update_stock = text(
            """
            UPDATE stock_lote_local
            SET cantidad = :nuevo_stock, actualizado_en = CURRENT_TIMESTAMP
            WHERE id_lote = :id_lote AND id_local = :id_local
            """
        )
        conn.execute(
            q_update_stock,
            {
                "nuevo_stock": nuevo_stock,
                "id_lote": id_lote,
                "id_local": id_local,
            },
        )

        costo_total_perdida = cantidad * costo_unitario

        return {
            "id_movimiento": id_movimiento,
            "motivo": motivo,
            "producto": producto,
            "codigo_lote_proveedor": codigo_lote_prov,
            "unidad_medida": unidad_medida,
            "cantidad": cantidad,
            "costo_unitario": costo_unitario,
            "costo_total_perdida": costo_total_perdida,
            "nuevo_stock": nuevo_stock,
        }


def load_historial_mermas(id_local: Optional[int] = None, limit: int = 50) -> pd.DataFrame:
    """
    Carga el historial de mermas registradas con su cálculo de costo financiero.
    """
    where_local = "AND m.id_local_origen = :id_local" if id_local else ""
    query = text(
        f"""
        SELECT
            m.id_movimiento,
            m.fecha_movimiento,
            loc.nombre AS local,
            p.nombre AS producto,
            l.id_lote,
            l.codigo_lote_proveedor,
            dm.cantidad,
            p.unidad_medida,
            COALESCE(dc.costo_unitario, 0) AS costo_unitario,
            ROUND(dm.cantidad * COALESCE(dc.costo_unitario, 0), 2) AS costo_total_merma,
            REPLACE(m.referencia, 'MERMA: ', '') AS motivo_merma,
            m.observaciones
        FROM detalle_movimiento AS dm
        JOIN movimientos AS m ON m.id_movimiento = dm.id_movimiento
        JOIN lotes AS l ON l.id_lote = dm.id_lote
        JOIN detalle_compra AS dc ON dc.id_detalle_compra = l.id_detalle_compra
        JOIN productos AS p ON p.id_producto = dc.id_producto
        JOIN locales AS loc ON loc.id_local = m.id_local_origen
        WHERE m.referencia LIKE 'MERMA:%'
        {where_local}
        ORDER BY m.fecha_movimiento DESC
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        params = {"id_local": id_local, "limit": limit} if id_local else {"limit": limit}
        return pd.read_sql(query, conn, params=params)


def load_resumen_mermas(id_local: Optional[int] = None) -> Dict[str, Any]:
    """Calcula totales de mermas (kilos y dinero) para el local o consolidado."""
    df_m = load_historial_mermas(id_local=id_local, limit=500)
    if df_m.empty:
        return {
            "total_eventos": 0,
            "total_kilos": 0.0,
            "total_costo_merma": 0.0,
        }
    return {
        "total_eventos": len(df_m),
        "total_kilos": float(df_m["cantidad"].sum()),
        "total_costo_merma": float(df_m["costo_total_merma"].sum()),
    }


def registrar_traslado_local(
    id_local_origen: int,
    id_local_destino: int,
    id_lote: int,
    cantidad: float,
    referencia: Optional[str] = None,
    observaciones: Optional[str] = None,
    id_usuario: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Registra un traslado de mercadería entre dos sucursales.
    El lote original mantiene su ID, descontándose del origen y sumándose al destino.
    """
    if id_local_origen == id_local_destino:
        raise ValueError("El local de destino debe ser diferente al local de origen.")
    if cantidad <= 0:
        raise ValueError("La cantidad a trasladar debe ser mayor a 0.")

    with engine.begin() as conn:
        # 1. Validar y bloquear stock en el local de origen
        q_stock = text(
            """
            SELECT cantidad
            FROM stock_lote_local
            WHERE id_lote = :id_lote AND id_local = :id_local_origen
            FOR UPDATE
            """
        )
        row = conn.execute(
            q_stock, {"id_lote": id_lote, "id_local_origen": id_local_origen}
        ).first()
        if not row:
            raise ValueError("El lote no cuenta con registro de stock en el local de origen.")

        stock_origen = float(row[0])
        if stock_origen < cantidad:
            raise ValueError(
                f"Stock insuficiente en origen: disponible {stock_origen:.3f}, a trasladar {cantidad:.3f}."
            )

        # 2. Registrar movimiento de tipo 'traslado'
        q_insert_mov = text(
            """
            INSERT INTO movimientos (
                tipo_movimiento, id_local_origen, id_local_destino,
                id_usuario, referencia, observaciones, estado
            )
            VALUES (
                'traslado', :id_local_origen, :id_local_destino,
                :id_usuario, :referencia, :observaciones, 'confirmado'
            )
            RETURNING id_movimiento;
            """
        )
        id_movimiento = conn.execute(
            q_insert_mov,
            {
                "id_local_origen": id_local_origen,
                "id_local_destino": id_local_destino,
                "id_usuario": id_usuario,
                "referencia": referencia or "Guía de traslado interno",
                "observaciones": observaciones,
            },
        ).scalar_one()

        # 3. Registrar detalle del movimiento
        q_insert_det = text(
            """
            INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad, observaciones)
            VALUES (:id_movimiento, :id_lote, :cantidad, :observaciones);
            """
        )
        conn.execute(
            q_insert_det,
            {
                "id_movimiento": id_movimiento,
                "id_lote": id_lote,
                "cantidad": cantidad,
                "observaciones": observaciones,
            },
        )

        # 4. Descontar en origen
        q_update_origen = text(
            """
            UPDATE stock_lote_local
            SET cantidad = cantidad - :cantidad, actualizado_en = CURRENT_TIMESTAMP
            WHERE id_lote = :id_lote AND id_local = :id_local_origen
            """
        )
        conn.execute(
            q_update_origen,
            {"cantidad": cantidad, "id_lote": id_lote, "id_local_origen": id_local_origen},
        )

        # 5. Incrementar o insertar en destino
        q_upsert_destino = text(
            """
            INSERT INTO stock_lote_local (id_lote, id_local, cantidad, actualizado_en)
            VALUES (:id_lote, :id_local_destino, :cantidad, CURRENT_TIMESTAMP)
            ON CONFLICT (id_lote, id_local) DO UPDATE
            SET cantidad = stock_lote_local.cantidad + EXCLUDED.cantidad,
                actualizado_en = CURRENT_TIMESTAMP;
            """
        )
        conn.execute(
            q_upsert_destino,
            {
                "id_lote": id_lote,
                "id_local_destino": id_local_destino,
                "cantidad": cantidad,
            },
        )

        # 6. Consultar saldo final en destino
        q_stock_dest = text(
            """
            SELECT cantidad FROM stock_lote_local
            WHERE id_lote = :id_lote AND id_local = :id_local_destino
            """
        )
        nuevo_stock_destino = float(conn.execute(
            q_stock_dest, {"id_lote": id_lote, "id_local_destino": id_local_destino}
        ).scalar_one())

        nuevo_stock_origen = stock_origen - cantidad

        return {
            "id_movimiento": id_movimiento,
            "tipo_movimiento": "traslado",
            "cantidad": cantidad,
            "id_local_origen": id_local_origen,
            "id_local_destino": id_local_destino,
            "nuevo_stock_origen": nuevo_stock_origen,
            "nuevo_stock_destino": nuevo_stock_destino,
        }


def load_historial_movimientos(id_local: Optional[int] = None, limit: int = 50) -> pd.DataFrame:
    """
    Carga el historial de movimientos de salida o traslados.
    Si se especifica id_local, filtra movimientos donde el local sea origen o destino.
    """
    where_clause = "WHERE m.id_local_origen = :id_local OR m.id_local_destino = :id_local" if id_local else ""
    query = text(
        f"""
        SELECT
            m.id_movimiento,
            CASE
                WHEN m.tipo_movimiento = 'salida_cocina' THEN '🍳 Salida Cocina'
                WHEN m.tipo_movimiento = 'traslado' THEN '🚚 Traslado'
                ELSE m.tipo_movimiento
            END AS tipo,
            m.fecha_movimiento,
            loc_o.nombre AS local_origen,
            COALESCE(loc_d.nombre, 'Consumo en Cocina') AS local_destino,
            p.nombre AS producto,
            l.id_lote,
            l.codigo_lote_proveedor,
            dm.cantidad,
            p.unidad_medida,
            m.referencia,
            m.observaciones,
            m.estado
        FROM detalle_movimiento AS dm
        JOIN movimientos AS m ON m.id_movimiento = dm.id_movimiento
        JOIN lotes AS l ON l.id_lote = dm.id_lote
        JOIN detalle_compra AS dc ON dc.id_detalle_compra = l.id_detalle_compra
        JOIN productos AS p ON p.id_producto = dc.id_producto
        JOIN locales AS loc_o ON loc_o.id_local = m.id_local_origen
        LEFT JOIN locales AS loc_d ON loc_d.id_local = m.id_local_destino
        {where_clause}
        ORDER BY m.fecha_movimiento DESC, m.id_movimiento DESC
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        params = {"id_local": id_local, "limit": limit} if id_local else {"limit": limit}
        return pd.read_sql(query, conn, params=params)


def load_recetas(solo_activas: bool = True) -> pd.DataFrame:
    """Carga todas las recetas con sus ingredientes y gramajes."""
    filtro = "WHERE r.activo = TRUE" if solo_activas else ""
    query = text(
        f"""
        SELECT
            r.id_receta,
            r.nombre AS receta,
            r.categoria,
            r.tiempo_preparacion_min,
            r.precio_venta,
            r.activo,
            p.id_producto,
            p.nombre AS ingrediente,
            p.unidad_medida,
            ri.cantidad_kg
        FROM recetas AS r
        JOIN receta_ingredientes AS ri ON ri.id_receta = r.id_receta
        JOIN productos AS p ON p.id_producto = ri.id_producto
        {filtro}
        ORDER BY r.categoria, r.nombre, p.nombre
        """
    )
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def load_recetas_catalogo(solo_activas: bool = True) -> pd.DataFrame:
    """Carga el catálogo agrupado de recetas con su ficha de escandallo resumida."""
    df_raw = load_recetas(solo_activas=solo_activas)
    if df_raw.empty:
        return pd.DataFrame()

    def agrupar_ingredientes(grupo):
        ings = [f"{row['ingrediente']} ({row['cantidad_kg']:.3f} {row['unidad_medida']})" for _, row in grupo.iterrows()]
        return ", ".join(ings)

    resumen = df_raw.groupby(["id_receta", "receta", "categoria", "tiempo_preparacion_min", "precio_venta", "activo"]).apply(agrupar_ingredientes).reset_index(name="escandallo_ingredientes")
    return resumen.sort_values(by=["categoria", "receta"])


def consumir_produccion_recetas(
    id_local: int,
    orden_platos: Dict[int, int],
    turno: str,
    observaciones: Optional[str] = None,
    id_usuario: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Descuenta de forma atómica los insumos requeridos para producir una comanda de platos,
    aplicando el algoritmo FEFO estricto por lote y calculando márgenes financieros.
    """
    # Filtrar solo recetas con cantidad > 0
    orden_filtrada = {int(k): int(v) for k, v in orden_platos.items() if int(v) > 0}
    if not orden_filtrada:
        raise ValueError("Debes especificar la cantidad de al menos un plato a preparar.")

    df_recetas = load_recetas(solo_activas=False)

    # 1. Calcular insumos requeridos consolidados
    # requerimientos: { id_producto: { "nombre": str, "unidad": str, "total_kg": float } }
    requerimientos: Dict[int, Dict[str, Any]] = {}
    detalle_platos_producidos: list[Dict[str, Any]] = []
    venta_total = 0.0

    for id_rec, cant_platos in orden_filtrada.items():
        filas_rec = df_recetas[df_recetas["id_receta"] == id_rec]
        if filas_rec.empty:
            continue
        nom_receta = filas_rec.iloc[0]["receta"]
        precio_vta = float(filas_rec.iloc[0]["precio_venta"])
        subtotal_vta = precio_vta * cant_platos
        venta_total += subtotal_vta

        detalle_platos_producidos.append({
            "id_receta": id_rec,
            "receta": nom_receta,
            "cantidad_platos": cant_platos,
            "precio_venta": precio_vta,
            "subtotal_venta": subtotal_vta,
        })

        for _, fila_ing in filas_rec.iterrows():
            id_prod = int(fila_ing["id_producto"])
            kg_necesarios = float(fila_ing["cantidad_kg"]) * cant_platos
            if id_prod not in requerimientos:
                requerimientos[id_prod] = {
                    "nombre": fila_ing["ingrediente"],
                    "unidad": fila_ing["unidad_medida"],
                    "total_kg": 0.0,
                }
            requerimientos[id_prod]["total_kg"] += kg_necesarios

    # 2. Transacción de validación, descuento FEFO y registro
    with engine.begin() as conn:
        # A. Validar stock disponible para todos los insumos involucrados
        lotes_por_producto: Dict[int, list[Dict[str, Any]]] = {}

        for id_prod, data_req in requerimientos.items():
            req_kg = data_req["total_kg"]
            q_lotes = text(
                """
                SELECT
                    s.id_stock,
                    s.id_lote,
                    s.cantidad,
                    l.codigo_lote_proveedor,
                    l.fecha_vencimiento,
                    COALESCE(dc.costo_unitario, 0) AS costo_unitario
                FROM stock_lote_local AS s
                JOIN lotes AS l ON l.id_lote = s.id_lote
                JOIN detalle_compra AS dc ON dc.id_detalle_compra = l.id_detalle_compra
                WHERE s.id_local = :id_local AND dc.id_producto = :id_producto AND s.cantidad > 0
                ORDER BY l.fecha_vencimiento ASC, l.fecha_recepcion ASC, l.id_lote ASC
                FOR UPDATE OF s
                """
            )
            rows = conn.execute(q_lotes, {"id_local": id_local, "id_producto": id_prod}).fetchall()
            stock_total_disp = sum(float(r[2]) for r in rows)

            if stock_total_disp < req_kg:
                raise ValueError(
                    f"Stock insuficiente de {data_req['nombre']}. "
                    f"Requerido para la producción: {req_kg:.3f} {data_req['unidad']}, "
                    f"disponible en este local: {stock_total_disp:.3f} {data_req['unidad']}."
                )

            lotes_por_producto[id_prod] = [
                {
                    "id_stock": r[0],
                    "id_lote": r[1],
                    "cantidad_disponible": float(r[2]),
                    "codigo_lote_proveedor": r[3],
                    "fecha_vencimiento": r[4],
                    "costo_unitario": float(r[5]),
                }
                for r in rows
            ]

        # B. Registrar el movimiento maestro de cocina
        resumen_platos_str = ", ".join(f"{item['cantidad_platos']} {item['receta']}" for item in detalle_platos_producidos)
        ref_movimiento = f"PRODUCCIÓN {turno.upper()}: {resumen_platos_str}"[:100]

        q_insert_mov = text(
            """
            INSERT INTO movimientos (
                tipo_movimiento, id_local_origen, id_local_destino,
                id_usuario, referencia, observaciones, estado
            )
            VALUES (
                'salida_cocina', :id_local, NULL,
                :id_usuario, :referencia, :observaciones, 'confirmado'
            )
            RETURNING id_movimiento;
            """
        )
        id_movimiento = conn.execute(
            q_insert_mov,
            {
                "id_local": id_local,
                "id_usuario": id_usuario,
                "referencia": ref_movimiento,
                "observaciones": observaciones or f"Comanda elaborada en {turno}",
            },
        ).scalar_one()

        # C. Descontar stock por FEFO y registrar detalle_movimiento
        costo_total_insumos = 0.0
        desglose_lotes_consumidos: list[Dict[str, Any]] = []

        for id_prod, data_req in requerimientos.items():
            kg_por_descontar = data_req["total_kg"]
            lista_lotes = lotes_por_producto[id_prod]

            for lote_info in lista_lotes:
                if kg_por_descontar <= 0:
                    break

                cant_a_descontar = min(lote_info["cantidad_disponible"], kg_por_descontar)
                nuevo_stock_lote = lote_info["cantidad_disponible"] - cant_a_descontar
                costo_consumo = cant_a_descontar * lote_info["costo_unitario"]
                costo_total_insumos += costo_consumo

                # Actualizar stock
                conn.execute(
                    text(
                        """
                        UPDATE stock_lote_local
                        SET cantidad = :nuevo_stock, actualizado_en = CURRENT_TIMESTAMP
                        WHERE id_stock = :id_stock
                        """
                    ),
                    {"nuevo_stock": nuevo_stock_lote, "id_stock": lote_info["id_stock"]},
                )

                # Insertar detalle_movimiento
                conn.execute(
                    text(
                        """
                        INSERT INTO detalle_movimiento (id_movimiento, id_lote, cantidad, observaciones)
                        VALUES (:id_movimiento, :id_lote, :cantidad, :obs)
                        """
                    ),
                    {
                        "id_movimiento": id_movimiento,
                        "id_lote": lote_info["id_lote"],
                        "cantidad": cant_a_descontar,
                        "obs": f"Producción {data_req['nombre']} ({turno})",
                    },
                )

                desglose_lotes_consumidos.append({
                    "id_lote": lote_info["id_lote"],
                    "producto": data_req["nombre"],
                    "codigo_lote_proveedor": lote_info["codigo_lote_proveedor"],
                    "cantidad_consumida": cant_a_descontar,
                    "unidad": data_req["unidad"],
                    "costo_unitario": lote_info["costo_unitario"],
                    "costo_total": costo_consumo,
                    "nuevo_stock": nuevo_stock_lote,
                })

                kg_por_descontar -= cant_a_descontar

        margen_bruto = venta_total - costo_total_insumos
        pct_margen = (margen_bruto / venta_total * 100) if venta_total > 0 else 0.0

        return {
            "id_movimiento": id_movimiento,
            "turno": turno,
            "platos_totales": sum(item["cantidad_platos"] for item in detalle_platos_producidos),
            "detalle_platos": detalle_platos_producidos,
            "desglose_insumos": desglose_lotes_consumidos,
            "costo_total_insumos": costo_total_insumos,
            "venta_total": venta_total,
            "margen_bruto": margen_bruto,
            "pct_margen": pct_margen,
        }


def test_connection():
    """Función de prueba de solo lectura para verificar la base de datos."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM locales;"))
            count = result.scalar()
            print(f"¡Conexión exitosa a PostgreSQL! Locales encontrados en la base de datos: {count}")
            return True
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return False


if __name__ == "__main__":
    test_connection()
