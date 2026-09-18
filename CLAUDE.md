# CLAUDE.md

Guidance for Claude Code (claude.ai/code) agents working in this repository.

## Always read `CODE_STYLE.md` first

Before creating, renaming or restructuring any file/class/function, **read [`CODE_STYLE.md`](./CODE_STYLE.md)**. It is the single source of truth for conventions: language, file organisation, naming, typing, properties vs `__init__`, imports, docstrings, comments, coordinator pattern, repairs/diagnostics layout, translations, lint workflow.

For user-facing topics (what the integration does, installation, options, entities), see [`README.md`](./README.md).

This file deliberately avoids restating those rules — it only adds:

1. The verification workflow agents must run after every change.
2. The architectural reasoning that is not obvious from `CODE_STYLE.md` alone.

## Verification workflow

**After every code change, always run lint then tests, in that order, before declaring the task done. Either run `scripts/lint` (a thin wrapper that only chains the four commands) or run them directly:**

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy custom_components/correios
uv run pytest
node --check custom_components/correios/www/correios-card.js
```

- Lint runs `ruff format`, `ruff check` and `mypy` — all configured in `pyproject.toml`. Fix any failure and re-run before moving on.
- `pytest` enforces a **90 % coverage gate** (`--cov-fail-under` in `pyproject.toml`).

Both gates mirror CI (`.github/workflows/ci.yml`). Skip this only when the change literally cannot affect lint or tests (e.g., README-only edits).

## Bumping the Home Assistant version

The Home Assistant version is pinned in two places and **must be updated together**, otherwise CI, HACS and the test harness drift apart:

1. `pyproject.toml` `[dependency-groups] dev` — `homeassistant==<X.Y.Z>` (runtime/CI lint + mypy) **and** `pytest-homeassistant-custom-component==<matching release>` (the test harness ships its own pinned `homeassistant`; the two pins must come from the same HA release, otherwise lint and tests resolve different cores).
2. `hacs.json` — `"homeassistant": "<X.Y.Z>"` (minimum HA core enforced by HACS).

Verify the pairing on PyPI before committing: the `requires_dist` of `pytest-homeassistant-custom-component` must list the same `homeassistant==<X.Y.Z>` you pinned in `pyproject.toml`.

## Conventions not obvious from the code

The integration follows the HA `DataUpdateCoordinator` pattern. A few choices are not evident from reading a single file:

- State lives on `entry.runtime_data` (auto-discarded on unload), **never** on `hass.data`.
- `data/__init__.py` holds the `type` aliases (`CorreiosConfigEntry`, `CorreiosPackages`, `Json*`) **and** re-exports every symbol from the sibling modules, so downstream code imports everything from `.data`.
- **There is no official API.** `api.py` drives the public tracking website: the single sign-on form at `cas.correios.com.br` (a hidden `execution` token plus username/password), then the JSON endpoints the website's own JavaScript calls (`app/controle.php` for the session status, `app/rastrocpfcnpj.php` for the packages). Authentication is cookie based, so the client **must** receive a session created with `async_create_clientsession` — the shared Home Assistant session would mix cookie jars.
- The package listing answers an anonymous request with an empty list (`[]`) instead of an error. `async_get_packages` therefore checks the session status before trusting an empty answer and logs in again when the session expired; only a rejected login (HTTP 401 from the sign-on form) becomes `CorreiosApiClientAuthenticationError` → `ConfigEntryAuthFailed` → reauth.
- `package_parser.py` is the only place that knows the website's field names (Portuguese, inconsistent casing). Everything above it works with the `CorreiosPackage` / `CorreiosPackageEvent` dataclasses.
- The coordinator payload is `dict[tracking_code, CorreiosPackage]`, already filtered: packages in transit plus the ones delivered within the `delivered_retention_days` option. `coordinator.latest_changes` holds what `package_changes.py` detected against the previous payload; the event entity announces those and nothing is announced on the first refresh.
- `sensor.py` adds a `CorreiosPackageSensor` per new tracking code and removes the entity registry entries of packages that left the payload — on every coordinator update and once at setup, which also clears leftovers from while Home Assistant was down.
- Entity classes live one per file under `sensors/`; `sensor.py` only wires the platform.
- The companion card lives in `www/correios-card.js` (zero-build vanilla web component, translations embedded) and is served under `/correios`. `card_registration.py` registers it as a **Lovelace dashboard resource** with `?v=<integration version>-<card content fingerprint>` as cache-buster, so an edited card invalidates browser caches even without a version bump — not through `add_extra_js_url`, which races the frontend at startup; that route remains only as the fallback for YAML-mode resources. The card discovers package sensors through `hass.entities` (`platform == "correios"`, `translation_key == "package"`), so it depends on those two values staying stable.
- Diagnostics never include tracking codes or free-text details: a tracking code identifies a person's parcel.
