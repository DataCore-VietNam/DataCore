import os
import requests
import pandas as pd
from typing import Optional, List, Dict, Any


class Datacore:
    """
    Python client library for Datacore API
    
    Similar to OpenAI, the API key can be provided in two ways:
    1. Via environment variable: X_DATACORE_API_KEY
    2. Via constructor parameter: datacore_key
    
    Example:
        # Using environment variable
        os.environ["X_DATACORE_API_KEY"] = "your-api-key"
        client = Datacore()
        
        # Or pass directly
        client = Datacore(api_key="your-api-key")
    """
    
    BASE_URL = "https://gateway.datacore.vn/data/ds/search"
    ENV_KEY = "X_DATACORE_API_KEY"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Datacore client
        
        Args:
            api_key (Optional[str]): Datacore API key. If not provided, 
                                    will try to read from X_DATACORE_API_KEY env variable
        """
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv(self.ENV_KEY)
            
        if not self.api_key:
            raise ValueError(
                f"Datacore API key not found. Please provide 'api_key' parameter "
                f"or set '{self.ENV_KEY}' environment variable."
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
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
        
        response = requests.post(
            self.BASE_URL,
            headers=self._get_headers(),
            json=payload
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
            df = client.get_dataframe(
                "dataset_historical_price",
                limit=100
            )
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
        Convenience method to get historical price data
        
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
