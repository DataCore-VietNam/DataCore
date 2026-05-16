from __future__ import annotations

import json
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import pandas as pd
import requests
from dotenv import dotenv_values


def _resolve_api_key(explicit: Optional[str]) -> str:
    """
    Resolve the API key from (in order):
      1. The explicit `api_key=` argument.
      2. The `X_API_KEY` environment variable.
      3. The `X_API_KEY` entry of a `.env` file in the current working
         directory at the time the client is constructed.
    Returns the empty string when nothing is found.
    """
    if explicit:
        return explicit.strip()

    env_value = os.environ.get("X_API_KEY")
    if env_value:
        return env_value.strip()

    # Read .env lazily, so changes to .env between imports and constructions
    # are picked up (the old module-level call only read once at import time).
    try:
        dotfile = dotenv_values()
    except Exception:
        dotfile = {}
    return (dotfile.get("X_API_KEY") or "").strip()


class DatacoreError(Exception):
    """Base exception for Datacore package."""


class AuthenticationError(DatacoreError):
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
        self.api_key = _resolve_api_key(api_key)

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

    @staticmethod
    def _to_polars(data: Dict[str, Any], error_prefix: str = "response"):
        """
        Convert a raw API response to a polars.DataFrame. Polars is an
        optional dependency; install with `pip install "datacore[polars]"`.
        """
        try:
            import polars as pl  # type: ignore
        except ImportError as exc:  # pragma: no cover -- exercised in install-path tests
            raise ImportError(
                "polars is required for return_type='polars'. "
                "Install with: pip install 'datacore[polars]'"
            ) from exc

        payload = Datacore._get_payload(data, error_prefix=error_prefix)
        rows = payload.get("dataDetail")
        fields = payload.get("fields")
        if rows is None:
            raise APIRequestError(
                f"Cannot convert {error_prefix} to polars DataFrame: missing key 'dataDetail'"
            )
        if fields is None:
            raise APIRequestError(
                f"Cannot convert {error_prefix} to polars DataFrame: missing key 'fields'"
            )

        try:
            return pl.DataFrame(rows, schema=fields, orient="row")
        except Exception as exc:
            raise APIRequestError(
                f"Cannot convert {error_prefix} to polars DataFrame: {exc}"
            ) from exc

    @staticmethod
    def _filter_polars_columns(df, columns: List[str]):
        if not columns:
            raise ValueError("columns cannot be empty")
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ValueError(
                f"Columns not found: {missing}. Available columns: {list(df.columns)}"
            )
        return df.select(columns)

    @classmethod
    def _build_dataframe_and_info(cls, raw_data: Dict[str, Any], error_prefix: str = "API response") -> tuple[pd.DataFrame, str]:
        df = cls._to_dataframe(raw_data, error_prefix=error_prefix)
        meta = cls._extract_metadata(raw_data, queried_rows=len(df))
        return df, cls._metadata_to_string(meta)

    def _check_body_error(self, data: Dict[str, Any]) -> None:
        """
        Some gateway endpoints return HTTP 200 with an error body, e.g.
        {"status": false, "message": "#030003 UnAuthorizedException",
         "httpCode": 401, "errorCode": "030003"}
        Inspect the body's httpCode/status fields and raise the correct
        exception so callers can distinguish auth failures from generic
        API errors.
        """
        if not isinstance(data, dict):
            return

        body_status = data.get("status")
        body_code = data.get("httpCode")
        if body_status is False or (isinstance(body_code, int) and body_code >= 400):
            message = (
                data.get("message")
                or data.get("error")
                or data.get("detail")
                or f"HTTP {body_code}"
            )
            full_message = f"HTTP {body_code}: {message}"
            if body_code in (401, 403):
                lowered = str(message).lower()
                if any(word in lowered for word in
                       ["permission", "forbidden", "denied", "not allowed"]):
                    raise PermissionDeniedError(full_message)
                raise AuthenticationError(full_message)
            raise APIRequestError(full_message)

    @retry_on_error(max_retries=3, delay=1.0)
    def preview_raw(self, dataset_code: str) -> Dict[str, Any]:
        response = self.session.get(
            self.PREVIEW_URL,
            params={"dataSetCode": dataset_code},
            timeout=self.timeout,
        )

        if not response.ok:
            self._raise_api_error(response)

        data = response.json()
        self._check_body_error(data)
        return data

    def preview(
        self,
        dataset_code: str,
        columns: Optional[List[str]] = None,
        return_type: str = "dataframe",
    ):
        """
        Preview a dataset (no API key required).

        return_type:
        - "dataframe" (default) -> pandas.DataFrame
        - "polars"              -> polars.DataFrame (requires `pip install "datacore[polars]"`)
        """
        if return_type not in {"dataframe", "polars"}:
            raise ValueError("preview return_type must be 'dataframe' or 'polars'")

        if return_type == "polars":
            try:
                import polars  # noqa: F401
            except ImportError as exc:
                raise ImportError(
                    "polars is required for return_type='polars'. "
                    "Install with: pip install 'datacore[polars]'"
                ) from exc

        data = self.preview_raw(dataset_code)

        # Gateway returns status="success" with data=null when the dataset
        # code is unknown. Surface a clear error instead of the misleading
        # "Cannot parse preview response: success".
        if isinstance(data, dict) and data.get("data") is None:
            raise APIRequestError(
                f"Dataset {dataset_code!r} not found or has no preview data. "
                f"Gateway response: status={data.get('status')!r}, "
                f"message={data.get('message')!r}"
            )

        if return_type == "polars":
            df = self._to_polars(data, error_prefix="preview response")
            if columns:
                return self._filter_polars_columns(df, columns)
            return df

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

        data = response.json()
        self._check_body_error(data)
        return data

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
        """
        Fetch a page of data from a dataset.

        return_type:
        - "dataframe" (default) -> pandas.DataFrame
        - "polars"              -> polars.DataFrame (requires `pip install "datacore-vn[polars]"`)
        - "json"                -> JSON string
        - "dict"                -> raw response dict

        conditions:
            **Experimental.** Server-side row filter, forwarded to the
            gateway verbatim. The accepted JSON shape is defined by the
            gateway and is not yet finalised -- the shapes tried so far are
            rejected with HTTP 400 by `gateway.datacore.vn`. Until the
            schema is confirmed, prefer fetching unfiltered data and
            filtering the returned DataFrame client-side. This parameter
            may change in a future release.
        """
        valid = {"dataframe", "polars", "json", "dict"}
        if return_type not in valid:
            raise ValueError(f"return_type must be one of {sorted(valid)}")

        # Fail fast on missing optional polars dep -- before any network I/O.
        if return_type == "polars":
            try:
                import polars  # noqa: F401
            except ImportError as exc:
                raise ImportError(
                    "polars is required for return_type='polars'. "
                    "Install with: pip install 'datacore[polars]'"
                ) from exc

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
        elif return_type == "polars":
            result = self._to_polars(raw_data, error_prefix="API response")
            if columns:
                result = self._filter_polars_columns(result, columns)
            meta = self._extract_metadata(raw_data, queried_rows=len(result))
            info = self._metadata_to_string(meta)
        elif return_type == "json":
            result = json.dumps(raw_data, indent=2, ensure_ascii=False)
            meta = self._extract_metadata(raw_data, queried_rows=None)
            info = self._metadata_to_string(meta)
        else:  # dict
            result = raw_data
            meta = self._extract_metadata(raw_data, queried_rows=None)
            info = self._metadata_to_string(meta)

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
        """Fetch a single page as a pandas.DataFrame (no info dict)."""
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

    def get_polars(
        self,
        dataset_code: str,
        conditions: Optional[List[Dict[str, Any]]] = None,
        select_fields: Optional[List[str]] = None,
        columns: Optional[List[str]] = None,
        page: int = 1,
        limit: Optional[int] = None,
        **kwargs: Any,
    ):
        """
        Fetch a single page as a polars.DataFrame (no info dict).
        Requires polars: `pip install "datacore[polars]"`.
        """
        return self.get_data(
            dataset_code=dataset_code,
            conditions=conditions,
            select_fields=select_fields,
            columns=columns,
            page=page,
            limit=limit,
            return_type="polars",
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
        columns: Optional[List[str]] = None,
        start_page: int = 1,
        end_page: Optional[int] = None,
        limit: Optional[int] = None,
        show_progress: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Download a paginated dataset to a CSV or JSON file.

        columns:
            Optional list of column names to keep in the output. Only applies
            when file_format == "csv" (JSON output preserves the full raw
            response). If a requested column is missing from the API response,
            ValueError is raised on the first page.
        """
        normalized_format = file_format.lower().strip()
        if normalized_format not in {"csv", "json"}:
            raise ValueError("file_format must be 'csv' or 'json'")

        if start_page < 1:
            raise ValueError("start_page must be >= 1")

        if end_page is not None and end_page < start_page:
            raise ValueError("end_page must be >= start_page")

        if columns is not None and normalized_format == "json":
            raise ValueError(
                "columns filter is only supported when file_format='csv'"
            )

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
                if columns:
                    df = self._filter_dataframe_columns(df, columns)
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
