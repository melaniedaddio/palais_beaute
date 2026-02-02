# Guide de déploiement - Le Palais de la Beauté

## Installation initiale

### 1. Cloner le projet

```bash
cd /chemin/vers/votre/dossier
```

### 2. Créer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# ou
venv\Scripts\activate  # Sur Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration de l'environnement

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Générer une nouvelle SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Éditer .env et coller la SECRET_KEY générée
nano .env  # ou vim, code, etc.
```

Exemple de configuration .env pour **développement** :

```env
SECRET_KEY=votre-cle-secrete-generee-ici
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
```

Exemple de configuration .env pour **production** :

```env
SECRET_KEY=votre-cle-secrete-generee-ici
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
CSRF_TRUSTED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com
```

### 5. Initialiser la base de données

```bash
# Créer les tables
python manage.py migrate

# Créer les instituts
python manage.py init_instituts

# Créer les utilisateurs
python manage.py create_users

# (Optionnel) Charger des données de test
python manage.py charger_catalogue_test
```

### 6. Hasher les codes PIN (IMPORTANT pour la sécurité)

```bash
python manage.py hash_pins
```

### 7. Lancer le serveur de développement

```bash
python manage.py runserver
```

Accédez à http://127.0.0.1:8000/

## Connexion

Utilisez l'un des comptes suivants :

| Utilisateur | PIN | Rôle | Accès |
|------------|-----|------|--------|
| patron | 123456 | Patron | Tous les instituts |
| manager_palais | 234567 | Manager | Le Palais uniquement |
| manager_klinic | 345678 | Manager | La Klinic uniquement |
| manager_express | 456789 | Manager | Express uniquement |

⚠️ **IMPORTANT** : Changez ces PINs en production !

## Déploiement en production

### Option 1 : Serveur avec Gunicorn + Nginx

1. **Installer Gunicorn**

```bash
pip install gunicorn
```

2. **Créer un fichier gunicorn_config.py**

```python
bind = "127.0.0.1:8000"
workers = 3
```

3. **Lancer Gunicorn**

```bash
gunicorn le_palais_beaute.wsgi:application -c gunicorn_config.py
```

4. **Configurer Nginx**

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /chemin/vers/staticfiles/;
    }
}
```

### Option 2 : Serveur avec mod_wsgi (Apache)

Créer un fichier `/etc/apache2/sites-available/palais-beaute.conf` :

```apache
<VirtualHost *:80>
    ServerName votre-domaine.com

    WSGIDaemonProcess palais python-path=/chemin/vers/projet python-home=/chemin/vers/venv
    WSGIProcessGroup palais
    WSGIScriptAlias / /chemin/vers/projet/le_palais_beaute/wsgi.py

    <Directory /chemin/vers/projet/le_palais_beaute>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    Alias /static /chemin/vers/staticfiles
    <Directory /chemin/vers/staticfiles>
        Require all granted
    </Directory>
</VirtualHost>
```

### Collecte des fichiers statiques

```bash
python manage.py collectstatic --noinput
```

## Commandes de gestion utiles

### Gestion des prestations

```bash
# Activer toutes les prestations
python manage.py activer_prestations

# Désactiver toutes les prestations
python manage.py activer_prestations --desactiver
```

### Gestion de la base de données

```bash
# Créer une sauvegarde
cp db.sqlite3 db.sqlite3.backup-$(date +%Y%m%d-%H%M%S)

# Restaurer une sauvegarde
cp db.sqlite3.backup-20260202-120000 db.sqlite3
```

### Gestion des utilisateurs

```bash
# Hasher les PINs en clair
python manage.py hash_pins

# Créer un superuser Django (pour l'admin)
python manage.py createsuperuser
```

## Maintenance

### Vérification de la sécurité

```bash
# Vérifier la configuration Django
python manage.py check --deploy
```

### Logs

Les logs sont affichés dans la console. Pour les rediriger vers un fichier :

```bash
gunicorn le_palais_beaute.wsgi:application >> logs/app.log 2>&1
```

## Sauvegarde

### Sauvegarde automatique quotidienne

Créer un script `backup.sh` :

```bash
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/chemin/vers/backups"
PROJECT_DIR="/chemin/vers/projet"

# Sauvegarder la base de données
cp $PROJECT_DIR/db.sqlite3 $BACKUP_DIR/db-$DATE.sqlite3

# Garder seulement les 30 dernières sauvegardes
cd $BACKUP_DIR
ls -t db-*.sqlite3 | tail -n +31 | xargs rm -f
```

Ajouter au crontab :

```bash
crontab -e
# Ajouter la ligne suivante pour une sauvegarde quotidienne à 2h du matin
0 2 * * * /chemin/vers/backup.sh
```

## Dépannage

### Problème : ModuleNotFoundError: No module named 'decouple'

**Solution** :
```bash
pip install python-decouple
```

### Problème : SECRET_KEY non définie

**Solution** :
1. Vérifier que le fichier .env existe
2. Vérifier qu'il contient SECRET_KEY=...
3. Redémarrer le serveur

### Problème : Connexion refusée avec le PIN

**Solution** :
1. Vérifier que les PINs ont été hashés : `python manage.py hash_pins`
2. Vérifier que l'utilisateur existe et est actif

### Problème : Erreur CSRF

**Solution** :
1. Vérifier CSRF_TRUSTED_ORIGINS dans .env
2. En développement, utiliser http:// (pas https://)
3. En production, utiliser https://

## Migration vers PostgreSQL (recommandé pour production)

1. **Installer PostgreSQL et psycopg2**

```bash
pip install psycopg2-binary
```

2. **Créer une base de données**

```bash
sudo -u postgres psql
CREATE DATABASE palais_beaute;
CREATE USER palais_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE palais_beaute TO palais_user;
\q
```

3. **Modifier .env**

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=palais_beaute
DB_USER=palais_user
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432
```

4. **Mettre à jour settings.py** (si pas déjà fait)

```python
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}
```

5. **Migrer les données**

```bash
python manage.py migrate
python manage.py loaddata backup.json  # Si vous avez exporté les données
```

## Support

Pour toute question ou problème :
1. Consulter [SECURITE.md](SECURITE.md) pour les questions de sécurité
2. Vérifier les logs d'erreur
3. Consulter la documentation Django : https://docs.djangoproject.com/

---

**Dernière mise à jour** : 2026-02-02
