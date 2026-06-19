# SAT20 Agent Wallet 1-Minute Video Build

This directory holds the shared build assets for the 1-minute SAT20 Agent Wallet / STP public video.

It is intentionally maintained only in `docs/`. Other docs can reference the same build tooling and manifest instead of duplicating it.

## Files

- `one-minute-manifest.json`: the editable source of truth for timing, captions, txids, and frame paths.
- `build_one_minute_video.py`: validates the manifest and generates a deterministic `ffmpeg` render script.
- `frames/`: real screenshots or short source clips captured from PWA, explorers, and indexers.
- `build/`: generated render script, concat list, and output mp4.

## Workflow

1. Capture real frame images into `frames/`.
2. Update `one-minute-manifest.json` if the frame paths, captions, or txids change.
3. Run:

```bash
python3 docs/ai/sat20-agent-wallet/video/build_one_minute_video.py
```

4. Review the generated file:

```bash
docs/ai/sat20-agent-wallet/video/build/render.sh
```

5. After `ffmpeg` is installed, render:

```bash
bash docs/ai/sat20-agent-wallet/video/build/render.sh
```

## Notes

- The current manifest is for the 1-minute public version only.
- The script assumes a 16:9 `1920x1080` output and burns captions directly into the video.
- Until real screenshots are captured, the generated render script is expected to report missing inputs.
