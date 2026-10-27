# Azure Foundry IRL

An evidence-led Microsoft/Azure AI Foundry capability expo for executives, architects, developers, and cloud solution architects.

## What exists today

This is a **functional local foundation**, not the complete showcase or a live AI service:

- A self-contained, responsive `docs/index.html` microsite suitable for a later GitHub Pages publication. It works offline, has audience journeys, search/category/audience filters, concept details, and a downloadable learning brief.
- Nine original, synthetic capability concepts spanning models, agents, RAG, vision/documents, voice, media generation, fine-tuning, evaluation/safety/observability, and enterprise MCP/API integration.
- An offline architecture atlas with six source-grounded reference diagrams, unchanged official Microsoft product icons, SVG downloads, editable Excalidraw sources, and per-flow citations.
- A typed, read-only FastAPI backend serving public catalog metadata from `data/catalog.json`.
- Focused pytest tests covering API contracts, invalid/missing registries, explicit CORS, configuration, and static snapshot consistency. **34 tests passed** in the isolated Windows/Python 3.14 environment, with one upstream Starlette TestClient/httpx deprecation warning.

Integrated-browser checks also passed for the standalone file, nine disabled demo concepts, category/search filtering, light/dark switching, and a 390px mobile viewport. These results validate the foundation, not live AI execution or the unimplemented visitor controls.

A real local Uvicorn process also passed HTTP checks for health, catalog-only readiness, status, nine capabilities, and the explicit Pages CORS origin. Temporary validation servers were stopped afterward.

**Every live demo is NOT DEPLOYED, and execution is disabled.** Visitor approval, email OTP sign-in, backend-enforced 15-minute sessions, the maximum of three sessions per visitor per day, persistent security/accounting state, live SDK calls, and usage safeguards are **NOT IMPLEMENTED YET**. The USD100/month figure is a future budget target, not a measured cost or enforced spending cap. There are no enrollment, session, upload, or runnable demo endpoints.

The public microsite never asks for an email address, requests a microphone, calls an AI service, or automatically contacts the backend. Its learning brief holds selected public metadata in the current tab only; this is not authentication or a visitor session.

## Open the microsite

Open `docs\index.html` directly in a modern browser. No Node.js, npm, CDN, fonts, assets, build, or backend is required.

Alternatively, serve it locally using Python's standard library:

```powershell
py -3 -m http.server 8080 --bind 127.0.0.1 --directory docs
```

Visit `http://localhost:8080`. Light/dark mode follows the system initially, supports `?clawpilotTheme=light` or `?clawpilotTheme=dark`, and can be changed using the page button. Preferences and selections are not persisted.

On desktop and mobile, the hamburger **Menu** opens a modal navigation drawer containing the site sections and theme control. Escape, the backdrop, Close, or a destination link dismisses it. Keyboard focus stays inside the open drawer, then follows the selected section or returns to Menu.

GitHub Pages publication is not configured or performed here. The `docs` directory is the proposed static site root; do not publish `.env` files, private metadata, or `.copilot-azure`.

## Run the metadata API locally

Use Python **3.11 or newer**. The following commands create an isolated local environment; no Azure credentials or model deployments are needed.

### Windows / PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PORT = "8000"
.\.venv\Scripts\python.exe -m uvicorn foundry_showcase.main:app --app-dir src --host 0.0.0.0 --port $env:PORT --reload
```

`--reload` is for local development only. Binding `0.0.0.0` permits access through other network interfaces; use appropriate local firewall rules.

### Linux production process reference

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export PORT="${PORT:-8000}"
gunicorn --chdir src -w 1 -k uvicorn.workers.UvicornWorker foundry_showcase.main:app --bind "0.0.0.0:$PORT"
```

Gunicorn is conditionally included on non-Windows platforms; use Uvicorn for Windows local development. This process command does **not** make the foundation a production-ready public service. Dependency locking, security review, identity, persistence, network controls, hosting, and operational safeguards still require implementation and validation.

### Configuration

`.env.sample` is a reference, **not automatically loaded**. Set variables in your shell or eventual hosting configuration:

| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `8000` in the run commands | HTTP listening port, passed explicitly to the server process. |
| `CATALOG_PATH` | `data/catalog.json` | Local synthetic registry. Relative overrides resolve from the repository root, not the current shell directory. |
| `CORS_ALLOWED_ORIGINS` | `https://chadhage.github.io` | Comma-separated, explicit HTTP(S) origins. No credentials, wildcard, query, fragment, trailing slash, or URL path. |

For intentional local cross-origin metadata access, opt in explicitly:

```powershell
$env:CORS_ALLOWED_ORIGINS = "https://chadhage.github.io,http://localhost:8080,http://127.0.0.1:8080"
```

The Pages origin is `https://chadhage.github.io`, **not** its repository URL path. CORS permits GET metadata requests without credentials. It is a browser policy, **not authorization**; the catalog is deliberately anonymous and public.

### API contract

| Endpoint | Behavior |
|---|---|
| `GET /healthz` | Anonymous, direct `200 {"status":"ok"}`. No redirect and no dependency check. |
| `GET /readyz` | Re-reads and validates the registry. `200` when the **local catalog only** is ready; `503` otherwise. Always reports `live_demos_enabled: false`. |
| `GET /api/catalog` | Validated synthetic public metadata. Missing, unreadable, malformed, oversized, empty, duplicate-ID, or execution-enabled data yields a logged failure and `503`, not an empty successful fallback. |
| `GET /api/status` | Honest foundation stage, unimplemented controls, and explicitly unenforced future constraints. This is descriptive status, not a dependency readiness probe. |

No Azure/model/provider readiness is checked or claimed. Liveness remains healthy when the catalog fails, while catalog readiness and catalog retrieval fail closed. No cache hides a broken file, and no credentials or cloud clients are needed. Interactive framework API docs are disabled to avoid external UI assets.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

The tests do not contact Azure, execute models, install packages, or write test fixtures into system temporary directories. Browser/keyboard and responsive visual validation remain separate checks.

## Files and content maintenance

```text
data\catalog.json                  Canonical synthetic registry
docs\index.html                    Self-contained microsite and embedded snapshot
src\foundry_showcase\main.py        FastAPI application factory and metadata routes
src\foundry_showcase\models.py      Strict metadata and status contracts
src\foundry_showcase\registry.py    File-backed validation and explicit failure
src\foundry_showcase\settings.py    Explicit environment and CORS configuration
tests\                            API, registry, configuration, and snapshot tests
```

The microsite embeds a snapshot to remain genuinely self-contained, including when opened as a local file or served from a GitHub Pages project path. Until later publishing automation exists, update **both** `data/catalog.json` and the `catalog-data` JSON block in `docs/index.html`; a test detects drift. Keep only original synthetic, publishable content in both. There is intentionally no catalog write endpoint.

The feature-level availability, sources, model/region support, lifecycle, licensing, and pricing review is **pending**. The [official Microsoft Foundry overview](https://learn.microsoft.com/azure/ai-foundry/) is introductory background, not evidence that any concept here is deployed, generally available, certified, or supported in a particular region. The catalog contains proposed exercises and acceptance criteria, **not measured test results**. This project is not an official Microsoft product.

The architecture atlas has a **separate, dated verification register**. Its Microsoft sources and icon provenance are checked; this does not change the capability catalog's pending status or certify a running cloud deployment.

## Proposed architecture

The [showcase architecture](docs/architecture.md) records the agreed scope, proposed visitor access contract, phased live rollout, current retail cost estimate, official sources, and unresolved deployment gates. It is not a claim that those future controls or resources exist.

### Reference architecture atlas

- [Topology and sequence documentation](docs/reference-architectures.md): lean showcase topology, enterprise private-connectivity pattern, visitor/session admission, and grounded-agent request flow.
- [Ontology and data-quality guide](docs/ontology-and-data-quality.md): synthetic business vocabulary, Fabric IQ preview bindings, medallion layers, Purview assessment, and an explicitly owned publication gate.
- [Source verification register](docs/architecture-sources.md): public Microsoft citations, supported claim boundaries, and verification scope.
- [Official icon terms and provenance](docs/assets/icons/NOTICE.md): pinned packages, file digests, and unchanged artwork.

The atlas is generated from `data\architecture-atlas.json`. Rebuild offline or explicitly refresh the public-source checks:

```powershell
.\.venv\Scripts\python.exe scripts\build_architecture_atlas.py
.\.venv\Scripts\python.exe scripts\build_architecture_atlas.py --check
.\.venv\Scripts\python.exe scripts\build_architecture_atlas.py --verify-sources
.\.venv\Scripts\python.exe -m pytest tests\test_architecture_atlas.py tests\test_static_catalog.py
```

Default builds and `--check` do not contact Azure or the internet. Online verification checks public pages and evidence terms, not tenant entitlements, deployment readiness or architecture correctness by itself. After an upstream change, review the source meaning manually. No Mermaid/CDN renderer, external fonts, browser installation or new package dependency is required.

## Deliberately deferred

- Approved-visitor registration, email OTP identity, authorization, durable backend security state, race-safe session accounting, and abuse protection.
- Backend-enforced 15-minute sessions and three-sessions-per-visitor-per-day policy; cost metering, enforceable usage limits, and an operational budget response.
- Verified live model/service adapters, safe tool execution, data retention and privacy controls, and real evaluation/observability.
- Further architecture coverage, articles, expanded executable samples and tests, wiki, lean one-command deployment, and opt-in advanced modules.
- Azure infrastructure, Bicep, deployment YAML, Dockerfiles, CI, provisioning, and publication. Scaffolding approval has been received; deployment and publication have not.

No infrastructure or live execution should be inferred from this starter. Later deployment automation follows architecture approval; none is generated here.
