# Authentication Guide

## Hai phương thức xác thực

### 1. API Key

Dành cho: server-to-server, scripts, automation.

```python
from datacore import Datacore

# Đọc từ .env
client = Datacore()

# Hoặc truyền trực tiếp
client = Datacore(api_key="your-api-key")
```

Setup `.env`:
```env
X_DATACORE_API_KEY=your-api-key-here
```

Lấy API key: liên hệ support@datacore.vn

### 2. Token (Login)

Dành cho: user-based access, web apps.

```python
from datacore import AuthManager, Datacore

# Login lấy token
token = AuthManager.login("email@example.com", "password")

# Tạo client
client = Datacore(token=token)
```

Token có thể hết hạn. Khi hết hạn, login lại để lấy token mới.

---

## Thứ tự ưu tiên

```
Datacore(api_key="A", token="B")
│
├─ 1. token parameter (nếu có)
├─ 2. api_key parameter (nếu không có token)
└─ 3. X_DATACORE_API_KEY trong .env (nếu không truyền gì)
```

## So sánh

| | API Key | Token |
|---|---|---|
| Best for | Services/Scripts | Web Apps/Users |
| Hết hạn | Không | Có |
| Setup | Lưu trong `.env` | Login mỗi lần |

## FAQ

**Q: Chưa có credentials?**
A: Liên hệ support@datacore.vn để lấy API key, hoặc đăng ký tài khoản trên portal.

**Q: Dùng cả 2 cùng lúc được không?**
A: Không, nhưng có thể tạo nhiều client instances:
```python
client1 = Datacore(api_key="key")
client2 = Datacore(token=token)
```

**Q: Lưu token ở đâu?**
A: Không hardcode. Lưu trong environment variables hoặc file config (git-ignored).
"""
DATACORE CLIENT AUTHENTICATION GUIDE
=====================================

For users with TWO situations:
1. Users WITH login credentials → Use Token/Login Authentication
2. Users WITHOUT credentials yet → Use API Key Authentication
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║            DATACORE CLIENT - DUAL AUTHENTICATION SYSTEM                   ║
╚════════════════════════════════════════════════════════════════════════════╝

TWO AUTHENTICATION PATHS:
════════════════════════════════════════════════════════════════════════════

1️⃣  FOR USERS WITH CREDENTIALS (Email + Password Login)
   ────────────────────────────────────────────────────
   
   Situation: You have account created in Datacore
   
   Use: Token Authentication
   
   Script to test: test_login_interactive.py
   
   Code example:
   ────────────
   from datacore import AuthManager, Datacore
   
   # Step 1: Login → Get Token
   token = AuthManager.login(
       username="your-email@example.com", 
       password="your-password"
   )
   
   # Step 2: Create client with token
   client = Datacore(token=token)
   
   # Step 3: Use normally
   df = client.get_historical_price(limit=100)


2️⃣  FOR USERS WITHOUT CREDENTIALS YET
   ────────────────────────────────────
   
   Situation: You're new, haven't created account yet
   
   Options:
   ├─ Request API Key from support@datacore.vn
   ├─ Create account on Datacore portal
   └─ Use demo/test API key (if available)
   
   Use: API Key Authentication
   
   Script to test: test_api_key_auth.py
   
   Code example:
   ────────────
   from datacore import Datacore
   
   # Option A: From environment (if key is set)
   client = Datacore()
   
   # Option B: Pass directly
   client = Datacore(api_key="your-api-key")
   
   # Step 2: Use normally
   df = client.get_historical_price(limit=100)


AVAILABLE TEST SCRIPTS:
════════════════════════════════════════════════════════════════════════════

File                          Purpose                    Authentication
───────────────────────────────────────────────────────────────────────────
test_login_interactive.py     Interactive test          Token/Login → API Key
test_api_key_auth.py          Test API key auth         API Key (from env)
test_dual_auth.py             Compare both methods      Both (demo)
auth_examples.py              Show both patterns        Both (demo)
debug_login.py                Debug login endpoint      Token/Login
debug_login_extended.py       Extended login tests      Token/Login


HOW TO GET STARTED:
════════════════════════════════════════════════════════════════════════════

STEP 1: Try Token Authentication (if you have credentials)
─────────────────────────────────────────────────────────
   cd c:\\Users\\tranglt\\Desktop\\package_datacore
   python test_login_interactive.py
   
   Follow the prompts to:
   - Test login (if you have credentials)
   - See API key fallback (if no credentials)


STEP 2: Try API Key Authentication (if you have API key)
──────────────────────────────────────────
   $env:X_DATACORE_API_KEY = "your-api-key"
   python test_api_key_auth.py


STEP 3: Review Documentation
────────────────────────────
   - README.md              = Quick start
   - USAGE_GUIDE.md         = Complete guide
   - EXTENSION_GUIDE.md     = Add new datasets
   - test_auth_query.ipynb  = Interactive notebook


QUICK REFERENCE:
════════════════════════════════════════════════════════════════════════════

API Authentication Priority (what the library tries first):
────────────────────────────────────────────────────────────

client = Datacore(api_key="A", token="B")
│
├─ 1st choice: token parameter → "B" (if provided)
├─ 2nd choice: api_key parameter → "A" (if token not provided)
└─ 3rd choice: X_DATACORE_API_KEY env variable (if both not provided)


Authentication Methods Summary:
──────────────────────────────

┌─────────────────────────────────────────────────────────────────────────┐
│ Method          │ Best For              │ Setup Time │ Token Expires  │
├─────────────────────────────────────────────────────────────────────────┤
│ API Key         │ Services/Scripts      │ 5 min      │ No (permanent) │
│ Token (Login)   │ Web Apps/Users        │ 1 min      │ Yes (temporary)│
└─────────────────────────────────────────────────────────────────────────┘


COMMON QUESTIONS:
════════════════════════════════════════════════════════════════════════════

Q: Which authentication should I use?
A: Use API Key if you're building a service/app without user login.
   Use Token if users log in with their own credentials.

Q: I don't have credentials. What do I do?
A: Contact support@datacore.vn to request an API key, or sign up for an
   account if that's available.

Q: Can I use both at the same time?
A: No, but you can create multiple client instances:
   client1 = Datacore(api_key="key")  # Service client
   client2 = Datacore(token=token)    # User client

Q: How do I store the token securely?
A: Don't hardcode tokens. Store them in:
   - Environment variables
   - Secure config files (git-ignored)
   - Secrets management system (AWS Secrets, etc.)

Q: Does token expire?
A: Yes, tokens typically expire. When they do:
   1. Call AuthManager.login() again
   2. Get new token
   3. Create new client with new token

Q: Can I reuse the token?
A: Yes! Get token once, save it, reuse it until it expires.
   token = AuthManager.login(username, password)
   # Save token to config/database
   # Later:
   client = Datacore(token=saved_token)


FILES TO READ:
════════════════════════════════════════════════════════════════════════════
- README.md              ← Start here (overview + quick start)
- USAGE_GUIDE.md         ← Both authentication methods in detail
- EXTENSION_GUIDE.md     ← How to add new datasets
- datacore/client.py     ← Source code + docstrings


═══════════════════════════════════════════════════════════════════════════════
                          Ready to test! 🚀
   Choose your path above and run the appropriate test script.
═══════════════════════════════════════════════════════════════════════════════
""")
