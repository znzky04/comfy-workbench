# Security and deployment boundary

This is a **single-user, local-only workbench**, not a multi-user or Internet-facing
generation service. It binds to loopback, checks Host headers and uses a per-process
request token for mutations. These are local browser protections, not user authentication.
Do not expose ports 8188/8199 through a proxy, tunnel or public listener.

- ComfyUI is user-managed. This project never starts, kills or updates it.
- Workflows, custom nodes and model files are executable/trusted local inputs.
  Only install them from sources you trust, after reviewing their licences.
- The repository does not ship model weights, reference images or generated images.
- Uploads are content-checked PNG/JPEG/WebP, subject to size and pixel limits.
  Uploaded references and outputs remain on the user's computer; there is no automatic
  deletion. Review disk usage yourself.
- Local manifests contain prompts, paths, seeds and reference hashes. Do not publish
  `runs`, local configuration, reference images or raw PNG metadata by accident.
- Image generation is performed by an upstream model. The workbench does not provide
  a content moderation service, and a successful job is not a quality or rights approval.

Report suspected vulnerabilities using the repository's GitHub **private vulnerability
reporting**, if enabled. Do not open a public issue containing tokens, personal prompts,
private images or filesystem details. If private reporting is unavailable, use an existing
private communication channel with the maintainer before sending sensitive details.
No response-time or supported-version security guarantee is currently offered.

Maintainers should enable private reporting and push protection where available before
public release. Scan all reachable history and review findings before changing visibility.
`scripts/audit_repository.py` is a redacted heuristic helper, not a security certification.
