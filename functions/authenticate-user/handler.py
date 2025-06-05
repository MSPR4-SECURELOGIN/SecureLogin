import json
import os
import psycopg2
import bcrypt
import pyotp
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:8081")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
    return response

@app.route("/", methods=["OPTIONS"])
def options():
    return make_response("", 204)

@app.route("/", methods=["POST"])
def main_route():
    return handle(request.get_data(as_text=True))

def handle(req):
    try:
        data = json.loads(req)
        username = data.get("username")
        password = data.get("password")
        code2fa = data.get("code2fa")

        if not username or not password or not code2fa:
            return jsonify({ "authenticated": False, "error": "Missing fields" })

        # Connexion à PostgreSQL
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "admin"),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "admin")
        )
        cur = conn.cursor()

        cur.execute("SELECT password, mfa_secret, gendate FROM users WHERE username = %s", (username,))
        row = cur.fetchone()

        if not row:
            return jsonify({ "authenticated": False, "error": "User not found" })

        hashed_pw, mfa_secret, gendate = row

        # Vérifie l'expiration (180 jours)
        if gendate < datetime.now() - timedelta(days=180):
            cur.execute("UPDATE users SET expired = TRUE WHERE username = %s", (username,))
            conn.commit()
            return jsonify({ "authenticated": False, "expired": True })

        # Vérification mot de passe
        if not bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
            return jsonify({ "authenticated": False, "error": "Wrong password" })

        # Vérification 2FA (TOTP)
        totp = pyotp.TOTP(mfa_secret)
        if not totp.verify(code2fa):
            return jsonify({ "authenticated": False, "error": "Invalid 2FA code" })

        return jsonify({ "authenticated": True })

    except Exception as e:
        return jsonify({ "authenticated": False, "error": str(e) })
