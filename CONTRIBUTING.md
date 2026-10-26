# Contributing

First read `README.md`, `SECURITY.md` and `THIRD_PARTY_NOTICES.md`.
Changes currently target a source checkout installed in editable mode, Python 3.11+.
ComfyUI Desktop/GPU integration has only been tested on the documented Windows setup;
offline CI is separate from hardware support.

```sh
python -m pip install "hatchling>=1.27" "editables>=0.5"
python -m pip install --no-build-isolation -e ".[web,dev]"
python -m pytest -q
python -m ruff check src tests scripts examples
python examples/offline_review.py
comfy-demo workflow validate --all
```

Keep `config.local.toml`, prompts/images, model files, generated ZIPs and `runs` out of Git.
Never change the user's ComfyUI lifecycle or remove/overwrite image artifacts.
Do not edit the 12 historical source canvases. A deliberate API graph change must update
its version/hash/bindings together and include focused validation; never silently modify
an already recorded workflow. Do not patch plugin private storage or `node_modules`.

`legacy` is disabled historical source, excluded from maintained-source lint.
The default tests need no ComfyUI, network, models or reference images. Local source and
reference hashes are checked separately with `scripts/check_local_baselines.py` and
explicit local directories. Browser/GPU checks are manual integration tests that require
user-managed services; `--generate` creates retained images and must be deliberate.

For a change, describe the problem, resulting behavior, tests actually run and limitations.
Do not claim live GPU validation based on mocked backends or offline screenshots.
Before contributing third-party materials, establish their provenance and redistribution
permission. The licence decision/status in `THIRD_PARTY_NOTICES.md` takes precedence over
any assumptions that public visibility means permission to reuse all repository material.
