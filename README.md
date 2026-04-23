# Datacore Python Client

Python client library for the Datacore API — supports two access modes:
- **Demo**: Preview datasets without an API key
- **Paid**: Full access with an API key

## Installation

```bash
pip install -e .
```

## Configuration (`.env`, optional)

```env
X_API_KEY=your-api-key-here
DATACORE_GATEWAY_URL=https://gateway.datacore.vn
```

---

## Usage

### 1. Initialize the client

```python
from datacore import Datacore

# Demo mode (no API key required)
client = Datacore()

# Paid mode
client = Datacore(api_key="your-api-key")
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
result = client.get_data("dataset_historical_price", columns=["symbol", "date", "close_price"])
print(result["data"].head())
print(result["info"])
```

Full parameters:

```python
result = client.get_data(
    dataset_code="dataset_historical_price",
    columns=["symbol", "date", "close_price"],  # filter columns (optional)
    conditions=[{"field": "symbol", "operator": "=", "value": "AAA"}],  # filter rows (optional)
    select_fields=[],        # select fields from API (optional)
    page=1,
    limit=100,
    return_type="dataframe", # "dataframe" | "json" | "dict"
    include_info=True,       # True: returns {"data": ..., "info": ...} | False: returns data directly
)
```

---

### 4. Get dataset info

```python
info = client.get_data_info("dataset_historical_price")
print(info)
# num: 3760607, totalPage: 37607, currentPage: 1, queried_rows: 100
```

---

### 5. List all datasets (Paid mode)

```python
df = client.list_datasets()
print(df)
```

---

### 6. Download data to file

```python
# Download all pages
download_result = client.download_data(
    dataset_code="dataset_historical_price",
    output_path="data.csv",
    file_format="csv",   # "csv" or "json"
    start_page=1,
    end_page=None,       # None = download all pages
    limit=1000,
    show_progress=True,
)
print(download_result)
# {"output_path": "data.csv", "pages_downloaded": 37607, "rows_downloaded": 3760607, ...}

# Download only first 3 pages
download_result = client.download_data(
    dataset_code="dataset_historical_price",
    output_path="data_page1_3.csv",
    file_format="csv",
    start_page=1,
    end_page=3,
    limit=1000,
    show_progress=True,
)
```

---

## Method Summary

| Method | Description | Requires API key |
|---|---|---|
| `preview(dataset_code, columns)` | Preview dataset | No |
| `get_data(dataset_code, columns, ...)` | Fetch data, returns `{"data", "info"}` | Yes |
| `get_data_info(dataset_code, ...)` | Get dataset summary info | Yes |
| `list_datasets()` | List all available datasets | Yes |
| `download_data(dataset_code, output_path, ...)` | Download data to CSV/JSON file | Yes |

---

## Error Handling

| Error | Cause | Solution |
|---|---|---|
| `AuthenticationError` | Missing or invalid API key | Pass `api_key=` or set `X_API_KEY` in `.env` |
| `PermissionDeniedError` | No access to dataset | Check your subscription plan |
| `APIRequestError` | Server error or invalid request | Check `dataset_code` and `conditions` |
| `ValueError` | Column name not found | Check available columns in the error message |
