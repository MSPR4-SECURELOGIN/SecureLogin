import json
import os
import psycopg2
import bcrypt
import pyotp
import secrets
import string
import qrcode
import base64
from io import BytesIO
from datetime import datetime

def generate_password(length=24):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

def handle(req):
    try:
        data = json.loads(req)
        username = data.get("username")

        if not username:
            return json.dumps({ "success": False, "error": "Missing username" })

        # Génération
        new_password = generate_password()
        hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        totp = pyotp.TOTP(pyotp.random_base32())
        secret = totp.secret
        uri = totp.provisioning_uri(name=username, issuer_name="COFRAP")

        # QR code 2FA
        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Connexion PostgreSQL
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "admin"),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "admin")
        )
        cur = conn.cursor()

        cur.execute("""
            UPDATE users
            SET password = %s, mfa_secret = %s, gendate = %s, expired = FALSE
            WHERE username = %s
        """, (hashed_pw, secret, datetime.now(), username))
        conn.commit()

        return json.dumps({
            "success": True,
            "new_password": new_password,
            "totp_qr_base64": qr_base64
        })

    except Exception as e:
        return json.dumps({ "success": False, "error": str(e) })
