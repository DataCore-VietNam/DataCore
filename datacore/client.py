import os
import requests
import pandas as pd
from typing import Optional, List, Dict, Any, Callable
from functools import wraps
import time


# Dataset Registry - Add new datasets here!
DATASETS = {
    "historical_price": {
        "code": "dataset_historical_price",
        "description": "Historical stock price data",
        "method_name": "get_historical_price"
    },
    "fundamentals": {
        "code": "dataset_fundamentals",
        "description": "Company fundamentals data",
        "method_name": "get_fundamentals"
    },
    "financial_statements": {
        "code": "dataset_financial_statements",
        "description": "Financial statements data",
        "method_name": "get_financial_statements"
    },
    "companys_information": {
        "code": "dataset_companys_information",
        "description": "Company information data",
        "method_name": "get_company_info"
    },
    "company_events": {
        "code": "dataset_company_events",
        "description": "Company events data",
        "method_name": "get_company_events"
    },
    # Add more datasets as needed
}


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry API calls on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                    continue
            raise last_error
        return wrapper
    return decorator


class Datacore:
    """
    Python client library for Datacore API
    
    Supports multiple datasets with flexible configuration.
    
    Example:
        # Using environment variable
        client = Datacore()
        df = client.get_historical_price(limit=50)
        
        # Or pass directly
        client = Datacore(api_key="your-api-key")
        df = client.get_fundamentals(limit=100)
    
    Available datasets:
        - historical_price: Historical stock price data
        - fundamentals: Company fundamentals
        - financial_statements: Financial statements
        - company_info: Company information
        - company_events: Company events
    """
    
    BASE_URL = "https://gateway.datacore.vn/data/ds/search"
    ENV_KEY = "X_DATACORE_API_KEY"
    DATASETS = DATASETS
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize Datacore client
        
        Args:
            api_key (Optional[str]): API key (reads from env if not provided)
            timeout (int): Request timeout in seconds (default: 30)
        """
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv(self.ENV_KEY)
            
        if not self.api_key:
            raise ValueError(
                f"Datacore API key not found. Provide 'api_key' or "
                f"set '{self.ENV_KEY}' environment variable."
            )
        
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(self._get_headers())
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    @retry_on_error(max_retries=3, delay=1.0)
    def search(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search data from Datacore
        
        Args:
            dataset_code (str): Code of the dataset to search
            conditions (Optional[List[Dict]]): Filter conditions
            select_fields (Optional[List[str]]): Fields to select
            page (int): Page number (default: 1)
            limit (int): Number of records per page (default: 10)
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            Dict[str, Any]: Response data from API
        
        Raises:
            requests.RequestException: If API request fails
        """
        payload = {
            "dataSetCode": dataset_code,
            "conditions": conditions or [],
            "selectFields": select_fields or [],
            "page": page,
            "limit": limit,
            **kwargs
        }
        
        response = self._session.post(
            self.BASE_URL,
            json=payload,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_dataframe(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs
    ) -> pd.DataFrame:
        """
        Get data from Datacore as a pandas DataFrame
        
        Args:
            dataset_code (str): Code of the dataset to search
            conditions (Optional[List[Dict]]): Filter conditions
            select_fields (Optional[List[str]]): Fields to select
            page (int): Page number (default: 1)
            limit (int): Number of records per page (default: 10)
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            pd.DataFrame: DataFrame containing the returned data
        
        Example:
            client = Datacore()
            df = client.get_dataframe("dataset_historical_price", limit=100)
        """
        data = self.search(
            dataset_code=dataset_code,
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            **kwargs
        )
        
        try:
            return pd.DataFrame(
                data["data"]["dataDetail"],
                columns=data["data"]["fields"]
            )
        except (KeyError, ValueError) as e:
            raise ValueError(
                f"Unable to convert response to DataFrame. "
                f"Response structure: {data}. Error: {e}"
            )
    
    def get_historical_price(
        self,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs
    ) -> pd.DataFrame:
        """
        Get historical price data
        
        Args:
            conditions (Optional[List[Dict]]): Filter conditions
            select_fields (Optional[List[str]]): Fields to select
            page (int): Page number (default: 1)
            limit (int): Number of records per page (default: 10)
            **kwargs: Additional parameters
        
        Returns:
            pd.DataFrame: Historical price data
        """
        return self.get_dataframe(
            dataset_code="dataset_historical_price",
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            **kwargs
        )
    
    def get_fundamentals(
        self,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs
    ) -> pd.DataFrame:
        """
        Get fundamentals data
        
        Args:
            conditions (Optional[List[Dict]]): Filter conditions
            select_fields (Optional[List[str]]): Fields to select
            page (int): Page number (default: 1)
            limit (int): Number of records per page (default: 10)
            **kwargs: Additional parameters
        
        Returns:
            pd.DataFrame: Fundamentals data
        """
        return self.get_dataframe(
            dataset_code="dataset_fundamentals",
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            **kwargs
        )
    
    def get_financial_statements(
        self,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs
    ) -> pd.DataFrame:
        """
        Get financial statements data
        
        Args:
            conditions (Optional[List[Dict]]): Filter conditions
            select_fields (Optional[List[str]]): Fields to select
            page (int): Page number (default: 1)
            limit (int): Number of records per page (default: 10)
            **kwargs: Additional parameters
        
        Returns:
            pd.DataFrame: Financial statements data
        """
        return self.get_dataframe(
            dataset_code="dataset_financial_statements",
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            **kwargs
        )
    
    def get_company_info(
        self,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs
    ) -> pd.DataFrame:
        """
        Get company information data
        
        Args:
            conditions (Optional[List[Dict]]): Filter conditions
            select_fields (Optional[List[str]]): Fields to select
            page (int): Page number (default: 1)
            limit (int): Number of records per page (default: 10)
            **kwargs: Additional parameters
        
        Returns:
            pd.DataFrame: Company information data
        """
        return self.get_dataframe(
            dataset_code="dataset_companys_information",
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            **kwargs
        )
    
    def get_company_events(
        self,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs
    ) -> pd.DataFrame:
        """
        Get company events data
        
        Args:
            conditions (Optional[List[Dict]]): Filter conditions
            select_fields (Optional[List[str]]): Fields to select
            page (int): Page number (default: 1)
            limit (int): Number of records per page (default: 10)
            **kwargs: Additional parameters
        
        Returns:
            pd.DataFrame: Company events data
        """
        return self.get_dataframe(
            dataset_code="dataset_company_events",
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            **kwargs
        )
    
    @staticmethod
    def list_datasets() -> Dict[str, Dict[str, str]]:
        """
        List all available datasets
        
        Returns:
            Dict: Dataset information including code, description, and method name
        """
        return Datacore.DATASETS
    
    def get_dataset_info(self, dataset_key: str) -> Optional[Dict[str, str]]:
        """
        Get information about a specific dataset
        
        Args:
            dataset_key (str): Dataset key (e.g., 'historical_price')
        
        Returns:
            Dict or None: Dataset information if found
        """
        return self.DATASETS.get(dataset_key)
    
    def paginate(
        self,
        dataset_code: str,
        max_pages: Optional[int] = None,
        limit: int = 100,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Generator for paginated results
        
        Args:
            dataset_code (str): Dataset code
            max_pages (Optional[int]): Maximum pages to fetch (None = all)
            limit (int): Records per page
            conditions (Optional[List[Dict]]): Filter conditions
            select_fields (Optional[List[str]]): Fields to select
            **kwargs: Additional parameters
        
        Yields:
            pd.DataFrame: DataFrame for each page
        
        Example:
            client = Datacore()
            for df in client.paginate("dataset_historical_price", max_pages=10):
                print(df.shape)
        """
        page = 1
        while True:
            if max_pages and page > max_pages:
                break
            
            try:
                df = self.get_dataframe(
                    dataset_code=dataset_code,
                    conditions=conditions,
                    select_fields=select_fields,
                    page=page,
                    limit=limit,
                    **kwargs
                )
                
                if len(df) == 0:
                    break
                
                yield df
                page += 1
                
            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                break
    
    def fetch_all(
        self,
        dataset_code: str,
        max_records: Optional[int] = None,
        limit: int = 100,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Fetch all data for a dataset (with optional limit)
        
        Args:
            dataset_code (str): Dataset code
            max_records (Optional[int]): Maximum records to fetch (None = all)
            limit (int): Records per page
            conditions (Optional[List[Dict]]): Filter conditions
            select_fields (Optional[List[str]]): Fields to select
            **kwargs: Additional parameters
        
        Returns:
            pd.DataFrame: Combined dataframe from all pages
        
        Example:
            client = Datacore()
            df = client.fetch_all("dataset_historical_price", max_records=1000)
        """
        all_data = []
        records_fetched = 0
        
        for df in self.paginate(
            dataset_code=dataset_code,
            limit=limit,
            conditions=conditions,
            select_fields=select_fields,
            **kwargs
        ):
            if max_records:
                remaining = max_records - records_fetched
                if len(df) > remaining:
                    df = df.iloc[:remaining]
            
            all_data.append(df)
            records_fetched += len(df)
            
            if max_records and records_fetched >= max_records:
                break
        
        if not all_data:
            return pd.DataFrame()
        
        return pd.concat(all_data, ignore_index=True)
