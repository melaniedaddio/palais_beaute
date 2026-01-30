# Tests Phase 4 - Module Agenda (Palais & Klinic)

## Prérequis

1. Serveur Django en cours d'exécution : `py manage.py runserver`
2. Données de test créées : `py test_agenda.py`
3. Se connecter avec le Patron (PIN: 123456)

## Tests à effectuer

### 1. Navigation vers l'agenda

- [ ] Depuis le Dashboard, cliquer sur "Agenda Le Palais"
- [ ] Vérifier la redirection vers `/agenda/palais/`
- [ ] Vérifier que la page s'affiche correctement

### 2. Affichage de la grille horaire

- [ ] La grille horaire affiche les créneaux de 7h à 23h (64 créneaux de 15 minutes)
- [ ] La colonne de gauche (heures) est fixe lors du scroll horizontal
- [ ] Les colonnes des employés s'affichent : Marthe, Brigitte, Jeanette
- [ ] Les 5 RDV de test s'affichent sur la grille aux bonnes heures
- [ ] Chaque RDV affiche :
  - Nom du client
  - Nom de la prestation
  - Prix total
  - Couleur de la famille de prestation (barre de gauche)

### 3. Navigation par date

- [ ] Le sélecteur de date affiche la date du jour
- [ ] Cliquer sur "Jour précédent" : la grille se recharge avec la date -1
- [ ] Cliquer sur "Jour suivant" : la grille se recharge avec la date +1
- [ ] Cliquer sur "Aujourd'hui" : retour à la date du jour
- [ ] Sélectionner manuellement une date : la grille se recharge

### 4. Statistiques du jour

- [ ] "RDV du jour" affiche 5
- [ ] "RDV validés" affiche 0 (tous en attente)
- [ ] "En attente" affiche 5
- [ ] "Chiffre d'affaires" affiche 0 CFA (aucun RDV validé)

### 5. Légende des couleurs

- [ ] La légende affiche toutes les familles de prestations avec leurs couleurs
- [ ] Les couleurs correspondent aux barres de gauche des RDV

### 6. Créer un nouveau RDV

#### 6.1 Ouvrir le modal de création

- [ ] Cliquer sur une cellule vide de la grille
- [ ] Le modal "Nouveau rendez-vous" s'ouvre
- [ ] La date est pré-remplie avec la date sélectionnée
- [ ] L'heure est pré-remplie avec l'heure du créneau cliqué

#### 6.2 Remplir le formulaire

- [ ] **Client** : Taper "Aminata" dans le champ de recherche
  - [ ] L'autocomplete affiche les clients correspondants
  - [ ] Cliquer sur "Aminata Koné - 0707070701"
  - [ ] Le client est sélectionné

- [ ] **Famille de prestation** : Sélectionner "Manucure"
  - [ ] Les prestations de la famille se chargent dans le select suivant

- [ ] **Prestation** : Sélectionner une prestation
  - [ ] Le prix de base se remplit automatiquement
  - [ ] La durée et le prix s'affichent sous le select
  - [ ] Le prix total se met à jour

- [ ] **Options** : Cocher "Strass" et "Dessins"
  - [ ] Le prix total augmente avec le prix des options

- [ ] **Prix de base** : Modifier manuellement le prix si nécessaire
  - [ ] Le prix total se recalcule

- [ ] **Remarques** : Ajouter un commentaire (optionnel)

#### 6.3 Enregistrer le RDV

- [ ] Cliquer sur "Enregistrer"
- [ ] Message de confirmation affiché
- [ ] La page se recharge
- [ ] Le nouveau RDV apparaît sur la grille

### 7. Modifier un RDV existant

#### 7.1 Ouvrir le modal de modification

- [ ] Cliquer sur un RDV en attente (par exemple, celui de Fatou Diallo)
- [ ] Une popup demande "Que voulez-vous faire ? OK = Modifier / Annuler = Valider"
- [ ] Cliquer sur "OK" pour modifier

#### 7.2 Modal de modification

- [ ] Le modal s'ouvre avec le titre "Modifier le rendez-vous"
- [ ] Tous les champs sont pré-remplis avec les données du RDV
- [ ] Les options cochées sont correctes
- [ ] Trois boutons sont visibles :
  - [ ] "Supprimer" (rouge, à gauche)
  - [ ] "Valider" (vert)
  - [ ] "Enregistrer" (bleu)

#### 7.3 Modifier les données

- [ ] Changer l'heure du RDV
- [ ] Changer la prestation
- [ ] Ajouter/retirer des options
- [ ] Modifier les remarques

#### 7.4 Enregistrer les modifications

- [ ] Cliquer sur "Enregistrer"
- [ ] Message de confirmation
- [ ] La page se recharge
- [ ] Les modifications sont visibles sur la grille

### 8. Valider un RDV

#### 8.1 Ouvrir le modal de validation

- [ ] Cliquer sur un RDV en attente
- [ ] Cliquer sur "Annuler" dans la popup (ou cliquer sur "Valider" dans le modal de modification)
- [ ] Le modal "Valider le rendez-vous" s'ouvre

#### 8.2 Informations du RDV

- [ ] Le récapitulatif affiche :
  - [ ] Client
  - [ ] Prestation
  - [ ] Date et heure
  - [ ] Prix total (en gros, doré)

#### 8.3 Paiement complet

- [ ] "Type de paiement" = "Paiement complet"
- [ ] Le champ "Montant payé" n'est pas visible
- [ ] "Moyen de paiement" = "Espèces" ou "Carte bancaire"
- [ ] Cliquer sur "Valider le RDV"
- [ ] Message de confirmation
- [ ] La page se recharge
- [ ] Le RDV apparaît avec une opacité plus forte (validé)
- [ ] Les stats se mettent à jour :
  - [ ] "RDV validés" = 1
  - [ ] "En attente" = 4
  - [ ] "Chiffre d'affaires" = prix du RDV validé

#### 8.4 Paiement partiel

- [ ] Ouvrir un autre RDV et cliquer sur "Valider"
- [ ] "Type de paiement" = "Paiement partiel"
- [ ] Le champ "Montant payé" apparaît
- [ ] Entrer un montant inférieur au total (ex: 5000 sur 10000)
- [ ] Le reste à payer s'affiche en doré
- [ ] Valider le RDV
- [ ] Message de confirmation
- [ ] Un crédit est créé pour le reste

#### 8.5 Paiement différé

- [ ] Ouvrir un autre RDV et cliquer sur "Valider"
- [ ] "Type de paiement" = "Paiement différé"
- [ ] Le champ "Montant payé" apparaît avec 0
- [ ] Valider le RDV
- [ ] Un crédit est créé pour le montant total

### 9. Supprimer un RDV

- [ ] Ouvrir un RDV en attente en mode modification
- [ ] Cliquer sur "Supprimer"
- [ ] Popup de confirmation : "Voulez-vous vraiment supprimer ce rendez-vous ?"
- [ ] Confirmer
- [ ] Message de confirmation
- [ ] La page se recharge
- [ ] Le RDV n'est plus visible sur la grille

### 10. Afficher un RDV validé

- [ ] Cliquer sur un RDV validé (avec opacité forte)
- [ ] Une alerte affiche les détails en lecture seule
- [ ] Pas de possibilité de modifier ou supprimer (sauf pour le patron)

### 11. Test Manager Palais

- [ ] Se déconnecter
- [ ] Se connecter avec Manager Palais (PIN: 234567)
- [ ] Vérifier la redirection automatique vers `/agenda/palais/`
- [ ] Le manager a accès à toutes les fonctionnalités
- [ ] Le manager ne peut pas :
  - [ ] Modifier un RDV validé
  - [ ] Supprimer un RDV validé
  - [ ] Accéder au Dashboard
  - [ ] Accéder aux autres agendas (Klinic)

### 12. Test Manager Klinic

- [ ] Se déconnecter
- [ ] Se connecter avec Manager Klinic (PIN: 345678)
- [ ] Vérifier la redirection automatique vers `/agenda/klinic/`
- [ ] Le manager ne peut pas accéder à `/agenda/palais/`
- [ ] Message d'erreur et redirection vers login

### 13. Vérifications de sécurité

- [ ] Essayer d'accéder à `/agenda/palais/` sans être connecté
  - [ ] Redirection vers `/` (login)

- [ ] En tant que Manager Palais, essayer d'accéder à `/agenda/klinic/`
  - [ ] Message d'erreur
  - [ ] Redirection vers login

### 14. Tests de performance

- [ ] La grille horaire se charge rapidement (< 1 seconde)
- [ ] L'autocomplete client répond rapidement
- [ ] Le chargement des prestations par famille est instantané
- [ ] Aucun délai lors du clic sur les cellules

### 15. Tests d'ergonomie

- [ ] Le scroll horizontal de la grille est fluide
- [ ] Les RDV sont facilement cliquables
- [ ] Les modals sont centrés et lisibles
- [ ] Les formulaires sont clairs et bien organisés
- [ ] Les messages de confirmation/erreur sont visibles

## Bugs connus à tester

### Bug potentiel : Chevauchement de RDV

- [ ] Créer 2 RDV pour le même employé à des heures qui se chevauchent
- [ ] Vérifier si le système l'autorise (devrait le permettre pour l'instant)
- [ ] Vérifier l'affichage sur la grille (les RDV doivent se superposer)

### Bug potentiel : RDV en dehors des heures

- [ ] Créer un RDV à 6h30 (avant 7h)
- [ ] Vérifier si le RDV s'affiche ou s'il est masqué

### Bug potentiel : Calcul du prix

- [ ] Créer un RDV avec plusieurs options
- [ ] Vérifier que le prix total = prix_base + somme des prix des options
- [ ] Modifier manuellement le prix de base
- [ ] Vérifier que le prix total se recalcule

## Checklist finale

- [ ] Tous les tests ci-dessus sont passés
- [ ] Aucune erreur JavaScript dans la console du navigateur
- [ ] Aucune erreur Django dans le terminal
- [ ] La navigation entre les pages fonctionne
- [ ] Les messages de succès/erreur s'affichent correctement
- [ ] Le design est cohérent avec la charte graphique

## Prochaine étape

**Phase 5 : Module Express**
- Formulaire de vente express sans agenda
- Sélection client + employé + prestations multiples
- Gestion des paiements (complet, partiel, différé)
- Liste des ventes du jour
- Total du jour (espèces + carte)
