# PRD COMPLÉMENTAIRE - RÉSERVATION MULTI-PRESTATIONS
## Le Palais de la Beauté

---

# 📋 SOMMAIRE

1. [Vue d'ensemble](#1-vue-densemble)
2. [Changements d'interface](#2-changements-dinterface)
3. [Modèles de données](#3-modèles-de-données)
4. [Nouveau modal de réservation](#4-nouveau-modal-de-réservation)
5. [Création des RDV groupés](#5-création-des-rdv-groupés)
6. [Affichage dans l'agenda](#6-affichage-dans-lagenda)
7. [Modification d'un RDV existant](#7-modification-dun-rdv-existant)
8. [Intégration avec la validation existante](#8-intégration-avec-la-validation-existante)
9. [Intégration avec les paiements et crédits](#9-intégration-avec-les-paiements-et-crédits)
10. [URLs à ajouter/modifier](#10-urls-à-ajoutermodifier)
11. [Templates à modifier](#11-templates-à-modifier)
12. [Checklist d'implémentation](#12-checklist-dimplémentation)

---

# 1. VUE D'ENSEMBLE

## 1.1 Description

Refonte du système de prise de rendez-vous pour permettre la création de plusieurs prestations en une seule opération, avec possibilité d'assigner des employés différents pour chaque prestation. Les RDV créés ensemble sont liés par un groupe.

## 1.2 Objectifs

- Permettre de créer plusieurs RDV en une seule fois
- Chaque prestation peut avoir un employé différent
- Les RDV sont automatiquement placés dans les bonnes colonnes de l'agenda
- Garder la compatibilité avec le système de validation groupée existant
- Permettre d'ajouter une prestation à un RDV existant

## 1.3 Règles métier

| Règle | Valeur |
|-------|--------|
| Nombre de prestations par réservation | Illimité |
| Employé par prestation | Un employé différent possible pour chaque |
| Date | Même jour pour toutes les prestations d'un groupe |
| Heure | Libre pour chaque prestation (enchaînées ou espacées) |
| Calcul automatique des heures | Oui si même employé (option) |
| Paiement | Groupé (système existant) |
| Crédit | Sur le groupe (système existant) |
| Forfaits | Compatible |
| Cartes cadeaux | Compatible |

## 1.4 Flux global

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  AVANT (actuel)                      APRÈS (nouveau)                        │
│  ───────────────                     ──────────────────                     │
│                                                                             │
│  Clic case vide                      Clic bouton "Prendre un RDV"           │
│       ↓                                    ↓                                │
│  Modal 1 prestation                  Modal multi-prestations                │
│       ↓                                    ↓                                │
│  1 RDV créé                          N RDV créés (liés par groupe)          │
│       ↓                                    ↓                                │
│  Répéter si plusieurs               Tous créés en une fois                  │
│                                                                             │
│                                                                             │
│  Clic case vide (toujours possible)                                         │
│       ↓                                                                     │
│  Ouvre le NOUVEAU modal avec employé + heure pré-remplis                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. CHANGEMENTS D'INTERFACE

## 2.1 Nouveaux éléments dans l'agenda

### Bouton "Prendre un RDV"

Ajouter un bouton en haut de l'agenda, à côté des autres boutons :

```html
<!-- Avant : navigation date + boutons existants -->
<!-- Après : ajouter ce bouton -->
<button onclick="ouvrirModalReservation()" class="btn btn-primary" 
        style="padding: 8px 15px; background-color: #c9a86a;">
    📅 Prendre un RDV
</button>
```

Position dans l'interface :

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Agenda Le Palais                                                           │
│                                                                             │
│  [← Jour précédent] [15/01/2025] [Jour suivant →] [Aujourd'hui]            │
│                                                                             │
│  [📅 Prendre un RDV]  [Vendre un forfait]  [Clôture caisse]                │
│                        (si Klinic)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Clic sur case vide

Le clic sur une case vide ouvre le **nouveau modal** avec :
- L'employé pré-sélectionné (celui de la colonne cliquée)
- L'heure pré-remplie (celle de la ligne cliquée)
- Le client à sélectionner

```javascript
// Modification de la fonction existante
function nouvelRdv(employeId, heure) {
    ouvrirModalReservation(employeId, heure);
}
```

---

# 3. MODÈLES DE DONNÉES

## 3.1 Nouveau modèle `GroupeRDV`

Ce modèle lie les RDV créés ensemble.

```python
# core/models.py - Ajouter ce nouveau modèle

class GroupeRDV(models.Model):
    """
    Groupe de rendez-vous créés ensemble.
    Permet de lier plusieurs RDV d'un même client créés en une seule réservation.
    """
    # Client (tous les RDV du groupe sont pour le même client)
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='groupes_rdv'
    )
    
    # Institut
    institut = models.ForeignKey(
        'Institut',
        on_delete=models.CASCADE,
        related_name='groupes_rdv'
    )
    
    # Date (tous les RDV du groupe sont le même jour)
    date = models.DateField()
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='groupes_rdv_crees'
    )
    
    # Nombre de RDV dans le groupe (dénormalisé pour performance)
    nombre_rdv = models.IntegerField(default=1)
    
    # Prix total du groupe (dénormalisé pour affichage rapide)
    prix_total = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Groupe de RDV"
        verbose_name_plural = "Groupes de RDV"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Groupe #{self.id} - {self.client} - {self.date} ({self.nombre_rdv} RDV)"
    
    def recalculer_totaux(self):
        """Recalcule le nombre de RDV et le prix total"""
        rdvs = self.rendez_vous.exclude(statut__in=['annule', 'annule_client'])
        self.nombre_rdv = rdvs.count()
        self.prix_total = sum(rdv.prix_total for rdv in rdvs)
        self.save()
    
    def get_rdvs_actifs(self):
        """Retourne les RDV non annulés du groupe"""
        return self.rendez_vous.exclude(
            statut__in=['annule', 'annule_client']
        ).order_by('heure_debut')
    
    def tous_valides(self):
        """Vérifie si tous les RDV du groupe sont validés"""
        return not self.get_rdvs_actifs().exclude(statut='valide').exists()
    
    def peut_etre_supprime(self):
        """Un groupe peut être supprimé si aucun RDV n'est validé"""
        return not self.rendez_vous.filter(statut='valide').exists()
```

## 3.2 Modification du modèle `RendezVous`

Ajouter le lien vers le groupe :

```python
# core/models.py - Modifier le modèle RendezVous existant

class RendezVous(models.Model):
    # ... champs existants ...
    
    # NOUVEAU : Lien vers le groupe de RDV
    groupe = models.ForeignKey(
        'GroupeRDV',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rendez_vous',
        help_text="Groupe auquel appartient ce RDV (si créé avec d'autres)"
    )
    
    # ... reste du modèle ...
    
    def fait_partie_groupe(self):
        """Vérifie si ce RDV fait partie d'un groupe avec d'autres RDV"""
        if not self.groupe:
            return False
        return self.groupe.nombre_rdv > 1
    
    def get_autres_rdv_groupe(self):
        """Retourne les autres RDV du même groupe"""
        if not self.groupe:
            return RendezVous.objects.none()
        return self.groupe.rendez_vous.exclude(id=self.id).exclude(
            statut__in=['annule', 'annule_client']
        )
```

## 3.3 Migrations

```bash
python manage.py makemigrations core
python manage.py migrate
```

---

# 4. NOUVEAU MODAL DE RÉSERVATION

## 4.1 Fonctionnalités reprises de l'existant

Le nouveau modal reprend **TOUTES les fonctionnalités** du modal actuel :

| Fonctionnalité | Comportement |
|----------------|--------------|
| **Recherche client** | Autocomplete comme actuellement |
| **Création client** | Bouton [+ Client] → ouvre le modal de création existant |
| **Forfaits client** | Si Klinic + client sélectionné → affiche forfaits actifs |
| **Achat forfait** | Si prestation forfait + client n'a pas ce forfait → bouton "Vendre forfait" |
| **Options** | Sélectionnables pour chaque prestation avec quantité |
| **Modification prix** | Prix de base modifiable pour chaque prestation |

## 4.2 Maquette complète

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📅 Nouvelle réservation                                              [X]   │
│─────────────────────────────────────────────────────────────────────────────│
│                                                                             │
│  ┌─────────────────────────────────────────┐  ┌────────────────────────┐    │
│  │ CLIENT *                                │  │ DATE *                 │    │
│  │ ┌─────────────────────────────────┐     │  │ ┌──────────────────┐   │    │
│  │ │ 🔍 Rechercher...           [+]  │     │  │ │ 15/01/2025       │   │    │
│  │ └─────────────────────────────────┘     │  │ └──────────────────┘   │    │
│  │ <div id="client-results"></div>         │  │                        │    │
│  └─────────────────────────────────────────┘  └────────────────────────┘    │
│                                                                             │
│  <!-- Section forfaits si Klinic et client a des forfaits -->               │
│  <div id="forfaits-client-section" style="display:none;">                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 📦 FORFAITS ACTIFS                                                  │    │
│  │ Ce client a des forfaits avec séances disponibles                   │    │
│  │ ┌─────────────────────────────────────────────────────────────┐     │    │
│  │ │ LPG 10 séances - 7 restantes  [Utiliser une séance]         │     │    │
│  │ └─────────────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  </div>                                                                     │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  📋 PRESTATIONS                                                             │
│                                                                             │
│  <div id="liste-prestations">                                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PRESTATION 1                                                   [🗑️] │    │
│  │                                                                     │    │
│  │ ┌─────────────────┐ ┌─────────────────┐ ┌───────────────────────┐   │    │
│  │ │ Employé *       │ │ Heure *         │ │ Durée                 │   │    │
│  │ │ [Maria      ▼]  │ │ [09:00]         │ │ 1h (auto)             │   │    │
│  │ └─────────────────┘ └─────────────────┘ └───────────────────────┘   │    │
│  │                                                                     │    │
│  │ ┌───────────────────────────┐ ┌─────────────────────────────────┐   │    │
│  │ │ Famille *                 │ │ Prestation *                    │   │    │
│  │ │ [Ongle               ▼]  │ │ [Manucure + pose vernis    ▼]  │   │    │
│  │ └───────────────────────────┘ └─────────────────────────────────┘   │    │
│  │                                                                     │    │
│  │ Options :                                                           │    │
│  │ ┌─────────────────────────────────────────────────────────────┐     │    │
│  │ │ [−] Strass (1 000 CFA) [0] [+]                               │     │    │
│  │ │ [−] Dessin (1 000 CFA) [0] [+]                               │     │    │
│  │ └─────────────────────────────────────────────────────────────┘     │    │
│  │                                                                     │    │
│  │ Prix : 8 000 CFA + 0 CFA options = 8 000 CFA                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PRESTATION 2                                                   [🗑️] │    │
│  │                                                                     │    │
│  │ ┌─────────────────┐ ┌─────────────────┐ ┌───────────────────────┐   │    │
│  │ │ Employé *       │ │ Heure *         │ │ Durée                 │   │    │
│  │ │ [Sophie     ▼]  │ │ [10:00]         │ │ 2h (auto)             │   │    │
│  │ └─────────────────┘ └─────────────────┘ └───────────────────────┘   │    │
│  │                                                                     │    │
│  │ ┌───────────────────────────┐ ┌─────────────────────────────────┐   │    │
│  │ │ Famille *                 │ │ Prestation *                    │   │    │
│  │ │ [Gel                 ▼]  │ │ [Pose gel mains couleur    ▼]  │   │    │
│  │ └───────────────────────────┘ └─────────────────────────────────┘   │    │
│  │                                                                     │    │
│  │ Prix : 45 000 CFA + 0 CFA options = 45 000 CFA                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  </div>                                                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    [+ Ajouter une prestation]                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  📊 RÉCAPITULATIF                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  • Manucure + pose vernis                                          │    │
│  │    Maria • 09:00 - 10:00                           8 000 CFA       │    │
│  │                                                                     │    │
│  │  • Pose gel des mains couleur                                      │    │
│  │    Sophie • 10:00 - 12:00                         45 000 CFA       │    │
│  │                                                                     │    │
│  │  ───────────────────────────────────────────────────────────────   │    │
│  │  TOTAL (2 prestations)                            53 000 CFA       │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌───────────────────────┐  ┌───────────────────────────────────────────┐   │
│  │       Annuler         │  │         ✅ Créer les rendez-vous         │   │
│  └───────────────────────┘  └───────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4.3 Calcul automatique des heures

Quand l'utilisateur ajoute une prestation avec le **même employé** que la précédente :
- L'heure de début est automatiquement = heure de fin de la prestation précédente
- L'utilisateur peut modifier manuellement s'il le souhaite

```javascript
function ajouterPrestation() {
    const prestations = document.querySelectorAll('.prestation-block');
    const dernierePrestation = prestations[prestations.length - 1];
    
    // Récupérer l'employé et l'heure de fin de la dernière prestation
    const dernierEmployeId = dernierePrestation.querySelector('.select-employe').value;
    const derniereHeureFin = dernierePrestation.dataset.heureFin;
    
    // Créer le nouveau bloc avec employé et heure pré-remplis
    const nouveauBloc = creerBlocPrestation({
        employeId: dernierEmployeId,
        heureDebut: derniereHeureFin
    });
    
    document.getElementById('liste-prestations').appendChild(nouveauBloc);
}
```

## 4.4 Création de client (comme actuellement)

Le bouton [+ Client] à côté de la recherche ouvre le **modal existant** `modal-nouveau-client`.

```javascript
function ouvrirModalNouveauClientDepuisReservation() {
    // Réinitialiser le formulaire
    document.getElementById('nouveau-client-prenom').value = '';
    document.getElementById('nouveau-client-nom').value = '';
    document.getElementById('nouveau-client-telephone').value = '';
    document.getElementById('nouveau-client-email').value = '';
    document.getElementById('nouveau-client-error').style.display = 'none';
    
    // Ouvrir le modal existant
    document.getElementById('modal-nouveau-client').style.display = 'flex';
    document.getElementById('nouveau-client-prenom').focus();
}

// Après création réussie du client, le sélectionner dans le modal de réservation
function onClientCree(clientId, clientNom) {
    // Fermer le modal de création
    document.getElementById('modal-nouveau-client').style.display = 'none';
    
    // Sélectionner le client dans le modal de réservation
    document.getElementById('reservation-client-id').value = clientId;
    document.getElementById('reservation-client-search').value = clientNom;
    
    // Charger les forfaits du client (si Klinic)
    if (institutCode === 'klinic') {
        chargerForfaitsClient(clientId);
    }
}
```

## 4.5 Gestion des forfaits (comme actuellement)

### Affichage des forfaits actifs du client

Quand un client est sélectionné à La Klinic :
1. Appeler `api_forfaits_client` pour récupérer ses forfaits actifs
2. Afficher la section "Forfaits actifs" si le client en a

```javascript
function chargerForfaitsClient(clientId) {
    fetch(`/agenda/klinic/api/forfaits-client/${clientId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.forfaits && data.forfaits.length > 0) {
                afficherForfaitsClient(data.forfaits);
            } else {
                masquerSectionForfaits();
            }
        });
}

function afficherForfaitsClient(forfaits) {
    const section = document.getElementById('reservation-forfaits-section');
    let html = '<label style="color: #9b59b6; font-weight: 600;">📦 Forfaits actifs du client</label>';
    html += '<div style="background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); border: 2px solid #9b59b6; border-radius: 8px; padding: 12px;">';
    
    forfaits.forEach(f => {
        html += `
            <div style="margin-bottom: 8px; padding: 8px; background: white; border-radius: 4px;">
                <strong>${f.prestation_nom}</strong> - ${f.seances_restantes}/${f.nombre_seances_total} séances restantes
            </div>
        `;
    });
    
    html += '</div>';
    section.innerHTML = html;
    section.style.display = 'block';
}
```

### Sélection d'une prestation forfait

Quand le manager sélectionne une prestation de type forfait dans la liste :

```javascript
function onPrestationChange(selectElement, blocIndex) {
    const prestationId = selectElement.value;
    const prestation = getPrestationById(prestationId);
    
    if (!prestation) return;
    
    // Mettre à jour le prix et la durée
    document.getElementById(`prix-base-${blocIndex}`).value = prestation.prix;
    mettreAJourDuree(blocIndex, prestation.duree);
    
    // Vérifier si c'est un forfait
    if (prestation.est_forfait) {
        gererSelectionForfait(blocIndex, prestation);
    } else {
        masquerSectionForfaitBloc(blocIndex);
    }
    
    calculerTotalGroupe();
}

function gererSelectionForfait(blocIndex, prestation) {
    const clientId = document.getElementById('reservation-client-id').value;
    
    if (!clientId) {
        afficherAlerteDansBloc(blocIndex, '⚠️ Sélectionnez d\'abord un client');
        return;
    }
    
    // Vérifier si le client a ce forfait
    const forfaitClient = forfaitsClientCache.find(f => f.prestation_id == prestation.id);
    
    if (forfaitClient && forfaitClient.seances_restantes > 0) {
        // Le client A le forfait → Afficher sélection de séance
        afficherSelectionSeanceForfait(blocIndex, forfaitClient);
    } else {
        // Le client N'A PAS le forfait → Afficher bouton "Vendre forfait"
        afficherBoutonVendreForfait(blocIndex, prestation);
    }
}
```

### Client n'a pas le forfait → Bouton "Vendre forfait"

```javascript
function afficherBoutonVendreForfait(blocIndex, prestation) {
    const container = document.getElementById(`forfait-action-${blocIndex}`);
    container.innerHTML = `
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 12px; margin-top: 10px;">
            <strong style="color: #856404;">⚠️ Ce client n'a pas ce forfait</strong>
            <br><br>
            <button type="button" class="btn" 
                    style="background-color: #9b59b6; color: white;"
                    onclick="ouvrirModalVendreForfait(${prestation.id})">
                🛒 Vendre ce forfait au client
            </button>
            <br><br>
            <small style="color: #856404;">OU choisissez une autre prestation</small>
        </div>
    `;
    container.style.display = 'block';
    
    // Désactiver le bouton "Créer les RDV" tant que le forfait n'est pas acheté
    verifierValiditeFormulaire();
}

function ouvrirModalVendreForfait(prestationId) {
    const clientId = document.getElementById('reservation-client-id').value;
    
    // Pré-remplir le modal de vente de forfait existant
    document.getElementById('forfait-prestation').value = prestationId;
    
    // Ouvrir le modal existant
    document.getElementById('modal-forfait').style.display = 'flex';
    
    // Charger le prix du forfait
    chargerDetailsForfait(prestationId);
}

// Après achat du forfait
function onForfaitAchete(forfaitId, prestationId) {
    // Fermer le modal de vente
    document.getElementById('modal-forfait').style.display = 'none';
    
    // Recharger les forfaits du client
    const clientId = document.getElementById('reservation-client-id').value;
    chargerForfaitsClient(clientId).then(() => {
        // Mettre à jour le bloc prestation pour montrer qu'on peut utiliser une séance
        const blocIndex = trouverBlocAvecPrestation(prestationId);
        if (blocIndex !== null) {
            const forfaitClient = forfaitsClientCache.find(f => f.prestation_id == prestationId);
            afficherSelectionSeanceForfait(blocIndex, forfaitClient);
        }
    });
}
```

### Client a le forfait → Sélection de séance

```javascript
function afficherSelectionSeanceForfait(blocIndex, forfaitClient) {
    const container = document.getElementById(`forfait-action-${blocIndex}`);
    
    // Construire la liste des séances disponibles
    let seancesHtml = '';
    forfaitClient.seances_disponibles.forEach(numero => {
        seancesHtml += `
            <button type="button" class="btn btn-sm" 
                    style="margin: 2px; background-color: #9b59b6; color: white;"
                    onclick="utiliserSeanceForfait(${blocIndex}, ${forfaitClient.id}, ${numero})">
                Séance ${numero}
            </button>
        `;
    });
    
    container.innerHTML = `
        <div style="background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); border: 2px solid #9b59b6; border-radius: 8px; padding: 12px; margin-top: 10px;">
            <strong style="color: #9b59b6;">📦 ${forfaitClient.prestation_nom}</strong>
            <br>
            <span style="font-size: 13px;">${forfaitClient.seances_restantes} séances restantes sur ${forfaitClient.nombre_seances_total}</span>
            <br><br>
            <div>Choisir une séance à utiliser :</div>
            <div style="margin-top: 8px;">${seancesHtml}</div>
        </div>
    `;
    container.style.display = 'block';
}

function utiliserSeanceForfait(blocIndex, forfaitId, numeroSeance) {
    const bloc = document.getElementById(`prestation-bloc-${blocIndex}`);
    
    // Stocker l'info de la séance forfait
    bloc.dataset.seanceForfaitId = `${forfaitId}_${numeroSeance}`;
    bloc.dataset.estSeanceForfait = 'true';
    
    // Mettre le prix de base à 0 (forfait déjà payé)
    const prixBaseInput = document.getElementById(`prix-base-${blocIndex}`);
    prixBaseInput.value = 0;
    prixBaseInput.disabled = true;
    
    // Afficher le badge forfait
    const container = document.getElementById(`forfait-action-${blocIndex}`);
    container.innerHTML = `
        <div style="background: #d4edda; border: 2px solid #28a745; border-radius: 8px; padding: 12px; margin-top: 10px; text-align: center;">
            <span style="font-size: 20px;">✅</span>
            <strong style="color: #28a745;"> Séance ${numeroSeance} sélectionnée</strong>
            <br>
            <span style="font-size: 13px; color: #155724;">Prix forfait : 0 CFA (déjà payé)</span>
            <br><br>
            <button type="button" class="btn btn-sm btn-secondary" onclick="annulerSeanceForfait(${blocIndex})">
                Changer de séance
            </button>
        </div>
    `;
    
    // Recalculer le total (les options sont toujours payantes)
    calculerTotalGroupe();
}
```

## 4.6 Options par prestation

Chaque bloc prestation a sa propre liste d'options avec quantités :

```javascript
function chargerOptionsPrestation(blocIndex, familleId) {
    // Les options sont chargées par famille comme actuellement
    const options = optionsParFamille[familleId] || optionsGlobales;
    
    let html = '';
    options.forEach(opt => {
        html += `
            <div class="option-counter" data-option-id="${opt.id}" data-prix="${opt.prix}">
                <div>
                    <div style="font-weight: 500;">${opt.nom}</div>
                    <div style="color: #666; font-size: 12px;">+${formatPrix(opt.prix)} CFA</div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <button type="button" onclick="ajusterOptionBloc(${blocIndex}, ${opt.id}, -1)">−</button>
                    <span id="option-qte-${blocIndex}-${opt.id}">0</span>
                    <button type="button" onclick="ajusterOptionBloc(${blocIndex}, ${opt.id}, 1)">+</button>
                </div>
            </div>
        `;
    });
    
    document.getElementById(`options-list-${blocIndex}`).innerHTML = html;
}

function ajusterOptionBloc(blocIndex, optionId, delta) {
    const spanQte = document.getElementById(`option-qte-${blocIndex}-${optionId}`);
    let qte = parseInt(spanQte.textContent) + delta;
    qte = Math.max(0, qte);
    spanQte.textContent = qte;
    
    calculerSousTotalBloc(blocIndex);
    calculerTotalGroupe();
}
```

## 4.7 Vérification des conflits

Avant de créer les RDV, vérifier qu'il n'y a pas de chevauchement pour un même employé :

```javascript
function verifierConflits() {
    const prestations = collecterPrestations();
    
    // Grouper par employé
    const parEmploye = {};
    prestations.forEach(p => {
        if (!parEmploye[p.employe_id]) {
            parEmploye[p.employe_id] = [];
        }
        parEmploye[p.employe_id].push(p);
    });
    
    // Vérifier les chevauchements pour chaque employé
    for (const employeId in parEmploye) {
        const rdvs = parEmploye[employeId].sort((a, b) => a.heure_debut.localeCompare(b.heure_debut));
        
        for (let i = 0; i < rdvs.length - 1; i++) {
            if (rdvs[i].heure_fin > rdvs[i + 1].heure_debut) {
                return {
                    conflit: true,
                    message: `Conflit d'horaire pour ${rdvs[i].employe_nom} : ${rdvs[i].prestation_nom} et ${rdvs[i + 1].prestation_nom} se chevauchent`
                };
            }
        }
    }
    
    return { conflit: false };
}
```

---

# 5. CRÉATION DES RDV GROUPÉS

## 5.1 Vue Django

```python
# agenda/views.py - Nouvelle vue

@login_required
@institut_required
@require_POST
def api_rdv_creer_groupe(request, institut_code):
    """
    API : Créer plusieurs rendez-vous en une seule fois (groupe).
    """
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    
    try:
        data = json.loads(request.body)
        
        client_id = data.get('client_id')
        date_str = data.get('date')
        prestations_data = data.get('prestations', [])
        
        if not prestations_data:
            return JsonResponse({
                'success': False,
                'message': 'Aucune prestation sélectionnée'
            }, status=400)
        
        # Validation
        client = get_object_or_404(Client, id=client_id)
        date_rdv = datetime.strptime(date_str, '%Y-%m-%d').date()
        utilisateur = request.user.utilisateur
        
        # Créer le groupe de RDV
        groupe = GroupeRDV.objects.create(
            client=client,
            institut=institut,
            date=date_rdv,
            cree_par=utilisateur,
            nombre_rdv=len(prestations_data),
            prix_total=0
        )
        
        rdvs_crees = []
        prix_total_groupe = 0
        
        for idx, prest_data in enumerate(prestations_data):
            employe = get_object_or_404(Employe, id=prest_data['employe_id'], institut=institut)
            prestation = get_object_or_404(Prestation, id=prest_data['prestation_id'])
            heure_debut = datetime.strptime(prest_data['heure'], '%H:%M').time()
            prix_base = Decimal(str(prest_data.get('prix_base', prestation.prix)))
            
            # Gérer les séances de forfait
            seance_forfait = None
            forfait_client = None
            est_seance_forfait = False
            
            seance_forfait_id = prest_data.get('seance_forfait_id')
            if seance_forfait_id:
                if '_' in str(seance_forfait_id):
                    forfait_id, numero = seance_forfait_id.split('_')
                    seance_forfait = get_object_or_404(
                        SeanceForfait,
                        forfait_id=forfait_id,
                        numero=int(numero),
                        forfait__client=client,
                        forfait__institut=institut,
                        statut='disponible'
                    )
                else:
                    seance_forfait = get_object_or_404(
                        SeanceForfait,
                        id=seance_forfait_id,
                        forfait__client=client,
                        forfait__institut=institut,
                        statut='disponible'
                    )
                forfait_client = seance_forfait.forfait
                est_seance_forfait = True
                prix_base = Decimal('0')
                prestation = forfait_client.prestation
            
            # Calculer le prix des options
            prix_options = Decimal('0')
            options_data = prest_data.get('options', [])
            if options_data:
                option_ids = [opt['id'] for opt in options_data]
                options = Option.objects.filter(id__in=option_ids)
                quantites = {str(opt['id']): int(opt['quantite']) for opt in options_data}
                for opt in options:
                    qte = quantites.get(str(opt.id), 1)
                    prix_options += opt.prix * qte
            
            # Créer le RDV
            rdv = RendezVous.objects.create(
                institut=institut,
                client=client,
                employe=employe,
                prestation=prestation,
                famille=prestation.famille,
                date=date_rdv,
                heure_debut=heure_debut,
                prix_base=prix_base,
                prix_options=prix_options,
                statut='planifie',
                cree_par=utilisateur,
                groupe=groupe,  # NOUVEAU : lier au groupe
                est_seance_forfait=est_seance_forfait,
                forfait=forfait_client,
                numero_seance=seance_forfait.numero if seance_forfait else None
            )
            
            # Programmer la séance forfait si applicable
            if seance_forfait:
                seance_forfait.programmer(rdv)
            
            # Ajouter les options
            if options_data:
                for option in options:
                    qte = quantites.get(str(option.id), 1)
                    RendezVousOption.objects.create(
                        rendez_vous=rdv,
                        option=option,
                        prix_unitaire=option.prix,
                        quantite=qte,
                        prix_total=option.prix * qte
                    )
            
            prix_total_groupe += rdv.prix_total
            rdvs_crees.append({
                'id': rdv.id,
                'prestation': prestation.nom,
                'employe': employe.nom,
                'heure_debut': rdv.heure_debut.strftime('%H:%M'),
                'heure_fin': rdv.heure_fin.strftime('%H:%M'),
                'prix_total': float(rdv.prix_total)
            })
        
        # Mettre à jour le prix total du groupe
        groupe.prix_total = prix_total_groupe
        groupe.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{len(rdvs_crees)} rendez-vous créés avec succès',
            'groupe_id': groupe.id,
            'rdvs': rdvs_crees,
            'prix_total': float(prix_total_groupe)
        })
        
    except Exception as e:
        # En cas d'erreur, supprimer le groupe s'il a été créé
        if 'groupe' in locals():
            groupe.delete()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
```

---

# 6. AFFICHAGE DANS L'AGENDA

## 6.1 Pas de changement visuel majeur

Les RDV s'affichent comme actuellement :
- Chaque RDV dans la colonne de son employé
- Couleur basée sur la famille/statut

Le lien entre les RDV du groupe est géré par la logique de validation (même client + même jour + même groupe).

## 6.2 Modification de la structure des données RDV

Ajouter l'info du groupe dans les données envoyées au template :

```python
# agenda/views.py - Modifier la fonction index

for rdv in rendez_vous.filter(employe=employe):
    rdv_data = {
        'id': rdv.id,
        'client': rdv.client.get_full_name(),
        'prestation': rdv.prestation.nom,
        'heure_debut': rdv.heure_debut.strftime('%H:%M'),
        'heure_fin': rdv.heure_fin.strftime('%H:%M'),
        'duree_creneaux': int((datetime.combine(date.today(), rdv.heure_fin) -
                              datetime.combine(date.today(), rdv.heure_debut)).total_seconds() / 900),
        'prix_total': float(rdv.prix_total),
        'statut': rdv.statut,
        'couleur': rdv.get_couleur(),
        'options': [opt.option.nom for opt in rdv.options_selectionnees.all()],
        'est_seance_forfait': rdv.est_seance_forfait,
        # NOUVEAU
        'groupe_id': rdv.groupe_id,
        'fait_partie_groupe': rdv.fait_partie_groupe(),
    }
    # ...
```

---

# 7. MODIFICATION D'UN RDV EXISTANT - AJOUT DE PRESTATION

## 7.1 Règle importante

**Quand on modifie un RDV existant et qu'on ajoute une prestation, c'est TOUJOURS avec le même employé.**

| Action | Employés |
|--------|----------|
| Bouton "📅 Prendre un RDV" | Plusieurs employés possibles |
| Modifier un RDV existant + ajouter prestation | **Même employé uniquement** |

**Raison :** Le RDV est dans une colonne d'employé. Ajouter une prestation = ajouter à la suite dans la même colonne.

Si le client veut une prestation avec un autre employé → utiliser le bouton "Prendre un RDV".

## 7.2 Interface de modification enrichie

Quand on clique sur "Modifier" pour un RDV existant, le modal permet maintenant :
- Modifier la prestation actuelle (comme avant)
- **OU** ajouter une prestation supplémentaire (avec le même employé)

### Maquette du modal de modification enrichi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ✏️ Modifier le rendez-vous                                           [X]   │
│─────────────────────────────────────────────────────────────────────────────│
│                                                                             │
│  Client: Mme Touré Mariam                                                   │
│  Employé: Maria (non modifiable)                                            │
│  Date: 15/01/2025                                                           │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  📋 PRESTATIONS POUR CE RDV                                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PRESTATION 1                                                        │    │
│  │                                                                     │    │
│  │ Heure: [09:00]                                                      │    │
│  │                                                                     │    │
│  │ ┌───────────────────────────┐ ┌─────────────────────────────────┐   │    │
│  │ │ Famille                   │ │ Prestation                      │   │    │
│  │ │ [Ongle               ▼]  │ │ [Manucure + pose vernis    ▼]  │   │    │
│  │ └───────────────────────────┘ └─────────────────────────────────┘   │    │
│  │                                                                     │    │
│  │ Options : Strass [3]  Dessin [0]                                   │    │
│  │                                                                     │    │
│  │ Prix: 8 000 CFA + 3 000 CFA = 11 000 CFA                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    [+ Ajouter une prestation]                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  <!-- Si on clique sur "+ Ajouter", un nouveau bloc apparaît -->           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PRESTATION 2 (nouvelle)                                        [🗑️] │    │
│  │                                                                     │    │
│  │ Heure: [10:00]  ← Auto-calculée (fin de la prestation 1)           │    │
│  │                                                                     │    │
│  │ ┌───────────────────────────┐ ┌─────────────────────────────────┐   │    │
│  │ │ Famille                   │ │ Prestation                      │   │    │
│  │ │ [Gel                 ▼]  │ │ [Pose gel mains couleur    ▼]  │   │    │
│  │ └───────────────────────────┘ └─────────────────────────────────┘   │    │
│  │                                                                     │    │
│  │ Prix: 45 000 CFA                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  📊 RÉCAPITULATIF                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Manucure + pose vernis (09:00-10:00)              11 000 CFA     │    │
│  │ • Pose gel mains couleur (10:00-12:00)              45 000 CFA     │    │
│  │ ─────────────────────────────────────────────────────────────────   │    │
│  │ TOTAL                                                56 000 CFA     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌───────────────────────┐  ┌───────────────────────────────────────────┐   │
│  │       Annuler         │  │            ✅ Enregistrer                 │   │
│  └───────────────────────┘  └───────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 7.3 Comportement

1. **L'employé n'est PAS modifiable** dans ce modal (affiché mais grisé)
2. **L'heure de la prestation ajoutée** est auto-calculée (fin de la précédente)
3. **Toutes les prestations** sont dans la même colonne d'agenda (même employé)
4. **Le bouton "Enregistrer"** :
   - Met à jour la prestation existante si modifiée
   - Crée un nouveau RDV pour chaque prestation ajoutée
   - Lie tous les RDV au même groupe

## 7.4 Vue Django pour modifier avec ajout de prestations

```python
@login_required
@institut_required
@require_POST
def api_rdv_modifier_avec_prestations(request, institut_code, rdv_id):
    """
    API : Modifier un RDV et potentiellement ajouter des prestations.
    Toutes les prestations sont avec le MÊME employé.
    """
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv_existant = get_object_or_404(RendezVous, id=rdv_id, institut=institut)
    
    # Vérifier que le RDV n'est pas déjà validé
    if rdv_existant.statut == 'valide':
        return JsonResponse({
            'success': False,
            'message': 'Impossible de modifier un RDV déjà validé'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        prestations_data = data.get('prestations', [])
        
        if not prestations_data:
            return JsonResponse({
                'success': False,
                'message': 'Aucune prestation'
            }, status=400)
        
        utilisateur = request.user.utilisateur
        employe = rdv_existant.employe  # MÊME employé pour toutes les prestations
        
        # Créer ou récupérer le groupe si plusieurs prestations
        groupe = rdv_existant.groupe
        if len(prestations_data) > 1 and not groupe:
            groupe = GroupeRDV.objects.create(
                client=rdv_existant.client,
                institut=institut,
                date=rdv_existant.date,
                cree_par=utilisateur,
                nombre_rdv=1,
                prix_total=0
            )
            rdv_existant.groupe = groupe
        
        rdvs_traites = []
        prix_total_groupe = 0
        
        for idx, prest_data in enumerate(prestations_data):
            prestation = get_object_or_404(Prestation, id=prest_data['prestation_id'])
            heure_debut = datetime.strptime(prest_data['heure'], '%H:%M').time()
            prix_base = Decimal(str(prest_data.get('prix_base', prestation.prix)))
            
            # Calculer le prix des options
            prix_options = Decimal('0')
            options_data = prest_data.get('options', [])
            if options_data:
                option_ids = [opt['id'] for opt in options_data]
                options = Option.objects.filter(id__in=option_ids)
                quantites = {str(opt['id']): int(opt['quantite']) for opt in options_data}
                for opt in options:
                    qte = quantites.get(str(opt.id), 1)
                    prix_options += opt.prix * qte
            
            if idx == 0:
                # Première prestation = modifier le RDV existant
                rdv_existant.prestation = prestation
                rdv_existant.famille = prestation.famille
                rdv_existant.heure_debut = heure_debut
                rdv_existant.prix_base = prix_base
                rdv_existant.prix_options = prix_options
                rdv_existant.save()
                
                # Supprimer les anciennes options et recréer
                rdv_existant.options_selectionnees.all().delete()
                if options_data:
                    for option in options:
                        qte = quantites.get(str(option.id), 1)
                        RendezVousOption.objects.create(
                            rendez_vous=rdv_existant,
                            option=option,
                            prix_unitaire=option.prix,
                            quantite=qte,
                            prix_total=option.prix * qte
                        )
                
                rdvs_traites.append(rdv_existant)
                prix_total_groupe += rdv_existant.prix_total
            else:
                # Prestations suivantes = créer de nouveaux RDV
                nouveau_rdv = RendezVous.objects.create(
                    institut=institut,
                    client=rdv_existant.client,
                    employe=employe,  # MÊME employé
                    prestation=prestation,
                    famille=prestation.famille,
                    date=rdv_existant.date,
                    heure_debut=heure_debut,
                    prix_base=prix_base,
                    prix_options=prix_options,
                    statut='planifie',
                    cree_par=utilisateur,
                    groupe=groupe
                )
                
                # Ajouter les options
                if options_data:
                    for option in options:
                        qte = quantites.get(str(option.id), 1)
                        RendezVousOption.objects.create(
                            rendez_vous=nouveau_rdv,
                            option=option,
                            prix_unitaire=option.prix,
                            quantite=qte,
                            prix_total=option.prix * qte
                        )
                
                rdvs_traites.append(nouveau_rdv)
                prix_total_groupe += nouveau_rdv.prix_total
        
        # Mettre à jour le groupe
        if groupe:
            groupe.recalculer_totaux()
        
        return JsonResponse({
            'success': True,
            'message': f'{len(rdvs_traites)} prestation(s) enregistrée(s)',
            'rdvs': [{'id': r.id, 'prestation': r.prestation.nom} for r in rdvs_traites],
            'prix_total': float(prix_total_groupe)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
```

---

# 8. INTÉGRATION AVEC LA VALIDATION EXISTANTE

## 8.1 Pas de modification majeure

Le système de validation groupée existant (`api_rdv_valider_groupe` et `api_rdv_client_jour`) fonctionne déjà bien.

Il détecte automatiquement les RDV du même client le même jour.

## 8.2 Amélioration optionnelle

On peut améliorer `api_rdv_client_jour` pour prioriser les RDV du même groupe :

```python
@login_required
@institut_required
def api_rdv_client_jour(request, institut_code, rdv_id):
    """
    API : Récupère tous les RDV du même client ce jour-là.
    Priorise les RDV du même groupe si applicable.
    """
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(RendezVous, id=rdv_id, institut=institut)
    
    # Récupérer tous les RDV du client ce jour-là (non annulés, non validés)
    rdvs_jour = RendezVous.objects.filter(
        institut=institut,
        client=rdv.client,
        date=rdv.date
    ).exclude(
        statut__in=['annule', 'annule_client', 'valide']
    ).select_related('employe', 'prestation').prefetch_related('options_selectionnees__option')
    
    # Si le RDV fait partie d'un groupe, prioriser les RDV du groupe
    if rdv.groupe:
        rdvs_groupe = rdvs_jour.filter(groupe=rdv.groupe)
        rdvs_autres = rdvs_jour.exclude(groupe=rdv.groupe)
        rdvs_jour = list(rdvs_groupe) + list(rdvs_autres)
    else:
        rdvs_jour = list(rdvs_jour)
    
    # ... reste de la fonction (inchangé)
```

---

# 9. LOGIQUE FINANCIÈRE COMPLÈTE

## 9.1 Calcul des prix

### Prix d'un RDV

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FORMULE DE CALCUL                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RDV NORMAL :                                                               │
│  prix_total = prix_base (prestation) + prix_options                         │
│                                                                             │
│  Exemple : Manucure 8 000 + Strass×3 (3 000) = 11 000 CFA                   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  SÉANCE FORFAIT :                                                           │
│  prix_total = 0 (forfait déjà payé) + prix_options                          │
│                                                                             │
│  Exemple : Séance LPG 0 + Strass×3 (3 000) = 3 000 CFA                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Prix total d'un groupe

```
prix_total_groupe = Somme de tous les prix_total des RDV du groupe
```

**Exemples :**

| Prestation 1 | Prestation 2 | Total groupe |
|--------------|--------------|--------------|
| Manucure 8 000 | Pose gel 45 000 | **53 000 CFA** |
| Séance forfait 0 | Manucure 10 000 | **10 000 CFA** |
| Séance forfait 0 + options 3 000 | Manucure 10 000 | **13 000 CFA** |

## 9.2 Modification de prix à la création

Le manager peut modifier le prix de base d'une prestation lors de la création (remise, erreur catalogue, etc.).

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Prestation : Manucure + pose vernis                                     │
│                                                                         │
│ Prix catalogue : 8 000 CFA                                              │
│ Prix saisi : [6 000] CFA  ← Modifiable (ex: remise fidélité)            │
│                                                                         │
│ Options : Strass ×3 = 3 000 CFA                                         │
│                                                                         │
│ Sous-total : 9 000 CFA                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 9.3 Affichage du récapitulatif dans le modal

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 📊 RÉCAPITULATIF                                                        │
│                                                                         │
│  • Séance forfait LPG (Maria, 09:00-10:00)                             │
│    📦 Forfait - Séance 3/6                              0 CFA          │
│    + Options : Strass ×3                                3 000 CFA      │
│                                                         ─────────      │
│                                                         3 000 CFA      │
│                                                                         │
│  • Manucure + pose vernis (Maria, 10:00-11:00)                         │
│    Prestation                                           8 000 CFA      │
│    + Options : Dessin ×2                                2 000 CFA      │
│                                                         ─────────      │
│                                                         10 000 CFA     │
│                                                                         │
│  ═══════════════════════════════════════════════════════════════════   │
│  TOTAL À PAYER                                          13 000 CFA     │
│  (dont 1 séance de forfait incluse)                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## 9.4 Flux de paiement à la validation

La validation utilise le système existant `api_rdv_valider_groupe` :

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FLUX DE VALIDATION GROUPÉE                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CALCULER LE TOTAL                                                       │
│     prix_total_global = Σ prix_total de chaque RDV                          │
│     (Les séances forfait ont prix_total = 0 + options éventuelles)          │
│                                                                             │
│  2. DÉDUIRE LES CARTES CADEAUX (si utilisées)                               │
│     montant_restant = prix_total_global - montant_cartes                    │
│     → Distribution proportionnelle sur chaque RDV                           │
│                                                                             │
│  3. DÉTERMINER LE MONTANT CASH                                              │
│     - Paiement complet : montant_cash = montant_restant                     │
│     - Paiement différé : montant_cash = 0                                   │
│     - Paiement partiel : montant_cash = montant saisi                       │
│                                                                             │
│  4. CRÉER LES PAIEMENTS                                                     │
│     → Distribution proportionnelle par RDV                                  │
│     → Support double moyen de paiement                                      │
│                                                                             │
│  5. CRÉER LE CRÉDIT (si paiement incomplet)                                 │
│     crédit = prix_total_global - montant_effectif                           │
│     → Lié au groupe (pas à un RDV spécifique)                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 9.5 Exemples de scénarios financiers

### Scénario 1 : Paiement complet simple

```
Prestations :
  • Manucure : 8 000 CFA
  • Pose gel : 45 000 CFA
  
Total : 53 000 CFA
Paiement : Complet en espèces

Résultat :
  → Paiement 1 : 8 000 CFA (Manucure)
  → Paiement 2 : 45 000 CFA (Pose gel)
  → Pas de crédit
```

### Scénario 2 : Paiement partiel

```
Prestations :
  • Manucure : 8 000 CFA
  • Pose gel : 45 000 CFA
  
Total : 53 000 CFA
Paiement : Partiel - 30 000 CFA en espèces

Résultat :
  → Paiement proportionnel sur chaque RDV
  → Crédit créé : 23 000 CFA
     Description : "Groupe de 2 prestations - Manucure, Pose gel"
```

### Scénario 3 : Double paiement

```
Prestations :
  • Manucure : 8 000 CFA
  • Pose gel : 45 000 CFA
  
Total : 53 000 CFA
Paiement : 30 000 CFA espèces + 23 000 CFA Wave

Résultat :
  → Paiements espèces distribués proportionnellement
  → Paiements Wave distribués proportionnellement
  → Pas de crédit
```

### Scénario 4 : Avec carte cadeau

```
Prestations :
  • Manucure : 8 000 CFA
  • Pose gel : 45 000 CFA
  
Total : 53 000 CFA
Carte cadeau : 20 000 CFA
Reste : 33 000 CFA payé en espèces

Résultat :
  → Utilisation carte cadeau distribuée proportionnellement
  → Paiement espèces : 33 000 CFA distribué proportionnellement
  → Pas de crédit
```

### Scénario 5 : Forfait + Prestation normale

```
Prestations :
  • Séance forfait LPG : 0 CFA
  • Manucure : 10 000 CFA
  
Total : 10 000 CFA
Paiement : Complet

Résultat :
  → Paiement forfait : 0 CFA (mode 'forfait')
  → Paiement Manucure : 10 000 CFA (mode 'especes')
```

### Scénario 6 : Forfait avec options + Prestation normale

```
Prestations :
  • Séance forfait LPG + Strass ×3 : 0 + 3 000 = 3 000 CFA
  • Manucure : 10 000 CFA
  
Total : 13 000 CFA
Paiement : Complet

Résultat :
  → Paiement forfait : 0 CFA (mode 'forfait')
  → Paiement options forfait : 3 000 CFA (mode 'especes')
  → Paiement Manucure : 10 000 CFA (mode 'especes')
```

### Scénario 7 : Forfait + Paiement partiel

```
Prestations :
  • Séance forfait LPG : 0 CFA
  • Manucure : 10 000 CFA
  
Total : 10 000 CFA
Paiement : Partiel - 5 000 CFA

Résultat :
  → Paiement forfait : 0 CFA
  → Paiement Manucure : 5 000 CFA
  → Crédit : 5 000 CFA
     Description : "Groupe de 2 prestations - Séance forfait LPG, Manucure"
```

## 9.6 BUG À CORRIGER : Options forfait en validation groupée

### Problème actuel

Dans `api_rdv_valider_groupe`, les options sur les séances forfait ne sont pas payées :

```python
# Ligne 1584-1598 de agenda/views.py - BUG ACTUEL
if rdv.est_seance_forfait:
    try:
        seance = SeanceForfait.objects.get(rendez_vous=rdv)
        seance.effectuer()
    except SeanceForfait.DoesNotExist:
        pass

    Paiement.objects.create(
        rendez_vous=rdv,
        mode='forfait',
        montant=0,
    )
    continue  # ⚠️ BUG : Les options ne sont pas payées !
```

### Correction à apporter

```python
# Correction du bug
if rdv.est_seance_forfait:
    try:
        seance = SeanceForfait.objects.get(rendez_vous=rdv)
        seance.effectuer()
    except SeanceForfait.DoesNotExist:
        pass

    # Créer le paiement forfait (0 CFA pour la prestation de base)
    Paiement.objects.create(
        rendez_vous=rdv,
        mode='forfait',
        montant=0,
    )
    
    # ✅ CORRECTION : Payer les options si présentes
    if rdv.prix_options > 0:
        # Calculer la part des options dans le paiement total
        if montant_paiement_1 > 0:
            if rdv == rdvs[-1]:  # Dernier RDV
                montant_options_1 = int(montant_paiement_1) - total_distribue_1
            else:
                proportion = Decimal(str(rdv.prix_options)) / Decimal(str(prix_total_global))
                montant_options_1 = int(montant_paiement_1 * proportion)
            if montant_options_1 > 0:
                Paiement.objects.create(
                    rendez_vous=rdv,
                    mode=moyen_paiement_1,
                    montant=montant_options_1,
                )
                total_distribue_1 += montant_options_1
        
        if utilise_double_paiement and montant_paiement_2 > 0:
            if rdv == rdvs[-1]:
                montant_options_2 = int(montant_paiement_2) - total_distribue_2
            else:
                proportion = Decimal(str(rdv.prix_options)) / Decimal(str(prix_total_global))
                montant_options_2 = int(montant_paiement_2 * proportion)
            if montant_options_2 > 0:
                Paiement.objects.create(
                    rendez_vous=rdv,
                    mode=moyen_paiement_2,
                    montant=montant_options_2,
                )
                total_distribue_2 += montant_options_2
    
    continue  # Passer au RDV suivant
```

## 9.7 Intégration avec le système existant

Le système de paiement groupé existant (`api_rdv_valider_groupe`) gère déjà :
- ✅ Paiement complet / partiel / différé
- ✅ Double moyen de paiement
- ✅ Cartes cadeaux (distribution proportionnelle)
- ✅ Création de crédit sur le groupe
- ⚠️ Forfaits (bug options à corriger)

**Aucune modification majeure nécessaire** sauf la correction du bug options forfait.

---

# 10. URLs À AJOUTER/MODIFIER

```python
# agenda/urls.py - Ajouter ces URLs

urlpatterns += [
    # Création groupée
    path('<str:institut_code>/api/rdv/creer-groupe/', views.api_rdv_creer_groupe, name='api_rdv_creer_groupe'),
    
    # Ajouter prestation à un RDV existant
    path('<str:institut_code>/api/rdv/<int:rdv_id>/ajouter-prestation/', views.api_rdv_ajouter_prestation, name='api_rdv_ajouter_prestation'),
]
```

---

# 11. TEMPLATES À MODIFIER

| Template | Modification |
|----------|--------------|
| `templates/agenda/agenda.html` | Ajouter bouton "Prendre un RDV", nouveau modal de réservation |
| `templates/agenda/modal_reservation.html` | **NOUVEAU** : Modal complet de réservation multi-prestations |
| `templates/agenda/modal_ajouter_prestation.html` | **NOUVEAU** : Modal pour ajouter une prestation à un RDV |

---

# 12. CHECKLIST D'IMPLÉMENTATION

## Phase 1 : Modèles
- [ ] Créer le modèle `GroupeRDV`
- [ ] Ajouter le champ `groupe` au modèle `RendezVous`
- [ ] Ajouter les méthodes `fait_partie_groupe()` et `get_autres_rdv_groupe()`
- [ ] Faire les migrations

## Phase 2 : Interface - Bouton et modal
- [ ] Ajouter le bouton "📅 Prendre un RDV" dans l'agenda
- [ ] Créer le nouveau modal de réservation multi-prestations
- [ ] Implémenter le JavaScript pour :
  - [ ] Ajouter/supprimer des prestations
  - [ ] Calcul automatique des heures (même employé)
  - [ ] Calcul du prix total
  - [ ] Vérification des conflits
  - [ ] Gestion des options par prestation

## Phase 3 : Clic sur case vide
- [ ] Modifier `nouvelRdv()` pour ouvrir le nouveau modal
- [ ] Pré-remplir employé et heure

## Phase 4 : Création groupée
- [ ] Créer la vue `api_rdv_creer_groupe`
- [ ] Tester la création de groupe avec :
  - [ ] 1 prestation (cas simple)
  - [ ] 2+ prestations, même employé
  - [ ] 2+ prestations, employés différents
  - [ ] Prestations avec options
  - [ ] Séance de forfait

## Phase 5 : Ajouter prestation à RDV existant
- [ ] Ajouter le bouton "➕ Ajouter prestation" dans le modal de détails
- [ ] Créer le modal d'ajout de prestation
- [ ] Créer la vue `api_rdv_ajouter_prestation`
- [ ] Tester l'ajout à un RDV sans groupe (création du groupe)
- [ ] Tester l'ajout à un RDV avec groupe existant

## Phase 6 : Affichage agenda
- [ ] Ajouter `groupe_id` et `fait_partie_groupe` aux données RDV
- [ ] Vérifier que les RDV s'affichent correctement

## Phase 7 : Validation groupée
- [ ] Vérifier que la validation groupée existante fonctionne
- [ ] Tester avec RDV du même groupe
- [ ] Tester avec RDV du même client/jour sans groupe

## Phase 8 : Tests complets
- [ ] Scénario complet : création groupe → affichage → validation → paiement partiel
- [ ] Scénario avec forfait
- [ ] Scénario avec carte cadeau
- [ ] Annulation d'un RDV du groupe
- [ ] Modification d'un RDV du groupe

---

# 13. EXEMPLE DE SCÉNARIO COMPLET

```
1. Le manager clique sur "📅 Prendre un RDV"
   
2. Il sélectionne :
   - Client : Mme Touré
   - Date : 15/01/2025
   
3. Il ajoute la prestation 1 :
   - Employé : Maria
   - Heure : 09:00
   - Prestation : Manucure + pose vernis (8 000 CFA)
   - Option : Strass x3 (3 000 CFA)
   → Sous-total : 11 000 CFA
   
4. Il clique sur "+ Ajouter une prestation"
   
5. Il ajoute la prestation 2 :
   - Employé : Sophie (différent)
   - Heure : 10:00
   - Prestation : Pose gel mains couleur (45 000 CFA)
   → Sous-total : 45 000 CFA
   
6. Récapitulatif affiché :
   - 2 prestations
   - Total : 56 000 CFA
   
7. Il clique sur "Créer les rendez-vous"
   
8. Résultat dans l'agenda :
   - Colonne Maria : RDV Manucure (09:00-10:00)
   - Colonne Sophie : RDV Pose gel (10:00-12:00)
   
9. Plus tard, le manager clique sur le RDV de Maria
   
10. Le système détecte que Mme Touré a 2 RDV ce jour
    → Affiche la validation groupée
    
11. Le manager choisit "Paiement partiel" : 30 000 CFA
    
12. Les 2 RDV sont validés
    Un crédit de 26 000 CFA est créé
```

---

**FIN DU PRD RÉSERVATION MULTI-PRESTATIONS**

*Document créé pour compléter le PRD principal*
*À fournir à Claude Code avec les autres PRD*
