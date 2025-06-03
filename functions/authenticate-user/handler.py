import json
import os
import psycopg2
import bcrypt
import pyotp
from datetime import datetime, timedelta

def handle(req):
    try:
        data = json.loads(req)
        username = data.get("username")
        password = data.get("password")
        code2fa = data.get("code2fa")

        if not username or not password or not code2fa:
            return json.dumps({ "authenticated": False, "error": "Missing fields" })

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
            return json.dumps({ "authenticated": False, "error": "User not found" })

        hashed_pw, mfa_secret, gendate = row

        # Vérifie l'expiration (180 jours)
        if gendate < datetime.now() - timedelta(days=180):
            cur.execute("UPDATE users SET expired = TRUE WHERE username = %s", (username,))
            conn.commit()
            return json.dumps({ "authenticated": False, "expired": True })

        # Vérification mot de passe
        if not bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
            return json.dumps({ "authenticated": False, "error": "Wrong password" })

        # Vérification 2FA (TOTP)
        totp = pyotp.TOTP(mfa_secret)
        if not totp.verify(code2fa):
            return json.dumps({ "authenticated": False, "error": "Invalid 2FA code" })

        return json.dumps({ "authenticated": True })

    except Exception as e:
        return json.dumps({ "authenticated": False, "error": str(e) })
