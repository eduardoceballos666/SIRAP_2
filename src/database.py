"""Acceso a datos de SIRAP: vehículos, propietarios, listas, garitas, usuarios e historial.

Dos motores con el mismo esquema (``sql/``):

* **PostgreSQL** (producción): se usa si existe el secreto ``PG_DSN``. Requiere ``psycopg``.
* **SQLite** (demostración): se crea sola en ``data/processed/sirap_demo.db`` con los datos
  ficticios de ``sql/seed_demo.sql``. Es lo que corre en Streamlit Community Cloud.

Todas las consultas usan parámetros (nunca concatenación de texto) para evitar inyección SQL.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator, Sequence

import pandas as pd

from src.utils import get_logger, get_secret, load_config, now_local, resolve_path

logger = get_logger("sirap.database")

RESULTADOS = ("AUTORIZADO", "DENEGADO", "NO_REGISTRADO", "VERIFICACION_MANUAL")
ACCIONES = ("APERTURA_AUTOMATICA", "APERTURA_MANUAL", "SOLO_REGISTRO", "RECHAZO")


class DatabaseError(RuntimeError):
    """Error al leer o escribir en la base de datos."""


class Database:
    """Repositorio de datos con la misma API para SQLite y PostgreSQL.

    Args:
        dsn: cadena de conexión de PostgreSQL. Si es ``None`` se usa SQLite.
        sqlite_path: archivo SQLite (modo demostración).
        seed: cargar los datos de demostración si la base está vacía.
    """

    def __init__(self, dsn: str | None = None, sqlite_path: str | Path | None = None, seed: bool = True):
        cfg = load_config()["base_datos"]
        self.dsn = dsn
        self.engine = "postgresql" if dsn else "sqlite"
        self._lock = threading.Lock()
        if self.engine == "sqlite":
            self.sqlite_path = resolve_path(sqlite_path or cfg["ruta_sqlite"])
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema(resolve_path(cfg[f"esquema_{'postgres' if dsn else 'sqlite'}"]),
                          resolve_path(cfg["datos_demo"]) if seed else None)

    @classmethod
    def from_environment(cls, **kwargs: Any) -> "Database":
        """Usa PostgreSQL si hay ``PG_DSN``; si no, SQLite de demostración."""
        dsn = get_secret("PG_DSN")
        if dsn:
            try:
                return cls(dsn=dsn, **kwargs)
            except DatabaseError as exc:
                logger.error("PostgreSQL no disponible (%s); se usa SQLite de demostración.", exc)
        return cls(**kwargs)

    # -- conexión ----------------------------------------------------------------------------
    @contextmanager
    def connect(self) -> Iterator[Any]:
        """Conexión con commit automático y rollback ante errores."""
        try:
            if self.engine == "postgresql":
                import psycopg  # type: ignore

                conn = psycopg.connect(self.dsn, connect_timeout=5)
            else:
                conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
                conn.execute("PRAGMA foreign_keys = ON")
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(f"No se pudo conectar a la base ({self.engine}): {exc}") from exc
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _sql(self, query: str) -> str:
        """Adapta los parámetros ``?`` de SQLite al ``%s`` de psycopg."""
        return query.replace("?", "%s") if self.engine == "postgresql" else query

    def execute(self, query: str, params: Sequence[Any] = ()) -> int:
        """Ejecuta una sentencia de escritura y devuelve las filas afectadas."""
        with self._lock, self.connect() as conn:
            try:
                cur = conn.execute(self._sql(query), tuple(params))
                return cur.rowcount
            except Exception as exc:  # noqa: BLE001
                raise DatabaseError(str(exc)) from exc

    def query(self, query: str, params: Sequence[Any] = ()) -> pd.DataFrame:
        """Ejecuta una consulta y devuelve un ``DataFrame``."""
        with self.connect() as conn:
            try:
                cur = conn.execute(self._sql(query), tuple(params))
                columns = [c[0] for c in cur.description] if cur.description else []
                return pd.DataFrame(cur.fetchall(), columns=columns)
            except Exception as exc:  # noqa: BLE001
                raise DatabaseError(str(exc)) from exc

    def _init_schema(self, schema_file: Path, seed_file: Path | None) -> None:
        """Crea las tablas si no existen y carga los datos de demostración en una base vacía."""
        with self._lock, self.connect() as conn:
            script = schema_file.read_text(encoding="utf-8")
            if self.engine == "sqlite":
                conn.executescript(script)
            else:
                conn.execute(script)
            count = conn.execute("SELECT COUNT(*) FROM vehiculos").fetchone()[0]
            if seed_file and count == 0:
                seed = seed_file.read_text(encoding="utf-8")
                if self.engine == "sqlite":
                    conn.executescript(seed)
                else:
                    conn.execute(seed)
                logger.info("Base %s inicializada con datos de demostración.", self.engine)

    # -- consultas de negocio ----------------------------------------------------------------
    def get_vehicle(self, placa: str) -> dict[str, Any] | None:
        """Datos del vehículo, su propietario y su autorización vigente (o ``None``)."""
        df = self.query(
            """
            SELECT v.placa, v.marca, v.modelo, v.color, v.tipo, v.transportista,
                   p.nombre AS propietario, p.tipo AS tipo_propietario
            FROM vehiculos v LEFT JOIN propietarios p ON p.id = v.propietario_id
            WHERE v.placa = ?
            """, (placa,))
        if df.empty:
            return None
        vehicle = df.iloc[0].to_dict()
        vehicle["autorizacion"] = self.get_authorization(placa)
        return vehicle

    def get_authorization(self, placa: str, on: date | None = None) -> dict[str, Any] | None:
        """Autorización activa y vigente de la placa. La lista RESTRINGIDA tiene prioridad."""
        today = (on or now_local().date()).isoformat()
        df = self.query(
            """
            SELECT lista, motivo, vigente_desde, vigente_hasta FROM autorizaciones
            WHERE placa = ? AND activa = ? AND vigente_desde <= ?
              AND (vigente_hasta IS NULL OR vigente_hasta >= ?)
            ORDER BY CASE lista WHEN 'RESTRINGIDA' THEN 0 ELSE 1 END
            """, (placa, True, today, today))
        return None if df.empty else {k: (str(v) if v is not None else None)
                                      for k, v in df.iloc[0].to_dict().items()}

    def registered_plates(self) -> list[str]:
        """Todas las placas registradas (para buscar coincidencias aproximadas)."""
        return self.query("SELECT placa FROM vehiculos")["placa"].tolist()

    def log_operation(self, *, garita: str, operador: str, tipo_movimiento: str, resultado: str,
                      accion: str, placa_leida: str | None = None, placa_final: str | None = None,
                      confianza_ocr: float | None = None, lista: str | None = None,
                      motivo: str | None = None, origen: str = "DETECCION",
                      tiempo_ms: float | None = None, fecha_hora: datetime | None = None) -> None:
        """Registra una operación en el historial (solo inserción: el historial no se edita).

        Raises:
            ValueError: si el resultado, la acción o el movimiento no son válidos.
        """
        tipo_movimiento = tipo_movimiento.upper()
        if tipo_movimiento not in ("ENTRADA", "SALIDA"):
            raise ValueError("tipo_movimiento debe ser ENTRADA o SALIDA")
        if resultado not in RESULTADOS:
            raise ValueError(f"resultado inválido: {resultado}")
        if accion not in ACCIONES:
            raise ValueError(f"acción inválida: {accion}")
        if accion == "APERTURA_MANUAL" and not (motivo and motivo.strip()):
            raise ValueError("La apertura manual exige un motivo.")
        stamp = (fecha_hora or now_local()).isoformat(sep=" ", timespec="seconds")
        self.execute(
            """
            INSERT INTO operaciones (fecha_hora, garita, operador, tipo_movimiento, placa_leida, placa_final,
                                     confianza_ocr, resultado, lista, accion, motivo, origen, tiempo_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (stamp, garita, operador, tipo_movimiento, placa_leida, placa_final,
             None if confianza_ocr is None else float(confianza_ocr), resultado, lista, accion,
             motivo, origen, None if tiempo_ms is None else int(tiempo_ms)))
        logger.info("Operación registrada: %s %s %s %s %s", garita, tipo_movimiento, placa_final, resultado, accion)

    def operations(self, desde: date | None = None, hasta: date | None = None, placa: str | None = None,
                   garita: str | None = None, resultado: str | None = None,
                   tipo_movimiento: str | None = None, limit: int = 5000) -> pd.DataFrame:
        """Historial filtrado, del más reciente al más antiguo."""
        conditions, params = [], []
        if desde:
            conditions.append("fecha_hora >= ?"); params.append(f"{desde.isoformat()} 00:00:00")
        if hasta:
            conditions.append("fecha_hora <= ?"); params.append(f"{hasta.isoformat()} 23:59:59")
        if placa:
            conditions.append("UPPER(COALESCE(placa_final, placa_leida, '')) LIKE ?")
            params.append(f"%{placa.upper().strip()}%")
        if garita:
            conditions.append("garita = ?"); params.append(garita)
        if resultado:
            conditions.append("resultado = ?"); params.append(resultado)
        if tipo_movimiento:
            conditions.append("tipo_movimiento = ?"); params.append(tipo_movimiento.upper())
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        df = self.query(f"SELECT * FROM operaciones {where} ORDER BY fecha_hora DESC, id DESC LIMIT {int(limit)}",
                        params)
        if not df.empty:
            df["fecha_hora"] = pd.to_datetime(df["fecha_hora"].astype(str), errors="coerce")
        return df

    # -- administración ----------------------------------------------------------------------
    def table(self, name: str) -> pd.DataFrame:
        """Contenido de una tabla de administración."""
        queries = {
            "vehiculos": """SELECT v.placa, v.marca, v.modelo, v.color, v.tipo, p.nombre AS propietario,
                                   v.transportista, v.fuente FROM vehiculos v
                            LEFT JOIN propietarios p ON p.id = v.propietario_id ORDER BY v.placa""",
            "propietarios": "SELECT id, nombre, tipo, contacto FROM propietarios ORDER BY nombre",
            "autorizaciones": """SELECT id, placa, lista, motivo, vigente_desde, vigente_hasta, activa, creado_por
                                 FROM autorizaciones WHERE activa = ? ORDER BY placa, lista""",
            "garitas": "SELECT id, nombre, ubicacion, activa FROM garitas ORDER BY nombre",
            "usuarios": "SELECT id, usuario, nombre, rol, activo FROM usuarios ORDER BY usuario",
        }
        if name not in queries:
            raise ValueError(f"Tabla desconocida: {name}")
        return self.query(queries[name], (True,)) if name == "autorizaciones" else self.query(queries[name])

    def garitas(self) -> list[str]:
        """Nombres de las garitas activas."""
        return self.query("SELECT nombre FROM garitas WHERE activa = ? ORDER BY nombre", (True,))["nombre"].tolist()

    def upsert_owner(self, nombre: str, tipo: str = "PERSONA", contacto: str | None = None) -> int:
        """Crea el propietario si no existe y devuelve su ``id``."""
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre del propietario es obligatorio.")
        found = self.query("SELECT id FROM propietarios WHERE nombre = ?", (nombre,))
        if not found.empty:
            return int(found.iloc[0]["id"])
        self.execute("INSERT INTO propietarios (nombre, tipo, contacto) VALUES (?, ?, ?)",
                     (nombre, tipo, contacto))
        return int(self.query("SELECT id FROM propietarios WHERE nombre = ?", (nombre,)).iloc[0]["id"])

    def upsert_vehicle(self, placa: str, marca: str = "", modelo: str = "", color: str = "",
                       tipo: str = "LIVIANO", propietario: str | None = None,
                       transportista: str | None = None) -> None:
        """Crea o actualiza un vehículo (la placa debe venir normalizada)."""
        owner_id = self.upsert_owner(propietario) if propietario else None
        exists = not self.query("SELECT 1 FROM vehiculos WHERE placa = ?", (placa,)).empty
        if exists:
            self.execute("""UPDATE vehiculos SET marca = ?, modelo = ?, color = ?, tipo = ?, propietario_id = ?,
                            transportista = ?, actualizado_en = ? WHERE placa = ?""",
                         (marca, modelo, color, tipo, owner_id, transportista,
                          now_local().isoformat(sep=" ", timespec="seconds"), placa))
        else:
            self.execute("""INSERT INTO vehiculos (placa, marca, modelo, color, tipo, propietario_id, transportista)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                         (placa, marca, modelo, color, tipo, owner_id, transportista))

    def set_authorization(self, placa: str, lista: str, motivo: str = "", hasta: date | None = None,
                          usuario: str = "admin") -> None:
        """Desactiva las autorizaciones anteriores de la placa y crea una nueva en ``lista``."""
        if lista not in ("BLANCA", "RESTRINGIDA"):
            raise ValueError("lista debe ser BLANCA o RESTRINGIDA")
        if self.query("SELECT 1 FROM vehiculos WHERE placa = ?", (placa,)).empty:
            raise ValueError(f"La placa {placa} no está registrada.")
        self.execute("UPDATE autorizaciones SET activa = ? WHERE placa = ?", (False, placa))
        self.execute("""INSERT INTO autorizaciones (placa, lista, motivo, vigente_hasta, creado_por)
                        VALUES (?, ?, ?, ?, ?)""",
                     (placa, lista, motivo, hasta.isoformat() if hasta else None, usuario))

    def update_authorization(self, placa: str, lista: str, motivo: str, hasta: date,
                            usuario: str = "admin") -> None:
        """Actualiza en el mismo registro la autorización existente, sin insertar otra fila."""
        if lista not in ("BLANCA", "RESTRINGIDA"):
            raise ValueError("lista debe ser BLANCA o RESTRINGIDA")
        if not motivo.strip():
            raise ValueError("El motivo es obligatorio.")
        rows = self.query("SELECT id FROM autorizaciones WHERE placa = ? AND activa = ? ORDER BY id DESC",
                          (placa, True))
        if rows.empty:
            rows = self.query("SELECT id FROM autorizaciones WHERE placa = ? ORDER BY id DESC LIMIT 1",
                              (placa,))
        if rows.empty:
            raise ValueError(f"La placa {placa} no tiene un registro de autorización para actualizar.")
        auth_id = int(rows.iloc[0]["id"])
        self.execute("UPDATE autorizaciones SET activa = ? WHERE placa = ? AND activa = ?", (False, placa, True))
        self.execute("""UPDATE autorizaciones
                        SET lista = ?, motivo = ?, vigente_desde = ?, vigente_hasta = ?, activa = ?, creado_por = ?
                        WHERE id = ?""",
                     (lista, motivo.strip(), now_local().date().isoformat(),
                      hasta.isoformat() if hasta else None, True, usuario, auth_id))

    def revoke_authorization(self, placa: str) -> None:
        """Quita la placa de cualquier lista (queda NO REGISTRADO para el control de acceso)."""
        self.execute("UPDATE autorizaciones SET activa = ? WHERE placa = ?", (False, placa))

    def add_garita(self, nombre: str, ubicacion: str) -> None:
        """Agrega una garita con nombre y ubicación obligatorios."""
        nombre, ubicacion = nombre.strip(), ubicacion.strip()
        if not nombre or not ubicacion:
            raise ValueError("El nombre y la ubicación de la garita son obligatorios.")
        self.execute("INSERT INTO garitas (nombre, ubicacion) VALUES (?, ?)", (nombre, ubicacion))

    def load_demo_history(self, n: int = 120, days: int = 7, seed: int = 7) -> int:
        """Genera ``n`` operaciones FICTICIAS con ``origen='DEMO'`` para mostrar el Dashboard.

        No son resultados del modelo: sirven solo para la demostración y se pueden borrar con
        :meth:`clear_demo_history` u ocultar en el Dashboard.
        """
        import random

        rng = random.Random(seed)
        vehicles = self.query("""SELECT v.placa, a.lista FROM vehiculos v
                                 LEFT JOIN autorizaciones a ON a.placa = v.placa AND a.activa = ?""", (True,))
        gates = self.garitas() or ["Garita 1"]
        now = now_local()
        created = 0
        for _ in range(int(n)):
            moment = now - timedelta(days=rng.randint(0, days - 1), hours=rng.randint(0, 9),
                                     minutes=rng.randint(0, 59))
            moment = moment.replace(hour=rng.choice([6, 7, 7, 8, 8, 9, 12, 13, 17, 18, 18, 19, 20]))
            if moment > now:
                moment -= timedelta(days=1)
            roll = rng.random()
            if roll < 0.08:
                plate, lista, result, action = f"G{rng.choice('ABCPST')}{rng.choice('ABCDE')}-{rng.randint(1000, 9999)}", \
                    None, "NO_REGISTRADO", "RECHAZO"
            elif roll < 0.13:
                plate, lista, result, action = None, None, "VERIFICACION_MANUAL", rng.choice(
                    ["APERTURA_MANUAL", "SOLO_REGISTRO"])
            else:
                row = vehicles.iloc[rng.randrange(len(vehicles))]
                plate, lista = row["placa"], row["lista"]
                result = "DENEGADO" if lista == "RESTRINGIDA" else ("AUTORIZADO" if lista == "BLANCA" else "NO_REGISTRADO")
                action = "APERTURA_AUTOMATICA" if result == "AUTORIZADO" else "RECHAZO"
            self.log_operation(
                garita=rng.choice(gates), operador=rng.choice(["Operador de garita", "Supervisor de turno"]),
                tipo_movimiento=rng.choice(["ENTRADA", "ENTRADA", "SALIDA"]), resultado=result, accion=action,
                placa_leida=plate.replace("-", "") if plate else None, placa_final=plate,
                confianza_ocr=round(rng.uniform(0.86, 1.0) if plate else rng.uniform(0.3, 0.8), 3),
                lista=lista if isinstance(lista, str) else None,
                motivo="Demostración" if action == "APERTURA_MANUAL" else None,
                origen="DEMO", tiempo_ms=rng.randint(90, 400), fecha_hora=moment)
            created += 1
        return created

    def clear_demo_history(self) -> int:
        """Borra solo las operaciones de demostración (``origen='DEMO'``)."""
        return self.execute("DELETE FROM operaciones WHERE origen = ?", ("DEMO",))

    def add_user(self, usuario: str, nombre: str, rol: str) -> None:
        """Agrega un usuario del sistema."""
        usuario, nombre = usuario.strip(), nombre.strip()
        if not usuario or not nombre:
            raise ValueError("Usuario y nombre son obligatorios.")
        if rol not in ("OPERADOR", "SUPERVISOR", "ADMINISTRADOR"):
            raise ValueError("Rol inválido.")
        self.execute("INSERT INTO usuarios (usuario, nombre, rol) VALUES (?, ?, ?)",
                     (usuario, nombre, rol))

    def deactivate_user(self, usuario: str) -> None:
        """Inactiva un usuario sin borrar su registro ni su historial."""
        usuario = usuario.strip()
        if not usuario:
            raise ValueError("Seleccione un usuario válido.")
        updated = self.execute("UPDATE usuarios SET activo = ? WHERE usuario = ? AND activo = ?",
                               (False, usuario, True))
        if updated:
            return
        existing = self.query("SELECT 1 FROM usuarios WHERE usuario = ?", (usuario,))
        if existing.empty:
            raise ValueError("El usuario no existe.")
        raise ValueError("El usuario ya está inactivo.")
