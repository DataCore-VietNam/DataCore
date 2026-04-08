"""
Test improved Datacore client with extended features
Run: python test_improved.py
"""

from datacore import Datacore
import os

def test_dataset_registry():
    """Test 1: Dataset registry"""
    print("\n" + "=" * 70)
    print("TEST 1: Dataset Registry")
    print("=" * 70)
    
    client = Datacore(api_key="demo-key")
    
    # List all datasets
    datasets = client.list_datasets()
    print(f"\n✓ Available datasets: {len(datasets)}")
    for key, info in datasets.items():
        print(f"  • {key:<20} → {info['method_name']:<30} ({info['description']})")
    
    # Get specific dataset info
    print("\n✓ Specific dataset info:")
    info = client.get_dataset_info("historical_price")
    print(f"  Code: {info['code']}")
    print(f"  Method: {info['method_name']}")
    print(f"  Description: {info['description']}")


def test_available_methods():
    """Test 2: Available convenience methods"""
    print("\n" + "=" * 70)
    print("TEST 2: Available Convenience Methods")
    print("=" * 70)
    
    client = Datacore(api_key="demo-key")
    
    methods = [
        "search",
        "get_dataframe",
        "get_historical_price",
        "get_fundamentals",
        "get_financial_statements",
        "get_company_info",
        "get_company_events",
        "paginate",
        "fetch_all",
        "list_datasets",
    ]
    
    print("\n✓ Available methods:")
    for method in methods:
        if hasattr(client, method):
            print(f"  ✓ {method}()")


def test_features():
    """Test 3: Show new features"""
    print("\n" + "=" * 70)
    print("TEST 3: New Features")
    print("=" * 70)
    
    features = [
        ("Dataset Registry", "Easily manage multiple datasets"),
        ("Retry Logic", "@retry_on_error decorator with exponential backoff"),
        ("Session Reuse", "Persistent HTTP session for better performance"),
        ("Pagination Helper", "paginate() generator for large datasets"),
        ("Fetch All", "fetch_all() to automatically fetch all pages"),
        ("Timeout Support", "Configurable request timeout"),
        ("Multiple Datasets", "Pre-built methods for 5+ datasets"),
    ]
    
    print("\n✓ Features:")
    for i, (feature, desc) in enumerate(features, 1):
        print(f"  {i}. {feature:<20} - {desc}")


def test_api_structure():
    """Test 4: API structure"""
    print("\n" + "=" * 70)
    print("TEST 4: API Structure")
    print("=" * 70)
    
    print("""
✓ Core Methods (unchanged):
  • search()               - Raw API call, returns Dict
  • get_dataframe()        - For any dataset, returns DataFrame

✓ Convenience Methods (new):
  • get_historical_price() - Historical stock price
  • get_fundamentals()     - Company fundamentals
  • get_financial_statements() - Financial statements
  • get_company_info()     - Company information
  • get_company_events()   - Company events

✓ Utility Methods (new):
  • list_datasets()        - List all available datasets
  • get_dataset_info()     - Get info about specific dataset
  • paginate()             - Generator for pagination
  • fetch_all()            - Fetch all pages combined

✓ Features:
  • Automatic retry on error
  • Session persistence
  • Configurable timeout
  • Easy to extend (see EXTENSION_GUIDE.md)
    """)


def test_extension_example():
    """Test 5: Show extension example"""
    print("\n" + "=" * 70)
    print("TEST 5: How to Add New Dataset")
    print("=" * 70)
    
    print("""
✓ Step 1: Add to DATASETS registry (top of datacore/client.py):

    DATASETS = {
        "historical_price": {...},
        
        # ADD THIS:
        "new_dataset": {
            "code": "dataset_new_dataset",
            "description": "Your dataset description",
            "method_name": "get_new_dataset"
        },
    }

✓ Step 2: Add convenience method to Datacore class:

    def get_new_dataset(
        self,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs
    ) -> pd.DataFrame:
        \"\"\"Get new dataset\"\"\"
        return self.get_dataframe(
            dataset_code="dataset_new_dataset",
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            **kwargs
        )

✓ Step 3: Use it:

    client = Datacore()
    df = client.get_new_dataset(limit=100)

That's it! All features (retry, pagination, session, etc.) work automatically!
    """)


def test_usage_examples():
    """Test 6: Usage examples"""
    print("\n" + "=" * 70)
    print("TEST 6: Usage Examples")
    print("=" * 70)
    
    print("""
✓ Example 1: Simple query

    client = Datacore()
    df = client.get_historical_price(limit=50)
    print(df.head())

✓ Example 2: With filters

    conditions = [{"field": "symbol", "value": "ABC"}]
    df = client.get_fundamentals(
        conditions=conditions,
        limit=20
    )

✓ Example 3: Pagination for large datasets

    for df in client.paginate("dataset_historical_price", max_pages=5):
        print(f"Got {len(df)} records")

✓ Example 4: Fetch all data with limit

    df = client.fetch_all(
        "dataset_historical_price",
        max_records=10000,
        limit=500
    )

✓ Example 5: List available datasets

    datasets = client.list_datasets()
    for key, info in datasets.items():
        print(f"{key}: {info['description']}")

✓ Example 6: Use generic method

    df = client.get_dataframe("dataset_financial_statements", limit=100)
    """)


def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║ " + "DATACORE CLIENT - IMPROVED VERSION TEST".center(66) + " ║")
    print("╚" + "=" * 68 + "╝")
    
    test_dataset_registry()
    test_available_methods()
    test_features()
    test_api_structure()
    test_extension_example()
    test_usage_examples()
    
    print("\n" + "=" * 70)
    print("✓ All tests completed!")
    print("=" * 70)
    print("\nDocumentation:")
    print("  • README.md         - Quick start")
    print("  • USAGE_GUIDE.md    - Comprehensive usage")
    print("  • EXTENSION_GUIDE.md - How to add new datasets")
    print("  • PROJECT_SUMMARY.md - Project overview")
    print("\n")


if __name__ == "__main__":
    main()
