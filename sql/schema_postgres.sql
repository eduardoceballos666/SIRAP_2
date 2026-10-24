-- =============================================================================
-- SIRAP – Esquema PostgreSQL (producción)
-- Vehículos, propietarios, listas de autorización, garitas, usuarios e historial.
-- Ejecutar una vez:  psql "$PG_DSN" -f sql/schema_postgres.sql
-- =============================================================================

CREATE TABLE IF NOT EXISTS propietarios (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL,
    tipo            VARCHAR(20)  NOT NULL DEFAULT 'PERSONA'   -- PERSONA | EMPRESA
                    CHECK (tipo IN ('PERSONA', 'EMPRESA')),
    contacto        VARCHAR(120),                              -- dato mínimo necesario (minimización)
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vehiculos (
    placa           VARCHAR(8)   PRIMARY KEY,                  -- formato XXX-0000
    marca           VARCHAR(60),
    modelo          VARCHAR(60),
    color           VARCHAR(30),
    tipo            VARCHAR(30)  DEFAULT 'LIVIANO',            -- LIVIANO | CAMION | MOTO | OTRO
    propietario_id  INTEGER      REFERENCES propietarios(id) ON DELETE SET NULL,
    transportista   VARCHAR(120),
    fuente          VARCHAR(20)  NOT NULL DEFAULT 'MANUAL',    -- MANUAL | SRI | ANT | IMPORTACION
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    actualizado_en  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Lista blanca (autorizados) y lista restringida (bloqueados) con vigencia.
CREATE TABLE IF NOT EXISTS autorizaciones (
    id              SERIAL PRIMARY KEY,
    placa           VARCHAR(8)   NOT NULL REFERENCES vehiculos(placa) ON DELETE CASCADE,
    lista           VARCHAR(12)  NOT NULL CHECK (lista IN ('BLANCA', 'RESTRINGIDA')),
    motivo          VARCHAR(200),
    vigente_desde   DATE         NOT NULL DEFAULT CURRENT_DATE,
    vigente_hasta   DATE,                                       -- NULL = sin vencimiento
    activa          BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_por      VARCHAR(60),
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_autorizaciones_placa ON autorizaciones(placa) WHERE activa;

CREATE TABLE IF NOT EXISTS garitas (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(60)  NOT NULL UNIQUE,
    ubicacion       VARCHAR(120),
    activa          BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS usuarios (
    id              SERIAL PRIMARY KEY,
    usuario         VARCHAR(40)  NOT NULL UNIQUE,
    nombre          VARCHAR(120) NOT NULL,
    rol             VARCHAR(20)  NOT NULL CHECK (rol IN ('OPERADOR', 'SUPERVISOR', 'ADMINISTRADOR')),
    activo          BOOLEAN      NOT NULL DEFAULT TRUE
);

-- Historial y auditoría: una fila por operación (append-only; no se actualiza ni se borra).
CREATE TABLE IF NOT EXISTS operaciones (
    id              BIGSERIAL PRIMARY KEY,
    fecha_hora      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    garita          VARCHAR(60)  NOT NULL,
    operador        VARCHAR(120) NOT NULL,
    tipo_movimiento VARCHAR(10)  NOT NULL CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA')),
    placa_leida     VARCHAR(16),                               -- lo que devolvió el OCR
    placa_final     VARCHAR(8),                                -- placa normalizada / corregida por el operador
    confianza_ocr   REAL,
    resultado       VARCHAR(30)  NOT NULL,                     -- AUTORIZADO | DENEGADO | NO_REGISTRADO | VERIFICACION_MANUAL
    lista           VARCHAR(12),
    accion          VARCHAR(30)  NOT NULL,                     -- APERTURA_AUTOMATICA | APERTURA_MANUAL | SOLO_REGISTRO | RECHAZO
    motivo          VARCHAR(250),
    origen          VARCHAR(20)  NOT NULL DEFAULT 'DETECCION', -- DETECCION | MANUAL
    tiempo_ms       INTEGER
);
CREATE INDEX IF NOT EXISTS ix_operaciones_fecha ON operaciones(fecha_hora DESC);
CREATE INDEX IF NOT EXISTS ix_operaciones_placa ON operaciones(placa_final);
