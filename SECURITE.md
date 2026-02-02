# Corrections de Sécurité - Le Palais de la Beauté

## Résumé des changements

Ce document décrit les corrections de sécurité critiques apportées à l'application.

## 1. Externalisation de SECRET_KEY et DEBUG

### Problème
- La clé secrète Django était hardcodée dans le code source
- DEBUG=True était activé en permanence, exposant des informations sensibles

### Solution
- Ajout de python-decouple pour gérer les variables d'environnement
- SECRET_KEY et DEBUG sont maintenant configurables via fichier .env
- Valeurs par défaut sécurisées (DEBUG=False par défaut)

### Configuration requise

1. Créer un fichier `.env` à la racine du projet (copier `.env.example`) :

```bash
cp .env.example .env
```

2. Générer une nouvelle SECRET_KEY :

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

3. Modifier le fichier `.env` avec vos valeurs :

```env
SECRET_KEY=votre-nouvelle-cle-secrete-generee
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com
CSRF_TRUSTED_ORIGINS=https://votre-domaine.com
```

## 2. Sécurisation des cookies de session

### Problème
- Les cookies de session n'avaient pas les flags de sécurité appropriés
- Vulnérabilité aux attaques XSS et CSRF

### Solution
Ajout des flags de sécurité suivants dans [settings.py:134-147](le_palais_beaute/settings.py#L134-L147) :

- `SESSION_COOKIE_SECURE = not DEBUG` : HTTPS uniquement en production
- `SESSION_COOKIE_HTTPONLY = True` : Protection contre XSS
- `SESSION_COOKIE_SAMESITE = 'Lax'` : Protection CSRF
- `CSRF_COOKIE_SECURE = not DEBUG` : HTTPS uniquement
- `CSRF_COOKIE_HTTPONLY = True` : Protection XSS
- `SECURE_BROWSER_XSS_FILTER = True` : Filtre XSS navigateur
- `SECURE_CONTENT_TYPE_NOSNIFF = True` : Pas de sniffing MIME
- `X_FRAME_OPTIONS = 'DENY'` : Pas d'embedding iframe

## 3. Hashage des codes PIN

### Problème
- Les codes PIN des utilisateurs étaient stockés en texte clair dans la base de données
- Risque élevé en cas de compromission de la base

### Solution
- Ajout de méthodes `set_pin()` et `check_pin()` au modèle Utilisateur
- Utilisation de l'algorithme de hashage PBKDF2-SHA256 de Django
- Migration des PINs existants via commande management

### Migration des PINs existants

Après mise à jour du code, exécuter :

```bash
python manage.py hash_pins
```

Cette commande :
- Détecte les PINs en clair
- Les hash avec l'algorithme PBKDF2-SHA256
- Conserve les PINs déjà hashés

### Création de nouveaux utilisateurs

Utiliser la méthode `set_pin()` :

```python
utilisateur = Utilisateur(...)
utilisateur.set_pin('123456')  # Le PIN sera automatiquement hashé
utilisateur.save()
```

Le script [create_users.py](create_users.py) a été mis à jour pour utiliser cette méthode.

## 4. Validation backend des montants

### Problème
- Pas de validation côté serveur pour les montants négatifs
- Risque de données incohérentes dans la base

### Solution
Ajout de `MinValueValidator(0)` sur tous les champs de montants :

- Prestation.prix
- RendezVous : prix_base, prix_options, prix_total, prix_original
- RendezVousOption : quantite, prix_unitaire, prix_total
- VenteExpressPrestation : quantite, prix_unitaire, prix_total
- Paiement.montant
- Credit : montant_total, montant_paye, reste_a_payer
- PaiementCredit.montant
- ForfaitClient : nombre_seances_*, prix_total
- SeanceForfait.numero
- CarteCadeau : montant_initial, solde
- UtilisationCarteCadeau.montant
- ClotureCaisse : tous les montants

## Déploiement

### Étape 1 : Installation des dépendances

```bash
pip install -r requirements.txt
```

### Étape 2 : Configuration de l'environnement

```bash
cp .env.example .env
# Éditer .env avec vos valeurs de production
```

### Étape 3 : Migration des PINs

```bash
python manage.py hash_pins
```

### Étape 4 : Créer les migrations Django

```bash
python manage.py makemigrations
python manage.py migrate
```

### Étape 5 : Vérification

1. Vérifier que DEBUG=False en production
2. Tester la connexion avec PIN hashé
3. Vérifier les flags de cookies dans les DevTools du navigateur
4. Tester la validation des montants négatifs

## Sécurité en production

### Checklist avant mise en production

- [ ] SECRET_KEY unique générée et stockée dans .env
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configuré avec le domaine de production
- [ ] CSRF_TRUSTED_ORIGINS configuré avec les URLs HTTPS
- [ ] Tous les PINs hashés (exécuter hash_pins)
- [ ] HTTPS activé sur le serveur
- [ ] Fichier .env ajouté au .gitignore
- [ ] Backup de la base de données avant déploiement

### Configuration serveur web

Pour Nginx, ajouter les headers de sécurité :

```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

## Notes importantes

1. **Ne jamais commiter le fichier .env** : Il contient des secrets
2. **Sauvegarder SECRET_KEY** : Perte = impossibilité de décrypter les sessions
3. **PINs hashés irréversibles** : Impossible de retrouver le PIN original
4. **Tests avant production** : Tester tous les flux de connexion et paiement

## Support

En cas de problème :
1. Vérifier les logs Django
2. Vérifier la configuration .env
3. Vérifier que python-decouple est installé
4. Consulter ce document

---

**Date de mise à jour** : 2026-02-02
**Version** : 1.0
