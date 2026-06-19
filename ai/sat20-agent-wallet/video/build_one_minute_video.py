#!/usr/bin/env python3
import argparse
import json
import math
import shlex
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
FRAMES_DIR = ROOT / "frames"


def seconds_to_timestamp(value: float) -> str:
    total_ms = int(round(value * 1000))
    hours = total_ms // 3600000
    total_ms %= 3600000
    minutes = total_ms // 60000
    total_ms %= 60000
    seconds = total_ms // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def validate_manifest(manifest: dict) -> list[str]:
    errors = []
    segments = manifest.get("segments", [])
    if not segments:
        errors.append("manifest.segments is empty")
        return errors

    total_duration = sum(float(segment["duration"]) for segment in segments)
    if not math.isclose(total_duration, 60.0, abs_tol=0.5):
        errors.append(f"segment duration total must be about 60s, got {total_duration:.2f}s")

    for index, segment in enumerate(segments, start=1):
        for field in ("id", "source", "duration", "caption"):
            if field not in segment:
                errors.append(f"segment {index} missing field: {field}")

    return errors


def build_segment_command(manifest: dict, segment: dict, index: int) -> tuple[str, str]:
    width = int(manifest["width"])
    height = int(manifest["height"])
    fps = int(manifest["fps"])
    duration = float(segment["duration"])
    source = ROOT / segment["source"]
    output = BUILD_DIR / f"segment_{index:02d}_{segment['id']}.mp4"

    fade_out_start = max(duration - 0.35, 0)

    filter_parts = [
        f"scale={width}:{height}:force_original_aspect_ratio=increase",
        f"crop={width}:{height}",
        "format=yuv420p",
        "fade=t=in:st=0:d=0.35",
        f"fade=t=out:st={fade_out_start:.2f}:d=0.35"
    ]

    cmd = (
        "ffmpeg -y "
        f"-loop 1 -framerate {fps} -i {shlex.quote(str(source))} "
        f"-vf \"{','.join(filter_parts)}\" "
        f"-t {duration:.2f} -r {fps} "
        f"{shlex.quote(str(output))}"
    )
    return cmd, str(output)


def build_render_script(manifest: dict) -> str:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    concat_list = BUILD_DIR / "segments.txt"
    output_file = BUILD_DIR / manifest["output_file"]

    segment_paths = []
    commands = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        f"cd {shlex.quote(str(ROOT))}",
        "mkdir -p build",
        ""
    ]

    missing_inputs = []
    for index, segment in enumerate(manifest["segments"], start=1):
        source = ROOT / segment["source"]
        if not source.exists():
            missing_inputs.append(str(source))
        command, segment_path = build_segment_command(manifest, segment, index)
        commands.append(command)
        commands.append("")
        segment_paths.append(segment_path)

    concat_lines = [f"file '{path}'" for path in segment_paths]
    concat_list.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    commands.extend(
        [
            (
                "ffmpeg -y -f concat -safe 0 "
                f"-i {shlex.quote(str(concat_list))} "
                "-c copy "
                f"{shlex.quote(str(output_file))}"
            ),
            "",
            f"echo 'Output: {output_file}'"
        ]
    )

    script = "\n".join(commands) + "\n"
    render_script = BUILD_DIR / "render.sh"
    render_script.write_text(script, encoding="utf-8")
    render_script.chmod(0o755)

    if missing_inputs:
        print("Missing frame inputs:")
        for path in missing_inputs:
            print(f"  - {path}")
        print("")
        print("Render script generated anyway. Add the missing files before running render.sh.")

    return script


def build_srt(manifest: dict) -> None:
    current = 0.0
    lines = []
    for index, segment in enumerate(manifest["segments"], start=1):
        start = current
        end = current + float(segment["duration"])
        lines.append(str(index))
        lines.append(f"{seconds_to_timestamp(start)} --> {seconds_to_timestamp(end)}")
        lines.append(segment["caption"])
        detail = segment.get("detail")
        if detail:
            lines.append(detail)
        lines.append("")
        current = end

    (BUILD_DIR / "captions.srt").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", default=str(ROOT / "one-minute-manifest.json"))
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    build_srt(manifest)
    build_render_script(manifest)
    print(f"Generated: {BUILD_DIR / 'render.sh'}")
    print(f"Generated: {BUILD_DIR / 'captions.srt'}")
    print(f"Generated: {BUILD_DIR / 'segments.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
