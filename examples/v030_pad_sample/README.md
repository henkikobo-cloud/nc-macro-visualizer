# v0.3.0 PAD-Inspired Sample

This directory contains generated sample artifacts for the v0.3.0 PAD-inspired view.

Input:

```text
samples/04_variables.nc
```

Generated with:

```bash
python3 nctool.py samples/04_variables.nc -o examples/v030_pad_sample --pad-html --pad-text --cfg
```

Files to inspect:

- `pad.html`: beginner-facing PAD-inspired structured view
- `pad.css`: standalone CSS used by `pad.html`
- `pad.txt`: text version of the PAD-inspired view
- `cfg.json`: internal Control Flow Graph
- `analysis.json`, `report.md`, `flow.mmd`: existing default outputs
