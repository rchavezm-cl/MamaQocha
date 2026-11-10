-- ==============================================================================
-- MAMÁ QOCHA: ESQUEMA DE SOPORTE PARA SINCRONIZACIÓN OFFLINE (LOCAL-FIRST)
-- Archivo: sql/01_soporte_offline.sql
-- Propósito:
--   1. Habilitar identificación universal única (UUID) para idempotencia.
--   2. Crear tabla de eventos 'outbox' del servidor para ingesta por lotes.
--   3. Índices de alta velocidad para snapshot y consulta de pendientes.
-- ==============================================================================

BEGIN;

-- 1. Extensión para generación de UUIDs nativos en PostgreSQL (si no está activa)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Tabla para almacenar y auditar los lotes de eventos recibidos desde los locales
--    Garantiza el patrón Outbox en el servidor con trazabilidad de origen y recepción.
CREATE TABLE IF NOT EXISTS cola_eventos_sync (
    id_evento UUID PRIMARY KEY,
    id_local BIGINT NOT NULL REFERENCES locales(id_local),
    tipo_evento VARCHAR(50) NOT NULL, -- 'PRODUCCION_RECETAS', 'SALIDA_COCINA_MANUAL', 'MERMA'
    payload JSONB NOT NULL,            -- Estructura JSON original generada por el navegador
    fecha_evento_local TIMESTAMPTZ NOT NULL, -- Momento exacto en que ocurrió en la cocina física
    fecha_recepcion_nube TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    procesado BOOLEAN NOT NULL DEFAULT FALSE,
    error_detalle TEXT,
    resultado_proceso JSONB
);

-- 3. Agregar columna id_evento_origen en la tabla de movimientos para trazabilidad e idempotencia
--    Si el cliente reenvía una comanda por intermitencia de red, la restricción UNIQUE
--    impide duplicar el movimiento físico en el inventario.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'movimientos' AND column_name = 'id_evento_origen'
    ) THEN
        ALTER TABLE movimientos ADD COLUMN id_evento_origen UUID UNIQUE;
    END IF;
END $$;

-- 4. Índices para acelerar el procesamiento de lotes y consultas de auditoría
CREATE INDEX IF NOT EXISTS ix_cola_eventos_local_procesado 
    ON cola_eventos_sync (id_local, procesado);

CREATE INDEX IF NOT EXISTS ix_cola_eventos_fecha_local 
    ON cola_eventos_sync (fecha_evento_local DESC);

CREATE INDEX IF NOT EXISTS ix_movimientos_evento_origen 
    ON movimientos (id_evento_origen);

COMMIT;
