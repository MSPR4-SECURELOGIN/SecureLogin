# MSPR TPRE912 – Projet Serverless avec OpenFaaS

Ce projet est une preuve de concept (PoC) de gestion de comptes utilisateurs sécurisés avec :

- 🔐 Mot de passe fort généré automatiquement
- 📲 Double authentification (2FA) avec TOTP
- ⏳ Expiration automatique au bout de 6 mois
- 🐳 Déploiement complet via Docker Compose
- 🌐 Frontend simple en HTML/JS + Bootstrap
- ⚙️ Backend Serverless avec OpenFaaS + Python

## 📁 Architecture

```
[Frontend] → [OpenFaaS Gateway] → [Fonctions Python] → [Base PostgreSQL]
```

## ▶️ Démarrage rapide

```bash
git clone <repo>
cd projet
docker compose up -d
```

- Frontend : http://localhost:8081  
- OpenFaaS Gateway : http://localhost:8080 (admin/admin)

## 🧪 Tester

1. Créer un utilisateur
2. Scanner le QR code avec Google Authenticator
3. Se connecter avec le mot de passe généré et le code 2FA
4. Tester l'expiration manuellement en modifiant la date dans la base
5. Utiliser le bouton de renouvellement

## 📂 Contenu

- `frontend/` : index.html, script.js
- `functions/` : create-user, authenticate-user, renew-user
- `docker-compose.yml` : tous les services (PostgreSQL, OpenFaaS, frontend)
- `init_cof_userdb.sql` : script de création de la table `users`

## 🛠️ Technologies

- Python 3, bcrypt, pyotp, qrcode, psycopg2
- PostgreSQL 15
- Docker / Docker Compose
- OpenFaaS
- HTML5, JS, Bootstrap 5
