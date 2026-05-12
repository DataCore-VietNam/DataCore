from __future__ import annotations

import json
import time
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import pandas as pd
import requests
from dotenv import dotenv_values

_env = dotenv_values()


class DatacoreError(Exception):
    """Base exception for Datacore package."""


class AuthenticationError(DatoreError if False else DatacoreError):
    """Raised when API key is missing or invalid."""


class PermissionDeniedError(DatacoreError):
    """Raised when access is denied."""


class APIRequestError(DatacoreError):
    """Raised when request fails or response format is invalid."""


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
    """Datacore API client."""

    GATEWAY_URL = "https://gateway.datacore.vn"
    SEARCH_URL = "https://gateway.datacore.vn/data/ds/search"
    PREVIEW_URL = "https://gateway.datacore.vn/data/ds/preview"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30, debug: bool = False):
        self.timeout = timeout
        self.debug = debug
        self.api_key = (api_key or _env.get("X_API_KEY") or "").strip()

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        if self.api_key:
            self.session.headers.update({"x-api-key": self.api_key})

    def set_api_key(self, api_key: str) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty.")
        self.api_key = api_key.strip()
        self.session.headers.update({"x-api-key": self.api_key})

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

        full_message = f"HTTP {response.status_code}: {message}\nResponse: {response.text}"

        if response.status_code in (401, 403):
            lowered = str(message).lower()
            if any(word in lowered for word in ["permission", "forbidden", "denied", "not allowed"]):
                raise PermissionDeniedError(full_message)
            raise AuthenticationError(full_message)

        raise APIRequestError(full_message)

    @staticmethod
    def _get_payload(data: Dict[str, Any], error_prefix: str = "response") -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise APIRequestError(f"Cannot parse {error_prefix}: response is not a dict")

        payload = data.get("data")
        if payload is None:
            message = data.get("message") or data.get("error") or data.get("detail") or "missing key 'data'"
            raise APIRequestError(f"Cannot parse {error_prefix}: {message}")

        if not isinstance(payload, dict):
            raise APIRequestError(f"Cannot parse {error_prefix}: key 'data' is not an object")

        return payload

    @staticmethod
    def _extract_metadata(data: Dict[str, Any], queried_rows: Optional[int] = None) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {"num": None, "totalPage": None, "currentPage": None, "queried_rows": queried_rows}

        payload = data.get("data", {})
        if not isinstance(payload, dict):
            payload = {}

        return {
            "num": data.get("num", payload.get("num")),
            "totalPage": data.get("totalPage", payload.get("totalPage")),
            "currentPage": data.get("currentPage", payload.get("currentPage")),
            "queried_rows": queried_rows,
        }

    @staticmethod
    def _metadata_to_string(meta: Dict[str, Any]) -> str:
        return (
            f"num: {meta.get('num')}, "
            f"totalPage: {meta.get('totalPage')}, "
            f"currentPage: {meta.get('currentPage')}, "
            f"queried_rows: {meta.get('queried_rows')}"
        )

    @staticmethod
    def _to_dataframe(data: Dict[str, Any], error_prefix: str = "response") -> pd.DataFrame:
        payload = Datacore._get_payload(data, error_prefix=error_prefix)

        rows = payload.get("dataDetail")
        fields = payload.get("fields")

        if rows is None:
            raise APIRequestError(f"Cannot convert {error_prefix} to DataFrame: missing key 'dataDetail'")
        if fields is None:
            raise APIRequestError(f"Cannot convert {error_prefix} to DataFrame: missing key 'fields'")

        try:
            return pd.DataFrame(rows, columns=fields)
        except Exception as exc:
            raise APIRequestError(f"Cannot convert {error_prefix} to DataFrame: {exc}") from exc

    @staticmethod
    def _filter_dataframe_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        if not columns:
            raise ValueError("columns cannot be empty")

        missing = [col for col in columns if col not in df.columns]
        if missing:
            raise ValueError(f"Columns not found: {missing}. Available columns: {list(df.columns)}")

        return df.loc[:, columns]

    @classmethod
    def _build_dataframe_and_info(cls, raw_data: Dict[str, Any], error_prefix: str = "API response") -> tuple[pd.DataFrame, str]:
        df = cls._to_dataframe(raw_data, error_prefix=error_prefix)
        meta = cls._extract_metadata(raw_data, queried_rows=len(df))
        return df, cls._metadata_to_string(meta)

    @retry_on_error(max_retries=3, delay=1.0)
    def preview_raw(self, dataset_code: str) -> Dict[str, Any]:
        response = requests.get(
            self.PREVIEW_URL,
            params={"dataSetCode": dataset_code},
            timeout=self.timeout,
        )

        if not response.ok:
            self._raise_api_error(response)

        return response.json()

    def preview(self, dataset_code: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        data = self.preview_raw(dataset_code)
        df = self._to_dataframe(data, error_prefix="preview response")
        if columns:
            return self._filter_dataframe_columns(df, columns)
        return df

    @retry_on_error(max_retries=3, delay=1.0)
    def _request_data(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        self._require_auth()

        if page < 1:
            raise ValueError("page must be >= 1")

        payload: Dict[str, Any] = {
            "dataSetCode": dataset_code,
            "page": page,
        }

        # Quan trọng: không gửi mảng rỗng nếu API không chấp nhận.
        if conditions:
            payload["conditions"] = conditions

        if select_fields:
            payload["selectFields"] = select_fields

        if limit is not None:
            payload["limit"] = limit

        # Chỉ gửi kwargs có giá trị thật, tránh đẩy None/list rỗng lên API.
        for key, value in kwargs.items():
            if value is not None and value != [] and value != {}:
                payload[key] = value

        if self.debug:
            print("REQUEST PAYLOAD:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))

        response = self.session.post(self.SEARCH_URL, json=payload, timeout=self.timeout)

        if self.debug:
            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text[:2000])

        if not response.ok:
            self._raise_api_error(response)

        return response.json()

    def get_data(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        columns: Optional[List[str]] = None,
        page: int = 1,
        limit: Optional[int] = None,
        return_type: str = "dataframe",
        include_info: bool = True,
        **kwargs: Any,
    ):
        raw_data = self._request_data(
            dataset_code=dataset_code,
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            **kwargs,
        )

        if return_type == "dataframe":
            result, info = self._build_dataframe_and_info(raw_data, error_prefix="API response")
            if columns:
                result = self._filter_dataframe_columns(result, columns)
        elif return_type == "json":
            result = json.dumps(raw_data, indent=2, ensure_ascii=False)
            meta = self._extract_metadata(raw_data, queried_rows=None)
            info = self._metadata_to_string(meta)
        elif return_type == "dict":
            result = raw_data
            meta = self._extract_metadata(raw_data, queried_rows=None)
            info = self._metadata_to_string(meta)
        else:
            raise ValueError("return_type must be 'dataframe', 'json', or 'dict'")

        if include_info:
            return {"data": result, "info": info}
        return result

    def get_dataframe(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        columns: Optional[List[str]] = None,
        page: int = 1,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        return self.get_data(
            dataset_code=dataset_code,
            conditions=conditions,
            select_fields=select_fields,
            columns=columns,
            page=page,
            limit=limit,
            return_type="dataframe",
            include_info=False,
            **kwargs,
        )

    def get_data_info(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        page: int = 1,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        result = self.get_data(
            dataset_code=dataset_code,
            conditions=conditions,
            select_fields=select_fields,
            page=page,
            limit=limit,
            return_type="dataframe",
            include_info=True,
            **kwargs,
        )
        return result["info"]

    def download_data(
        self,
        dataset_code: str,
        output_path: str,
        file_format: str = "csv",
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        start_page: int = 1,
        end_page: Optional[int] = None,
        limit: Optional[int] = None,
        show_progress: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        normalized_format = file_format.lower().strip()
        if normalized_format not in {"csv", "json"}:
            raise ValueError("file_format must be 'csv' or 'json'")

        if start_page < 1:
            raise ValueError("start_page must be >= 1")

        if end_page is not None and end_page < start_page:
            raise ValueError("end_page must be >= start_page")

        path = Path(output_path)
        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        page = start_page
        page_count = 0
        total_rows = 0
        dataframes: List[pd.DataFrame] = []
        raw_pages: List[Dict[str, Any]] = []
        discovered_total_page: Optional[int] = None

        while True:
            if end_page is not None and page > end_page:
                break

            raw_data = self._request_data(
                dataset_code=dataset_code,
                conditions=conditions,
                select_fields=select_fields,
                page=page,
                limit=limit,
                **kwargs,
            )

            meta = self._extract_metadata(raw_data, queried_rows=None)
            current_page = meta.get("currentPage") or page
            total_page = meta.get("totalPage")
            if isinstance(total_page, int):
                discovered_total_page = total_page

            if show_progress:
                total_page_text = str(total_page) if total_page is not None else "?"
                print(f"Downloading currentPage {current_page}/{total_page_text}...")

            page_count += 1

            payload = raw_data.get("data", {}) if isinstance(raw_data, dict) else {}
            rows = payload.get("dataDetail", []) if isinstance(payload, dict) else []

            if normalized_format == "csv":
                df, _ = self._build_dataframe_and_info(raw_data, error_prefix="API response")
                if df.empty:
                    break
                dataframes.append(df)
                total_rows += len(df)
            else:
                raw_pages.append(raw_data)
                if isinstance(rows, list):
                    total_rows += len(rows)
                    if not rows:
                        break

            if discovered_total_page is not None and page >= discovered_total_page:
                break

            # Nếu API không trả totalPage và trang hiện tại không có dữ liệu thì dừng.
            if not rows:
                break

            page += 1

        if normalized_format == "csv":
            final_df = pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()
            final_df.to_csv(path, index=False)
        else:
            with path.open("w", encoding="utf-8") as f:
                json.dump(raw_pages, f, ensure_ascii=False, indent=2)

        return {
            "output_path": str(path),
            "file_format": normalized_format,
            "pages_downloaded": page_count,
            "rows_downloaded": total_rows,
            "start_page": start_page,
            "end_page": end_page if end_page is not None else discovered_total_page,
        }

    def paginate(
        self,
        dataset_code: str,
        max_pages: Optional[int] = None,
        limit: Optional[int] = None,
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Iterator[pd.DataFrame]:
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
