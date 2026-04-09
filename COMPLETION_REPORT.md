# Completion Report

## Status: COMPLETE

## Tính năng

- Authentication: API Key (từ `.env`) + Token (login)
- API calls: `get_data()` (search), `preview()` (preview dataset)
- Auto retry: 3 lần với exponential backoff
- Session management: persistent headers
- Config: tất cả URLs đọc từ `.env`

## Authentication

| Method | Cách dùng |
|--------|-----------|
| API Key từ `.env` | `client = Datacore()` |
| API Key trực tiếp | `client = Datacore(api_key="key")` |
| Token login | `token = AuthManager.login(email, pwd)` → `Datacore(token=token)` |

## Environment Variables (`.env`)

| Variable | Mục đích |
|----------|----------|
| `X_DATACORE_API_KEY` | API key xác thực |
| `DATACORE_BASE_URL` | Base URL cho data API |
| `DATACORE_LOGIN_URL` | URL login endpoint |

## Files

| File | Mục đích |
|------|----------|
| `datacore/client.py` | Client chính (AuthManager, Datacore) |
| `datacore/__init__.py` | Export public API |
| `setup.py` | Package install config |
| `pyproject.toml` | Project metadata |
| `requirements.txt` | Dependencies |
| `.env` | API key & URLs (git-ignored) |
