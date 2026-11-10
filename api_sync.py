"""
==============================================================================
MAMÁ QOCHA: MICRO-API DE SINCRONIZACIÓN OFFLINE (LOCAL-FIRST)
Archivo: api_sync.py
Descripción:
  Servicio REST liviano para la Terminal de Cocina Autónoma (PWA).
  1. GET  /api/bootstrap/{id_local}: Descarga el estado inicial (recetas + stock FEFO).
  2. POST /api/sync: Recibe lotes de eventos generados offline/online con idempotencia.
  3. GET  /api/eventos/{id_local}: Consulta el historial de eventos sincronizados.
==============================================================================
"""

import json
from datetime import datetime, timezone, date, timedelta
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text

import db

app = FastAPI(
    title="Mamá Qocha - API de Sincronización Offline",
    description="Servicio de continuidad operativa y sincronización asíncrona para cocina local",
    version="1.0.0",
)

# Habilitar CORS para permitir peticiones desde PWA en navegador local o dominio web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# MODELOS PYDANTIC DE ENTRADA Y SALIDA
# ==============================================================================
class EventoSyncItem(BaseModel):
    id_evento: str = Field(..., description="UUID v4 único generado por el cliente local")
    tipo_evento: str = Field(..., description="PRODUCCION_RECETAS | SALIDA_COCINA_MANUAL | MERMA | RECEPCION_MERCADERIA_OFFLINE")
    fecha_local: str = Field(..., description="Fecha/hora ISO 8601 del momento de la acción física")
    payload: Dict[str, Any] = Field(..., description="Datos detallados de la orden, consumo o recepción")


class LoteSyncRequest(BaseModel):
    id_local: int = Field(..., ge=1, description="ID del local que envía los datos")
    timestamp_envio: str = Field(..., description="Fecha/hora de despacho del paquete")
    eventos: List[EventoSyncItem] = Field(default_factory=list, description="Lista de eventos a procesar")


# ==============================================================================
# ENDPOINTS PRINCIPALES
# ==============================================================================
@app.get("/", tags=["Diagnóstico"])
def root():
    """Diagnóstico de salud del microservicio y conectividad con la base central."""
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "Conectado a Neon PostgreSQL"
    except Exception as e:
        db_status = f"Error de conexión: {str(e)}"

    return {
        "sistema": "Mamá Qocha - Micro-API Offline Sync",
        "estado": "Activo",
        "base_datos": db_status,
        "hora_servidor": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/bootstrap/{id_local}", tags=["Bootstrap / Inicio de Turno"])
def get_bootstrap_local(id_local: int):
    """
    Descarga el snapshot mínimo necesario para que el navegador opere sin internet:
    - Datos del local.
    - Catálogo completo de recetas e ingredientes.
    - Lotes y stock activo del local ordenados bajo criterio FEFO.
    """
    # 1. Validar existencia del local
    df_locales = db.load_locales()
    local_match = df_locales[df_locales["id_local"] == id_local]
    if local_match.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con ID {id_local} no encontrado en el sistema."
        )
    nombre_local = local_match.iloc[0]["nombre"]

    # 2. Cargar recetas con ingredientes
    df_recetas = db.load_recetas(solo_activas=True)
    recetas_dict: Dict[int, Dict[str, Any]] = {}
    for _, fila in df_recetas.iterrows():
        r_id = int(fila["id_receta"])
        if r_id not in recetas_dict:
            recetas_dict[r_id] = {
                "id_receta": r_id,
                "nombre": fila["receta"],
                "categoria": fila["categoria"],
                "precio_venta": float(fila["precio_venta"]),
                "tiempo_min": int(fila["tiempo_preparacion_min"]) if fila["tiempo_preparacion_min"] else 15,
                "ingredientes": [],
            }
        recetas_dict[r_id]["ingredientes"].append({
            "id_producto": int(fila["id_producto"]),
            "nombre": fila["ingrediente"],
            "unidad": fila["unidad_medida"],
            "cantidad_kg": float(fila["cantidad_kg"]),
        })

    # 3. Cargar stock de lotes activos del local (ordenado por FEFO: fecha_vencimiento ASC)
    q_stock = text(
        """
        SELECT 
            s.id_lote,
            l.codigo_lote_proveedor,
            p.id_producto,
            p.nombre AS producto,
            p.unidad_medida,
            s.cantidad,
            l.fecha_vencimiento,
            l.fecha_recepcion
        FROM stock_lote_local s
        JOIN lotes l ON s.id_lote = l.id_lote
        JOIN detalle_compra dc ON l.id_detalle_compra = dc.id_detalle_compra
        JOIN productos p ON dc.id_producto = p.id_producto
        WHERE s.id_local = :id_local AND s.cantidad > 0
        ORDER BY l.fecha_vencimiento ASC, l.fecha_recepcion ASC
        """
    )

    with db.engine.connect() as conn:
        res = conn.execute(q_stock, {"id_local": id_local}).mappings().all()

    stock_lotes = []
    for r in res:
        stock_lotes.append({
            "id_lote": int(r["id_lote"]),
            "codigo_lote": str(r["codigo_lote_proveedor"]),
            "id_producto": int(r["id_producto"]),
            "producto": str(r["producto"]),
            "unidad_medida": str(r["unidad_medida"]),
            "cantidad": float(r["cantidad"]),
            "fecha_vencimiento": str(r["fecha_vencimiento"]),
            "fecha_recepcion": str(r["fecha_recepcion"]),
        })

    # 4. Cargar proveedores activos para recepciones offline en cocina
    df_prov = db.load_proveedores(solo_activos=True)
    proveedores = [
        {
            "id_proveedor": int(row["id_proveedor"]),
            "nombre": str(row["nombre"]),
            "rut": str(row["rut"] or ""),
        }
        for _, row in df_prov.iterrows()
    ]

    # 5. Cargar catálogo maestro de productos para recepciones offline
    df_prod = db.load_productos(solo_activos=True)
    productos = [
        {
            "id_producto": int(row["id_producto"]),
            "nombre": str(row["nombre"]),
            "unidad_medida": str(row["unidad_medida"]),
        }
        for _, row in df_prod.iterrows()
    ]

    return {
        "id_local": id_local,
        "nombre_local": nombre_local,
        "timestamp_snapshot": datetime.now(timezone.utc).isoformat(),
        "total_recetas": len(recetas_dict),
        "total_lotes_disponibles": len(stock_lotes),
        "recetas": list(recetas_dict.values()),
        "stock_fefo": stock_lotes,
        "proveedores": proveedores,
        "productos": productos,
    }


@app.post("/api/sync", tags=["Sincronización por Lote"])
def sync_batch(lote: LoteSyncRequest):
    """
    Recibe un lote de eventos generados offline/online por la cocina.
    Aplica idempotencia por UUID y procesa atómicamente en PostgreSQL Neon.
    """
    if not lote.eventos:
        return {
            "status": "ok",
            "mensaje": "Lote vacío, nada que sincronizar.",
            "procesados": 0,
            "duplicados": 0,
            "timestamp_sync": datetime.now(timezone.utc).isoformat(),
        }

    procesados = 0
    duplicados = 0
    errores = []

    # Validar que exista la tabla cola_eventos_sync en Neon
    with db.engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS cola_eventos_sync (
                id_evento UUID PRIMARY KEY,
                id_local BIGINT NOT NULL REFERENCES locales(id_local),
                tipo_evento VARCHAR(50) NOT NULL,
                payload JSONB NOT NULL,
                fecha_evento_local TIMESTAMPTZ NOT NULL,
                fecha_recepcion_nube TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                procesado BOOLEAN NOT NULL DEFAULT FALSE,
                error_detalle TEXT,
                resultado_proceso JSONB
            );
            """
        ))

    for ev in lote.eventos:
        # Validar formato UUID
        try:
            ev_uuid = str(uuid.UUID(ev.id_evento))
        except ValueError:
            errores.append({"id_evento": ev.id_evento, "error": "UUID inválido"})
            continue

        with db.engine.begin() as conn:
            # 1. Registrar en outbox del servidor con protección de duplicados
            insert_q = text(
                """
                INSERT INTO cola_eventos_sync 
                    (id_evento, id_local, tipo_evento, payload, fecha_evento_local, procesado)
                VALUES 
                    (:id_evento, :id_local, :tipo_evento, :payload, :fecha_local, FALSE)
                ON CONFLICT (id_evento) DO NOTHING
                RETURNING id_evento;
                """
            )
            inserted = conn.execute(
                insert_q,
                {
                    "id_evento": ev_uuid,
                    "id_local": lote.id_local,
                    "tipo_evento": ev.tipo_evento,
                    "payload": json.dumps(ev.payload),
                    "fecha_local": ev.fecha_local,
                }
            ).first()

            if not inserted:
                # Ya existía en la base de datos (idempotencia)
                duplicados += 1
                continue

        # 2. Procesar el evento según su tipo usando la lógica de negocio central
        try:
            if ev.tipo_evento == "PRODUCCION_RECETAS":
                orden_platos = {int(k): int(v) for k, v in ev.payload.get("orden_platos", {}).items()}
                turno = str(ev.payload.get("turno", "General"))
                obs = f"Sync Offline [{ev_uuid[:8]}]: {ev.payload.get('observaciones', '')}".strip()

                resultado = db.consumir_produccion_recetas(
                    id_local=lote.id_local,
                    orden_platos=orden_platos,
                    turno=turno,
                    observaciones=obs,
                )

                # Marcar evento como procesado
                with db.engine.begin() as conn:
                    conn.execute(
                        text(
                            """
                            UPDATE cola_eventos_sync
                            SET procesado = TRUE,
                                resultado_proceso = :res
                            WHERE id_evento = :id_evento
                            """
                        ),
                        {"id_evento": ev_uuid, "res": json.dumps({"status": "exito", "platos": len(orden_platos)})},
                    )
                procesados += 1

            elif ev.tipo_evento == "SALIDA_COCINA_MANUAL":
                id_lote = int(ev.payload["id_lote"])
                cantidad = float(ev.payload["cantidad"])
                obs = f"Sync Offline [{ev_uuid[:8]}]: {ev.payload.get('observaciones', '')}".strip()

                db.registrar_salida_cocina(
                    id_local=lote.id_local,
                    id_lote=id_lote,
                    cantidad=cantidad,
                    referencia="SALIDA_OFFLINE",
                    observaciones=obs,
                )

                with db.engine.begin() as conn:
                    conn.execute(
                        text(
                            """
                            UPDATE cola_eventos_sync
                            SET procesado = TRUE,
                                resultado_proceso = :res
                            WHERE id_evento = :id_evento
                            """
                        ),
                        {"id_evento": ev_uuid, "res": json.dumps({"status": "exito"})},
                    )
                procesados += 1

            elif ev.tipo_evento == "RECEPCION_MERCADERIA_OFFLINE":
                id_proveedor = int(ev.payload["id_proveedor"])
                id_producto = int(ev.payload["id_producto"])
                cantidad = float(ev.payload["cantidad"])
                codigo_lote = str(ev.payload.get("codigo_lote_proveedor", f"LOTE-OFFLINE-{ev_uuid[:6]}"))
                
                fecha_venc_raw = ev.payload.get("fecha_vencimiento")
                if fecha_venc_raw:
                    try:
                        fecha_venc = datetime.strptime(fecha_venc_raw[:10], "%Y-%m-%d").date()
                    except Exception:
                        fecha_venc = datetime.now().date() + timedelta(days=5)
                else:
                    fecha_venc = datetime.now().date() + timedelta(days=5)

                fecha_rec_raw = ev.payload.get("fecha_recepcion")
                if fecha_rec_raw:
                    try:
                        fecha_rec = datetime.strptime(fecha_rec_raw[:10], "%Y-%m-%d").date()
                    except Exception:
                        fecha_rec = datetime.now().date()
                else:
                    fecha_rec = datetime.now().date()

                temperatura = float(ev.payload.get("temperatura_recepcion", 2.0))
                tipo_doc = str(ev.payload.get("tipo_documento", "GUIA_DESPACHO"))
                num_doc = str(ev.payload.get("numero_documento", f"DOC-OFF-{ev_uuid[:8]}"))
                obs = f"Sync Offline KDS [{ev_uuid[:8]}]: {ev.payload.get('observaciones', '')}".strip()

                resultado_recepcion = db.registrar_recepcion_compra(
                    id_proveedor=id_proveedor,
                    id_local_receptor=lote.id_local,
                    tipo_documento=tipo_doc,
                    numero_documento=num_doc,
                    fecha_compra=fecha_rec,
                    fecha_recepcion=fecha_rec,
                    id_producto=id_producto,
                    cantidad=cantidad,
                    codigo_lote_proveedor=codigo_lote,
                    fecha_vencimiento=fecha_venc,
                    temperatura_recepcion=temperatura,
                    observaciones=obs,
                )

                with db.engine.begin() as conn:
                    conn.execute(
                        text(
                            """
                            UPDATE cola_eventos_sync
                            SET procesado = TRUE,
                                resultado_proceso = :res
                            WHERE id_evento = :id_evento
                            """
                        ),
                        {
                            "id_evento": ev_uuid,
                            "res": json.dumps({"status": "exito", "recepcion": resultado_recepcion}),
                        },
                    )
                procesados += 1

            else:
                errores.append({"id_evento": ev_uuid, "error": f"Tipo de evento no reconocido: {ev.tipo_evento}"})

        except Exception as ex:
            # Registrar el error sin que aborte la sincronización de los siguientes eventos
            with db.engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        UPDATE cola_eventos_sync
                        SET error_detalle = :err
                        WHERE id_evento = :id_evento
                        """
                    ),
                    {"id_evento": ev_uuid, "err": str(ex)},
                )
            errores.append({"id_evento": ev_uuid, "error": str(ex)})

    return {
        "status": "completado",
        "id_local": lote.id_local,
        "total_recibidos": len(lote.eventos),
        "procesados_exitosamente": procesados,
        "duplicados_ignorados": duplicados,
        "errores": errores,
        "timestamp_sync": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/eventos/{id_local}", tags=["Auditoría de Eventos"])
def get_eventos_recientes(id_local: int, limite: int = 20):
    """Consulta los últimos eventos recibidos y procesados para un local específico."""
    q = text(
        """
        SELECT 
            id_evento,
            tipo_evento,
            fecha_evento_local,
            fecha_recepcion_nube,
            procesado,
            error_detalle,
            resultado_proceso
        FROM cola_eventos_sync
        WHERE id_local = :id_local
        ORDER BY fecha_recepcion_nube DESC
        LIMIT :limite
        """
    )
    with db.engine.connect() as conn:
        res = conn.execute(q, {"id_local": id_local, "limite": limite}).mappings().all()

    return {
        "id_local": id_local,
        "total": len(res),
        "eventos": [dict(r) for r in res],
    }


# ==============================================================================
# MONTAJE DE LA TERMINAL DE COCINA PWA (CERO INSTALACIÓN)
# ==============================================================================
import os
pwa_dir = os.path.join(os.path.dirname(__file__), "pwa_cocina")
if os.path.exists(pwa_dir):
    app.mount("/cocina", StaticFiles(directory=pwa_dir, html=True), name="cocina")

@app.get("/terminal", tags=["Redirección"])
def redirect_terminal():
    """Acceso directo a la terminal de cocina."""
    return RedirectResponse(url="/cocina/")


# ==============================================================================
# EJECUCIÓN DIRECTA PARA DESARROLLO LOCAL
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    print("Iniciando Micro-API y PWA Mamá Qocha en puerto 8000 (disponible para PC y Tablets en red local)...")
    uvicorn.run("api_sync:app", host="0.0.0.0", port=8000, reload=True)
