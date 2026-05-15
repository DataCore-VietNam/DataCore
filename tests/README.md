# Tests

`test_extensive.py` is a standalone test runner covering every public
method of the `datacore` client, the exception hierarchy, argument
validation, the pandas and polars code paths, and the internal helpers.

## Running

```bash
# From the repo root, with the package installed (pip install -e ".[dev]")
python tests/test_extensive.py
```

The runner has two tiers:

- **Offline assertions** — import checks, exception hierarchy, argument
  validation, static helpers, the demo `preview()` endpoint. These run
  unconditionally and are what CI executes.
- **Live paid-endpoint assertions** — `get_data`, `get_dataframe`,
  `get_polars`, `paginate`, `download_data`, etc. These run **only** when
  the `X_API_KEY` environment variable is set to a valid Datacore key:

  ```bash
  X_API_KEY=your-real-key python tests/test_extensive.py
  ```

  Without `X_API_KEY`, the live section is skipped (reported as SKIPPED,
  not failed).

The polars assertions run only when the `polars` extra is installed
(`pip install -e ".[dev]"` or `".[polars]"`); otherwise they are skipped
and the runner instead verifies that requesting `return_type="polars"`
raises a clear `ImportError`.

## Exit code

`0` if all assertions pass, `1` if any fail — suitable for CI gating.
