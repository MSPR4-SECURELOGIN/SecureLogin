import json
import os
import psycopg2
import bcrypt
import pyotp
import secrets
import string
import base64
import qrcode
from io import BytesIO
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

def generate_password(length=24):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

def handle(req):  # <-- maintenant avec paramètre
    try:
        data = json.loads(req)
        username = data.get("username")
        
        if not username:
            return jsonify({ "success": False, "error": "Missing username" })

        raw_password = generate_password()
        hashed_password = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

        totp = pyotp.TOTP(pyotp.random_base32())
        secret = totp.secret
        uri = totp.provisioning_uri(name=username, issuer_name="COFRAP")

        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "admin"),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "admin")
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, password, mfa_secret, gendate)
            VALUES (%s, %s, %s, %s)
        """, (username, hashed_password, secret, datetime.now()))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "username": username,
            "password": raw_password,
            "totp_qr_base64": qr_base64
        })

    except Exception as e:
        return jsonify({ "success": False, "error": str(e) })

@app.route("/", methods=["POST"])
def main_route():
    return handle(request.get_data(as_text=True))  # ici aussi, on passe bien les données
