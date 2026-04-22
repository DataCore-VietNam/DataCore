# Datacore Python Client

Python client library cho Datacore API — hỗ trợ hai chế độ:
- **Demo**: Xem trước dataset không cần API key
- **Paid**: Truy cập đầy đủ với API key

## Cài đặt

```bash
pip install -e .
```

## Cấu hình `.env` (tuỳ chọn)

```env
X_API_KEY=your-api-key-here
DATACORE_GATEWAY_URL=https://gateway.datacore.vn
```

---

## Sử dụng

### 1. Khởi tạo client

```python
from datacore import Datacore

# Demo mode (không cần API key)
client = Datacore()

# Paid mode
client = Datacore(api_key="your-api-key")
```

---

### 2. Preview dataset (Demo mode)

Xem trước data mà không cần API key.

```python
# Lấy toàn bộ cột
df = client.preview("dataset_historical_price")
print(df.head())

# Lọc cột cần xem
df = client.preview("dataset_historical_price", columns=["symbol", "date", "close_price"])
print(df.head())
```

---

### 3. Lấy data (Paid mode)

```python
# Lấy toàn bộ cột — trả về {"data": DataFrame, "info": str}
result = client.get_data("dataset_historical_price")
print(result["data"].head())
print(result["info"])
# num: 3760607, totalPage: 37607, currentPage: 1, queried_rows: 100

# Lọc cột
result = client.get_data("dataset_historical_price", columns=["symbol", "date", "close_price"])
print(result["data"].head())
print(result["info"])
```

Tham số đầy đủ:

```python
result = client.get_data(
    dataset_code="dataset_historical_price",
    columns=["symbol", "date", "close_price"],  # lọc cột (tuỳ chọn)
    conditions=[{"field": "symbol", "operator": "=", "value": "AAA"}],  # lọc dữ liệu (tuỳ chọn)
    select_fields=[],        # chọn fields từ API (tuỳ chọn)
    page=1,
    limit=100,
    return_type="dataframe", # "dataframe" | "json" | "dict"
    include_info=True,       # True: trả về {"data": ..., "info": ...} | False: trả về data trực tiếp
)
```

---

### 4. Lấy thông tin dataset

```python
info = client.get_data_info("dataset_historical_price")
print(info)
# num: 3760607, totalPage: 37607, currentPage: 1, queried_rows: 100
```

---

### 5. Download data về file

```python
# Download tất cả các trang
download_result = client.download_data(
    dataset_code="dataset_historical_price",
    output_path="data.csv",
    file_format="csv",   # "csv" hoặc "json"
    start_page=1,
    end_page=None,       # None = tải hết tất cả trang
    limit=1000,
    show_progress=True,
)
print(download_result)
# {"output_path": "data.csv", "pages_downloaded": 37607, "rows_downloaded": 3760607, ...}

# Download chỉ 3 trang đầu
download_result = client.download_data(
    dataset_code="dataset_historical_price",
    output_path="data_page1_3.csv",
    file_format="csv",
    start_page=1,
    end_page=3,
    limit=1000,
    show_progress=True,
)
```

---

## Tổng hợp các phương thức

| Phương thức | Mô tả | Cần API key |
|---|---|---|
| `preview(dataset_code, columns)` | Xem trước data | Không |
| `get_data(dataset_code, columns, ...)` | Lấy data (trả về `{"data", "info"}`) | Có |
| `get_data_info(dataset_code, ...)` | Lấy thông tin tổng quan dataset | Có |
| `download_data(dataset_code, output_path, ...)` | Tải data về file CSV/JSON | Có |

---

## Xử lý lỗi

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `AuthenticationError` | Thiếu hoặc sai API key | Truyền `api_key=` hoặc set `X_API_KEY` trong `.env` |
| `PermissionDeniedError` | Không có quyền truy cập dataset | Kiểm tra gói dịch vụ |
| `APIRequestError` | Lỗi từ server hoặc sai format | Kiểm tra `dataset_code`, `conditions` |
| `ValueError` | Tên cột không tồn tại | Xem danh sách cột trong thông báo lỗi |
