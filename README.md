# ygg-rss-proxy

# 🚨 Important Notice 🚨

**Currently, the site is under heavy cloudflare protection. It is recommended to use flaresolver in parallel to ensure smooth operation.**

Please be aware of this and make sure to use flaresolver accordingly to avoid any issues.

Big thanks to [@FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) for their amazing work!

## 🔧 Quick Setup

### 1. Create Environment File

**IMPORTANT:** Create a `.env` file from the template:

```bash
cp env.example .env
```

Then edit `.env` and update these **REQUIRED** variables:
```bash
YGG_USER=your_actual_ygg_username
YGG_PASS=your_actual_ygg_password
SECRET_KEY=your_generated_secure_key_here
```

### 2. Generate Secure Secret Key (REQUIRED!)

⚠️ **CRITICAL**: The application will NOT start without a secure SECRET_KEY!

Generate a secure secret key:

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

Copy the output and replace the `SECRET_KEY` value in your `.env` file.

**Security Requirements:**
- Must be at least 32 characters long
- Cannot use default/weak values  
- Protects your YGG authentication cookies and session data

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

## 🔒 Security Improvements

This application has undergone a comprehensive security audit and implementation of critical security enhancements:

### ✅ **Vulnerabilities Fixed**
- **Hardcoded Credentials Removal**: All sensitive credentials moved to environment variables with secure `.env` file setup
- **Mandatory SECRET_KEY Protection**: Application now requires and validates secure SECRET_KEY with startup enforcement
- **XXE Attack Prevention**: Secure XML parser implementation prevents XML External Entity attacks
- **Configuration Security**: Fixed hardcoded URLs and implemented proper configuration management
- **Complete Error Handling**: Fixed incomplete exception handling that could cause application crashes

### 🛡️ **Security Features**
- **Credential Protection**: YGG credentials and session data never exposed in logs or responses
- **Session Security**: Strong SECRET_KEY validation protects Flask sessions and authentication cookies
- **XML Security**: Parser configured to prevent external entity attacks, file disclosure, and SSRF
- **Robust Error Handling**: Comprehensive exception coverage with appropriate HTTP status codes
- **Secure Logging**: Loguru integration with automatic sensitive data redaction

### 🩺 **Health Monitoring**
New `/health` endpoint provides comprehensive connectivity testing:
```bash
curl http://localhost:8080/health
```

Returns JSON status for:
- **FlareSolverr connectivity** and version information
- **Internet connectivity** via external service
- **YGG site reachability** (expects Cloudflare protection)

**Example response:**
```json
{
  "status": "healthy",
  "flaresolverr": "✅ Connected (v3.3.16)",
  "internet": "✅ Connected",
  "ygg": "✅ Reachable (Cloudflare protected)",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Description

`ygg-rss-proxy` est une application Python sécurisée qui sert de proxy pour récupérer des flux RSS et des fichiers torrent depuis un site protégé nécessitant une authentification. Cette application est conteneurisée à l'aide de Docker et utilise Poetry pour la gestion des dépendances.

## Fonctionnalités

- **Authentification Sécurisée**: Authentifie sur le site et récupère les cookies de session avec protection des credentials.
- **Proxy RSS Intelligent**: Récupère et modifie les flux RSS pour remplacer les URL de téléchargement par des URL de proxy.
- **Téléchargement Torrent**: Récupère les fichiers torrent via le proxy avec authentification.
- **Protection XXE**: Parser XML sécurisé prévenant les attaques d'entités externes.
- **Monitoring de Santé**: Endpoint `/health` pour surveiller la connectivité FlareSolverr, Internet et YGG.
- **Gestion d'Erreurs Robuste**: Gestion complète des exceptions avec codes HTTP appropriés.
- **Logging Sécurisé**: Redaction automatique des données sensibles dans les journaux.

## Exigences

- Docker
- Docker Compose (pour la configuration Docker Compose)

## Configuration

Le scripte peut désormais être configuré en utilisant des variables d'environnement, un ficher `.env` ou les docker secrets. Pour les Docker secrets, il faut les nommer comme les variable d'environnement.

### Variables d'Environnement

#### ⚠️ OBLIGATOIRES
- `YGG_USER` : Votre nom d'utilisateur pour l'authentification sur le site YGG. **(OBLIGATOIRE)**
- `YGG_PASS` : Votre mot de passe pour l'authentification sur le site YGG. **(OBLIGATOIRE)**
- `SECRET_KEY` : Clé secrète pour la sécurité des sessions Flask. **(OBLIGATOIRE - minimum 32 caractères)**
  - ⚠️ **CRITIQUE**: L'application ne démarrera PAS sans cette clé
  - Protège vos cookies d'authentification YGG et données de session
  - Générez avec: `python -c "import secrets; print(secrets.token_hex(32))"`
  - Ne peut pas utiliser de valeurs par défaut/faibles

#### Optionnelles (avec valeurs par défaut)
- `YGG_URL`: L'URL du site YGG. définie par default.
- `RSS_HOST`: L'hôte sur lequel le serveur RSS est en cours d'exécution. Par défaut, il est défini sur 'localhost'. **C'est ici que l'on peut mettre le noms de container si l'on utilise docker compose.**
- `RSS_PORT`: Le port sur lequel le serveur RSS est en cours d'exécution. Par défaut, il est défini sur '8080'.
- `RSS_SHEMA`: Le schéma (http ou https) utilisé pour accéder au serveur RSS. Par défaut, il est défini sur 'http'.
- `FLARESOLVERR_SHEMA`: Le schéma (http ou https) utilisé pour accéder à l'instance de Flaresolverr. Par défaut, il est défini sur 'http'.
- `FLARESOLVERR_HOST`: L'hôte sur lequel l'instance de Flaresolverr est en cours d'exécution. Par défaut, il est défini sur 'localhost'.
- `FLARESOLVERR_PORT`: Le port sur lequel l'instance de Flaresolverr est en cours d'exécution. Par défaut, il est défini sur '8191'.
- `GUNICORN_PORT`: Le port sur lequel le serveur proxy interne est en cours d'exécution. Par défaut, il est défini sur '8080'.
- `GUNICORN_WORKERS`: Le nombre de travailleurs Gunicorn à utiliser. Par défaut, il est défini sur '4'.
- `GUNICORN_BINDER`: L'adresse IP sur laquelle le serveur proxy interne est lié. Par défaut, il est défini sur '0.0.0.0'.
- `GUNICORN_TIMEOUT`: Le délai d'attente pour les requêtes Gunicorn. Par défaut, il est défini sur '120'.
- `LOG_PATH`: Le chemin du fichier journal pour le serveur proxy. Par défaut, il est défini sur '/app/config/logs/rss-proxy.log'. Il y a une rotaion de fichier journal déja configuré. Attention c'est le chemin dans le container.
- `LOG_LEVEL`: Le niveau de journalisation pour le serveur proxy. Par défaut, il est défini sur 'INFO'.
- `LOG_REDACTED`: Si les journaux doivent être anonymisés. Par défaut, il est défini sur 'True'.
- `DB_PATH`: Le chemin de la base de données SQLite pour le serveur proxy. Par défaut, il est défini sur '/app/config/rss-proxy.db'. Attention c'est le chemin dans le container.

## Comment Utiliser

## 🚨 Important Notice 🚨

**Attention, l'installation nécessite FlareSolverr quand le site et sous protocole cloudflare. C'est a dire à peu près tout le temps.**

Please be aware of this and make sure to use FlareSolverr accordingly to avoid any issues.

For optimal performance and to bypass Cloudflare's protection, it is essential to run FlareSolverr alongside this application. This is because the site is frequently protected by Cloudflare, which can cause difficulties in accessing the content.

### Exemple avec Docker Compose + 🚨 FlareSolverr 🚨 + Qbittorrent

Cet exemple utilise Docker Compose pour lancer l'application `ygg-rss-proxy`, FlareSolverr, et Qbittorrent en même temps.
C'est pour illustré l'utilisation de l'application avec d'autres services.

**Attention, Flaresolverr est un super projet 🤩 mais il peut être très gourmand en ressources si des petits malins trouve votre instance et ne doit pas être exoposé en dehors de votre réseau local. Il est donc recommandé de ne pas binder le port 8191 sur l'hôte. On utilisera donc le nom du container pour communiquer entre les deux pour rester dans le réseau docker.**

1. **Créer un fichier `.env` avec vos identifiants**

   ```bash
   # Copier le fichier template
   cp env.example .env
   
   # Éditer le fichier .env et mettre vos vraies informations
   YGG_USER=your_real_username
   YGG_PASS=your_real_password
   ```

2. **Le fichier `docker-compose.yml` est déjà configuré**

   Le fichier utilise maintenant des variables d'environnement sécurisées:

   ```yaml
   version: "3.8"

   services:
      qbittorrent:
         image: lscr.io/linuxserver/qbittorrent:latest
         container_name: qbittorrent
         env_file:
            - .env
         environment:
            WEBUI_PORT: 8080
         volumes:
            - ./config:/config
            - ./downloads:/downloads
         ports:
            - 6881:6881
            - 6881:6881/udp
            - 8080:8080
         restart: unless-stopped

      ygg-rss-proxy:
         image: ghcr.io/limedrive/ygg-rss-proxy:latest
         container_name: ygg-rss-proxy
         expose:
            - 8080
         env_file:
            - .env
         environment:
            # Override specific values for containerized environment
            FLARESOLVERR_HOST: flaresolverr
            RSS_HOST: ygg-rss-proxy
         volumes:
            - ./config:/app/config
         restart: unless-stopped
         depends_on:
            - flaresolverr

      flaresolverr:
         image: ghcr.io/flaresolverr/flaresolverr:latest
         container_name: flaresolverr
         env_file:
            - .env
         environment:
            CAPTCHA_SOLVER: none
         expose:
            - 8191
         restart: unless-stopped
   ```

3. **Exécuter Docker Compose**

   ```bash
   docker-compose up -d
   ```

## Comment Utiliser le Proxy

L'URL RSS à utiliser est la même que sur le site concerné, mais vous devez changer le nom de domaine de `www.ygg.re` à `localhost:8080` ou tout autre HOST que vous avez définie dans les variable `RSS_HOST` `RSS_PORT`. Assurez-vous de bien conserver tous les paramètres car notre script les réutilise.

### Exemple d'URL RSS

URL d'origine : `https://www.ygg.re/rss?action=generate&type=subcat&id=2183&passkey=xxxxxxxxxxxxxxxxxxxxxxxxxxx`

URL à utiliser dans le client torrent : `http://localhost:8080/rss?action=generate&type=subcat&id=2183&passkey=xxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Surveillance et Monitoring

#### Endpoint de Santé
Utilisez l'endpoint `/health` pour vérifier le statut de l'application:

```bash
# Vérification rapide du statut
curl http://localhost:8080/health

# Avec formatage JSON (si jq est installé)
curl http://localhost:8080/health | jq
```

Cet endpoint vérifie:
- ✅ **Connectivité FlareSolverr**: Version et disponibilité
- ✅ **Connectivité Internet**: Accès aux services externes
- ✅ **Accessibilité YGG**: Vérification que le site est joignable

#### Codes de Statut HTTP
- **200**: Tout fonctionne correctement
- **500**: Erreur serveur interne
- **502**: Problème de connectivité (FlareSolverr/YGG)
- **504**: Timeout de connexion


## Structure du Projet

```
ygg-rss-proxy/
│
├── Dockerfile
├── pyproject.toml
├── poetry.lock
├── .github/
│   └── workflows/
│       └── release.yml
│
└── ygg_rss_proxy/
    ├── __init__.py
    ├── app.py
    ├── auth.py
    ├── logging_config.py
    ├── rss.py
    ├── run_gunicorn.py
    ├── session_manager.py.py
    └── settings.py
```

## Contribuer

N'hésitez pas à ouvrir des issues ou à soumettre des pull requests si vous trouvez des bugs ou avez des suggestions de fonctionnalités.