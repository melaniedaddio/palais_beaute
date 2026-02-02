# Le Palais de la Beauté - Système de Gestion

Application web de gestion pour les instituts de beauté Le Palais, La Klinic et Express.

## Fonctionnalités principales

### Gestion multi-instituts
- **Le Palais** : Institut principal avec agenda complet
- **La Klinic** : Institut avec forfaits multi-séances
- **Express** : Point de vente rapide sans agenda

### Modules
- **Agenda** : Gestion des rendez-vous avec drag & drop
- **Catalogue** : Familles de prestations, prestations normales/options/forfaits
- **Clients** : Fiche client avec historique complet
- **Paiements** : Support multi-modes (Espèces, Carte, OM, Wave, Cartes cadeaux)
- **Crédits** : Suivi des paiements partiels
- **Forfaits** : Gestion des forfaits multi-séances (La Klinic)
- **Cartes cadeaux** : Vente et utilisation de cartes cadeaux
- **Clôture de caisse** : Bilan journalier par institut
- **Dashboard** : Vue d'ensemble pour le patron

### Fonctionnalités UX
- ✅ Système de notifications toast
- ✅ Indicateurs de chargement (spinners)
- ✅ Validation de formulaires en temps réel
- ✅ Interface drag & drop pour réorganiser
- ✅ Design responsive et moderne

## Installation rapide

```bash
# Cloner et se placer dans le répertoire
cd palais_beaute

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Éditer .env et configurer SECRET_KEY

# Initialiser la base de données
python manage.py migrate
python manage.py init_instituts
python manage.py create_users

# Hasher les PINs (sécurité)
python manage.py hash_pins

# Lancer le serveur
python manage.py runserver
```

Accédez à http://127.0.0.1:8000/

## Comptes par défaut

| Utilisateur | PIN | Rôle | Accès |
|------------|-----|------|--------|
| patron | 123456 | Patron | Tous les instituts |
| manager_palais | 234567 | Manager | Le Palais uniquement |
| manager_klinic | 345678 | Manager | La Klinic uniquement |
| manager_express | 456789 | Manager | Express uniquement |

⚠️ **Changez ces PINs en production !**

## Documentation

- [SECURITE.md](SECURITE.md) - Corrections de sécurité et meilleures pratiques
- [DEPLOIEMENT.md](DEPLOIEMENT.md) - Guide de déploiement complet

## Sécurité

Ce projet implémente les mesures de sécurité suivantes :

✅ Externalisation de SECRET_KEY et DEBUG vers variables d'environnement
✅ Hashage PBKDF2-SHA256 des codes PIN
✅ Validation backend des montants (>= 0)
✅ Flags de sécurité pour cookies (SECURE, HTTPONLY, SAMESITE)
✅ Protection XSS, CSRF et clickjacking
✅ Protection des fichiers sensibles (.gitignore)

## Technologies

- **Backend** : Django 6.0+
- **Base de données** : SQLite (développement) / PostgreSQL (recommandé pour production)
- **Frontend** : HTML, CSS, JavaScript vanilla
- **Librairies** :
  - python-decouple : Variables d'environnement
  - openpyxl : Export Excel
  - Pillow : Gestion d'images
  - python-dateutil : Manipulation de dates

## Structure du projet

```
palais_beaute/
├── core/               # Modèles principaux, clients, employés
├── agenda/             # Gestion des rendez-vous
├── express/            # Module Express (vente rapide)
├── credits/            # Gestion des crédits clients
├── dashboard/          # Vue d'ensemble pour le patron
├── gestion/            # Catalogue et configuration
├── templates/          # Templates HTML
├── static/             # CSS, JS, images
├── le_palais_beaute/   # Configuration Django
├── .env.example        # Template de configuration
├── requirements.txt    # Dépendances Python
└── manage.py          # CLI Django
```

## Commandes utiles

```bash
# Activer/désactiver toutes les prestations
python manage.py activer_prestations
python manage.py activer_prestations --desactiver

# Hasher les PINs en clair
python manage.py hash_pins

# Charger un catalogue de test
python manage.py charger_catalogue_test

# Créer un backup de la base de données
cp db.sqlite3 db.sqlite3.backup-$(date +%Y%m%d-%H%M%S)
```

## Développement

### Variables d'environnement (.env)

```env
SECRET_KEY=votre-cle-secrete-generee
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
```

### Générer une nouvelle SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Production

Consultez [DEPLOIEMENT.md](DEPLOIEMENT.md) pour le guide complet de déploiement.

Points clés :
- DEBUG=False
- SECRET_KEY unique et sécurisée
- HTTPS obligatoire
- PostgreSQL recommandé
- Sauvegardes automatiques

## Support

Pour toute question :
1. Consulter la documentation ([SECURITE.md](SECURITE.md), [DEPLOIEMENT.md](DEPLOIEMENT.md))
2. Vérifier les logs Django
3. Consulter la documentation Django : https://docs.djangoproject.com/

## Licence

Usage interne - Le Palais de la Beauté

---

**Version** : 1.0
**Dernière mise à jour** : 2026-02-02
