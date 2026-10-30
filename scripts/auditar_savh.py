"""Audita la revisión manual SAVH sin confirmar automáticamente placas.

Ejemplo Colab:
  python scripts/auditar_savh.py --output-dir /content/drive/MyDrive/proyecto_integrador_placas/auditoria_savh

Con --csv se usa una copia exportada de la hoja Google (sin autorización a la API).
Los CSV generados incluyen datos de placas: guárdelos en Drive privado, NO en el repositorio público.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

SHEET_ID = "1l79GrAYGFkTiOYxgKDT1_BEi_b-6Duo1_QqUNlcv7yM"
ANSWER = "revision: ok o placa correcta"
REQUIRED = {"n", "fila_gt", "imagen", "texto_actual", "sugerencia", "igual_a", ANSWER}
ACCEPT = {"ok", "si", "sí", "ilegible", "no legible", "excluir"}


def load_sheet(csv_path: str | None, sheet_id: str) -> pd.DataFrame:
    if csv_path:
        return pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    try:
        import gspread
        from google.colab import auth
        from google.auth import default
    except ImportError as exc:
        raise RuntimeError(
            "Ejecute en Google Colab o indique --csv con la hoja descargada."
        ) from exc
    auth.authenticate_user()
    credentials, _ = default()
    records = gspread.authorize(credentials).open_by_key(sheet_id).sheet1.get_all_records(
        default_blank="", numericise_ignore=["all"]
    )
    return pd.DataFrame(records, dtype=str)


def normalize_answer(value: str) -> str:
    value = str(value).strip().lower().strip(" .")
    if not value:
        return ""
    if value in ACCEPT:
        return value
    plate = re.sub(r"[-\s]", "", value.upper())
    return plate if re.fullmatch(r"[A-Z]{3}[0-9]{3,4}", plate) else "INVALIDA:" + value


def audit(frame: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    frame = frame.fillna("").astype(str)
    frame.columns = [c.strip() for c in frame.columns]
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(f"Faltan columnas de la hoja: {sorted(missing)}")
    frame = frame.copy()
    frame["n"] = frame["n"].str.strip()
    frame["igual_a"] = frame["igual_a"].str.strip()
    frame["grupo"] = frame["igual_a"].where(frame["igual_a"].ne(""), frame["n"])
    frame["_respuesta_normalizada"] = frame[ANSWER].map(normalize_answer)
    pending = []
    conflicting = []
    invalid = []
    reviewed = 0
    for group, sub in frame.groupby("grupo", sort=False):
        answers = sorted({x for x in sub["_respuesta_normalizada"] if x})
        if any(x.startswith("INVALIDA:") for x in answers):
            invalid.append(group)
        if len(answers) > 1:
            conflicting.append(group)
        if not answers:
            representative = sub.iloc[0]
            pending.append({
                "grupo": group,
                "fila_gt": representative["fila_gt"],
                "imagen": representative["imagen"],
                "texto_actual": representative["texto_actual"],
                "sugerencia": representative["sugerencia"],
                "chequeo_visual": representative.get("chequeo_visual", ""),
                "nota": representative.get("nota", ""),
                "copias_en_grupo": len(sub),
                "estado": "PENDIENTE_REVISION_VISUAL",
            })
        elif len(answers) == 1 and not answers[0].startswith("INVALIDA:"):
            reviewed += 1
    summary = {
        "filas_hoja": len(frame),
        "grupos_unicos": frame["grupo"].nunique(),
        "grupos_pendientes": len(pending),
        "grupos_revisados": reviewed,
        "grupos_conflicto": len(conflicting),
        "grupos_respuesta_invalida": len(invalid),
        "ids_grupos_conflicto": conflicting,
        "ids_grupos_respuesta_invalida": invalid,
        "nota": "Una respuesta no es una verdad validada por software: exige revisión visual humana.",
    }
    return summary, pd.DataFrame(pending, columns=[
        "grupo", "fila_gt", "imagen", "texto_actual", "sugerencia",
        "chequeo_visual", "nota", "copias_en_grupo", "estado"
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditar referencias SAVH pendientes de revisión visual")
    parser.add_argument("--csv", help="CSV exportado de la hoja; omitido: conectar Google Sheets desde Colab")
    parser.add_argument("--sheet-id", default=SHEET_ID)
    parser.add_argument("--output-dir", required=True, help="Carpeta PRIVADA para el informe y las placas")
    args = parser.parse_args()
    output = Path(args.output_dir).expanduser()
    output.mkdir(parents=True, exist_ok=True)
    summary, pending = audit(load_sheet(args.csv, args.sheet_id))
    pending.to_csv(output / "savh_pendientes_revision.csv", index=False)
    (output / "savh_auditoria.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("Pendientes privados:", output / "savh_pendientes_revision.csv")


if __name__ == "__main__":
    main()
