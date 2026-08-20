"""`logs/` altındaki oda başına gecikme dosyalarından (`logs/<room>.jsonl`) basit bir
benchmark raporu üretir.

Kullanım:
    uv run scripts/latency_report.py                # logs/ altındaki tüm odalar
    uv run scripts/latency_report.py logs/oda1.jsonl # tek bir oda
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

# metric türü -> raporlanacak (alan adı, gösterim etiketi) listesi
FIELDS_BY_TYPE: dict[str, list[tuple[str, str]]] = {
    "stt_metrics": [("duration", "duration"), ("audio_duration", "audio_duration")],
    "eou_metrics": [
        ("end_of_utterance_delay", "end_of_utterance_delay"),
        ("transcription_delay", "transcription_delay"),
        ("on_user_turn_completed_delay", "on_user_turn_completed_delay"),
    ],
    "llm_metrics": [("ttft", "ttft"), ("duration", "duration")],
    "tts_metrics": [("ttfb", "ttfb"), ("duration", "duration")],
    "eot_inference_metrics": [
        ("total_duration", "total_duration"),
        ("detection_delay", "detection_delay"),
        ("prediction_duration", "prediction_duration"),
    ],
    "turn_latency": [
        ("end_of_utterance_delay", "end_of_utterance_delay"),
        ("transcription_delay", "transcription_delay"),
        ("llm_ttft", "llm_ttft"),
        ("tts_ttfb", "tts_ttfb"),
        ("total_delay", "total_delay (uçtan uca)"),
    ],
}


def load_records(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def percentile(values: list[float], pct: float) -> float:
    if len(values) == 1:
        return values[0]
    quantiles = statistics.quantiles(values, n=100, method="inclusive")
    return quantiles[int(pct) - 1]


def print_stats(label: str, values: list[float]) -> None:
    if not values:
        return
    avg = statistics.mean(values)
    p50 = percentile(values, 50)
    p95 = percentile(values, 95) if len(values) > 1 else values[0]
    print(f"  {label:32s} n={len(values):5d}  avg={avg:7.3f}s  p50={p50:7.3f}s  p95={p95:7.3f}s  max={max(values):7.3f}s")


def main() -> None:
    arg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "logs"
    if not arg.exists():
        print(f"Bulunamadı: {arg}")
        sys.exit(1)

    paths = sorted(arg.glob("*.jsonl")) if arg.is_dir() else [arg]
    if not paths:
        print(f"'{arg}' altında .jsonl dosyası yok.")
        sys.exit(1)

    records = []
    for p in paths:
        records.extend(load_records(p))
    if not records:
        print(f"'{arg}' içinde okunabilir kayıt yok.")
        sys.exit(1)

    room_desc = f"{len(paths)} oda dosyası" if arg.is_dir() else str(arg)
    print(f"Toplam kayıt: {len(records)}  (kaynak: {room_desc})\n")

    for metric_type, fields in FIELDS_BY_TYPE.items():
        matching = [r for r in records if r.get("type") == metric_type]
        if not matching:
            continue
        print(f"{metric_type} ({len(matching)} kayıt):")
        for field, label in fields:
            values = [r[field] for r in matching if isinstance(r.get(field), (int, float))]
            print_stats(label, values)
        print()


if __name__ == "__main__":
    main()
