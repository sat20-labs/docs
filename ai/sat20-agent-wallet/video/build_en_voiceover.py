#!/usr/bin/env python3
import json
import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build" / "voiceover-en"
MANIFEST = ROOT / "one-minute-en.json"
NARRATION = ROOT / "narration-en.txt"
SILENT_VIDEO = ROOT / "build" / "sat20-agent-wallet-one-minute-en-silent.mp4"
VOICE = "Samantha"
RATE = "190"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return float(result.stdout.strip())


def main() -> int:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    lines = [line.strip() for line in NARRATION.read_text(encoding="utf-8").splitlines() if line.strip()]
    segments = manifest["segments"]

    if len(lines) != len(segments):
        raise SystemExit(f"narration line count {len(lines)} does not match segments {len(segments)}")

    concat_list = BUILD_DIR / "segments.txt"
    concat_entries = []

    for idx, (line, segment) in enumerate(zip(lines, segments), start=1):
        raw = BUILD_DIR / f"raw_{idx:02d}.aiff"
        padded = BUILD_DIR / f"segment_{idx:02d}.m4a"
        target_duration = float(segment["duration"])

        run(["say", "-v", VOICE, "-r", RATE, "-o", str(raw), line])
        raw_duration = duration_seconds(raw)
        if raw_duration > target_duration:
            raise SystemExit(
                f"segment {idx} narration too long: {raw_duration:.2f}s > {target_duration:.2f}s\n{line}"
            )

        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(raw),
                "-af",
                f"apad=pad_dur={target_duration:.3f},atrim=duration={target_duration:.3f}",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(padded),
            ]
        )
        concat_entries.append(f"file {shlex.quote(str(padded))}")

    concat_list.write_text("\n".join(concat_entries) + "\n", encoding="utf-8")

    joined_audio = BUILD_DIR / "sat20-agent-wallet-one-minute-en.m4a"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(joined_audio),
        ]
    )

    final_video = ROOT / "build" / "sat20-agent-wallet-one-minute-en.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(SILENT_VIDEO),
            "-i",
            str(joined_audio),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(final_video),
        ]
    )

    print(final_video)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
