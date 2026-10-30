"""Evaluate SIRAP's video recognition path with a private event ground-truth CSV.

CSV columns: video_path,plate_gt. Keep that CSV and any detailed per-event labels private.
The public JSON output contains aggregate counts only; it does not include plate text.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import platform
import time
from pathlib import Path
from typing import Any

import cv2

from src.data_processing import normalize_plate
from src.model import ALPRPipeline
from src.utils import ROOT_DIR


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_video(path: Path, reference: str, pipeline: ALPRPipeline, interval_s: float,
                   threshold: float, max_gap_s: float, end_grace_s: float) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_s = frame_count / fps if fps > 0 else 0
    if duration_s <= 0:
        cap.release()
        raise ValueError(f"No se pudo determinar la duración del video: {path}")

    expected = normalize_plate(reference)
    pending = ""
    pending_at: float | None = None
    started = time.perf_counter()
    timeline_s = 0.0
    sampled = accepted = 0
    confirmed_at: float | None = None
    confirmed_plate: str | None = None
    confirming_latency_ms: float | None = None
    stop_at = duration_s + end_grace_s

    while timeline_s < stop_at and confirmed_plate is None:
        source_time_s = timeline_s % duration_s
        cap.set(cv2.CAP_PROP_POS_MSEC, source_time_s * 1000)
        ok, frame_bgr = cap.read()
        if ok:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            reading = pipeline.recognize(frame_rgb)
            sampled += 1
            plate = normalize_plate(reading.plate)
            confidence = float(reading.ocr_confidence or 0.0)
            if plate and confidence >= threshold:
                accepted += 1
                candidate = plate.replace("-", "")
                if candidate != pending or (pending_at is not None and timeline_s - pending_at > max_gap_s):
                    pending = candidate
                elif pending:
                    confirmed_plate = plate
                    confirmed_at = timeline_s
                    confirming_latency_ms = float(reading.timings_ms.get("total", 0.0))
                pending_at = timeline_s
        timeline_s += interval_s

    cap.release()
    wall_s = time.perf_counter() - started
    return {
        "video": path.name,
        "duration_s": round(duration_s, 3),
        "frames_sampled": sampled,
        "accepted_frames": accepted,
        "confirmed": confirmed_plate is not None,
        "exact_event_match": bool(confirmed_plate and expected and confirmed_plate == expected),
        "time_to_confirmation_s": round(confirmed_at, 3) if confirmed_at is not None else None,
        "confirmation_inference_ms": round(confirming_latency_ms, 1) if confirming_latency_ms is not None else None,
        "wall_runtime_s": round(wall_s, 3),
        "video_sha256": sha256(path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, help="Private CSV: video_path,plate_gt")
    parser.add_argument("--output", default="results/metrics/video_e2e.json")
    parser.add_argument("--sample-interval", type=float, default=1.0)
    parser.add_argument("--ocr-threshold", type=float, default=0.94)
    parser.add_argument("--same-plate-gap", type=float, default=7.5)
    parser.add_argument("--video-end-grace", type=float, default=15.0)
    args = parser.parse_args()
    if args.sample_interval <= 0:
        parser.error("--sample-interval debe ser mayor que 0")

    logging.getLogger("sirap.model").setLevel(logging.ERROR)
    csv_path = Path(args.csv).expanduser().resolve()
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        events = list(csv.DictReader(stream))
    if not events or not {"video_path", "plate_gt"} <= set(events[0]):
        raise SystemExit("El CSV debe tener las columnas video_path,plate_gt y al menos una fila.")

    pipeline = ALPRPipeline.from_config()
    details = []
    for event in events:
        video_path = Path(event["video_path"]).expanduser()
        if not video_path.is_absolute():
            video_path = ROOT_DIR / video_path
        details.append(evaluate_video(video_path.resolve(), event["plate_gt"], pipeline,
                                      args.sample_interval, args.ocr_threshold,
                                      args.same_plate_gap, args.video_end_grace))
    n = len(details)
    result = {
        "protocol": {
            "sample_interval_s": args.sample_interval,
            "ocr_confidence_threshold": args.ocr_threshold,
            "consecutive_same_plate": 2,
            "max_gap_s": args.same_plate_gap,
            "replay_after_video_end_s": args.video_end_grace,
            "detector": pipeline.detector.name,
            "ocr": pipeline.reader.model_name,
            "inference_device": "CPU",
            "repository_commit": __import__("subprocess").run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT_DIR, capture_output=True, text=True, check=False
            ).stdout.strip() or None,
            "detector_sha256": sha256(ROOT_DIR / "models/best_model.onnx"),
            "platform": platform.platform(),
        },
        "summary": {
            "videos": n,
            "events_confirmed": sum(row["confirmed"] for row in details),
            "exact_event_matches": sum(row["exact_event_match"] for row in details),
            "event_emr": sum(row["exact_event_match"] for row in details) / n,
            "mean_time_to_confirmation_s": round(
                sum(row["time_to_confirmation_s"] or 0 for row in details if row["confirmed"])
                / max(1, sum(row["confirmed"] for row in details)), 3),
            "median_time_to_confirmation_s": None,
        },
        "events": details,
        "ground_truth_sha256": sha256(csv_path),
    }
    times = sorted(row["time_to_confirmation_s"] for row in details if row["time_to_confirmation_s"] is not None)
    if times:
        mid = len(times) // 2
        result["summary"]["median_time_to_confirmation_s"] = round(
            times[mid] if len(times) % 2 else (times[mid - 1] + times[mid]) / 2, 3)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT_DIR / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "output": str(output)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
