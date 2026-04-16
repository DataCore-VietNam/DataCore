from __future__ import annotations

import time
from functools import wraps
from typing import Optional, Dict, Any, List, Iterator

import pandas as pd
import requests
from dotenv import dotenv_values

_env = dotenv_values()


class DatacoreError(Exception):
    """Base exception for Datacore package."""
    pass


class AuthenticationError(DatacoreError):
    """Raised when API key is missing or invalid."""
    pass


class PermissionDeniedError(DatacoreError):
    """Raised when access is denied."""
    pass


class APIRequestError(DatacoreError):
    """Raised when request fails or response format is invalid."""
    pass


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as exc:
                    last_error = exc
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))
            raise last_error
        return wrapper
    return decorator


class Datacore:
    """
    Datacore API client.

    Demo:
        client = Datacore()
        df = client.preview("vsic")

    Paid:
        client = Datacore(api_key="your-api-key")
        df = client.get_dataframe("dataset_historical_price")
    """

    GATEWAY_URL = _env.get("DATACORE_GATEWAY_URL", "https://gateway.datacore.vn")
    SEARCH_URL = _env.get("DATACORE_SEARCH", f"{GATEWAY_URL}/data/ds/search")
    PREVIEW_URL = _env.get("DATACORE_PREVIEW", "").strip()

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.timeout = timeout
        self.api_key = (api_key or _env.get("X_API_KEY") or "").strip()

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

        if self.api_key:
            self.session.headers.update({
                "x-api-key": self.api_key
            })

    def set_api_key(self, api_key: str) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty.")
        self.api_key = api_key.strip()
        self.session.headers.update({
            "x-api-key": self.api_key
        })

    def is_authenticated(self) -> bool:
        return bool(self.api_key)

    def _require_auth(self) -> None:
        if not self.is_authenticated():
            raise AuthenticationError(
                "API key not found. Pass api_key to Datacore(api_key='your-key') "
                "or set X_API_KEY in .env"
            )

    def _raise_api_error(self, response: requests.Response) -> None:
        try:
            err_data = response.json()
        except ValueError:
            err_data = {}

        message = (
            err_data.get("message")
            or err_data.get("error")
            or err_data.get("detail")
            or response.text
            or f"HTTP {response.status_code}"
        )

        if response.status_code in (401, 403):
            lowered = str(message).lower()
            if any(word in lowered for word in ["permission", "forbidden", "denied", "not allowed"]):
                raise PermissionDeniedError(message)
            raise AuthenticationError(message)

        raise APIRequestError(message)

    @staticmethod
    def _to_dataframe(data: Dict[str, Any], error_prefix: str = "response") -> pd.DataFrame:
        try:
            payload = data["data"]
            rows = payload["dataDetail"]
            fields = payload["fields"]
            return pd.DataFrame(rows, columns=fields)
        except (KeyError, TypeError, ValueError) as exc:
            raise APIRequestError(
                f"Cannot convert {error_prefix} to DataFrame: {exc}"
            ) from exc

    @retry_on_error(max_retries=3, delay=1.0)
    def preview_raw(self, dataset_code: str) -> Dict[str, Any]:
        """
        Demo mode, no API key required.
        Need DATACORE_PREVIEW in .env
        """
        if not self.PREVIEW_URL:
            raise APIRequestError("DATACORE_PREVIEW is not configured in .env")

        response = requests.get(
            self.PREVIEW_URL,
            params={"dataSetCode": dataset_code},
            timeout=self.timeout,
        )

        if not response.ok:
            self._raise_api_error(response)

        return response.json()

    def preview(self, dataset_code: str) -> pd.DataFrame:
        data = self.preview_raw(dataset_code)
        return self._to_dataframe(data, error_prefix="preview response")

    @retry_on_error(max_retries=3, delay=1.0)
    def get_data(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Paid API mode, requires API key.
        """
        self._require_auth()

        payload = {
            "dataSetCode": dataset_code,
            "conditions": conditions or [],
            "selectFields": select_fields or [],
            "page": page,
            "limit": limit,
            **kwargs,
        }

        response = self.session.post(
            self.SEARCH_URL,
            json=payload,
            timeout=self.timeout,
        )

        if not response.ok:
            self._raise_api_error(response)

        return response.json()

    def get_dataframe(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 10,
        **kwargs: Any,
    ) -> pd.DataFrame:
        data = self.get_data(
            dataset_code=dataset_code,
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            **kwargs,
        )
        return self._to_dataframe(data, error_prefix="API response")

    def paginate(
        self,
        dataset_code: str,
        max_pages: Optional[int] = None,
        limit: int = 1000,
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Iterator[pd.DataFrame]:
        """
        Paid API pagination.
        """
        page = 1
        while True:
            if max_pages is not None and page > max_pages:
                break

            df = self.get_dataframe(
                dataset_code=dataset_code,
                conditions=conditions,
                select_fields=select_fields,
                page=page,
                limit=limit,
                **kwargs,
            )

            if df.empty:
                break

            yield df
            page += 1