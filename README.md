# Datacore Python Client

[![PyPI version](https://img.shields.io/pypi/v/datacore-vn.svg)](https://pypi.org/project/datacore-vn/)
[![Python versions](https://img.shields.io/pypi/pyversions/datacore-vn.svg)](https://pypi.org/project/datacore-vn/)
[![CI](https://github.com/DataCore-VietNam/DataCore/actions/workflows/ci.yml/badge.svg)](https://github.com/DataCore-VietNam/DataCore/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/pypi/l/datacore-vn.svg)](https://github.com/DataCore-VietNam/DataCore/blob/main/LICENSE)

Python client library for the Datacore API — supports two access modes:

- **Demo**: Preview datasets without an API key
- **Paid**: Full access with an API key

> **Distribution name vs. import name**: install as `datacore-vn`, import as
> `datacore`. (Same pattern as `pip install scikit-learn` → `import sklearn`.)
> The shorter `datacore` distribution name on PyPI is a 2022 abandoned
> project unrelated to us; we have a request open to reclaim it.

## Installation

From PyPI:

```bash
pip install datacore-vn                # core (pandas-only)
pip install "datacore-vn[polars]"      # also installs polars
pip install "datacore-vn[all]"         # all optional extras
```

Or with `uv`:

```bash
uv add datacore-vn
uv add "datacore-vn[polars]"
```

From GitHub directly:

```bash
pip install git+https://github.com/DataCore-VietNam/DataCore.git
pip install "datacore-vn[polars] @ git+https://github.com/DataCore-VietNam/DataCore.git"
```

For contributors only (you do **not** need this to use the library — the
commands above are all an end user needs):

```bash
git clone https://github.com/DataCore-VietNam/DataCore.git
cd DataCore
pip install -e ".[dev]"
```

## Configuration (`.env`, optional)

Create a `.env` file in your working directory (see `.env.example`):

```env
X_API_KEY=your-api-key-here
```

> **Never commit your real API key.** `.env` is git-ignored. Use `.env.example` as a template.

---

## Usage

### 1. Initialize the client

```python
from datacore import Datacore

# Demo mode (no API key required)
client = Datacore()

# Paid mode — pass the key explicitly...
client = Datacore(api_key="your-api-key")

# ...or rely on X_API_KEY from .env / environment
client = Datacore()

# Enable request/response debug logging
client = Datacore(api_key="your-api-key", debug=True)
```

---

### 2. Preview a dataset (Demo mode)

Preview data without an API key.

```python
# All columns
df = client.preview("dataset_historical_price")
print(df.head())

# Filter specific columns
df = client.preview("dataset_historical_price", columns=["symbol", "date", "close_price"])
print(df.head())
```

---

### 3. Fetch data (Paid mode)

```python
# All columns — returns {"data": DataFrame, "info": str}
result = client.get_data("dataset_historical_price")
print(result["data"].head())
print(result["info"])
# num: 3760607, totalPage: 37607, currentPage: 1, queried_rows: 100

# Filter specific columns
result = client.get_data(
    "dataset_historical_price",
    columns=["symbol", "date", "close_price"],
)
print(result["data"].head())
```

Full parameters:

```python
result = client.get_data(
    dataset_code="dataset_historical_price",
    columns=["symbol", "date", "close_price"],   # client-side column filter (optional)
    conditions=None,         # server-side row filter -- see note below (optional)
    select_fields=None,      # server-side field selection (optional)
    page=1,
    limit=100,               # max 100 server-side (HTTP 400 if higher)
    return_type="dataframe", # "dataframe" | "polars" | "json" | "dict"
    include_info=True,       # True: returns {"data": ..., "info": ...} | False: data only
)
```

> **Page size**: the gateway currently caps `limit` at **100** rows per
> request. Passing a larger value returns `HTTP 400: Invalid request content`.
> For larger downloads, paginate with `download_data` or `paginate`.

> **`conditions` format**: the server-side `conditions` filter is forwarded
> to the gateway verbatim. The exact accepted JSON shape is defined by the
> gateway, not by this client; the shape that worked in earlier internal
> examples is **not** currently accepted by `gateway.datacore.vn/data/ds/search`.
> Contact the Datacore backend team for the documented filter schema before
> relying on `conditions` in production. As a workaround you can fetch
> unfiltered data and filter client-side on the returned DataFrame.

A convenience wrapper that returns the DataFrame directly (no info dict):

```python
df = client.get_dataframe("dataset_historical_price", limit=100)
```

---

### 3b. Polars output (optional)

If you installed with `pip install "datacore-vn[polars]"`, you can ask for a
[polars](https://pola.rs/) `DataFrame` instead of pandas:

```python
# Via return_type
result = client.get_data(
    "dataset_historical_price",
    columns=["symbol", "date", "close_price"],
    limit=100,
    return_type="polars",
)
print(type(result["data"]))     # <class 'polars.DataFrame'>
print(result["data"].head())

# Convenience method (no info dict, just the polars frame)
df_pl = client.get_polars("dataset_historical_price", limit=100)

# Preview supports polars too
df_pl = client.preview("dataset_historical_price", return_type="polars")
```

Pandas is the default for backwards compatibility; polars is purely opt-in.
The same `columns=` filter works for both backends.

---

### 4. Iterate all pages (Paid mode)

```python
for page_df in client.paginate("dataset_historical_price", limit=100, max_pages=5):
    print(page_df.shape)
```

---

### 5. Download data to file

```python
# Download all pages of a small dataset (76 pages, ~7.5k rows)
download_result = client.download_data(
    dataset_code="gross_domestic_product_dataset_ds",
    output_path="data.csv",
    file_format="csv",     # "csv" or "json"
    start_page=1,
    end_page=None,         # None = download until the last page
    limit=100,             # max per-request page size (see note above)
    show_progress=True,
)
print(download_result)
# {"output_path": "data.csv", "pages_downloaded": 76, "rows_downloaded": 7551, ...}

# `dataset_historical_price` is large (~3.7M rows / 37k pages at limit=100);
# expect it to take a long time and a lot of network.

# Download only first 3 pages, filtered to specific columns (CSV only)
download_result = client.download_data(
    dataset_code="dataset_historical_price",
    columns=["symbol", "date", "close_price"],
    output_path="data_page1_3.csv",
    file_format="csv",
    start_page=1,
    end_page=3,
    show_progress=True,
)
```

> `columns` filtering only applies to `file_format="csv"`. JSON output preserves the full raw API response.

---

## Method Summary

| Method | Description | Requires API key |
|---|---|---|
| `preview(dataset_code, columns, return_type)` | Preview a dataset (pandas or polars) | No |
| `preview_raw(dataset_code)` | Preview a dataset, raw dict response | No |
| `get_data(dataset_code, ...)` | Fetch data, returns `{"data", "info"}` by default | Yes |
| `get_dataframe(dataset_code, ...)` | Fetch data, returns pandas DataFrame directly | Yes |
| `get_polars(dataset_code, ...)` | Fetch data, returns polars DataFrame directly *(needs `[polars]` extra)* | Yes |
| `get_data_info(dataset_code, ...)` | Get dataset metadata summary | Yes |
| `paginate(dataset_code, ...)` | Generator yielding one pandas DataFrame per page | Yes |
| `download_data(dataset_code, output_path, ...)` | Download data to CSV/JSON file | Yes |
| `set_api_key(api_key)` | Set / replace the API key on an existing client | — |
| `is_authenticated()` | Returns `True` if an API key is configured | — |

---

## Error Handling

| Error | Cause | Solution |
|---|---|---|
| `AuthenticationError` | Missing or invalid API key (HTTP 401 or `httpCode:401` in body) | Pass `api_key=` or set `X_API_KEY` in `.env` |
| `PermissionDeniedError` | No access to dataset (HTTP 403) | Check your subscription plan |
| `APIRequestError` | Server error, invalid request, or unknown dataset | Check `dataset_code` and `conditions` |
| `ValueError` | Bad argument (e.g. unknown column, `page < 1`, bad `file_format`) | Check the error message |

All exceptions inherit from `DatacoreError`, so you can catch them generically:

```python
from datacore import Datacore, DatacoreError

try:
    client.get_data("dataset_historical_price")
except DatacoreError as e:
    print(f"Datacore call failed: {e}")
```

---

## License

MIT — see [LICENSE](LICENSE).
