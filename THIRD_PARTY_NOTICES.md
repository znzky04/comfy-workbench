# Licence scope and upstream materials

Updated 2026-10-26. The maintainer selected MIT for original engineering code.
`LICENSE` covers the original Python/JavaScript/CSS/templates, tests, utilities and
original documentation. It does **not** relicense third-party material, model weights,
images, character rights or a generation pipeline as a whole.

## Included configurations and patches

- On 2026-10-26 the maintainer confirmed that the workflow canvases/API graphs and
  `comfyui-anima-incontext` node were self-authored. The original configuration graphs
  and original compatibility edits in this repository are included under MIT on that
  declaration. Node types and model names refer to separately supplied components;
  the graph licence does not grant permission to use those components or their outputs.
- `integrations/dsh/patches/*.diff` contains original compatibility edits and context
  from that self-authored installed node; the full node is not bundled here. The local
  directory has no independent Git remote. Its parent ComfyUI remote is **not** evidence
  of the node's provenance. An online similarly named directory returned HTTP 401 and
  was not used to claim ownership or copy new material. Attribution here relies on the
  maintainer's explicit declaration, not on an independently verified publication history.
- Historical workflow names, benchmark prompts and hashes are records, not grants of
  rights to original characters, anime IP, models or reference images.

## External runtime components — not bundled

| Component | Primary source / status |
| --- | --- |
| ComfyUI | https://github.com/Comfy-Org/ComfyUI — separate application; consult its own licence |
| Official comfy-mcp | https://github.com/Comfy-Org/comfy-mcp — separate integration, not this project's implementation |
| dsh-comfyui 0.5.x | Installed separately in DSH; this repository generates preset v1 data, not plugin source |
| Anima | https://huggingface.co/circlestone-labs/Anima — publisher lists CircleStone Labs Non-Commercial License and an upstream NVIDIA model agreement; do not infer commercial model rights from MIT code |
| Animagine XL 4.0 Opt | https://huggingface.co/cagliostrolab/animagine-xl-4.0 — publisher lists CreativeML Open RAIL++-M |
| Qwen text encoder / VAE, LoRAs, upscaler | Exact filenames are declared in `workflows/registry.json`; no weights are shipped. Per-artifact origin/licence still needs checking before use or redistribution |
| UltimateSDUpscale and Anima reference nodes | Separate ComfyUI custom nodes; users supply their own installation. The reference node is self-authored per the declaration above, but a distributable full-node package is not included |

Links/model-card labels were checked on 2026-10-26; full terms and revisions must be
reviewed for the intended use. The statements above do not certify rights to generated
outputs or relax any upstream conditions. There is no automatic model download.

## Images and public samples

Images are excluded from Git. `benchmarks/public-selection.json` records permission to
display one particular local output on the personal website, **not** a general image
licence, model licence or approval to publish every benchmark. Fan character images
remain AI-generated, non-commercial technical evaluations with the original rights
holders credited. The code licence grants no character, trademark or image rights.

## Dependencies

Python dependencies are installed from PyPI by the user, not vendored. Their own
licences apply. Keep dependency copyright/licence notices if packaging a binary or
vendoring code in a future release. No such distribution is offered in v0.1.
