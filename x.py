import re
import tls_client

# URL ที่รับเข้ามา
url = "https://gift.truemoney.com/campaign/?v=01970caa6aba71908bff56300579021206o"

# ตรวจสอบว่า URL ตรงตาม pattern หรือไม่
match = re.match(r"https:\/\/gift\.truemoney\.com\/campaign\/\?v=([a-zA-Z0-9]+)", url)
if not match:
    print("❌ URL ไม่ถูกต้อง")
else:
    voucher_hash = match.group(1)  # ดึง voucher hash

    session = tls_client.Session(
        client_identifier="chrome_120",
        random_tls_extension_order=True
    )

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://gift.truemoney.com",
        "referer": "https://gift.truemoney.com/campaign/card",
        "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "accept-language": "th-TH,th;q=0.9,en;q=0.8",
    }

    payload = {
        "mobile": "0954459175",
        "voucher_hash": voucher_hash
    }

    response = session.post(
        f"https://gift.truemoney.com/campaign/vouchers/{voucher_hash}/redeem",
        headers=headers,
        json=payload
    )

    print("✅ Status:", response.status_code)
    print("🔄 Response:", response.text)
