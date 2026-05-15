# Changelog

All notable changes to `datacore` are recorded here. This project follows
[Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH).

## [0.2.0] - 2026-05-14

First publicly stable release.

> **Distribution name**: the package is published on PyPI as
> `datacore-vn` because the shorter `datacore` slot is held by an
> unrelated 2022 abandoned project (single release, no description).
> The import name is unchanged: `import datacore`. A PEP 541 request
> to reclaim the canonical `datacore` name is in flight.

### Added
- **Polars support** as an optional dependency. Install with
  `pip install "datacore[polars]"`. New `Datacore.get_polars()`
  convenience method, plus `return_type="polars"` on both `get_data()`
  and `preview()`.
- `debug=True` constructor flag prints request payload + response.
- `Datacore.get_dataframe()` convenience that returns a pandas DataFrame
  directly (no `{"data", "info"}` wrapper).
- `download_data(columns=[...])` parameter that actually filters the
  output CSV (previously the kwarg was silently swallowed).
- `download_data` validates `start_page < 1` and
  `end_page < start_page`.
- `_check_body_error()` inspects 200-OK responses with body
  `{"status": false, "httpCode": 401, ...}` and raises the correct
  `AuthenticationError` / `PermissionDeniedError`.
- `py.typed` marker so downstream type checkers can see annotations.
- LICENSE (MIT), `.env.example`, GitHub Actions CI + PyPI publishing
  workflows.

### Fixed
- `paginate()` called a non-existent `self.get_dataframe()` method,
  raising `AttributeError` on first iteration. Method now exists.
- `AuthenticationError` base class had a leftover edit artifact
  (`DatoreError if False else DatacoreError`) — restored to
  `DatacoreError`.
- `preview_raw()` used bare `requests.get`, bypassing the session and
  its configured headers / connection pool. Now uses `self.session.get`.
- `preview()` on an unknown dataset raised a misleading
  `Cannot parse preview response: success`. Now raises a clear
  `Dataset '...' not found or has no preview data.`
- `get_data(return_type=...)` validation only fired after the network
  call. Moved to the top of the method to fail fast.
- `Datacore()` only resolved `X_API_KEY` from `.env` (read once at
  module import). Now resolves from explicit arg → `os.environ` → `.env`
  on every instance construction.

### Changed
- `requires-python` bumped from `>=3.8` to `>=3.9`. Pandas 2.1+ dropped
  3.8; pandas 3.0 requires 3.11.
- `pyproject.toml` populated with author, license, classifiers,
  keywords, project URLs.
- `__author__` no longer reads "Your Name".
- README rewritten with all current methods documented, polars examples,
  observed `limit=100` gateway cap, and a note about the `conditions`
  filter format being gateway-defined.

### Removed
- **Trang's local Windows venv that was committed into the package
  directory** (24 `.exe` files, activate scripts, and a `pyvenv.cfg`
  containing the path `C:\Users\tranglt\Desktop\package_datacore\datacore`).
  This was shipping inside every wheel install.
- The hardcoded API key in `test_demo.ipynb`. Cell now reads
  `X_API_KEY` from environment. Outputs cleared from every cell.

### Security
- A previously committed API key was removed from `test_demo.ipynb` and
  scrubbed from the git history with `git filter-repo`. The credential
  has been rotated server-side and is no longer valid.

[0.2.0]: https://github.com/DataCore-VietNam/DataCore/releases/tag/v0.2.0
