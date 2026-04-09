# Datacore Python Client

Simple Python client library for Datacore API - with two access tiers:
- **DEMO Tier**: Browse datasets without authentication
- **Full Tier**: Unlimited access with API key or token

## Features

✅ **DEMO Mode** - Preview datasets without creating an account  
✅ **API Key Authentication** - For server-to-server access  
✅ **Token Authentication** - For user account access  
✅ **Pandas Support** - Get data as DataFrames  
✅ **Automatic Retries** - Exponential backoff for network resilience  
✅ **Pagination** - Handle large datasets efficiently  

## Installation

```bash
pip install -e .
```

## Quick Start - Three Ways

### 1️⃣ DEMO Mode (No Login Needed)

```python
from datacore import Datacore

# No credentials required!
client = Datacore()

# Preview any dataset
preview = client.preview("vsic")
print(preview)

# List all datasets
datasets = client.list_datasets()
print(datasets)
```

### 2️⃣ With API Key

```python
from datacore import Datacore

# Using API key from environment
client = Datacore()

# Or pass directly
client = Datacore(api_key="your-key-here")

# Search data
data = client.search("vsic", limit=100)
```

### 3️⃣ With Login Token

```python
from datacore import AuthManager, Datacore

# Login
token = AuthManager.login("email@example.com", "password")

# Create authenticated client
client = Datacore(token=token)

# Search data
data = client.search("vsic", limit=100)
```

---

## API Reference

### DEMO Methods (No Authentication Required)

#### `preview(dataset_code: str) -> Dict`
Get sample records from a dataset.
```python
client = Datacore()
preview = client.preview("vsic")
# Returns: {"status": true, "data": {"fields": [...], "dataDetail": [...]}}
```

#### `list_datasets() -> Dict`
List all public datasets.
```python
datasets = client.list_datasets()
```

#### `get_dataset_info(dataset_code: str) -> Dict`
Get metadata about a dataset.
```python
info = client.get_dataset_info("vsic")
```

---

### Authenticated Methods (Requires API Key or Token)

#### `search(dataset_code, conditions=None, select_fields=None, page=1, limit=10) -> Dict`
Search data in the dataset.
```python
data = client.search(
    dataset_code="vsic",
    conditions=[{"field": "Level", "operator": "=", "value": "1"}],
    select_fields=["Code", "Name"],
    limit=100
)
```

#### `get_dataframe(dataset_code, ...) -> pd.DataFrame`
Get search results as pandas DataFrame.
```python
df = client.get_dataframe("vsic", limit=100)
df.to_csv("data.csv")
```

#### `paginate(dataset_code, max_pages=None, limit=100) -> Generator`
Generator for paginated results.
```python
for df in client.paginate("vsic", limit=1000, max_pages=10):
    process_data(df)
```

#### `fetch_all(dataset_code, max_records=None, limit=100) -> pd.DataFrame`
Fetch all data at once.
```python
df = client.fetch_all("vsic", max_records=50000)
```

---

## Configuration

Create `.env` file in your project:

```env
# For authenticated access (optional)
X_DATACORE_API_KEY=your-api-key-here

# For login authentication (optional)
DATACORE_USERNAME=your-email@example.com
DATACORE_PASSWORD=your-password

# API Settings (usually no changes needed)

API_TIMEOUT=30
API_MAX_RETRIES=3
```

**Security**: Add `.env` to `.gitignore` - never commit credentials!

---

## Examples

### Example 1: Explore Datasets (DEMO Tier)

```python
from datacore import Datacore

client = Datacore()

# What datasets are available?
datasets = client.list_datasets()
print(f"Available: {len(datasets['data'])} datasets")

# Preview VSIC industry codes
preview = client.preview("vsic")
fields = preview['data']['fields']
records = preview['data']['dataDetail']
print(f"VSIC: {len(records)} sample records with {len(fields)} fields")
```

### Example 2: Search & Analyze (Full Tier)

```python
from datacore import Datacore
import pandas as pd

client = Datacore(api_key="your-key")

# Get data as DataFrame
df = client.get_dataframe("vsic", limit=1000)

# Analyze
print(df.groupby("Level").size())
df.to_csv("vsic_analysis.csv")
```

### Example 3: Batch Processing

```python
from datacore import Datacore

client = Datacore(api_key="your-key")

# Process in chunks
total = 0
for df in client.paginate("vsic", limit=5000):
    total += len(df)
    process_batch(df)
print(f"Total records: {total}")
```

---

## Documentation

- **[DEMO_USAGE_GUIDE.md](DEMO_USAGE_GUIDE.md)** - Comprehensive guide with all features
- **[ENV_SETUP.md](ENV_SETUP.md)** - Configuration and security best practices
- **[EXTENSION_GUIDE.md](EXTENSION_GUIDE.md)** - How to add new datasets/methods

---

## Two Access Tiers Explained

| Feature | DEMO Mode | Full Tier |
|---------|-----------|-----------|
| No login required | ✅ | ❌ |
| Preview datasets | ✅ | ✅ |
| Search/filter | ❌ | ✅ |
| Export data | ❌ | ✅ |
| Pagination | ❌ | ✅ |
| API key required | ❌ | ✅ |
| Best for | Exploration | Analysis |

---

## Troubleshooting

**Q: How do I get started without credentials?**  
A: Use DEMO mode! Call `client.preview()` with no setup.

**Q: I get "UnAuthorizedException"**  
A: Your API key is invalid. Check `.env` or use DEMO mode first.

**Q: My request times out**  
A: Try increasing timeout: `Datacore(timeout=60)`

---

## Support

- 📧 Email: support@datacore.vn
- 📊 [Datacore Portal](https://datacore.vn)
- 📖 See [DEMO_USAGE_GUIDE.md](DEMO_USAGE_GUIDE.md) for full documentation

