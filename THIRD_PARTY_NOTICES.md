# Licence scope and upstream materials

Updated 2026-10-26. The maintainer selected MIT for original engineering code.
`LICENSE` covers the original Python/JavaScript/CSS/templates, tests, utilities and
original documentation. It does **not** relicense third-party material, model weights,
images, character rights or a generation pipeline as a whole.

## Included configurations and patches

### Downloaded workflows / 下载工作流

| 项目 | 当前记录 |
| --- | --- |
| 原作者 / Original author | 未知 / Unknown |
| 来源 / Source | 网上下载，原始链接待追溯 / Downloaded online; original URL unconfirmed |
| 许可证 / License | 未确认 / Unconfirmed |
| 本项目 MIT 授权范围 | 不包含这些下载工作流及其来源未确认的派生配置 |

此记录仅针对来源未确认的下载工作流；目前尚未逐项确定对应文件。
“作者未知”是署名状态，不是一种许可证，也不表示原作者放弃权利或已授权转载。
不将这些工作流描述为本项目原创，不替原作者授予 MIT 或其他使用许可。

- Correction on 2026-10-26: the maintainer clarified that **some workflows were downloaded
  online and their authors could not be identified**. The earlier statement that all
  graphs were self-authored is withdrawn. Until provenance is established per file,
  `workflows/api/*.json`, root workflow JSON and their corresponding original canvases
  are **excluded from this project's MIT grant**. Availability for download is not
  evidence of permission to redistribute or relicense. No author or licence is invented.
  The full repository remains private; this notice alone does not resolve redistribution
  permission. Original local graphs are retained unchanged for private use and inspection.
- The affected subset is not yet mapped to individual graphs. Treat all five registered
  graphs (Anima standard/HQ, Animagine standard, Larkie img2img/incontext) as provenance
  pending for public distribution. Future options are to identify compatible original
  terms, omit unverified graphs from a separately reviewed publication, or independently
  author replacements. None of these options has silently altered the local workflows.
- The original compatibility edits remain MIT. The earlier separate declaration that
  the reference node was self-authored has not been independently verified; the latest
  correction specifically concerns downloaded workflows. Node types and model names
  refer to separately supplied components and grant no model or output rights.
- `integrations/dsh/patches/*.diff` contains original compatibility edits and context
  from that self-authored installed node; the full node is not bundled here. The local
  directory has no independent Git remote. Its parent ComfyUI remote is **not** evidence
  of the node's provenance. An online similarly named directory returned HTTP 401 and
  was not used to claim ownership or copy new material. Attribution here relies on the
  maintainer's explicit declaration, not on an independently verified publication history.

GitHub's general licensing guidance: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
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
