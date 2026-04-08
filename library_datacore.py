"""
Datacore Python Client Library - Setup and usage guide
========================================================

This package has been restructured into a proper Python package.

DIRECTORY STRUCTURE:
├── setup.py                 # Package setup configuration
├── pyproject.toml          # Modern Python project config
├── requirements.txt        # Dependencies
├── README.md               # Full documentation
├── .env.example            # Example environment variables
├── examples.py             # Usage examples
└── datacore/
    ├── __init__.py         # Package exports
    └── client.py           # Main Datacore client class


INSTALLATION:
=============

1. From local directory:
   pip install -e .

2. Or build and install:
   pip install .


QUICK START:
============

# Method 1: Using environment variable (recommended)
import os
os.environ["X_DATACORE_API_KEY"] = "your-api-key"
from datacore import Datacore

client = Datacore()
df = client.get_historical_price(limit=50)
print(df.head())


# Method 2: Pass API key directly
from datacore import Datacore

client = Datacore(api_key="your-api-key")
df = client.get_historical_price(limit=50)


KEY FEATURES:
=============

✓ Auto-reads X_DATACORE_API_KEY environment variable
✓ Option to pass API key directly (like OpenAI)
✓ Returns data as pandas DataFrame
✓ Support for all search parameters
✓ Convenience methods for common datasets
✓ Full type hints for better IDE support
✓ Comprehensive error handling


See examples.py and README.md for more information.
"""
