-- =============================================================================
-- SIRAP – Esquema SQLite (modo demostración / Streamlit Cloud)
-- Mismo modelo de datos que sql/schema_postgres.sql con tipos de SQLite.
-- =============================================================================
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS propietarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    tipo            TEXT NOT NULL DEFAULT 'PERSONA' CHECK (tipo IN ('PERSONA', 'EMPRESA')),
    contacto        TEXT,
    creado_en       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS vehiculos (
    placa           TEXT PRIMARY KEY,
    marca           TEXT,
    modelo          TEXT,
    color           TEXT,
    tipo            TEXT DEFAULT 'LIVIANO',
    propietario_id  INTEGER REFERENCES propietarios(id) ON DELETE SET NULL,
    transportista   TEXT,
    fuente          TEXT NOT NULL DEFAULT 'MANUAL',
    creado_en       TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS autorizaciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    placa           TEXT NOT NULL REFERENCES vehiculos(placa) ON DELETE CASCADE,
    lista           TEXT NOT NULL CHECK (lista IN ('BLANCA', 'RESTRINGIDA')),
    motivo          TEXT,
    vigente_desde   TEXT NOT NULL DEFAULT (date('now')),
    vigente_hasta   TEXT,
    activa          INTEGER NOT NULL DEFAULT 1,
    creado_por      TEXT,
    creado_en       TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_autorizaciones_placa ON autorizaciones(placa);

CREATE TABLE IF NOT EXISTS garitas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    ubicacion       TEXT,
    activa          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario         TEXT NOT NULL UNIQUE,
    nombre          TEXT NOT NULL,
    rol             TEXT NOT NULL CHECK (rol IN ('OPERADOR', 'SUPERVISOR', 'ADMINISTRADOR')),
    activo          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS operaciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora      TEXT NOT NULL,
    garita          TEXT NOT NULL,
    operador        TEXT NOT NULL,
    tipo_movimiento TEXT NOT NULL CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA')),
    placa_leida     TEXT,
    placa_final     TEXT,
    confianza_ocr   REAL,
    resultado       TEXT NOT NULL,
    lista           TEXT,
    accion          TEXT NOT NULL,
    motivo          TEXT,
    origen          TEXT NOT NULL DEFAULT 'DETECCION',
    tiempo_ms       INTEGER
);
CREATE INDEX IF NOT EXISTS ix_operaciones_fecha ON operaciones(fecha_hora);
CREATE INDEX IF NOT EXISTS ix_operaciones_placa ON operaciones(placa_final);
