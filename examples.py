"""
Example usage of Datacore Python client library
"""

import os
from datacore import Datacore

# Example 1: Using environment variable
print("=" * 50)
print("Example 1: Using environment variable")
print("=" * 50)

# Set your API key (or use .env file with python-dotenv)
# os.environ["X_DATACORE_API_KEY"] = "your-api-key"

try:
    client = Datacore()
    
    # Get historical price data as DataFrame
    df = client.get_historical_price(limit=10)
    print(df.head())
    print(f"\nData shape: {df.shape}")
    
except ValueError as e:
    print(f"Error: {e}")
    print("Please set X_DATACORE_API_KEY environment variable or pass api_key parameter")


# Example 2: Using API key directly
print("\n" + "=" * 50)
print("Example 2: Passing API key directly")
print("=" * 50)

try:
    # Replace with your actual API key
    client = Datacore(api_key="your-api-key-here")
    
    # Get data with custom parameters
    df = client.get_dataframe(
        dataset_code="dataset_historical_price",
        limit=20,
        page=1
    )
    print(df.head())
    
except Exception as e:
    print(f"Error: {e}")


# Example 3: Using raw search method
print("\n" + "=" * 50)
print("Example 3: Using raw search method")
print("=" * 50)

try:
    client = Datacore()
    
    # Get raw response
    response = client.search(
        dataset_code="dataset_historical_price",
        limit=5
    )
    print(f"Response: {response}")
    
except Exception as e:
    print(f"Error: {e}")
