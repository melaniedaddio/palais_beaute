# Historique des changements

## [1.0.0] - 2026-02-02

### 🔒 Sécurité (CRITIQUE)

#### Externalisation des secrets
- **SECRET_KEY externalisée** : Déplacement de la clé secrète Django vers variables d'environnement
  - Fichiers modifiés : [settings.py:14-24](le_palais_beaute/settings.py#L14-L24)
  - Ajout de python-decouple pour la gestion des variables d'environnement
  - Création de `.env.example` comme template
  - Valeur par défaut sécurisée (identique à l'ancienne uniquement en développement)

- **DEBUG configurable** : Mode DEBUG maintenant contrôlable via variable d'environnement
  - Par défaut : `DEBUG=False` (production-ready)
  - Configuration via `.env` pour le développement

#### Hashage des codes PIN
- **Stockage sécurisé des PINs** : Implémentation du hashage PBKDF2-SHA256
  - Fichiers modifiés : [core/models.py:5-6](core/models.py#L5-L6), [core/models.py:59-71](core/models.py#L59-L71)
  - Ajout des méthodes `set_pin()` et `check_pin()` au modèle Utilisateur
  - Migration de la logique de connexion pour utiliser `check_pin()` dans [core/views.py:23-30](core/views.py#L23-L30)
  - Script de migration `hash_pins.py` pour hasher les PINs existants
  - Mise à jour de `create_users.py` pour utiliser `set_pin()`

#### Sécurisation des cookies
- **Flags de sécurité pour cookies de session et CSRF**
  - Fichiers modifiés : [settings.py:134-145](le_palais_beaute/settings.py#L134-L145)
  - `SESSION_COOKIE_SECURE = not DEBUG` : HTTPS uniquement en production
  - `SESSION_COOKIE_HTTPONLY = True` : Protection contre XSS
  - `SESSION_COOKIE_SAMESITE = 'Lax'` : Protection CSRF
  - `CSRF_COOKIE_SECURE = not DEBUG` : HTTPS uniquement en production
  - `CSRF_COOKIE_HTTPONLY = True` : Protection contre XSS
  - `CSRF_COOKIE_SAMESITE = 'Lax'` : Protection CSRF

- **Headers de sécurité additionnels**
  - `SECURE_BROWSER_XSS_FILTER = True` : Filtre XSS du navigateur
  - `SECURE_CONTENT_TYPE_NOSNIFF = True` : Empêche le sniffing MIME
  - `X_FRAME_OPTIONS = 'DENY'` : Empêche l'embedding en iframe

#### Validation backend des montants
- **Validation MinValueValidator(0)** : Ajout de validateurs sur tous les champs de montants
  - Fichiers modifiés : [core/models.py:4](core/models.py#L4)
  - Modèles concernés :
    - `Prestation.prix`
    - `RendezVous` : prix_base, prix_options, prix_total, prix_original
    - `RendezVousOption` : quantite, prix_unitaire, prix_total
    - `VenteExpressPrestation` : quantite, prix_unitaire, prix_total
    - `Paiement.montant`
    - `Credit` : montant_total, montant_paye, reste_a_payer
    - `PaiementCredit.montant`
    - `ForfaitClient` : nombre_seances_*, prix_total
    - `SeanceForfait.numero`
    - `CarteCadeau` : montant_initial, solde
    - `UtilisationCarteCadeau.montant`
    - `ClotureCaisse` : tous les montants
  - Protection contre les montants négatifs au niveau de la base de données

### 📚 Documentation

#### Nouveaux fichiers de documentation
- **SECURITE.md** : Documentation complète des corrections de sécurité
  - Détails des problèmes et solutions
  - Guide de migration des PINs
  - Configuration de l'environnement
  - Checklist de production

- **DEPLOIEMENT.md** : Guide complet de déploiement
  - Installation initiale
  - Configuration développement vs production
  - Déploiement avec Gunicorn + Nginx
  - Déploiement avec Apache + mod_wsgi
  - Scripts de sauvegarde
  - Dépannage

- **README.md** : Documentation principale du projet
  - Vue d'ensemble des fonctionnalités
  - Installation rapide
  - Comptes par défaut
  - Structure du projet
  - Commandes utiles

- **CHANGELOG.md** : Ce fichier - Historique des changements

#### Fichiers de configuration
- **.env.example** : Template de configuration pour les variables d'environnement
  - SECRET_KEY (à générer)
  - DEBUG (True/False)
  - ALLOWED_HOSTS
  - CSRF_TRUSTED_ORIGINS
  - Configuration PostgreSQL (optionnelle)

- **.gitignore** : Protection des fichiers sensibles
  - Exclusion de `.env` et variantes
  - Base de données SQLite
  - Fichiers Python compilés
  - Environnements virtuels
  - Fichiers IDE
  - Logs et backups

### 🛠️ Commandes de gestion

#### Nouvelle commande : hash_pins
- **Objectif** : Hasher les codes PIN existants en clair
- **Usage** : `python manage.py hash_pins`
- **Fonctionnalités** :
  - Détecte automatiquement les PINs en clair
  - Hash avec PBKDF2-SHA256
  - Préserve les PINs déjà hashés
  - Affiche un résumé des opérations

### ✨ Améliorations UX (sessions précédentes)

#### Système de notifications
- Remplacement de 76 `alert()` par des notifications toast modernes
- Animations fluides et design cohérent
- Support des types : succès, erreur, avertissement, info

#### États de chargement
- Spinners au niveau des boutons (11 opérations catalogue, 7 opérations agenda)
- Loader pleine page pour opérations longues
- Fonction utilitaire `withLoader()` pour wrapping automatique

#### Validation de formulaires
- Validation côté client en temps réel
- 10 règles de validation (required, email, phone, numeric, pattern, etc.)
- Messages d'erreur contextuels
- Debouncing (300ms) pour éviter les validations excessives
- Intégration dans catalogue (famille, prestation) et agenda (RDV, forfait, validation)

### 🔧 Dépendances

#### Ajouts
- **python-decouple>=3.8** : Gestion des variables d'environnement

#### Existantes
- Django>=4.2
- openpyxl>=3.1.2
- Pillow>=10.0.0
- python-dateutil>=2.8.2

### ⚠️ Actions requises pour la mise à jour

#### Migration depuis version précédente

1. **Installer la nouvelle dépendance**
   ```bash
   pip install -r requirements.txt
   ```

2. **Créer le fichier .env**
   ```bash
   cp .env.example .env
   # Générer une nouvelle SECRET_KEY
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   # Coller la clé dans .env
   ```

3. **Hasher les PINs existants**
   ```bash
   python manage.py hash_pins
   ```

4. **Créer les nouvelles migrations Django**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Vérifier la configuration**
   - Tester la connexion avec un PIN hashé
   - Vérifier que DEBUG=False en production
   - Tester la validation des montants négatifs

#### Configuration production

1. **Variables d'environnement obligatoires**
   - SECRET_KEY : Générer une nouvelle clé unique
   - DEBUG=False
   - ALLOWED_HOSTS : Votre domaine de production
   - CSRF_TRUSTED_ORIGINS : URLs HTTPS de production

2. **Sécurité serveur**
   - Activer HTTPS
   - Configurer les headers de sécurité (Nginx/Apache)
   - Configurer les sauvegardes automatiques

### 📊 Statistiques

- **Fichiers modifiés** : 9
- **Fichiers créés** : 8
- **Lignes de code ajoutées** : ~600
- **Validateurs ajoutés** : 30+ champs
- **Corrections de sécurité critiques** : 4

### 🔗 Références

- Documentation Django : https://docs.djangoproject.com/
- OWASP Top 10 : https://owasp.org/www-project-top-ten/
- Django Security : https://docs.djangoproject.com/en/stable/topics/security/

---

## Légende

- 🔒 Sécurité
- ✨ Nouvelles fonctionnalités
- 🐛 Corrections de bugs
- 📚 Documentation
- 🛠️ Outils et commandes
- 🔧 Dépendances
- ⚠️ Actions requises
- 📊 Statistiques
