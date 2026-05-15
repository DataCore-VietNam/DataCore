"""Extensive smoke + live API tests for datacore client.

Runs unauthenticated demo path, validates all error classes, and (when
X_API_KEY is set) exercises every authenticated method end-to-end.
"""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
import traceback
from pathlib import Path

PASS = []
FAIL = []
SKIP = []


def section(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def check(label: str, cond: bool, detail: str = "") -> None:
    icon = "PASS" if cond else "FAIL"
    (PASS if cond else FAIL).append(label)
    print(f"  [{icon}] {label}" + (f"  -- {detail}" if detail else ""))


def expect_raises(label: str, exc_type, fn, *args, **kwargs) -> Exception | None:
    try:
        fn(*args, **kwargs)
    except exc_type as e:
        PASS.append(label)
        print(f"  [PASS] {label}  -- raised {type(e).__name__}: {str(e)[:80]}")
        return e
    except Exception as e:
        FAIL.append(label)
        print(f"  [FAIL] {label}  -- raised {type(e).__name__} (wanted {exc_type.__name__}): {str(e)[:80]}")
        return e
    FAIL.append(label)
    print(f"  [FAIL] {label}  -- no exception raised (wanted {exc_type.__name__})")
    return None


def safe(label: str, fn, *args, **kwargs):
    try:
        r = fn(*args, **kwargs)
        PASS.append(label)
        print(f"  [PASS] {label}  -- returned {type(r).__name__}")
        return r
    except Exception as e:
        FAIL.append(label)
        print(f"  [FAIL] {label}  -- {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)
        return None


# -----------------------------------------------------------------------------

section("1) Import + metadata")
import datacore
from datacore import (
    Datacore,
    DatacoreError,
    AuthenticationError,
    PermissionDeniedError,
    APIRequestError,
)
print(f"  version = {datacore.__version__}")
print(f"  author  = {datacore.__author__}")
check("version is 0.2.0", datacore.__version__ == "0.2.0")
check("author no longer placeholder", datacore.__author__ != "Your Name")
check("all expected exceptions exported", set(datacore.__all__) >= {
    "Datacore", "DatacoreError", "AuthenticationError",
    "PermissionDeniedError", "APIRequestError"
})

# -----------------------------------------------------------------------------
section("2) Exception hierarchy")
for cls in (AuthenticationError, PermissionDeniedError, APIRequestError):
    check(f"{cls.__name__} subclasses DatacoreError",
          issubclass(cls, DatacoreError))

# Critical: AuthenticationError must NOT contain DatoreError typo workaround
import datacore.client as _client
src = Path(_client.__file__).read_text()
check("DatoreError typo workaround removed", "DatoreError" not in src)

# -----------------------------------------------------------------------------
# Stash X_API_KEY for sections 3-12 so we exercise the truly-unauthenticated
# code paths. Restored before section 13 (live API).
_saved_env_key = os.environ.pop("X_API_KEY", None)

section("3) Instantiation (no key)")
client = Datacore()
check("no api_key by default", client.api_key == "")
check("not authenticated", not client.is_authenticated())
check("default timeout=30", client.timeout == 30)
check("Content-Type header set",
      client.session.headers.get("Content-Type") == "application/json")
check("no x-api-key header when unauthenticated",
      "x-api-key" not in client.session.headers)

# -----------------------------------------------------------------------------
section("4) Method surface")
public = sorted([n for n, _ in inspect.getmembers(Datacore, inspect.isfunction)
                 if not n.startswith("_")])
for m in ("preview", "preview_raw", "get_data", "get_dataframe", "get_data_info",
          "paginate", "download_data", "set_api_key", "is_authenticated"):
    check(f"method present: {m}", m in public)

# -----------------------------------------------------------------------------
section("5) set_api_key validation")
expect_raises("empty key rejected", ValueError, client.set_api_key, "")
expect_raises("whitespace key rejected", ValueError, client.set_api_key, "   ")
client.set_api_key("test-123")
check("after set: authenticated", client.is_authenticated())
check("x-api-key header set",
      client.session.headers.get("x-api-key") == "test-123")
client = Datacore()  # reset

# -----------------------------------------------------------------------------
section("6) preview() — demo, no key")
df = safe("preview('vsic')", client.preview, "vsic")
if df is not None:
    check("DataFrame returned", df.shape[0] > 0 and df.shape[1] > 0,
          f"shape={df.shape}")
    check("expected columns present",
          {"ID", "Code", "Name"} <= set(df.columns))

raw = safe("preview_raw('vsic')", client.preview_raw, "vsic")
check("preview_raw goes through session (no bare requests.get)",
      "self.session.get" in src and "    response = requests.get(" not in src)

# -----------------------------------------------------------------------------
section("7) preview() column filter")
df2 = safe("preview with col filter", client.preview, "vsic", ["ID", "Code"])
if df2 is not None:
    check("filter applied",
          list(df2.columns) == ["ID", "Code"],
          f"got {list(df2.columns)}")
expect_raises("unknown column rejected", ValueError,
              client.preview, "vsic", ["__nope__"])

# -----------------------------------------------------------------------------
section("8) preview() with unknown dataset → clear error")
err = expect_raises("unknown dataset raises APIRequestError",
                    APIRequestError,
                    client.preview, "definitely_not_real_xyz_12345")
if err is not None:
    msg = str(err)
    check("error mentions 'not found'",
          "not found" in msg.lower(),
          f"msg={msg[:120]}")

# -----------------------------------------------------------------------------
section("9) Auth-required methods without key")
expect_raises("get_data → AuthenticationError",
              AuthenticationError, client.get_data, "x")
expect_raises("get_dataframe → AuthenticationError",
              AuthenticationError, client.get_dataframe, "x")
expect_raises("get_data_info → AuthenticationError",
              AuthenticationError, client.get_data_info, "x")
expect_raises("download_data → AuthenticationError",
              AuthenticationError, client.download_data, "x", "/tmp/x.csv")

# paginate is a generator; auth fires on first next()
gen = client.paginate("x")
expect_raises("paginate → AuthenticationError on first next()",
              AuthenticationError, next, gen)

# -----------------------------------------------------------------------------
section("10) Argument validation")
c2 = Datacore(api_key="placeholder")
expect_raises("bad return_type", ValueError,
              c2.get_data, "x", return_type="xml")
expect_raises("bad file_format", ValueError,
              c2.download_data, "x", "/tmp/x.csv", file_format="xml")
expect_raises("start_page<1", ValueError,
              c2.download_data, "x", "/tmp/x.csv", start_page=0)
expect_raises("end_page<start_page", ValueError,
              c2.download_data, "x", "/tmp/x.csv", start_page=5, end_page=2)
expect_raises("columns w/ json format rejected", ValueError,
              c2.download_data, "x", "/tmp/x.csv",
              file_format="json", columns=["a"])

# -----------------------------------------------------------------------------
section("11) Body-level auth error classification (live)")
# Invalid key gets HTTP 200 with httpCode:401 body — must classify as
# AuthenticationError now.
c_bad = Datacore(api_key="definitely-not-a-real-key-xyz")
err = expect_raises("bad key → AuthenticationError (body-level)",
                    AuthenticationError,
                    c_bad.get_data, "dataset_historical_price", limit=1)

# -----------------------------------------------------------------------------
section("12) Static helpers")
expect_raises("_get_payload(not-dict)", APIRequestError,
              Datacore._get_payload, "x")
expect_raises("_get_payload({})", APIRequestError,
              Datacore._get_payload, {})
r = Datacore._get_payload({"data": {"x": 1}})
check("_get_payload happy path", r == {"x": 1})
df3 = Datacore._to_dataframe({"data": {"dataDetail": [[1, 2]], "fields": ["a", "b"]}})
check("_to_dataframe happy path", df3.shape == (1, 2))
expect_raises("_to_dataframe missing fields", APIRequestError,
              Datacore._to_dataframe, {"data": {"dataDetail": [[1]]}})

# -----------------------------------------------------------------------------
section("13) Live API — paid endpoints (X_API_KEY required)")
if _saved_env_key is not None:
    os.environ["X_API_KEY"] = _saved_env_key
api_key = os.environ.get("X_API_KEY")
if not api_key:
    print("  SKIPPED — X_API_KEY not set")
    SKIP.append("live API tests")
else:
    paid = Datacore(api_key=api_key)
    check("authenticated", paid.is_authenticated())

    # get_data
    r = safe("get_data dataset_historical_price",
             paid.get_data, "dataset_historical_price", limit=5)
    if r is not None:
        check("get_data returns dict with data+info",
              isinstance(r, dict) and "data" in r and "info" in r)
        check("data is DataFrame with rows",
              r["data"].shape[0] > 0)

    # get_data columns filter
    r = safe("get_data with columns",
             paid.get_data, "dataset_historical_price",
             columns=["symbol", "date", "close_price"], limit=5)
    if r is not None:
        check("columns filtered",
              list(r["data"].columns) == ["symbol", "date", "close_price"])

    # get_dataframe shortcut
    df_paid = safe("get_dataframe", paid.get_dataframe,
                   "dataset_historical_price", limit=5)
    if df_paid is not None:
        check("get_dataframe returns DataFrame", df_paid.shape[0] > 0)

    # return_type variants
    j = safe("get_data return_type=json",
             paid.get_data, "dataset_historical_price",
             limit=2, return_type="json", include_info=False)
    check("json result is str", isinstance(j, str))

    d = safe("get_data return_type=dict",
             paid.get_data, "dataset_historical_price",
             limit=2, return_type="dict", include_info=False)
    check("dict result is dict", isinstance(d, dict))

    # get_data_info
    info = safe("get_data_info", paid.get_data_info,
                "dataset_historical_price", limit=2)
    check("info is str with totalPage", isinstance(info, str)
          and "totalPage" in info)

    # paginate
    pages_seen = 0
    try:
        for page_df in paid.paginate("dataset_historical_price",
                                     max_pages=2, limit=3):
            pages_seen += 1
        check(f"paginate yielded {pages_seen} pages", pages_seen == 2)
    except Exception as e:
        FAIL.append("paginate")
        print(f"  [FAIL] paginate raised: {type(e).__name__}: {e}")

    # download_data CSV with column filter (THE BUG WE FIXED)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "test.csv"
        r = safe("download_data CSV with columns filter",
                 paid.download_data,
                 dataset_code="dataset_historical_price",
                 columns=["symbol", "date", "close_price"],
                 output_path=str(out),
                 file_format="csv",
                 start_page=1, end_page=1, limit=3,
                 show_progress=False)
        if r is not None and out.exists():
            import pandas as pd
            actual = pd.read_csv(out)
            check("CSV column filter actually applied",
                  list(actual.columns) == ["symbol", "date", "close_price"],
                  f"got {list(actual.columns)}")
            check("CSV has rows", len(actual) > 0)

        # JSON output
        out_json = Path(d) / "test.json"
        r = safe("download_data JSON",
                 paid.download_data,
                 dataset_code="dataset_historical_price",
                 output_path=str(out_json),
                 file_format="json",
                 start_page=1, end_page=1, limit=3,
                 show_progress=False)
        check("JSON file written", out_json.exists() and out_json.stat().st_size > 10)

    # debug flag smoke
    paid_debug = Datacore(api_key=api_key, debug=True)
    print("  -- debug=True output below --")
    try:
        paid_debug.get_data("dataset_historical_price", limit=1, include_info=False)
        PASS.append("debug flag works")
        print("  [PASS] debug flag works")
    except Exception as e:
        FAIL.append("debug flag")
        print(f"  [FAIL] debug flag: {e}")

    # ---- polars (optional dep) ----
    try:
        import polars as pl  # type: ignore
        has_polars = True
    except ImportError:
        has_polars = False

    section("13b) Polars return type")
    if not has_polars:
        SKIP.append("polars tests (polars not installed)")
        print("  SKIPPED -- polars not installed in this venv")

        # Even without polars, asking for return_type='polars' should raise
        # ImportError with a helpful message, not blow up cryptically.
        err = expect_raises("return_type='polars' raises ImportError when polars absent",
                            ImportError,
                            paid.get_data, "dataset_historical_price",
                            limit=1, return_type="polars")
        if err and "datacore[polars]" not in str(err):
            FAIL.append("polars ImportError mentions install hint")
            print(f"  [FAIL] ImportError missing install hint: {err}")
        else:
            PASS.append("polars ImportError mentions install hint")
            print(f"  [PASS] polars ImportError mentions install hint")
    else:
        r = safe("get_data return_type='polars'",
                 paid.get_data, "dataset_historical_price",
                 limit=5, return_type="polars")
        if r is not None:
            check("polars result wrapped in dict with data+info",
                  isinstance(r, dict) and isinstance(r["data"], pl.DataFrame))
            check("polars frame has rows", r["data"].height > 0)
            check("polars frame width matches API fields",
                  r["data"].width == 28,
                  f"width={r['data'].width}")

        # columns filter on polars
        r2 = safe("get_data polars + columns filter",
                  paid.get_data, "dataset_historical_price",
                  limit=5, return_type="polars",
                  columns=["symbol", "date", "close_price"])
        if r2 is not None:
            check("polars columns filter applied",
                  r2["data"].columns == ["symbol", "date", "close_price"],
                  f"got {r2['data'].columns}")

        # get_polars convenience
        dfp = safe("get_polars convenience", paid.get_polars,
                   "dataset_historical_price", limit=5)
        if dfp is not None:
            check("get_polars returns polars.DataFrame",
                  isinstance(dfp, pl.DataFrame))

        # preview polars
        dfp_preview = safe("preview return_type='polars'",
                           Datacore().preview, "vsic", None, "polars")
        if dfp_preview is not None:
            check("preview polars has rows", dfp_preview.height > 0)

        # bad columns on polars
        expect_raises("polars bad columns", ValueError,
                      paid.get_polars, "dataset_historical_price",
                      columns=["__nope__"], limit=2)

        # pandas <-> polars row counts agree on same query
        df_pd = paid.get_dataframe("dataset_historical_price", limit=10)
        df_pl = paid.get_polars("dataset_historical_price", limit=10)
        check("pandas vs polars row count matches",
              len(df_pd) == df_pl.height, f"pd={len(df_pd)} pl={df_pl.height}")
        check("pandas vs polars column count matches",
              len(df_pd.columns) == df_pl.width)

# -----------------------------------------------------------------------------
section("SUMMARY")
print(f"  PASSED: {len(PASS)}")
print(f"  FAILED: {len(FAIL)}")
print(f"  SKIPPED: {len(SKIP)}")
if FAIL:
    print("\n  Failed cases:")
    for f in FAIL:
        print(f"    - {f}")
    sys.exit(1)
else:
    print("\n  ALL PASS")
    sys.exit(0)
