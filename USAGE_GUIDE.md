# Usage Guide - Datacore Python Client

## Installation

```bash
cd package_datacore
pip install -e .
```

## Setup Authentication

### Tạo file `.env`

```env
# API Key (bắt buộc)
X_DATACORE_API_KEY=your-api-key-here

# URLs (optional)
DATACORE_BASE_URL=https://gateway.datacore.vn/data/ds
DATACORE_LOGIN_URL=https://gateway.datacore.vn/auth/login
```

> **Security**: Thêm `.env` vào `.gitignore`, không commit credentials.

---

## Authentication

### Method 1: API Key (Recommended)

API key được đọc từ file `.env`.

```python
from datacore import Datacore

# Đọc API key từ .env
client = Datacore()

# Hoặc truyền trực tiếp
client = Datacore(api_key="your-api-key")
```

### Method 2: Token (Login)

```python
from datacore import AuthManager, Datacore

# Login lấy token
token = AuthManager.login("email@example.com", "password")

# Tạo client với token
client = Datacore(token=token)
```

**Thứ tự ưu tiên**: token > api_key parameter > `X_DATACORE_API_KEY` trong `.env`

---

## Gọi API

### Search Data

```python
response = client.get_data(
    dataset_code="vsic",
    conditions=[
        {"field": "Level", "operator": "=", "value": "1"}
    ],
    select_fields=["Code", "Name"],
    page=1,
    limit=100
)
print(response)
```

### Preview Dataset

```python
response = client.preview("vsic")
print(response)
```

---

## Error Handling

```python
from datacore import Datacore
import requests

try:
    client = Datacore()
    response = client.get_data("vsic", limit=10)
except ValueError as e:
    print(f"Auth error: {e}")
except requests.RequestException as e:
    print(f"Network error: {e}")
```

Client tự động retry 3 lần với exponential backoff khi gặp lỗi network.

---

## Environment Variables

| Variable | Mô tả | Bắt buộc |
|----------|--------|----------|
| `X_DATACORE_API_KEY` | API key xác thực | Có (nếu không dùng token) |
| `DATACORE_BASE_URL` | Base URL cho data API | Không (có default) |
| `DATACORE_LOGIN_URL` | URL endpoint login | Không (có default) |
# USAGE GUIDE - Datacore Python Client

## Introduction

The Datacore Python client library is a modern, user-friendly wrapper around the Datacore API. It handles authentication, request formatting, and data conversion to pandas DataFrames automatically.

**Key features:**
- 🔐 Automatic API key management (environment variable or direct)
- 🐼 Built-in pandas DataFrame support
- ✨ Simple, Pythonic API
- 💪 Type hints for IDE support
- ⚡ Proper error handling

---

## Installation

### Step 1: Install the Package

```bash
# Option A: Install from local directory (recommended for development)
cd /path/to/package_datacore
pip install -e .

# Option B: Install as regular package
pip install .

# Option C: Install from GitHub (when uploaded)
pip install git+https://github.com/yourusername/datacore-client.git
```

### Step 2: Set Up API Key

Choose one of these methods:

#### Method A: Environment Variable (Recommended)

**Windows (PowerShell):**
```powershell
$env:X_DATACORE_API_KEY = "your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set X_DATACORE_API_KEY=your-api-key-here
```

**Linux/Mac (Bash):**
```bash
export X_DATACORE_API_KEY="your-api-key-here"
```

**Using .env file (with python-dotenv):**
```bash
pip install python-dotenv
```

Create `.env` file in your project:
```
X_DATACORE_API_KEY=your-api-key-here
```

Then in your Python code:
```python
from dotenv import load_dotenv
load_dotenv()
from datacore import Datacore

client = Datacore()  # Reads from .env
```

#### Method B: Pass Directly in Code

```python
from datacore import Datacore

client = Datacore(api_key="your-api-key-here")
```

---

## Authentication Methods

The Datacore client supports **two authentication methods**:

### Method 1: API Key Authentication (Recommended for Services)

Best for: Server applications, microservices, automated scripts

```python
from datacore import Datacore

# Option A: From environment variable (recommended)
client = Datacore()

# Option B: Direct parameter
client = Datacore(api_key="your-api-key-here")
```

**Advantages:**
- ✓ No need for user account
- ✓ Long-lived credentials
- ✓ Suitable for service-to-service communication
- ✓ Easy integration

### Method 2: Token Authentication via Login (For User Accounts)

Best for: Web applications, user-based access, personal accounts

```python
from datacore import AuthManager, Datacore

# Step 1: Login with credentials to get access token
token = AuthManager.login(
    username="user@example.com",
    password="password123"
)

# Step 2: Create client with token
client = Datacore(token=token)
```

**Advantages:**
- ✓ Per-user authentication
- ✓ Temporary tokens (more secure)
- ✓ User account-based access control
- ✓ Activity tracking per user

**Note:** Requires an existing Datacore account

---

## Getting Started Without Credentials

Don't have login credentials yet? No problem! Here are your options:

### Option 1: Request an API Key

**For Service/Application Access:**
- Contact: support@datacore.vn
- Include in request:
  - Your company/organization name
  - Intended use case
  - Estimated data volume needs
- Receive: Long-lived API key for programmatic access

### Option 2: Create a User Account

**For Personal/Test Access:**
1. Visit the Datacore portal (if available)
2. Sign up with your email
3. Verify your email address
4. Use credentials with `AuthManager.login()`

### Option 3: Test with Demo Key

If available, test with the demo API key:

```python
from datacore import Datacore

# Using demo key (if X_DATACORE_API_KEY is set)
client = Datacore()
df = client.get_historical_price(limit=10)
```

**Current Status:**
- API Key support: ✓ Available
- Token/Login support: ✓ Available (for users with accounts)
- Try both to see which works for your use case

---

## Basic Usage

### Get Historical Price Data

```python
from datacore import Datacore
import os

# Initialize client (reads X_DATACORE_API_KEY from environment)
client = Datacore()

# Get data as pandas DataFrame
df = client.get_historical_price(limit=10)

# Display the data
print(df.head())
print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
```

### Pagination

```python
# Get page 2 with 50 records per page
df = client.get_historical_price(page=2, limit=50)

# Load all data (multiple pages)
all_data = []
page = 1
while True:
    df = client.get_historical_price(page=page, limit=100)
    if len(df) == 0:
        break
    all_data.append(df)
    page += 1

full_df = pd.concat(all_data, ignore_index=True)
```

### With Field Selection

```python
# Select specific columns
df = client.get_historical_price(
    select_fields=["symbol", "price", "date", "volume"],
    limit=50
)
```

### With Conditions (Filters)

```python
# Filter by symbol
conditions = [
    {
        "field": "symbol",
        "operator": "=",
        "value": "ABC"
    }
]

df = client.get_historical_price(
    conditions=conditions,
    limit=100
)
```

---

## Advanced Usage

### Generic Search for Any Dataset

```python
# Search any available dataset
df = client.get_dataframe(
    dataset_code="dataset_name",
    limit=20
)

# Or get raw response
response = client.search(
    dataset_code="dataset_name",
    limit=20
)
print(response)
```

### Multiple Conditions

```python
conditions = [
    {"field": "symbol", "operator": "=", "value": "ABC"},
    {"field": "date", "operator": ">=", "value": "2024-01-01"},
    {"field": "price", "operator": ">", "value": "100"}
]

df = client.get_historical_price(
    conditions=conditions,
    limit=200
)
```

### Error Handling

```python
from datacore import Datacore
import requests

try:
    client = Datacore()
    df = client.get_historical_price(limit=50)
    print(df.head())
    
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Make sure X_DATACORE_API_KEY is set or pass api_key directly")
    
except requests.RequestException as e:
    print(f"API request failed: {e}")
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Migration Guide: From Old Code to New Library

### Before (Old Code):

```python
import os
import requests
import pandas as pd

your_key = os.getenv("X_API_KEY")
print(your_key)
url = "https://gateway.datacore.vn/data/ds/search"

headers = {
    "x-api-key": your_key,
    "Content-Type": "application/json"
}

payload = {
    "dataSetCode": "dataset_historical_price",
    "conditions": [],
    "selectFields": [],
    "page": 1,
    "limit": 10}

res = requests.post(url, headers=headers, json=payload)
print(res)

data = res.json()
print(data)

df_stock_price = pd.DataFrame(
    data["data"]["dataDetail"],
    columns=data["data"]["fields"]
)

display(df_stock_price.head())
```

### After (Using New Library):

```python
from datacore import Datacore

# Just 3 lines!
client = Datacore()
df_stock_price = client.get_historical_price(limit=10)
display(df_stock_price.head())
```

**Benefits:**
✅ Much cleaner and more readable
✅ Automatic error handling
✅ Better maintainability
✅ Type hints for IDE support
✅ Less boilerplate code

---

## Real-World Examples

### Example 1: Analysis and Visualization

```python
from datacore import Datacore
import matplotlib.pyplot as plt

client = Datacore()

# Get data
df = client.get_historical_price(
    select_fields=["symbol", "price", "date", "volume"],
    limit=500
)

# Basic analysis
print(f"Shape: {df.shape}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nBasic statistics:\n{df.describe()}")

# Plot price trend
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['price'], marker='o')
plt.title('Stock Price Trend')
plt.xlabel('Date')
plt.ylabel('Price')
plt.grid(True)
plt.tight_layout()
plt.show()
```

### Example 2: Export to CSV

```python
from datacore import Datacore

client = Datacore()
df = client.get_historical_price(limit=1000)

# Export to CSV
df.to_csv('stock_data.csv', index=False)
print(f"Data exported to stock_data.csv ({len(df)} rows)")
```

### Example 3: Data Processing Pipeline

```python
from datacore import Datacore
from datetime import datetime, timedelta

client = Datacore()

# Get last 30 days of data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

conditions = [
    {"field": "date", "operator": ">=", "value": start_date.isoformat()},
    {"field": "date", "operator": "<=", "value": end_date.isoformat()}
]

df = client.get_historical_price(
    conditions=conditions,
    limit=1000
)

# Data cleaning
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

# Calculate rolling average
df['price_ma_7'] = df['price'].rolling(window=7).mean()
df['price_ma_30'] = df['price'].rolling(window=30).mean()

print(df.tail())
```

### Example 4: Multiple Dataset Queries

```python
from datacore import Datacore

client = Datacore()

# Query different datasets
df_price = client.get_dataframe(
    dataset_code="dataset_historical_price",
    limit=50
)

df_fundamentals = client.get_dataframe(
    dataset_code="dataset_fundamentals",
    limit=50
)

# Merge or analyze separately
print(f"Price data shape: {df_price.shape}")
print(f"Fundamentals data shape: {df_fundamentals.shape}")
```

---

## API Reference

### `Datacore(api_key=None)`

Initialize a Datacore client.

**Parameters:**
- `api_key` (str, optional): Your Datacore API key
  - If not provided, reads from `X_DATACORE_API_KEY` environment variable
  - Required if environment variable is not set

**Returns:**
- `Datacore`: Client instance

**Raises:**
- `ValueError`: If API key is not found

**Example:**
```python
# Using environment variable
client = Datacore()

# Or pass directly
client = Datacore(api_key="your-api-key")
```

---

### `search(dataset_code, conditions=None, select_fields=None, page=1, limit=10, **kwargs)`

Execute a search query and return raw API response.

**Parameters:**
- `dataset_code` (str): Code of the dataset
- `conditions` (List[Dict], optional): Filter conditions
- `select_fields` (List[str], optional): Fields to select
- `page` (int): Page number (default: 1)
- `limit` (int): Records per page (default: 10)
- `**kwargs`: Additional parameters

**Returns:**
- `Dict`: Raw API response

**Example:**
```python
response = client.search(
    dataset_code="dataset_historical_price",
    limit=50
)
print(response)
```

---

### `get_dataframe(dataset_code, conditions=None, select_fields=None, page=1, limit=10, **kwargs)`

Execute a search query and return result as pandas DataFrame.

**Parameters:**
- Same as `search()`

**Returns:**
- `pd.DataFrame`: Query results as DataFrame

**Raises:**
- `ValueError`: If response cannot be converted to DataFrame

**Example:**
```python
df = client.get_dataframe(
    dataset_code="dataset_historical_price",
    select_fields=["symbol", "price", "date"],
    limit=100
)
```

---

### `get_historical_price(conditions=None, select_fields=None, page=1, limit=10, **kwargs)`

Convenience method for querying historical price dataset.

**Parameters:**
- Same as `get_dataframe()` (dataset_code is predefined)

**Returns:**
- `pd.DataFrame`: Historical price data

**Example:**
```python
df = client.get_historical_price(limit=50)
```

---

## Tips & Best Practices

### 1. Reuse Client Instance

```python
# ✅ Good: Reuse client
client = Datacore()
df1 = client.get_historical_price(limit=10)
df2 = client.get_dataframe("another_dataset", limit=20)

# ❌ Avoid: Creating new client each time
df1 = Datacore().get_historical_price(limit=10)
df2 = Datacore().get_historical_price(limit=20)
```

### 2. Handle Large Datasets

```python
# Use pagination for large datasets
all_data = []
for page in range(1, 11):  # Get 10 pages
    df = client.get_historical_price(page=page, limit=100)
    all_data.append(df)

full_df = pd.concat(all_data, ignore_index=True)
```

### 3. Cache Results

```python
import pickle

client = Datacore()

# Load from cache if exists
try:
    with open('data_cache.pkl', 'rb') as f:
        df = pickle.load(f)
except:
    # Or fetch from API
    df = client.get_historical_price(limit=1000)
    with open('data_cache.pkl', 'wb') as f:
        pickle.dump(df, f)
```

### 4. Use Type Hints in Your Code

```python
from datacore import Datacore
import pandas as pd

def analyze_stock_data(symbol: str) -> pd.DataFrame:
    client = Datacore()
    df = client.get_historical_price(
        conditions=[{"field": "symbol", "value": symbol}],
        limit=100
    )
    return df
```

---

## Troubleshooting

### Issue: "API key not found"

**Solution:**
```python
import os
from datacore import Datacore

# Check if env variable is set
print(os.getenv("X_DATACORE_API_KEY"))

# Or pass directly
client = Datacore(api_key="your-key")
```

### Issue: "Unable to convert response to DataFrame"

**Solution:**
```python
# Use search() to see raw response
response = client.search(dataset_code="your_dataset")
print(response)  # Check structure
```

### Issue: Connection timeout

**Solution:**
```python
try:
    df = client.get_historical_price(limit=10)
except requests.ConnectionError:
    print("Connection failed. Check internet and API URL.")
```

---

## Support

For issues, questions, or feature requests, please visit the GitHub repository or contact support.
