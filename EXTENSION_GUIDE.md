# Extension Guide

Hướng dẫn thêm API endpoint mới vào client.

## Thêm method mới

Thêm vào class `Datacore` trong `datacore/client.py`:

```python
@retry_on_error(max_retries=3, delay=1.0)
def your_new_method(self, param1: str, **kwargs) -> Dict[str, Any]:
    """Gọi endpoint mới"""
    url = f"{self.BASE_URL}/your-endpoint"
    payload = {"param1": param1, **kwargs}
    
    response = self.session.post(url, json=payload, timeout=self.timeout)
    response.raise_for_status()
    
    return response.json()
```

## Thêm URL mới vào `.env`

Nếu endpoint có base URL khác:

```env
DATACORE_NEW_ENDPOINT_URL=https://gateway.datacore.vn/new/endpoint
```

Đọc trong code:
```python
NEW_URL = _env.get("DATACORE_NEW_ENDPOINT_URL", "https://gateway.datacore.vn/new/endpoint")
```

## Ví dụ: Thêm endpoint export

```python
@retry_on_error(max_retries=3, delay=1.0)
def export(self, dataset_code: str, format: str = "json") -> Dict[str, Any]:
    """Export dataset"""
    url = f"{self.BASE_URL}/export"
    params = {"dataSetCode": dataset_code, "format": format}
    
    response = self.session.get(url, params=params, timeout=self.timeout)
    response.raise_for_status()
    
    return response.json()
```

Sử dụng:
```python
client = Datacore()
response = client.export("vsic", format="json")
```
# 📚 EXTENSION GUIDE - How to Add New Datasets

Cấu trúc của library đã được thiết kế để dễ dàng mở rộng. Đây là hướng dẫn để add dataset mới.

## 🎯 Architecture Overview

```
Datacore Client
├── DATASETS (Registry)     ← Add new datasets here
├── search()               ← Core API method (no change)
├── get_dataframe()        ← Auto convert to DataFrame (no change)
├── Convenience Methods    ← get_historical_price(), get_fundamentals(), etc.
├── list_datasets()        ← Show all available datasets
└── Pagination Helpers     ← paginate(), fetch_all()
```

---

## 📝 Step 1: Add Dataset to Registry

File: `datacore/client.py`

```python
DATASETS = {
    "historical_price": {
        "code": "dataset_historical_price",
        "description": "Historical stock price data",
        "method_name": "get_historical_price"
    },
    # ✅ ADD HERE:
    "my_new_dataset": {
        "code": "dataset_my_new_dataset",
        "description": "Description of your dataset",
        "method_name": "get_my_new_dataset"
    },
}
```

---

## 🔧 Step 2: Add Convenience Method

Add to the `Datacore` class:

```python
def get_my_new_dataset(
    self,
    conditions: Optional[List[Dict]] = None,
    select_fields: Optional[List[str]] = None,
    page: int = 1,
    limit: int = 10,
    **kwargs
) -> pd.DataFrame:
    """
    Get my new dataset
    
    Args:
        conditions (Optional[List[Dict]]): Filter conditions
        select_fields (Optional[List[str]]): Fields to select
        page (int): Page number (default: 1)
        limit (int): Records per page (default: 10)
        **kwargs: Additional parameters
    
    Returns:
        pd.DataFrame: Data from my_new_dataset
    """
    return self.get_dataframe(
        dataset_code="dataset_my_new_dataset",
        conditions=conditions,
        select_fields=select_fields,
        page=page,
        limit=limit,
        **kwargs
    )
```

---

## 📌 Complete Example

### 1️⃣ Add to DATASETS registry (top of file):

```python
DATASETS = {
    "historical_price": { ... },
    
    # NEW: Company dividend dataset
    "dividends": {
        "code": "dataset_dividends",
        "description": "Company dividend payment history",
        "method_name": "get_dividends"
    },
}
```

### 2️⃣ Add convenience method (Datacore class):

```python
def get_dividends(
    self,
    conditions: Optional[List[Dict]] = None,
    select_fields: Optional[List[str]] = None,
    page: int = 1,
    limit: int = 10,
    **kwargs
) -> pd.DataFrame:
    """
    Get company dividend data
    
    Example:
        client = Datacore()
        df = client.get_dividends(limit=100)
    """
    return self.get_dataframe(
        dataset_code="dataset_dividends",
        conditions=conditions,
        select_fields=select_fields,
        page=page,
        limit=limit,
        **kwargs
    )
```

### 3️⃣ Use it:

```python
from datacore import Datacore

client = Datacore()

# ✅ Works automatically!
df = client.get_dividends(limit=50)

# ✅ Also works with pagination helpers
for df in client.paginate("dataset_dividends", max_pages=5):
    print(df.shape)

# ✅ Show all datasets
all_datasets = client.list_datasets()
print(all_datasets)
```

---

## 🚀 Advanced Features Already Built-in

### 1. Automatic Retry on Error

```python
# Automatically retries 3 times with exponential backoff
df = client.get_historical_price(limit=1000)
```

### 2. Pagination Helper

```python
# Generator for efficient large dataset processing
for df in client.paginate("dataset_historical_price", max_pages=10):
    process(df)  # Process each page
```

### 3. Fetch All (with optional limit)

```python
# Automatically fetches all pages and combines
df = client.fetch_all(
    "dataset_historical_price",
    max_records=5000,  # Optional limit
    limit=500  # Records per page
)
```

### 4. Session Reuse

```python
# Uses persistent session for better performance
# Headers are set once, reused for all requests
client = Datacore(timeout=30)  # Set custom timeout
```

### 5. Dataset Registry

```python
# List all available datasets
datasets = client.list_datasets()
for key, info in datasets.items():
    print(f"{key}: {info['description']}")

# Get specific dataset info
info = client.get_dataset_info("historical_price")
print(info)  # {'code': '...', 'description': '...', ...}
```

---

## 📋 Minimal Template for New Dataset

Copy & paste this template:

```python
def get_REPLACE_WITH_NAME(
    self,
    conditions: Optional[List[Dict]] = None,
    select_fields: Optional[List[str]] = None,
    page: int = 1,
    limit: int = 10,
    **kwargs
) -> pd.DataFrame:
    """
    Get REPLACE_WITH_DESCRIPTION
    
    Args:
        conditions (Optional[List[Dict]]): Filter conditions
        select_fields (Optional[List[str]]): Fields to select
        page (int): Page number (default: 1)
        limit (int): Records per page (default: 10)
        **kwargs: Additional parameters
    
    Returns:
        pd.DataFrame: REPLACE_WITH_DATA_TYPE data
    """
    return self.get_dataframe(
        dataset_code="dataset_REPLACE_WITH_CODE",
        conditions=conditions,
        select_fields=select_fields,
        page=page,
        limit=limit,
        **kwargs
    )
```

---

## 🔍 Finding Dataset Codes

Get all available dataset codes from Datacore:
1. Check API documentation
2. Or use browser DevTools to see network requests
3. Add to DATASETS registry with correct code

---

## ✅ Checklist for Adding New Dataset

- [ ] Add entry to `DATASETS` dict (top of client.py)
- [ ] Add convenience method to `Datacore` class
- [ ] Method uses `get_dataframe()` internally
- [ ] Method passes correct `dataset_code`
- [ ] Add docstring with examples
- [ ] Test with: `client.get_my_dataset(limit=5)`
- [ ] Update README/docs (optional)

---

## 🧪 Testing New Dataset

```python
from datacore import Datacore

client = Datacore()

# Test 1: Basic call
print("Test 1: Basic call")
df = client.get_my_new_dataset(limit=10)
print(df.shape)

# Test 2: Show columns
print("\nTest 2: Columns")
print(df.columns.tolist())

# Test 3: With conditions
print("\nTest 3: With conditions")
df_filtered = client.get_my_new_dataset(
    conditions=[{"field": "symbol", "value": "ABC"}],
    limit=10
)
print(df_filtered.shape)

# Test 4: Pagination
print("\nTest 4: Pagination")
for i, df in enumerate(client.paginate("dataset_my_new_dataset", max_pages=3)):
    print(f"  Page {i+1}: {len(df)} records")

print("\n✓ All tests passed!")
```

---

## 🎁 Built-in Utilities

### Error Handling with Retry

```python
# Automatically includes retry logic
@retry_on_error(max_retries=3, delay=1.0)
def search(...):
    # Already decorated - no changes needed
```

### Session Management

```python
# Persistent session for better performance
self._session = requests.Session()
self._session.headers.update(self._get_headers())

# Used in all API calls automatically
response = self._session.post(..., timeout=self.timeout)
```

---

## 📚 Real-world Example: Adding 5 New Datasets

```python
# 1. Add to DATASETS registry
DATASETS = {
    "historical_price": {...},
    "stock_splits": {
        "code": "dataset_stock_splits",
        "description": "Stock split information",
        "method_name": "get_stock_splits"
    },
    "earnings": {
        "code": "dataset_earnings",
        "description": "Company earnings reports",
        "method_name": "get_earnings"
    },
    "options": {
        "code": "dataset_options",
        "description": "Options data",
        "method_name": "get_options"
    },
    "indices": {
        "code": "dataset_indices",
        "description": "Market indices data",
        "method_name": "get_indices"
    },
}

# 2. Add 5 convenience methods (copy template, change names)
def get_stock_splits(...) -> pd.DataFrame:
    return self.get_dataframe(dataset_code="dataset_stock_splits", ...)

def get_earnings(...) -> pd.DataFrame:
    return self.get_dataframe(dataset_code="dataset_earnings", ...)

# ... etc

# 3. Usage
client = Datacore()
df_splits = client.get_stock_splits(limit=100)
df_earnings = client.get_earnings(limit=100)
df_options = client.get_options(limit=100)
```

---

## 🤔 FAQ

**Q: Do I need to modify anything else?**
A: No! Just add to DATASETS and add the method. Everything else is automatic.

**Q: Can I use generic search() instead?**
A: Yes, but convenience methods are cleaner:
```python
# Generic (less readable)
df = client.get_dataframe("dataset_my_data", limit=50)

# Convenience method (more readable)
df = client.get_my_data(limit=50)
```

**Q: What about caching?**
A: Can be added to `search()` decorator if needed.

**Q: Does pagination work automatically?**
A: Yes! `paginate()` and `fetch_all()` work with any dataset_code.

---

## 🎯 Summary

Adding a new dataset requires:
1. **One entry** in `DATASETS` registry
2. **One method** in `Datacore` class
3. **Done!** ✓

All other features (retry, pagination, session, etc.) work automatically!
