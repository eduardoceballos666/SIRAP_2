#!/usr/bin/env python3
"""Prepare private, OCR-blind gatehouse video review materials.

This script reads a local raw video. It does not run OCR/detection, upload frames,
or change ground-truth or metric files. Keep output in private storage.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

import cv2


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_ranges(value: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for item in value.split(","):
        if not item.strip():
            continue
        start_text, separator, end_text = item.strip().partition(":")
        if not separator:
            raise argparse.ArgumentTypeError(
                f"Rango inválido {item!r}; use inicio:fin inclusivos."
            )
        start, end = int(start_text), int(end_text)
        if start < 0 or end < start:
            raise argparse.ArgumentTypeError(f"Rango inválido {item!r}.")
        ranges.append((start, end))
    return ranges


def write_review_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    fields = [
        "sample_id",
        "frame_index",
        "time_seconds",
        "image_file",
        "label",
        "plate_box_count",
        "transcription_if_readable",
        "notes",
        "reviewer_id",
        "reviewed_at_utc",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def extract_samples(video: Path, image_dir: Path, sample_seconds: float) -> tuple[list[dict], float, int]:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"No se pudo abrir el video: {video}")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    reported_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if fps <= 0:
        capture.release()
        raise RuntimeError("OpenCV no pudo determinar los FPS del video.")
    frame_step = max(1, round(fps * sample_seconds))
    image_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % frame_step == 0:
            sample_id = f"frame_{frame_index:08d}"
            image_path = image_dir / f"{sample_id}.jpg"
            if not cv2.imwrite(str(image_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                capture.release()
                raise RuntimeError(f"No se pudo escribir el fotograma {frame_index}.")
            rows.append(
                {
                    "sample_id": sample_id,
                    "frame_index": frame_index,
                    "time_seconds": f"{frame_index / fps:.3f}",
                    "image_file": f"frames/{image_path.name}",
                    "label": "",
                    "plate_box_count": "",
                    "transcription_if_readable": "",
                    "notes": "",
                    "reviewer_id": "",
                    "reviewed_at_utc": "",
                }
            )
        frame_index += 1
    capture.release()
    return rows, fps, frame_index or reported_frames


def extract_clip(
    ffmpeg: str, video: Path, output: Path, start: int, end_inclusive: int
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    video_filter = (
        f"trim=start_frame={start}:end_frame={end_inclusive + 1},"
        "setpts=PTS-STARTPTS"
    )
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        video_filter,
        "-fps_mode",
        "passthrough",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        str(output),
    ]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrae muestras privadas y clips de pasadas excluidas."
    )
    parser.add_argument("--video", required=True, type=Path, help="Video original sin overlays.")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--sample-seconds",
        type=float,
        default=1.0,
        help="Intervalo entre cuadros de muestreo para revisar el video y candidatos negativos.",
    )
    parser.add_argument(
        "--excluded-ranges",
        default="0:247,1142:1488",
        help="Rangos de cuadros inclusivos separados por coma, en formato inicio:fin.",
    )
    args = parser.parse_args()

    video = args.video.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not video.is_file():
        parser.error(f"No existe el video: {video}")
    if args.sample_seconds <= 0:
        parser.error("--sample-seconds debe ser mayor que cero.")
    ranges = parse_ranges(args.excluded_ranges)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.error("No se encontró ffmpeg en PATH.")

    output_dir.mkdir(parents=True, exist_ok=True)
    rows, fps, frame_count = extract_samples(
        video, output_dir / "frames", args.sample_seconds
    )
    for start, end in ranges:
        if end >= frame_count:
            raise RuntimeError(
                f"El rango {start}:{end} excede los {frame_count} cuadros disponibles."
            )
        clip_path = output_dir / "excluded_passes" / f"frames_{start:06d}_{end:06d}.mp4"
        extract_clip(ffmpeg, video, clip_path, start, end)

    write_review_csv(output_dir / "reviewer_1.csv", rows)
    write_review_csv(output_dir / "reviewer_2.csv", rows)
    manifest = {
        "source_video_name": video.name,
        "source_video_sha256": sha256_file(video),
        "frame_count": frame_count,
        "fps": fps,
        "duration_seconds": frame_count / fps,
        "sampling_interval_seconds": args.sample_seconds,
        "sampled_frames": len(rows),
        "excluded_pass_ranges_inclusive": [
            {"start_frame": start, "end_frame": end} for start, end in ranges
        ],
        "review_labels": [
            "no_plate_visible",
            "plate_visible_readable",
            "plate_visible_unreadable",
            "uncertain",
        ],
        "note": (
            "An unreadable visible plate remains a positive plate-detection example. "
            "Reviewers must not see OCR/detector overlays or each other's labels. "
            "Frames sampled from one continuous video are correlated; report the "
            "sampling unit and do not treat adjacent frames as independent passes."
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "sampled_frames": len(rows),
                "frame_count": frame_count,
                "fps": fps,
                "clips": len(ranges),
                "video_sha256": manifest["source_video_sha256"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
