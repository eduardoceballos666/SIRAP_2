-- =============================================================================
-- SIRAP – Datos de DEMOSTRACIÓN (ficticios).
-- Nombres, placas y vehículos son inventados para probar la interfaz; no
-- corresponden a personas reales ni a autorizaciones de producción. Compatible con
-- SQLite y PostgreSQL.
-- =============================================================================

INSERT INTO propietarios (nombre, tipo, contacto) VALUES
  ('Juan Pérez',                 'PERSONA', 'residente Mz. 4'),
  ('Transportes Andinos S.A.',   'EMPRESA', 'logistica@ejemplo.ec'),
  ('María López',                'PERSONA', 'residente Mz. 9'),
  ('Distribuidora del Pacífico', 'EMPRESA', 'despacho@ejemplo.ec'),
  ('Carlos Mendoza',             'PERSONA', 'visitante frecuente');

INSERT INTO vehiculos (placa, marca, modelo, color, tipo, propietario_id, transportista, fuente) VALUES
  ('PBA-8901', 'Toyota',    'Camioneta',  'Gris',   'LIVIANO', 1, NULL,                         'MANUAL'),
  ('GBO-0429', 'Hino',      '500 GH',     'Blanco', 'CAMION',  2, 'Transportes Andinos S.A.',   'MANUAL'),
  ('GSB-4512', 'Chevrolet', 'D-Max',      'Rojo',   'LIVIANO', 3, NULL,                         'MANUAL'),
  ('PCD-5678', 'Kia',       'Sportage',   'Negro',  'LIVIANO', 3, NULL,                         'MANUAL'),
  ('GTH-2210', 'Isuzu',     'NPR',        'Blanco', 'CAMION',  4, 'Distribuidora del Pacífico', 'MANUAL'),
  ('MBC-7781', 'Hyundai',   'Tucson',     'Azul',   'LIVIANO', 5, NULL,                         'MANUAL');

INSERT INTO autorizaciones (placa, lista, motivo, creado_por) VALUES
  ('PBA-8901', 'BLANCA',      'Residente',                                   'admin'),
  ('GSB-4512', 'BLANCA',      'Residente',                                   'admin'),
  ('PCD-5678', 'BLANCA',      'Residente',                                   'admin'),
  ('GTH-2210', 'BLANCA',      'Proveedor con contrato vigente',              'admin'),
  ('MBC-7781', 'BLANCA',      'Visitante frecuente',                         'admin'),
  ('GBO-0429', 'RESTRINGIDA', 'Acceso suspendido por la administración',     'admin');

INSERT INTO garitas (nombre, ubicacion) VALUES
  ('Garita 1', 'Ingreso principal'),
  ('Garita 2', 'Ingreso de carga'),
  ('Garita 3', 'Ingreso residentes');

INSERT INTO usuarios (usuario, nombre, rol) VALUES
  ('operador',   'Operador de garita', 'OPERADOR'),
  ('supervisor', 'Supervisor de turno', 'SUPERVISOR'),
  ('admin',      'Administrador SIRAP', 'ADMINISTRADOR');
