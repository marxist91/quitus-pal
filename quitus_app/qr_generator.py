# quitus_app/qr_generator.py
import json
import qrcode
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from io import BytesIO
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIVATE_KEY_PATH = os.path.join(BASE_DIR, "private.pem")

def load_private_key():
    if not os.path.exists(PRIVATE_KEY_PATH):
        key = RSA.generate(2048)
        with open(PRIVATE_KEY_PATH, "wb") as f:
            f.write(key.export_key())
        with open(os.path.join(BASE_DIR, "public.pem"), "wb") as f:
            f.write(key.publickey().export_key())
        print("[+] Clés RSA générées : private.pem & public.pem")
    return RSA.import_key(open(PRIVATE_KEY_PATH, "rb").read())

def generate_secure_qr(data: dict) -> bytes:
    private_key = load_private_key()
    data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    h = SHA256.new(data_str.encode())
    signature = pkcs1_15.new(private_key).sign(h).hex()
    qr_content = f"id:{data['id']}|sig:{signature}"

    qr = qrcode.QRCode(version=3, box_size=10, border=5)
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()