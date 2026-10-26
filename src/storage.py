"""Persistencia de SIRAP en archivos CSV locales."""
from __future__ import annotations
import csv, os, tempfile, threading, random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Sequence
import pandas as pd
from src.utils import now_local, resolve_path

HEADERS = {
    "vehiculos": ["placa","marca","modelo","color","tipo","propietario","transportista","fuente","actualizado_en"],
    "autorizaciones": ["id","placa","lista","motivo","vigente_desde","vigente_hasta","activa","creado_por"],
    "operaciones": ["id","fecha_hora","garita","operador","tipo_movimiento","placa_leida","placa_final","confianza_ocr","resultado","lista","accion","motivo","origen","tiempo_ms"],
    "garitas": ["id","nombre","ubicacion","activa"],
    "usuarios": ["id","usuario","nombre","rol","activo"],
    "credenciales": ["usuario","password_hash"],
}
LOCK = threading.RLock()

class StorageError(RuntimeError):
    """Fallo al leer o escribir archivos CSV."""

class CsvStore:
    """Almacena los registros de la aplicación en CSV, sin servidor externo."""
    def __init__(self, data_dir: str | Path | None = None, **_: Any):
        self.data_dir = resolve_path(data_dir or os.getenv("SIRAP_DATA_DIR","data/processed"))
        self.data_dir.mkdir(parents=True,exist_ok=True)
        self.engine = "csv"
        for name, cols in HEADERS.items():
            if not self._path(name).exists(): self._write(name,pd.DataFrame(columns=cols))
    @classmethod
    def from_environment(cls,**kwargs): return cls(**kwargs)
    def _path(self,name):
        if name not in HEADERS: raise ValueError("CSV desconocido: "+name)
        return self.data_dir/(name+".csv")
    def _read(self,name):
        try:
            d=pd.read_csv(self._path(name),dtype=str,keep_default_na=False)
            for col in HEADERS[name]:
                if col not in d: d[col]=""
            return d[HEADERS[name]]
        except pd.errors.EmptyDataError: return pd.DataFrame(columns=HEADERS[name])
        except OSError as exc: raise StorageError(f"No se pudo leer {name}.csv: {exc}") from exc
    def _write(self,name,frame):
        path=self._path(name); temp=None
        try:
            with tempfile.NamedTemporaryFile("w",encoding="utf-8",newline="",dir=path.parent,delete=False,suffix=".tmp") as f:
                temp=f.name; frame.reindex(columns=HEADERS[name],fill_value="").to_csv(f,index=False,quoting=csv.QUOTE_MINIMAL)
            os.replace(temp,path)
        except OSError as exc:
            if temp and os.path.exists(temp): os.unlink(temp)
            raise StorageError(f"No se pudo guardar {name}.csv: {exc}") from exc
    @staticmethod
    def _active(v): return str(v).lower() in ("1","true","si","sí","yes")
    @staticmethod
    def _next_id(d):
        nums=pd.to_numeric(d.get("id",pd.Series(dtype=str)),errors="coerce").dropna()
        return int(nums.max())+1 if len(nums) else 1
    def is_user_active(self,user):
        d=self._read("usuarios"); d=d[d.usuario==user]
        return bool(len(d) and self._active(d.iloc[-1].activo))
    def active_users(self):
        d = self._read("usuarios")
        # Evita que una tabla antigua o incompleta detenga el arranque de la API.
        if "activo" not in d.columns:
            d["activo"] = ""
        if "usuario" not in d.columns:
            d["usuario"] = ""
        active = d["activo"].map(self._active)
        return [
            user.strip()
            for user in d.loc[active, "usuario"].fillna("").astype(str).tolist()
            if user.strip()
        ]
    def credential_hash(self,user):
        d=self._read("credenciales"); d=d[d.usuario==user]
        return None if d.empty else d.iloc[-1].password_hash
    def set_credential(self,user,password_hash):
        with LOCK:
            d=self._read("credenciales"); m=d.usuario==user
            if m.any(): d.loc[m,"password_hash"]=password_hash
            else: d.loc[len(d)]=[user,password_hash]
            self._write("credenciales",d)
    def get_vehicle(self,plate):
        d=self._read("vehiculos"); d=d[d.placa.str.upper()==plate.upper()]
        if d.empty:return None
        row=d.iloc[-1].to_dict(); row["autorizacion"]=self.get_authorization(plate); return row
    def get_authorization(self,plate,on=None):
        today=(on or now_local().date()).isoformat(); d=self._read("autorizaciones")
        d=d[(d.placa.str.upper()==plate.upper())&d.activa.map(self._active)]
        d=d[(d.vigente_desde=="")|(d.vigente_desde<=today)]
        d=d[(d.vigente_hasta=="")|(d.vigente_hasta>=today)]
        if d.empty:return None
        d=d.assign(_rank=d.lista.map(lambda x:0 if x=="RESTRINGIDA" else 1))
        row=d.sort_values("_rank").iloc[0].drop(labels=["_rank"]).to_dict()
        return {k:(v if v!="" else None) for k,v in row.items()}
    def registered_plates(self): return self._read("vehiculos").placa.tolist()
    def log_operation(self,*,garita,operador,tipo_movimiento,resultado,accion,placa_leida=None,placa_final=None,confianza_ocr=None,lista=None,motivo=None,origen="DETECCION",tiempo_ms=None,fecha_hora=None):
        movement=tipo_movimiento.upper()
        if movement not in ("ENTRADA","SALIDA"): raise ValueError("tipo_movimiento debe ser ENTRADA o SALIDA")
        if accion=="APERTURA_MANUAL" and not(motivo and motivo.strip()): raise ValueError("La apertura manual exige un motivo.")
        with LOCK:
            d=self._read("operaciones")
            d.loc[len(d)]=[self._next_id(d),(fecha_hora or now_local()).isoformat(sep=" ",timespec="seconds"),garita,operador,movement,placa_leida or "",placa_final or "",confianza_ocr if confianza_ocr is not None else "",resultado,lista or "",accion,motivo or "",origen,tiempo_ms if tiempo_ms is not None else ""]
            self._write("operaciones",d)
    def operations(self,desde=None,hasta=None,placa=None,garita=None,resultado=None,tipo_movimiento=None,limit=5000):
        d=self._read("operaciones")
        if desde:d=d[d.fecha_hora>=str(desde)+" 00:00:00"]
        if hasta:d=d[d.fecha_hora<=str(hasta)+" 23:59:59"]
        if placa:
            q=placa.upper().strip(); d=d[d.apply(lambda r:q in (r.placa_final or r.placa_leida).upper(),axis=1)]
        if garita:d=d[d.garita==garita]
        if resultado:d=d[d.resultado==resultado]
        if tipo_movimiento:d=d[d.tipo_movimiento==tipo_movimiento.upper()]
        d=d.sort_values(["fecha_hora","id"],ascending=False).head(int(limit)).copy()
        if len(d):
            d["fecha_hora"]=pd.to_datetime(d.fecha_hora,errors="coerce")
            for col in ("confianza_ocr","tiempo_ms"):d[col]=pd.to_numeric(d[col],errors="coerce")
        return d.reset_index(drop=True)
    def table(self,name):
        if name=="vehiculos":return self._read(name).sort_values("placa").reset_index(drop=True)
        if name == "autorizaciones":
            d = self._read(name)
            # Asegura el esquema aunque el CSV existente esté incompleto.
            for col in HEADERS["autorizaciones"]:
                if col not in d.columns:
                    d[col] = ""
            active = d["activa"].map(self._active)
            return d.loc[active].sort_values(["placa", "lista"]).reset_index(drop=True)
        if name in ("garitas","usuarios"):return self._read(name).sort_values("nombre" if name=="garitas" else "usuario").reset_index(drop=True)
        if name=="propietarios":
            d=self._read("vehiculos"); return d[d.propietario!=""][["propietario"]].drop_duplicates().rename(columns={"propietario":"nombre"}).sort_values("nombre").reset_index(drop=True)
        raise ValueError("CSV desconocido: "+name)
    def garitas(self):
        d = self._read("garitas")
        # Tolera CSV antiguos o incompletos y evita que el endpoint /api/system falle.
        if "activa" not in d.columns:
            d["activa"] = ""
        if "nombre" not in d.columns:
            d["nombre"] = ""
        active = d["activa"].map(self._active)
        return [
            name.strip()
            for name in d.loc[active, "nombre"].fillna("").astype(str).tolist()
            if name.strip()
        ]
    def upsert_owner(self,nombre,tipo="PERSONA",contacto=None):
        if not nombre.strip():raise ValueError("El nombre del propietario es obligatorio.")
        return 1
    def upsert_vehicle(self,placa,marca="",modelo="",color="",tipo="LIVIANO",propietario=None,transportista=None):
        placa=placa.strip().upper()
        if not placa:raise ValueError("La placa es obligatoria.")
        row={"placa":placa,"marca":marca,"modelo":modelo,"color":color,"tipo":tipo,"propietario":propietario or "","transportista":transportista or "","fuente":"ADMIN","actualizado_en":now_local().isoformat(sep=" ",timespec="seconds")}
        with LOCK:
            d=self._read("vehiculos"); m=d.placa.str.upper()==placa
            if m.any():
                i=d[m].index[-1]
                for k,v in row.items():d.at[i,k]=v
            else:d.loc[len(d)]=row
            self._write("vehiculos",d)
    def set_authorization(self,placa,lista,motivo="",hasta=None,usuario="admin"):
        if lista not in ("BLANCA","RESTRINGIDA"):raise ValueError("Lista inválida.")
        if self.get_vehicle(placa) is None:raise ValueError(f"La placa {placa} no está registrada.")
        with LOCK:
            d=self._read("autorizaciones"); d.loc[d.placa.str.upper()==placa.upper(),"activa"]="false"
            d.loc[len(d)]=[self._next_id(d),placa.upper(),lista,motivo,now_local().date().isoformat(),hasta.isoformat() if hasta else "","true",usuario]; self._write("autorizaciones",d)
    def update_authorization(self,placa,lista,motivo,hasta,usuario="admin"):
        if lista not in ("BLANCA","RESTRINGIDA") or not motivo.strip():raise ValueError("Lista y motivo son obligatorios.")
        with LOCK:
            d=self._read("autorizaciones"); ids=d.index[(d.placa.str.upper()==placa.upper())&d.activa.map(self._active)]
            if len(ids)==0:raise ValueError("No hay autorización activa para actualizar.")
            i=ids[-1]; d.loc[d.placa.str.upper()==placa.upper(),"activa"]="false"
            for k,v in {"lista":lista,"motivo":motivo.strip(),"vigente_desde":now_local().date().isoformat(),"vigente_hasta":hasta.isoformat(),"activa":"true","creado_por":usuario}.items():d.at[i,k]=v
            self._write("autorizaciones",d)
    def revoke_authorization(self,placa):
        with LOCK:
            d=self._read("autorizaciones"); d.loc[d.placa.str.upper()==placa.upper(),"activa"]="false"; self._write("autorizaciones",d)
    def add_garita(self,nombre,ubicacion):
        nombre,ubicacion=nombre.strip(),ubicacion.strip()
        if not nombre or not ubicacion:raise ValueError("Nombre y ubicación son obligatorios.")
        with LOCK:
            d=self._read("garitas")
            if (d.nombre.str.casefold()==nombre.casefold()).any():raise ValueError("La garita ya existe.")
            d.loc[len(d)]=[self._next_id(d),nombre,ubicacion,"true"]; self._write("garitas",d)
    def set_garitas_active(self,nombres,activa):
        wanted={str(x).strip() for x in nombres if str(x).strip()}
        if not wanted:raise ValueError("Seleccione garitas.")
        with LOCK:
            d=self._read("garitas"); missing=wanted-set(d.nombre)
            if missing:raise ValueError("No existen: "+", ".join(sorted(missing)))
            m=d.nombre.isin(wanted); d.loc[m,"activa"]="true" if activa else "false"; self._write("garitas",d); return int(m.sum())
    def load_demo_history(self,n=120,days=7,seed=7):
        rng=random.Random(seed); plates=self.registered_plates() or ["GBA-1234","GBO-0429"]; gates=self.garitas() or ["Garita 1"]
        for _ in range(int(n)):
            plate=rng.choice(plates); result,action=rng.choice([("AUTORIZADO","APERTURA_AUTOMATICA"),("DENEGADO","RECHAZO"),("NO_REGISTRADO","RECHAZO")])
            self.log_operation(garita=rng.choice(gates),operador="Operador de garita",tipo_movimiento="ENTRADA",resultado=result,accion=action,placa_leida=plate,placa_final=plate,confianza_ocr=.99,origen="DEMO")
        return int(n)
    def clear_demo_history(self):
        with LOCK:
            d=self._read("operaciones"); keep=d.origen!="DEMO"; removed=int((~keep).sum()); self._write("operaciones",d[keep]); return removed
    def add_user(self,usuario,nombre,rol):
        usuario,nombre=usuario.strip(),nombre.strip()
        if not usuario or not nombre:raise ValueError("Usuario y nombre son obligatorios.")
        with LOCK:
            d=self._read("usuarios")
            if (d.usuario.str.casefold()==usuario.casefold()).any():raise ValueError("El usuario ya existe.")
            d.loc[len(d)]=[self._next_id(d),usuario,nombre,rol,"true"]; self._write("usuarios",d)
    def deactivate_user(self,usuario):self.set_users_active([usuario],False)
    def set_users_active(self,usuarios,activo):
        wanted={str(x).strip() for x in usuarios if str(x).strip()}
        if not wanted:raise ValueError("Seleccione usuarios.")
        with LOCK:
            d=self._read("usuarios"); missing=wanted-set(d.usuario)
            if missing:raise ValueError("No existen: "+", ".join(sorted(missing)))
            m=d.usuario.isin(wanted); d.loc[m,"activo"]="true" if activo else "false"; self._write("usuarios",d); return int(m.sum())
