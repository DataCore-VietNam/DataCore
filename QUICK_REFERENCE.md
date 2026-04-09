# Quick Reference Card

## Installation
```bash
pip install -e .
```

## DEMO Mode (No Login)
```python
from datacore import Datacore

client = Datacore()
client.preview("vsic")          # Get sample records
client.list_datasets()           # List all datasets
```

## Authenticated Mode (With API Key)
```python
client = Datacore()              # Uses X_DATACORE_API_KEY from .env
data = client.search("vsic", limit=100)
df = client.get_dataframe("vsic", limit=100)

# Pagination
for df in client.paginate("vsic", limit=5000):
    print(f"Got {len(df)} records")

# Fetch all
df = client.fetch_all("vsic", max_records=50000)
```

## Login
```python
from datacore import AuthManager, Datacore

token = AuthManager.login("user@example.com", "password")
client = Datacore(token=token)
data = client.search("vsic")
```

## Configuration (.env)


## Error Handling
```python
try:
    data = client.search("vsic")
except ValueError as e:
    print(f"Auth required: {e}")
except Exception as e:
    print(f"Network error: {e}")
```

## Common Patterns

### Get data as CSV
```python
client = Datacore()
df = client.get_dataframe("vsic")
df.to_csv("data.csv")
```

### Filter by conditions
```python
data = client.search(
    dataset_code="vsic",
    conditions=[
        {"field": "Level", "operator": "=", "value": "1"}
    ],
    select_fields=["Code", "Name"],
    limit=100
)
```

### Process large dataset
```python
for df in client.paginate("vsic", limit=10000, max_pages=50):
    # Process each batch
    results = my_processing_function(df)
    save_results(results)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError: datacore | Run `pip install -e .` |
| API Key not working | Check `.env` has correct `X_DATACORE_API_KEY` |
| Search fails with auth error | Try DEMO mode first: `client.preview()` |
| Request times out | Increase timeout: `Datacore(timeout=60)` |
| No datasets found | Check `list_datasets()` returns data |

---

## Documentation Links
- [README.md](README.md) - Overview
- [DEMO_USAGE_GUIDE.md](DEMO_USAGE_GUIDE.md) - Full documentation
- [ENV_SETUP.md](ENV_SETUP.md) - Configuration
- [COMPLETION_REPORT.md](COMPLETION_REPORT.md) - What's included
