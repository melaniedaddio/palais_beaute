# Tests Phase 3 - Template de base et navigation

## Comment tester

### 1. Démarrer le serveur
```bash
py manage.py runserver
```

### 2. Ouvrir le navigateur
Aller sur `http://localhost:8000/`

### 3. Se connecter

#### Connexion Patron
- Sélectionner : **Patron (Patron)**
- PIN : **123456**
- Redirection attendue : Dashboard avec navigation complète

#### Connexion Manager Palais
- Sélectionner : **Manager Palais (Le Palais)**
- PIN : **234567**
- Redirection attendue : Agenda Le Palais

#### Connexion Manager Klinic
- Sélectionner : **Manager Klinic (La Klinic)**
- PIN : **345678**
- Redirection attendue : Agenda La Klinic

#### Connexion Manager Express
- Sélectionner : **Manager Express (Express)**
- PIN : **456789**
- Redirection attendue : Caisse Express

## Ce qui doit fonctionner

### ✅ Page de connexion
- [x] Design élégant avec logo
- [x] Liste déroulante des utilisateurs
- [x] 6 cases pour le PIN
- [x] Navigation automatique entre les cases
- [x] Message d'erreur si PIN incorrect

### ✅ Template de base
- [x] Sidebar avec logo
- [x] Titre et sous-titre (nom de l'institut ou "Vue globale")
- [x] Navigation adaptée au rôle (patron vs manager)
- [x] Informations utilisateur en bas
- [x] Bouton de déconnexion
- [x] Zone de contenu principale
- [x] Affichage des messages (success, error, warning, info)

### ✅ Navigation Patron
- [x] Accès au Dashboard
- [x] Accès aux 3 agendas (Palais, Klinic, Express)
- [x] Accès aux Clients

### ✅ Navigation Manager
- [x] Accès à son agenda uniquement (ou caisse pour Express)
- [x] Accès aux Clients
- [x] PAS d'accès aux autres instituts

### ✅ Sécurité
- [x] Redirection vers login si non authentifié
- [x] Vérification des rôles (@role_required)
- [x] Vérification des instituts (@institut_required)
- [x] Session expire après 1 heure

### ✅ Design
- [x] Couleurs de la charte graphique (rose poudré, doré)
- [x] Cards avec ombres légères
- [x] Boutons avec effets hover
- [x] Responsive pour tablettes

## Pages actuelles (temporaires)

### Dashboard Patron
- URL : `/dashboard/`
- Accès : Patron uniquement
- Contenu : Page d'information sur Phase 8

### Agenda Le Palais
- URL : `/agenda/palais/`
- Accès : Patron + Manager Palais
- Contenu : Page d'information sur Phase 4

### Agenda La Klinic
- URL : `/agenda/klinic/`
- Accès : Patron + Manager Klinic
- Contenu : Page d'information sur Phase 4

### Express (Caisse)
- URL : `/express/`
- Accès : Patron + Manager Express
- Contenu : Page d'information sur Phase 5

### Clients
- URL : `/clients/`
- Accès : Tous les utilisateurs authentifiés
- Contenu : À implémenter dans Phase 9

## Tests de sécurité

### Test 1 : Manager ne peut pas accéder à un autre institut
1. Se connecter en tant que Manager Palais
2. Essayer d'accéder à `/agenda/klinic/`
3. Résultat attendu : Message d'erreur + redirection vers login

### Test 2 : Manager ne peut pas accéder au Dashboard
1. Se connecter en tant que Manager (n'importe lequel)
2. Essayer d'accéder à `/dashboard/`
3. Résultat attendu : Message d'erreur + redirection vers login

### Test 3 : Session expire
1. Se connecter
2. Attendre 1 heure (ou modifier SESSION_COOKIE_AGE pour tester)
3. Essayer d'accéder à une page
4. Résultat attendu : Redirection vers login

## Checklist complète

- [x] ✅ Page de connexion fonctionnelle
- [x] ✅ Template de base créé avec sidebar
- [x] ✅ Navigation adaptée au rôle
- [x] ✅ CSS principal créé
- [x] ✅ JavaScript principal créé
- [x] ✅ Pages temporaires pour Dashboard, Agenda, Express
- [x] ✅ Sécurité (décorateurs) fonctionnelle
- [x] ✅ Messages d'information affichés
- [x] ✅ Déconnexion fonctionnelle
- [x] ✅ Design responsive
- [x] ✅ Aucune erreur Django (check passed)

## Prochaine étape

**Phase 4 : Module Agenda (Palais & Klinic)**
- Implémenter la grille horaire
- Créer/Modifier/Supprimer des RDV
- Modal de validation avec paiements
- Gestion des options
