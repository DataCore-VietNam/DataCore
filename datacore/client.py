"""
Datacore Python Client Library

Simple wrapper for Datacore API:
- Handles authentication (API key or Token/Login)
- Manages request headers
- Calls API endpoints
- Returns responses

Backend handles: dataset permissions, data filtering, API key validation
Client handles: auth management, request wrapping, response parsing
"""

import os
import requests
import pandas as pd
from typing import Optional, Dict, Any, List
from functools import wraps
import time
from dotenv import dotenv_values

_env = dotenv_values()


class AuthManager:
    """Manages authentication - API key or Login/Token"""
    
    LOGIN_URL = _env.get("DATACORE_LOGIN_URL")
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.token: Optional[str] = None
        self.auth_type: str = None  # 'api_key' or 'token'
    
    def authenticate_with_api_key(self, api_key: Optional[str] = None) -> None:
        """Set up API key authentication"""
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = _env.get("X_DATACORE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "API key not found. Provide via api_key parameter or "
                "set X_DATACORE_API_KEY in .env file."
            )
        
        self.auth_type = "api_key"
        self.token = None
    
    @staticmethod
    def login(username: str, password: str, timeout: int = 30) -> str:
        """
        Login to Datacore API and get access token
        
        Args:
            username: Email or username
            password: Password
            timeout: Request timeout in seconds
        
        Returns:
            Access token
        
        Raises:
            ValueError: If login fails
        """
        payload = {
            "username": username,
            "password": password
        }
        
        response = requests.post(
            AuthManager.LOGIN_URL,
            json=payload,
            timeout=timeout
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Try different token field names
        token = data.get("access_token") or data.get("token") or data.get("data", {}).get("token")
        
        if not token:
            raise ValueError(f"Login failed: {data.get('message', str(data))}")
        
        return token
    
    def authenticate_with_token(self, token: str) -> None:
        """Set up token authentication"""
        if not token:
            raise ValueError("Token cannot be empty")
        
        self.token = token
        self.auth_type = "token"
        self.api_key = None
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication"""
        headers = {"Content-Type": "application/json"}
        
        if self.auth_type == "api_key":
            headers["x-api-key"] = self.api_key
        elif self.auth_type == "token":
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers
    
    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return bool(self.auth_type and (self.api_key or self.token))


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Retry decorator for API calls"""
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
                        time.sleep(delay * (2 ** attempt))
                    continue
            raise last_error
        return wrapper
    return decorator


class Datacore:
    """
    Datacore API Client
    
    Simple wrapper to call Datacore APIs with proper authentication.
    Backend handles permissions and data filtering.
    Client handles auth and request formatting.
    
    Example - API Key:
        client = Datacore(api_key="your-api-key")
        response = client.get_data("dataset_code", limit=10)
    
    Example - Token/Login:
        token = AuthManager.login("user@example.com", "password")
        client = Datacore(token=token)
        response = client.get_data("dataset_code", limit=10)
    
    Example - From Environment:
        # Set X_DATACORE_API_KEY
        client = Datacore()
        response = client.get_data("dataset_code", limit=10)
    """
    
    BASE_URL = _env.get("DATACORE_BASE_URL")
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize Datacore client
        
        Args:
            api_key: API key (reads from X_DATACORE_API_KEY in .env if not provided)
            token: Access token from login
            timeout: Request timeout in seconds
        
        Authentication priority: token > api_key > X_DATACORE_API_KEY in .env
        """
        self.auth = AuthManager()
        
        # Try authentication methods in order
        if token:
            self.auth.authenticate_with_token(token)
        elif api_key:
            self.auth.authenticate_with_api_key(api_key)
        else:
            self.auth.authenticate_with_api_key()  # Tries env variable
        
        if not self.auth.is_authenticated():
            raise ValueError(
                "Authentication failed. Provide token, api_key, or "
                "set X_DATACORE_API_KEY environment variable."
            )
        
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.auth.get_headers())
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_data(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get data from a dataset
        
        Args:
            dataset_code: Dataset code (e.g., "dataset_historical_price")
            conditions: Filter conditions (backend handles permissions)
            select_fields: Fields to select
            page: Page number
            limit: Records per page
            **kwargs: Additional parameters
        
        Returns:
            Response from API
        """
        payload = {
            "dataSetCode": dataset_code,
            "conditions": conditions or [],
            "selectFields": select_fields or [],
            "page": page,
            "limit": limit,
            **kwargs
        }
        
        url = f"{self.BASE_URL}/search"
        response = self.session.post(url, json=payload, timeout=self.timeout)
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
        """Get data as pandas DataFrame"""
        data = self.get_data(
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
            raise ValueError(f"Cannot convert to DataFrame: {e}")
    
    @retry_on_error(max_retries=3, delay=1.0)
    def preview(self, dataset_code: str) -> Dict[str, Any]:
        """
        Get dataset preview
        
        Example:
            preview = client.preview("vsic")
            print(preview)
        """
        url = f"{self.BASE_URL}/preview"
        params = {"dataSetCode": dataset_code}
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()
    
    def paginate(
        self,
        dataset_code: str,
        max_pages: Optional[int] = None,
        limit: int = 100,
        conditions: Optional[List[Dict]] = None,
        select_fields: Optional[List[str]] = None,
        **kwargs
    ):
        """Generator for paginated results"""
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
        """Fetch all data (with optional limit)"""
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
