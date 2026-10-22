-- ============================================================
-- Mamá Qocha - Dataset inicial de pruebas (solo origen animal)
-- Compatible con schema.sql en PostgreSQL 18.
-- Datos completamente ficticios.
--
-- Incluye únicamente vacuno, cerdo, pollo y pescados/mariscos.
-- No incluye verduras, lácteos ni otros productos no cárnicos.
--
-- Carga: locales, proveedores, productos, usuario de referencia,
-- compras, detalles de compra, lotes y stock inicial.
-- No carga movimientos: primero se validará el inventario inicial.
-- ============================================================

BEGIN;

-- 1. Cinco locales ficticios
INSERT INTO locales (nombre, direccion, activo)
VALUES
 ('Local 1 - Centro', 'Dirección ficticia 101', TRUE),
 ('Local 2 - Norte', 'Dirección ficticia 202', TRUE),
 ('Local 3 - Sur', 'Dirección ficticia 303', TRUE),
 ('Local 4 - Oriente', 'Dirección ficticia 404', TRUE),
 ('Local 5 - Poniente', 'Dirección ficticia 505', TRUE)
ON CONFLICT (nombre) DO UPDATE
SET direccion = EXCLUDED.direccion, activo = EXCLUDED.activo;

-- 2. Proveedores ficticios. Identificadores TEST, no RUT reales.
INSERT INTO proveedores (nombre, rut, telefono, correo, direccion, activo)
VALUES
 ('Distribuidora Vacuno Demo', 'TEST-PRV-001', '+56 9 0000 0001', 'vacuno.demo@example.invalid', 'Dirección ficticia proveedor 1', TRUE),
 ('Carnes de Cerdo Demo', 'TEST-PRV-002', '+56 9 0000 0002', 'cerdo.demo@example.invalid', 'Dirección ficticia proveedor 2', TRUE),
 ('Avícola Demo', 'TEST-PRV-003', '+56 9 0000 0003', 'pollo.demo@example.invalid', 'Dirección ficticia proveedor 3', TRUE),
 ('Pescados y Mariscos Demo', 'TEST-PRV-004', '+56 9 0000 0004', 'mariscos.demo@example.invalid', 'Dirección ficticia proveedor 4', TRUE)
ON CONFLICT (rut) DO UPDATE
SET nombre = EXCLUDED.nombre,
    telefono = EXCLUDED.telefono,
    correo = EXCLUDED.correo,
    direccion = EXCLUDED.direccion,
    activo = EXCLUDED.activo;

-- 3. Catálogo de materias primas exclusivamente de origen animal
INSERT INTO productos (nombre, descripcion, unidad_medida, activo)
VALUES
 ('Lomo vetado', 'Corte de vacuno de prueba.', 'kg', TRUE),
 ('Sobrecostilla', 'Corte de vacuno de prueba.', 'kg', TRUE),
 ('Posta rosada', 'Corte de vacuno de prueba.', 'kg', TRUE),
 ('Pulpa de cerdo', 'Corte de cerdo de prueba.', 'kg', TRUE),
 ('Pechuga de pollo', 'Materia prima avícola de prueba.', 'kg', TRUE),
 ('Trutro de pollo', 'Materia prima avícola de prueba.', 'kg', TRUE),
 ('Atún', 'Pescado de prueba.', 'kg', TRUE),
 ('Camarón', 'Marisco de prueba.', 'kg', TRUE),
 ('Reineta', 'Pescado de prueba.', 'kg', TRUE)
ON CONFLICT (nombre) DO UPDATE
SET descripcion = EXCLUDED.descripcion,
    unidad_medida = EXCLUDED.unidad_medida,
    activo = EXCLUDED.activo;

-- 4. Usuario de referencia sin contraseña configurada.
-- No habilita autenticación; los permisos se desarrollarán después.
INSERT INTO usuarios (nombre, nombre_usuario, hash_password, rol, id_local, activo)
VALUES ('Administrador de prueba', 'admin_demo', NULL, 'administrador', NULL, TRUE)
ON CONFLICT (nombre_usuario) DO UPDATE
SET nombre = EXCLUDED.nombre, rol = EXCLUDED.rol, activo = EXCLUDED.activo;

-- 5. Compras ficticias, una por local, con múltiples productos cárnicos.
INSERT INTO compras
 (id_proveedor, id_local_receptor, tipo_documento, numero_documento,
  fecha_compra, fecha_recepcion, observaciones)
SELECT p.id_proveedor, l.id_local, 'factura', x.numero_documento,
       x.fecha_compra, x.fecha_recepcion, 'Compra ficticia para pruebas de Mamá Qocha'
FROM (VALUES
 ('TEST-PRV-001', 'Local 1 - Centro',   'DEMO-F001', DATE '2026-10-10', DATE '2026-10-11'),
 ('TEST-PRV-002', 'Local 2 - Norte',    'DEMO-F002', DATE '2026-10-12', DATE '2026-10-12'),
 ('TEST-PRV-004', 'Local 3 - Sur',      'DEMO-F003', DATE '2026-10-14', DATE '2026-10-15'),
 ('TEST-PRV-001', 'Local 4 - Oriente',  'DEMO-F004', DATE '2026-10-16', DATE '2026-10-16'),
 ('TEST-PRV-003', 'Local 5 - Poniente', 'DEMO-F005', DATE '2026-10-18', DATE '2026-10-19')
) AS x(rut_proveedor, nombre_local, numero_documento, fecha_compra, fecha_recepcion)
JOIN proveedores p ON p.rut = x.rut_proveedor
JOIN locales l ON l.nombre = x.nombre_local
ON CONFLICT (id_proveedor, tipo_documento, numero_documento) DO UPDATE
SET id_local_receptor = EXCLUDED.id_local_receptor,
    fecha_compra = EXCLUDED.fecha_compra,
    fecha_recepcion = EXCLUDED.fecha_recepcion,
    observaciones = EXCLUDED.observaciones;

-- 6. Detalles de compra: las cantidades son coherentes con los lotes de abajo.
INSERT INTO detalle_compra (id_compra, id_producto, cantidad_recibida, costo_unitario, observaciones)
SELECT c.id_compra, p.id_producto, x.cantidad, x.costo, 'Línea ficticia de prueba'
FROM (VALUES
 ('DEMO-F001', 'Lomo vetado',      15.000::numeric, 8900.00::numeric),
 ('DEMO-F001', 'Sobrecostilla',    20.000::numeric, 7600.00::numeric),
 ('DEMO-F001', 'Atún',             20.000::numeric, 5200.00::numeric),

 ('DEMO-F002', 'Pulpa de cerdo',   18.000::numeric, 6100.00::numeric),
 ('DEMO-F002', 'Pechuga de pollo', 16.000::numeric, 4300.00::numeric),
 ('DEMO-F002', 'Sobrecostilla',    12.000::numeric, 7500.00::numeric),

 ('DEMO-F003', 'Camarón',          10.000::numeric, 7800.00::numeric),
 ('DEMO-F003', 'Reineta',          14.000::numeric, 4900.00::numeric),
 ('DEMO-F003', 'Atún',             12.000::numeric, 5300.00::numeric),

 ('DEMO-F004', 'Lomo vetado',      22.000::numeric, 9000.00::numeric),
 ('DEMO-F004', 'Trutro de pollo',  18.000::numeric, 3900.00::numeric),
 ('DEMO-F004', 'Pulpa de cerdo',   10.000::numeric, 6200.00::numeric),

 ('DEMO-F005', 'Posta rosada',     18.000::numeric, 7200.00::numeric),
 ('DEMO-F005', 'Pechuga de pollo', 16.000::numeric, 4250.00::numeric),
 ('DEMO-F005', 'Reineta',          10.000::numeric, 4950.00::numeric)
) AS x(numero_documento, nombre_producto, cantidad, costo)
JOIN compras c ON c.numero_documento = x.numero_documento
JOIN productos p ON p.nombre = x.nombre_producto
ON CONFLICT (id_compra, id_producto) DO UPDATE
SET cantidad_recibida = EXCLUDED.cantidad_recibida,
    costo_unitario = EXCLUDED.costo_unitario,
    observaciones = EXCLUDED.observaciones;

-- 7. Lotes. Se incluyen distintos lotes con igual vencimiento para probar trazabilidad.
INSERT INTO lotes
 (id_detalle_compra, codigo_lote_proveedor, cantidad_inicial, fecha_vencimiento, fecha_recepcion)
SELECT dc.id_detalle_compra, x.codigo_lote, x.cantidad, x.vencimiento, c.fecha_recepcion
FROM (VALUES
 ('DEMO-F001', 'Lomo vetado',      'LV-101-A', 15.000::numeric, DATE '2026-11-05'),
 ('DEMO-F001', 'Sobrecostilla',    'SC-101-A',  4.000::numeric, DATE '2026-10-25'),
 ('DEMO-F001', 'Sobrecostilla',    'SC-101-B', 16.000::numeric, DATE '2026-10-25'),
 ('DEMO-F001', 'Atún',             'AT-101-A', 12.000::numeric, DATE '2026-11-15'),
 ('DEMO-F001', 'Atún',             'AT-101-B',  8.000::numeric, DATE '2026-11-15'),

 ('DEMO-F002', 'Pulpa de cerdo',   'PC-201-A', 10.000::numeric, DATE '2026-11-02'),
 ('DEMO-F002', 'Pulpa de cerdo',   'PC-201-B',  8.000::numeric, DATE '2026-11-02'),
 ('DEMO-F002', 'Pechuga de pollo', 'PP-201-A', 16.000::numeric, DATE '2026-10-29'),
 ('DEMO-F002', 'Sobrecostilla',    'SC-201-A', 12.000::numeric, DATE '2026-11-08'),

 ('DEMO-F003', 'Camarón',          'CA-301-A', 10.000::numeric, DATE '2026-10-30'),
 ('DEMO-F003', 'Reineta',          'RE-301-A', 14.000::numeric, DATE '2026-11-06'),
 ('DEMO-F003', 'Atún',             'AT-301-A', 12.000::numeric, DATE '2026-11-20'),

 ('DEMO-F004', 'Lomo vetado',      'LV-401-A', 12.000::numeric, DATE '2026-11-12'),
 ('DEMO-F004', 'Lomo vetado',      'LV-401-B', 10.000::numeric, DATE '2026-11-12'),
 ('DEMO-F004', 'Trutro de pollo',  'TP-401-A', 18.000::numeric, DATE '2026-11-01'),
 ('DEMO-F004', 'Pulpa de cerdo',   'PC-401-A', 10.000::numeric, DATE '2026-11-10'),

 ('DEMO-F005', 'Posta rosada',     'PR-501-A',  8.000::numeric, DATE '2026-10-27'),
 ('DEMO-F005', 'Posta rosada',     'PR-501-B', 10.000::numeric, DATE '2026-11-10'),
 ('DEMO-F005', 'Pechuga de pollo', 'PP-501-A', 16.000::numeric, DATE '2026-11-03'),
 ('DEMO-F005', 'Reineta',          'RE-501-A', 10.000::numeric, DATE '2026-11-09')
) AS x(numero_documento, nombre_producto, codigo_lote, cantidad, vencimiento)
JOIN compras c ON c.numero_documento = x.numero_documento
JOIN detalle_compra dc ON dc.id_compra = c.id_compra
JOIN productos p ON p.id_producto = dc.id_producto AND p.nombre = x.nombre_producto
ON CONFLICT (id_detalle_compra, codigo_lote_proveedor) DO UPDATE
SET cantidad_inicial = EXCLUDED.cantidad_inicial,
    fecha_vencimiento = EXCLUDED.fecha_vencimiento,
    fecha_recepcion = EXCLUDED.fecha_recepcion;

-- 8. Stock inicial por lote y local receptor.
INSERT INTO stock_lote_local (id_lote, id_local, cantidad)
SELECT lo.id_lote, c.id_local_receptor, lo.cantidad_inicial
FROM lotes lo
JOIN detalle_compra dc ON dc.id_detalle_compra = lo.id_detalle_compra
JOIN compras c ON c.id_compra = dc.id_compra
ON CONFLICT (id_lote, id_local) DO UPDATE
SET cantidad = EXCLUDED.cantidad,
    actualizado_en = CURRENT_TIMESTAMP;

COMMIT;

-- Consultas de verificación (ejecutar por separado):
-- SELECT COUNT(*) AS locales FROM locales;
-- SELECT COUNT(*) AS proveedores FROM proveedores;
-- SELECT COUNT(*) AS productos FROM productos;
-- SELECT COUNT(*) AS compras FROM compras;
-- SELECT COUNT(*) AS lotes FROM lotes;
-- SELECT l.nombre AS local, p.nombre AS producto, lo.codigo_lote_proveedor,
--        lo.fecha_vencimiento, s.cantidad
-- FROM stock_lote_local s
-- JOIN lotes lo ON lo.id_lote = s.id_lote
-- JOIN detalle_compra dc ON dc.id_detalle_compra = lo.id_detalle_compra
-- JOIN productos p ON p.id_producto = dc.id_producto
-- JOIN locales l ON l.id_local = s.id_local
-- ORDER BY l.nombre, p.nombre, lo.fecha_vencimiento;
