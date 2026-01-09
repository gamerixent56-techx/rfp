from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import secrets
import requests
from datetime import datetime

app = FastAPI(title="RFP Triage API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

YOUR_TRON_WALLET = "TAe5PygupQLrGRueQs91RTNFjaBskywekp"
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
REQUIRED_AMOUNT = 19

licenses = {}
pending_verifications = {}

class PaymentVerification(BaseModel):
    transaction_hash: str
    email: EmailStr

class LicenseValidation(BaseModel):
    license_key: str

class LicenseGeneration(BaseModel):
    email: EmailStr
    transaction_hash: str

def generate_license_key():
    part1 = secrets.token_hex(2).upper()
    part2 = secrets.token_hex(2).upper()
    part3 = secrets.token_hex(2).upper()
    return f"RFP-{part1}-{part2}-{part3}"

def verify_tron_payment(tx_hash: str):
    try:
        url = f"https://api.tronscan.org/api/transaction-info?hash={tx_hash}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "trc20TransferInfo" not in data:
            return False, 0, ""
        
        transfers = data["trc20TransferInfo"]
        
        for transfer in transfers:
            to_address = transfer.get("to_address", "")
            contract = transfer.get("contract_address", "")
            amount_str = transfer.get("amount_str", "0")
            amount = float(amount_str) / (10 ** 6)
            from_address = transfer.get("from_address", "")
            
            if (to_address == YOUR_TRON_WALLET and contract == USDT_TRC20_CONTRACT):
                if 18.5 <= amount <= 19.5:
                    return True, amount, from_address
        
        return False, 0, ""
    except Exception as e:
        print(f"Error: {e}")
        return False, 0, ""

def send_notification_email(email: str, license_key: str, tx_hash: str):
    notification = {
        "email": email,
        "license_key": license_key,
        "transaction_hash": tx_hash,
        "timestamp": datetime.now().isoformat(),
        "status": "pending_email"
    }
    pending_verifications[tx_hash] = notification
    print(f"NEW LICENSE: {email} -> {license_key}")

@app.get("/")
def root():
    return {"service": "RFP Triage API", "version": "1.0.0", "status": "operational"}

@app.post("/verify-payment")
async def verify_payment(data: PaymentVerification, background_tasks: BackgroundTasks):
    if data.transaction_hash in [v["transaction_hash"] for v in licenses.values()]:
        raise HTTPException(status_code=400, detail="Transaction already used")
    
    is_valid, amount, from_address = verify_tron_payment(data.transaction_hash)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Payment verification failed")
    
    license_key = generate_license_key()
    
    licenses[license_key] = {
        "email": data.email,
        "transaction_hash": data.transaction_hash,
        "amount": amount,
        "from_address": from_address,
        "created_at": datetime.now().isoformat(),
        "active": True
    }
    
    background_tasks.add_task(send_notification_email, data.email, license_key, data.transaction_hash)
    
    return {
        "success": True,
        "message": "Payment verified! Check email for license key.",
        "amount_paid": amount
    }

@app.post("/validate-license")
async def validate_license(data: LicenseValidation):
    license_info = licenses.get(data.license_key)
    if license_info and license_info.get("active"):
        return {"valid": True, "plan": "unlimited", "email": license_info["email"]}
    return {"valid": False, "error": "Invalid license key"}

@app.get("/admin/pending")
async def get_pending_verifications():
    return {"pending_count": len(pending_verifications), "verifications": list(pending_verifications.values())}

@app.get("/admin/licenses")
async def get_all_licenses():
    return {"total_licenses": len(licenses), "licenses": licenses}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "total_licenses": len(licenses),
        "pending_verifications": len(pending_verifications)
    }
```

- Click **"Commit new file"** (green button at bottom)

**✅ Done? Type "MAIN.PY DONE"**

---

### **3.2 Create requirements.txt**
- Click **"Add file"** again
- Click **"Create new file"**
- Filename: `requirements.txt`
- Paste this:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic[email]==2.5.3
requests==2.31.0
python-multipart==0.0.6
