# Datacore Python Client - Usage Guide

## Quick Start

### 1. Installation (DEMO Mode - No Auth Required)

```bash
# Install the library
pip install -e .

# For preview/list datasets without authentication
from datacore import Datacore

client = Datacore()
preview = client.preview("vsic")
print(preview)
```

### 2. Two Tiers of Access

#### TIER 1: DEMO (No Authentication Required)
Perfect for customers who want to **explore datasets before creating an account**.

```python
from datacore import Datacore

# Create client in DEMO mode (no credentials needed)
client = Datacore()

# Preview any dataset
preview = client.preview("vsic")
print(preview)
# Response: {"status": true, "data": {"fields": [...], "dataDetail": [...]}}

# List all available datasets
datasets = client.list_datasets()
print(datasets)

# Get dataset info
info = client.get_dataset_info("vsic")
print(info)
```

**Available Endpoints (DEMO):**
- `preview(dataset_code)` - Get dataset preview with sample records
- `list_datasets()` - List all public datasets
- `get_dataset_info(dataset_code)` - Get dataset metadata

---

#### TIER 2: AUTHENTICATED (With API Key or Token)
For registered users with full data access.

##### Option A: Using API Key

```python
from datacore import Datacore

# Create client with API key
client = Datacore(api_key="your-api-key-here")

# Now you can search the full dataset
data = client.search(
    dataset_code="vsic",
    conditions=[],
    select_fields=["ID", "Code", "Name"],
    limit=100,
    page=1
)
print(data)
```

##### Option B: Using Token (Login)

```python
from datacore import Datacore, AuthManager

# Login to get a token
token = AuthManager.login("your-email@example.com", "your-password")

# Create client with token
client = Datacore(token=token)

# Search data
data = client.search(
    dataset_code="vsic",
    limit=100
)
```

---

## Advanced Usage

### Get Data as DataFrame

```python
from datacore import Datacore

client = Datacore(api_key="your-key")

# Get search results as pandas DataFrame
df = client.get_dataframe(
    dataset_code="vsic",
    limit=100
)

print(df.head())
```

### Pagination - Get Large Datasets

```python
from datacore import Datacore

client = Datacore(api_key="your-key")

# Generator for paginated results
for df in client.paginate("vsic", limit=1000, max_pages=10):
    print(f"Got {len(df)} records")
    # Process each page
    process_data(df)
```

### Fetch All Data

```python
from datacore import Datacore

client = Datacore(api_key="your-key")

# Get entire dataset (be careful with large datasets)
df = client.fetch_all(
    dataset_code="vsic",
    max_records=50000,
    limit=1000
)

print(f"Total records: {len(df)}")
```

---

## Configuration

All endpoints and settings are configured via `.env` file:


---

## API Reference

### Datacore Class

#### DEMO Methods (No Authentication)

**`preview(dataset_code: str) -> Dict`**
- Get sample data from a dataset
- Perfect for DEMO tier users
- No authentication required
- Returns: `{"status": true, "data": {"fields": [...], "dataDetail": [...]}}`

**`list_datasets() -> Dict`**
- Get list of all available datasets
- No authentication required
- Returns dataset list

**`get_dataset_info(dataset_code: str) -> Dict`**
- Get metadata about a dataset
- No authentication required

#### Authenticated Methods

**`search(dataset_code, conditions=None, select_fields=None, page=1, limit=10) -> Dict`**
- Search data in authenticated mode
- Requires API key or token
- Supports filtering with conditions
- Returns paginated results

**`get_dataframe(dataset_code, ...) -> pd.DataFrame`**
- Same as search() but returns pandas DataFrame
- Easier for data analysis

**`paginate(dataset_code, max_pages=None, limit=100) -> Generator`**
- Generator for large datasets
- Automatically handles pagination

**`fetch_all(dataset_code, max_records=None, limit=100) -> pd.DataFrame`**
- Fetch all data at once
- Be careful with memory usage for large datasets

---

## Authentication Manager

### Login

```python
from datacore import AuthManager

# Get token by login
token = AuthManager.login("email@example.com", "password")

# Use token to create authenticated client
from datacore import Datacore
client = Datacore(token=token)
```

---

## Error Handling

The client includes automatic retry with exponential backoff for network errors:

```python
from datacore import Datacore

client = Datacore()

try:
    preview = client.preview("vsic")
except requests.RequestException as e:
    print(f"Network error: {e}")
except ValueError as e:
    print(f"Validation error: {e}")
```

---

## Environment Variables

Create a `.env` file in your project root:

```env
# Required for authenticated access
X_DATACORE_API_KEY=your-key-here

# Optional (use if you have a token already)
X_DATACORE_ACCESS_TOKEN=your-token-here

# Optional (use for login authentication)
DATACORE_USERNAME=your-email@example.com
DATACORE_PASSWORD=your-password

# API Endpoints (usually don't need to change)


# Settings
API_TIMEOUT=30
API_MAX_RETRIES=3
```

**Security Note**: Never commit `.env` to version control. Use `.env.example` for sharing without credentials.

---

## Examples

### Example 1: Customer Exploration (DEMO Tier)

```python
from datacore import Datacore

# No credentials needed
client = Datacore()

# Browse available datasets
datasets = client.list_datasets()
for dataset in datasets['data']:
    print(f"- {dataset['code']}: {dataset['name']}")

# Preview the VSIC dataset
preview = client.preview("vsic")
print(f"VSIC has {len(preview['data']['dataDetail'])} sample records")
print(f"Fields: {[f['name'] for f in preview['data']['fields']]}")
```

### Example 2: Full Access (Authenticated Tier)

```python
from datacore import Datacore

# Create authenticated client
client = Datacore(api_key="your-key")

# Search with filters
data = client.search(
    dataset_code="vsic",
    conditions=[
        {"field": "Level", "operator": "=", "value": "1"}
    ],
    select_fields=["Code", "Name", "Level"],
    limit=50
)

# Convert to DataFrame
df = client.get_dataframe(
    dataset_code="vsic",
    limit=1000
)

# Save to CSV
df.to_csv("vsic_data.csv", index=False)
```

### Example 3: Batch Processing

```python
from datacore import Datacore
import pandas as pd

client = Datacore(api_key="your-key")

# Process in chunks
all_data = []
for df in client.paginate("vsic", limit=5000, max_pages=20):
    # Process each batch
    df_filtered = df[df['Level'] == 2]
    all_data.append(df_filtered)

# Combine all data
result = pd.concat(all_data, ignore_index=True)
print(f"Total records after filtering: {len(result)}")
```

---

## Troubleshooting

### Q: I get "API Key not provided" error
A: Set `X_DATACORE_API_KEY` in your `.env` file OR pass `api_key` parameter when creating client.

### Q: Preview works but search fails
A: Make sure your API key is valid. Try testing with `client.preview()` first (no auth needed).

### Q: How do I know which datasets are available?
A: Call `client.list_datasets()` - no authentication required!

### Q: My preview request times out
A: Check your internet connection. You can increase timeout: `Datacore(timeout=60)`

---

## Support

For issues or questions:
1. Check configuration in `.env`
2. Try DEMO endpoints first - `preview()`, `list_datasets()`
3. Verify API key is correct
4. Check network connectivity

