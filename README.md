# Datacore Python Client

Python client library for Datacore API with pandas support.

## Installation

```bash
# From local directory
pip install -e .

# Or build and install
pip install .
```

## Quick Start

### Using environment variable (recommended)

```python
import os
from datacore import Datacore

# Set your API key
os.environ["X_DATACORE_API_KEY"] = "your-api-key"

# Create client
client = Datacore()

# Get data as DataFrame
df = client.get_historical_price(limit=50)
print(df.head())
```

### Passing API key directly

```python
from datacore import Datacore

client = Datacore(api_key="your-api-key")
df = client.get_historical_price(limit=50)
```

## Usage Examples

### Get historical price data

```python
client = Datacore()

# Simple query
df = client.get_historical_price(page=1, limit=100)

# With conditions and field selection
df = client.get_historical_price(
    conditions=[{"field": "symbol", "value": "ABC"}],
    select_fields=["symbol", "price", "date"],
    limit=50
)
```

### Generic search method

```python
# Returns raw response
response = client.search(
    dataset_code="dataset_historical_price",
    limit=10
)

# Get as DataFrame
df = client.get_dataframe(
    dataset_code="dataset_historical_price",
    limit=10
)
```

## Configuration

The client reads API key from `X_DATACORE_API_KEY` environment variable by default.

### Setting environment variable

**On Windows (PowerShell):**
```powershell
$env:X_DATACORE_API_KEY = "your-api-key"
```

**On Windows (Command Prompt):**
```cmd
set X_DATACORE_API_KEY=your-api-key
```

**On Linux/Mac:**
```bash
export X_DATACORE_API_KEY="your-api-key"
```

Or add to `.env` file and use python-dotenv:
```python
from dotenv import load_dotenv
load_dotenv()
from datacore import Datacore
client = Datacore()
```

## API Reference

### `Datacore(api_key=None)`

Initialize Datacore client.

**Parameters:**
- `api_key` (str, optional): Your Datacore API key. If not provided, uses `X_DATACORE_API_KEY` env variable.

**Raises:**
- `ValueError`: If API key is not provided and not found in environment.

### `search(dataset_code, conditions=None, select_fields=None, page=1, limit=10, **kwargs)`

Execute a generic search query.

**Returns:** Dictionary with API response

### `get_dataframe(dataset_code, conditions=None, select_fields=None, page=1, limit=10, **kwargs)`

Execute query and return result as pandas DataFrame.

**Returns:** pandas.DataFrame

### `get_historical_price(conditions=None, select_fields=None, page=1, limit=10, **kwargs)`

Convenience method for historical price dataset.

**Returns:** pandas.DataFrame

## Requirements

- Python >= 3.7
- requests >= 2.28.0
- pandas >= 1.0.0

## License

MIT
