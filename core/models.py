import random
import string
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinValueValidator
from django.utils import timezone


class Institut(models.Model):
    """
    Représente un institut/salon du groupe.
    3 instituts : Le Palais, La Klinic, Express
    """
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)  # 'palais', 'klinic', 'express'
    a_agenda = models.BooleanField(default=True)  # False pour Express
    heure_ouverture = models.TimeField(default='07:00')
    heure_fermeture = models.TimeField(default='23:00')
    fond_caisse = models.IntegerField(default=30000)  # Montant en CFA
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Institut"
        verbose_name_plural = "Instituts"

    def __str__(self):
        return self.nom


class Utilisateur(models.Model):
    """
    Extension du modèle User Django pour gérer les rôles.
    """
    ROLE_CHOICES = [
        ('patron', 'Patron'),
        ('manager', 'Manager'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    institut = models.ForeignKey(
        Institut,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="NULL pour le patron (accès à tous)"
    )
    pin = models.CharField(max_length=256)  # Code PIN hashé
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def is_patron(self):
        return self.role == 'patron'

    def is_manager(self):
        return self.role == 'manager'

    def set_pin(self, raw_pin):
        """
        Hash et enregistre le PIN de manière sécurisée.
        """
        self.pin = make_password(raw_pin)

    def check_pin(self, raw_pin):
        """
        Vérifie si le PIN fourni correspond au PIN hashé.
        """
        return check_password(raw_pin, self.pin)


class Employe(models.Model):
    """
    Employé d'un institut qui réalise les prestations.
    """
    nom = models.CharField(max_length=100)
    institut = models.ForeignKey(Institut, on_delete=models.CASCADE, related_name='employes')
    actif = models.BooleanField(default=True)
    ordre_affichage = models.IntegerField(default=0)  # Pour l'ordre dans l'agenda

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['institut', 'ordre_affichage', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.institut.nom})"


class Client(models.Model):
    """
    Client des instituts. Le numéro de téléphone est unique.
    """
    SEXE_CHOICES = [
        ('F', 'Femme'),
        ('H', 'Homme'),
    ]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, default='F')
    date_naissance = models.DateField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)  # Observations / notes libres
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def get_full_name(self):
        return f"{self.prenom} {self.nom}"

    def get_total_depense(self):
        """Calcule le total dépensé par le client (tous instituts)"""
        from django.db.models import Sum
        total = Paiement.objects.filter(
            rendez_vous__client=self
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        # Ajouter les paiements de crédits
        total += PaiementCredit.objects.filter(
            credit__client=self
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        return total

    def get_nombre_visites(self):
        """Compte le nombre de visites (RDV validés)"""
        return RendezVous.objects.filter(client=self, statut='valide').count()

    def get_credit_total(self):
        """Calcule le crédit total en cours"""
        from django.db.models import Sum
        return Credit.objects.filter(
            client=self,
            solde=False
        ).aggregate(Sum('reste_a_payer'))['reste_a_payer__sum'] or 0

    @property
    def credits_non_soldes(self):
        """Retourne True si le client a des crédits non soldés"""
        return Credit.objects.filter(client=self, solde=False).exists()


class FamillePrestation(models.Model):
    """
    Famille/catégorie de prestations (ex: Ongle, Gel, Laser femme, Coiffure...)
    Chaque famille a une couleur attribuée automatiquement pour l'agenda.
    """
    nom = models.CharField(max_length=100)
    institut = models.ForeignKey(Institut, on_delete=models.CASCADE, related_name='familles')
    couleur = models.CharField(
        max_length=7,
        default='#e8b4b8',
        help_text="Couleur hexadécimale pour l'affichage dans l'agenda"
    )
    ordre_affichage = models.IntegerField(default=0, help_text="Ordre d'affichage dans le catalogue")

    # Statut
    actif = models.BooleanField(default=True)

    # Métadonnées
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Famille de prestation"
        verbose_name_plural = "Familles de prestations"
        ordering = ['institut', 'ordre_affichage', 'nom']
        unique_together = ['nom', 'institut']

    def __str__(self):
        return f"{self.nom} ({self.institut.nom})"

    def get_prestations_count(self):
        """Retourne le nombre total de prestations dans cette famille"""
        return self.prestations.count()

    def delete(self, *args, **kwargs):
        """Supprime la famille ET toutes ses prestations"""
        self.prestations.all().delete()
        super().delete(*args, **kwargs)


class Prestation(models.Model):
    """
    Prestation proposée par un institut.
    Peut être une prestation normale, une option ou un forfait multi-séances.
    """
    TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('option', 'Option'),
        ('forfait', 'Forfait'),
    ]

    # Informations de base
    nom = models.CharField(max_length=200)
    famille = models.ForeignKey(FamillePrestation, on_delete=models.CASCADE, related_name='prestations')

    # Prix et durée
    prix = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Prix en CFA"
    )
    duree = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Durée en heures (ancien format, sera migré vers duree_minutes)"
    )  # En heures - gardé pour compatibilité
    duree_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Durée en minutes (peut être vide pour les options)"
    )

    # Type de prestation
    type_prestation = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='normal'
    )

    # Pour les options : unité de mesure
    unite = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Unité pour les options (ex: 'par strass', 'par ongle', 'par mèche')"
    )

    # Pour les forfaits : nombre de séances
    est_forfait = models.BooleanField(default=False, help_text="True si c'est un forfait multi-séances")
    nombre_seances = models.IntegerField(
        default=1,
        help_text="Nombre de séances (pour les forfaits)"
    )

    # Disponibilité multi-institut
    instituts = models.ManyToManyField(
        Institut,
        related_name='prestations_disponibles',
        blank=True,
        help_text="Instituts où cette prestation est disponible"
    )

    # Ordre et statut
    ordre_affichage = models.IntegerField(default=0, help_text="Ordre d'affichage dans la famille")
    actif = models.BooleanField(default=True)

    # Métadonnées
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Prestation"
        verbose_name_plural = "Prestations"
        ordering = ['famille', 'ordre_affichage', 'nom']

    def __str__(self):
        if self.type_prestation == 'forfait' or self.est_forfait:
            return f"{self.nom} ({self.nombre_seances} séances) - {self.prix:,} CFA"
        elif self.type_prestation == 'option' and self.unite:
            return f"⭐ {self.nom} ({self.unite}) - {self.prix:,} CFA"
        return f"{self.nom} - {self.prix:,} CFA"

    def get_duree_display(self):
        """Retourne la durée formatée"""
        # Utiliser duree_minutes si disponible, sinon duree
        if self.duree_minutes:
            minutes = self.duree_minutes
        elif self.duree:
            minutes = int(float(self.duree) * 60)
        else:
            return "-"

        heures = minutes // 60
        mins = minutes % 60

        if heures > 0 and mins > 0:
            return f"{heures}h{mins:02d}"
        elif heures > 0:
            return f"{heures}h"
        else:
            return f"{mins} min"

    def is_option(self):
        return self.type_prestation == 'option'

    def is_forfait(self):
        return self.type_prestation == 'forfait' or self.est_forfait

    def get_prix_par_seance(self):
        """Pour les forfaits, retourne le prix par séance"""
        if self.is_forfait() and self.nombre_seances > 0:
            return self.prix // self.nombre_seances
        return self.prix

    def save(self, *args, **kwargs):
        # Synchroniser type_prestation et est_forfait
        if self.type_prestation == 'forfait':
            self.est_forfait = True
        elif self.est_forfait:
            self.type_prestation = 'forfait'

        # Synchroniser duree et duree_minutes
        if self.duree and not self.duree_minutes:
            self.duree_minutes = int(float(self.duree) * 60)
        elif self.duree_minutes and not self.duree:
            self.duree = self.duree_minutes / 60

        super().save(*args, **kwargs)


class Option(models.Model):
    """
    Option supplémentaire pour une prestation (ex: Strass, Dessin, etc.)
    Peut avoir une quantité variable.
    """
    nom = models.CharField(max_length=100)
    institut = models.ForeignKey(Institut, on_delete=models.CASCADE, related_name='options')
    prix = models.IntegerField()  # Prix unitaire en CFA
    a_quantite = models.BooleanField(default=False)  # Si True, on peut spécifier une quantité
    unite = models.CharField(max_length=50, blank=True, null=True)  # Ex: "strass", "ongle"
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Option"
        verbose_name_plural = "Options"
        ordering = ['institut', 'nom']

    def __str__(self):
        return f"{self.nom} - {self.prix} CFA"


class GroupeRDV(models.Model):
    """
    Groupe de rendez-vous créés ensemble.
    Permet de lier plusieurs RDV d'un même client créés en une seule réservation.
    """
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='groupes_rdv'
    )
    institut = models.ForeignKey(
        'Institut',
        on_delete=models.CASCADE,
        related_name='groupes_rdv'
    )
    date = models.DateField()
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='groupes_rdv_crees'
    )
    nombre_rdv = models.IntegerField(default=1)
    prix_total = models.IntegerField(default=0)
    duree_personnalisee = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Durée totale personnalisée en minutes (remplace la somme des durées des prestations)"
    )

    class Meta:
        verbose_name = "Groupe de RDV"
        verbose_name_plural = "Groupes de RDV"
        ordering = ['-date_creation']

    def __str__(self):
        return f"Groupe #{self.id} - {self.client} - {self.date} ({self.nombre_rdv} RDV)"

    def get_duree_totale(self):
        """Retourne la durée totale en minutes (personnalisée si définie, sinon somme des RDVs actifs)."""
        if self.duree_personnalisee:
            return self.duree_personnalisee
        rdvs = self.get_rdvs_actifs()
        total = 0
        for rdv in rdvs:
            if rdv.prestation.duree_minutes:
                total += rdv.prestation.duree_minutes
            elif rdv.prestation.duree:
                total += int(float(rdv.prestation.duree) * 60)
        return total

    def get_duree_display(self):
        """Retourne la durée formatée (ex: '1h30' ou '45 min')."""
        minutes = self.get_duree_totale()
        if not minutes:
            return "-"
        heures = minutes // 60
        mins = minutes % 60
        if heures > 0 and mins > 0:
            return f"{heures}h{mins:02d}"
        elif heures > 0:
            return f"{heures}h"
        return f"{mins} min"

    def a_duree_personnalisee(self):
        return self.duree_personnalisee is not None

    def recalculer_totaux(self):
        rdvs = self.rendez_vous.exclude(statut__in=['annule', 'annule_client'])
        self.nombre_rdv = rdvs.count()
        self.prix_total = sum(rdv.prix_total for rdv in rdvs)
        self.save()

    def get_rdvs_actifs(self):
        return self.rendez_vous.exclude(
            statut__in=['annule', 'annule_client']
        ).order_by('heure_debut')

    def tous_valides(self):
        return not self.get_rdvs_actifs().exclude(statut='valide').exists()

    def peut_etre_supprime(self):
        return not self.rendez_vous.filter(statut='valide').exists()


class RendezVous(models.Model):
    """
    Rendez-vous dans l'agenda (Palais, Klinic) ou vente Express.
    """
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),      # RDV créé, non encore validé
        ('valide', 'Validé'),          # RDV validé par le manager
        ('annule', 'Annulé'),          # RDV annulé
        ('absent', 'Absent'),          # Client ne s'est pas présenté
        ('annule_client', 'Annulé par le client'),  # Annulé par le client
    ]

    # Informations principales
    institut = models.ForeignKey(Institut, on_delete=models.CASCADE, related_name='rendez_vous')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='rendez_vous')
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='rendez_vous')

    # Date et heure
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()  # Calculée automatiquement selon durée

    # Prestation
    prestation = models.ForeignKey(Prestation, on_delete=models.PROTECT, related_name='rendez_vous')
    famille = models.ForeignKey(FamillePrestation, on_delete=models.PROTECT)  # Pour la couleur

    # Prix (peut être modifié par rapport au prix standard)
    prix_base = models.IntegerField(
        validators=[MinValueValidator(0)]
    )  # Prix de la prestation au moment du RDV
    prix_options = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )  # Total des options
    prix_total = models.IntegerField(
        validators=[MinValueValidator(0)]
    )  # prix_base + prix_options

    # Modification de prix
    prix_modifie = models.BooleanField(default=False)  # True si le prix a été modifié
    prix_original = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )  # Prix avant modification
    raison_modification = models.CharField(max_length=200, blank=True, null=True)

    # Statut et validation
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifie')
    date_validation = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rdv_valides'
    )

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='rdv_crees'
    )

    # Groupe de RDV (si créé avec d'autres en même temps)
    groupe = models.ForeignKey(
        'GroupeRDV',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rendez_vous',
        help_text="Groupe auquel appartient ce RDV (si créé avec d'autres)"
    )

    # Champs pour forfaits multi-séances
    est_seance_forfait = models.BooleanField(
        default=False,
        help_text="True si ce RDV est une séance de forfait"
    )
    forfait = models.ForeignKey(
        'ForfaitClient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rendez_vous'
    )
    numero_seance = models.IntegerField(
        null=True,
        blank=True,
        help_text="Numéro de la séance dans le forfait (ex: 3 sur 6)"
    )

    # Rappel WhatsApp
    rappel_envoye = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['date', 'heure_debut', 'employe']

    def __str__(self):
        return f"{self.client} - {self.prestation.nom} - {self.date} {self.heure_debut}"

    def save(self, *args, **kwargs):
        # Calculer l'heure de fin automatiquement
        from datetime import datetime, timedelta
        debut = datetime.combine(self.date, self.heure_debut)
        duree_minutes = int(float(self.prestation.duree) * 60)
        fin = debut + timedelta(minutes=duree_minutes)
        self.heure_fin = fin.time()

        # Calculer le prix total
        self.prix_total = self.prix_base + self.prix_options

        super().save(*args, **kwargs)

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

    def get_couleur(self):
        """Retourne la couleur basée sur le statut et la famille"""
        if self.statut == 'valide':
            return '#28a745'  # Vert pour validé
        elif self.statut == 'annule':
            return '#6c757d'  # Gris pour annulé
        elif self.statut in ('absent', 'annule_client'):
            return '#dc3545'  # Rouge pour absent ou annulé par le client
        elif self.est_seance_forfait:
            return '#9b59b6'  # Violet pour séance de forfait
        else:
            return self.famille.couleur  # Couleur de la famille

    def get_label_agenda(self):
        """Retourne le label à afficher dans l'agenda"""
        if self.est_seance_forfait and self.numero_seance and self.forfait:
            return f"{self.prestation.nom} ({self.numero_seance}/{self.forfait.nombre_seances_total})"
        return self.prestation.nom

    def get_creneaux(self):
        """Retourne la liste des créneaux de 15 min occupés par ce RDV"""
        from datetime import datetime, timedelta
        creneaux = []
        debut = datetime.combine(self.date, self.heure_debut)
        fin = datetime.combine(self.date, self.heure_fin)

        current = debut
        while current < fin:
            creneaux.append(current.strftime('%H:%M'))
            current += timedelta(minutes=15)

        return creneaux


class RendezVousOption(models.Model):
    """
    Options sélectionnées pour un rendez-vous.
    """
    rendez_vous = models.ForeignKey(RendezVous, on_delete=models.CASCADE, related_name='options_selectionnees')
    option = models.ForeignKey(Option, on_delete=models.PROTECT)
    quantite = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    prix_unitaire = models.IntegerField(
        validators=[MinValueValidator(0)]
    )  # Prix au moment de la sélection
    prix_total = models.IntegerField(
        validators=[MinValueValidator(0)]
    )  # prix_unitaire * quantite

    class Meta:
        verbose_name = "Option de rendez-vous"
        verbose_name_plural = "Options de rendez-vous"

    def save(self, *args, **kwargs):
        self.prix_total = self.prix_unitaire * self.quantite
        super().save(*args, **kwargs)


class VenteExpressPrestation(models.Model):
    """
    Liaison entre un RDV Express et ses prestations multiples.
    """
    rendez_vous = models.ForeignKey(RendezVous, on_delete=models.CASCADE, related_name='prestations_express')
    prestation = models.ForeignKey(Prestation, on_delete=models.PROTECT)
    quantite = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    prix_unitaire = models.IntegerField(
        validators=[MinValueValidator(0)]
    )
    prix_total = models.IntegerField(
        validators=[MinValueValidator(0)]
    )

    def save(self, *args, **kwargs):
        self.prix_total = self.prix_unitaire * self.quantite
        super().save(*args, **kwargs)


class Paiement(models.Model):
    """
    Paiement associé à un rendez-vous validé.
    """
    MODE_CHOICES = [
        ('especes', 'Espèces'),
        ('carte', 'Carte'),
        ('cheque', 'Chèque'),
        ('om', 'Orange Money'),
        ('wave', 'Wave'),
        ('carte_cadeau', 'Carte cadeau'),
        ('forfait', 'Forfait'),  # Séance de forfait (0 CFA car déjà payé)
        ('offert', 'Offert'),  # Prestation offerte par le patron (0 CFA)
    ]

    rendez_vous = models.ForeignKey(RendezVous, on_delete=models.CASCADE, related_name='paiements')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    montant = models.IntegerField(
        validators=[MinValueValidator(0)]
    )
    date = models.DateTimeField(auto_now_add=True)
    utilisation_carte_cadeau = models.ForeignKey(
        'UtilisationCarteCadeau',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"{self.montant} CFA ({self.get_mode_display()}) - {self.rendez_vous}"


class Credit(models.Model):
    """
    Crédit/dette d'un client (paiement partiel ou différé).
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='credits')
    institut = models.ForeignKey(Institut, on_delete=models.CASCADE, related_name='credits')
    rendez_vous = models.ForeignKey(
        RendezVous,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credits'
    )

    # Montants
    montant_total = models.IntegerField(
        validators=[MinValueValidator(0)]
    )  # Montant total de la prestation
    montant_paye = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )  # Ce qui a été payé
    reste_a_payer = models.IntegerField(
        validators=[MinValueValidator(0)]
    )  # Ce qui reste à payer

    # Statut
    solde = models.BooleanField(default=False)  # True quand entièrement payé
    date_creation = models.DateTimeField(auto_now_add=True)
    date_solde = models.DateTimeField(null=True, blank=True)

    # Description
    description = models.CharField(max_length=200)  # Ex: "Forfait 10 séances LPG"

    class Meta:
        verbose_name = "Crédit"
        verbose_name_plural = "Crédits"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.client} - {self.reste_a_payer} CFA restants"

    def save(self, *args, **kwargs):
        self.reste_a_payer = self.montant_total - self.montant_paye
        if self.reste_a_payer <= 0:
            self.solde = True
            if not self.date_solde:
                self.date_solde = timezone.now()
        super().save(*args, **kwargs)


class PaiementCredit(models.Model):
    """
    Paiement partiel ou total d'un crédit.
    """
    MODE_CHOICES = [
        ('especes', 'Espèces'),
        ('carte', 'Carte'),
        ('cheque', 'Chèque'),
        ('om', 'Orange Money'),
        ('wave', 'Wave'),
        ('carte_cadeau', 'Carte cadeau'),
    ]

    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, related_name='paiements')
    montant = models.IntegerField(
        validators=[MinValueValidator(0)]
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    enregistre_par = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True
    )
    utilisation_carte_cadeau = models.ForeignKey(
        'UtilisationCarteCadeau',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_credit'
    )

    class Meta:
        verbose_name = "Paiement de crédit"
        verbose_name_plural = "Paiements de crédits"
        ordering = ['-date']

    def __str__(self):
        return f"{self.montant} CFA pour {self.credit.client}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour le crédit
        self.credit.montant_paye += self.montant
        self.credit.save()


class ForfaitClient(models.Model):
    """
    Forfait acheté par un client avec suivi des séances.
    Uniquement pour La Klinic.
    """
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]

    # Client et prestation
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='forfaits'
    )
    prestation = models.ForeignKey(
        'Prestation',
        on_delete=models.PROTECT,
        related_name='forfaits_vendus',
        limit_choices_to={'est_forfait': True}
    )

    # Institut (toujours La Klinic mais on garde la flexibilité)
    institut = models.ForeignKey(
        'Institut',
        on_delete=models.PROTECT,
        related_name='forfaits_vendus'
    )

    # Séances
    nombre_seances_total = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Nombre total de séances du forfait"
    )
    nombre_seances_utilisees = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Nombre de séances déjà effectuées"
    )
    nombre_seances_programmees = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Nombre de séances avec RDV planifié"
    )

    # Prix
    prix_total = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Prix total du forfait"
    )
    montant_paye_initial = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Montant payé à l'achat du forfait"
    )

    # Statut
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')

    # Dates
    date_achat = models.DateTimeField(auto_now_add=True)
    date_derniere_seance = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True, help_text="Date de fin quand toutes les séances sont utilisées")

    # Métadonnées
    vendu_par = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='forfaits_vendus'
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Forfait client"
        verbose_name_plural = "Forfaits clients"
        ordering = ['-date_achat']

    def __str__(self):
        return f"{self.client} - {self.prestation.nom} ({self.get_seances_restantes()}/{self.nombre_seances_total})"

    def get_seances_restantes(self):
        """Retourne le nombre de séances restantes"""
        return self.nombre_seances_total - self.nombre_seances_utilisees

    def get_seances_a_programmer(self):
        """Retourne le nombre de séances non encore programmées"""
        return self.nombre_seances_total - self.nombre_seances_programmees

    def utiliser_seance(self):
        """Consomme une séance du forfait"""
        if self.nombre_seances_utilisees >= self.nombre_seances_total:
            raise ValueError("Toutes les séances ont déjà été utilisées")

        self.nombre_seances_utilisees += 1
        self.date_derniere_seance = timezone.now()

        if self.nombre_seances_utilisees >= self.nombre_seances_total:
            self.statut = 'termine'
            self.date_fin = timezone.now()

        self.save()

    def programmer_seance(self):
        """Incrémente le compteur de séances programmées"""
        if self.nombre_seances_programmees >= self.nombre_seances_total:
            raise ValueError("Toutes les séances sont déjà programmées")

        self.nombre_seances_programmees += 1
        self.save()

    def deprogrammer_seance(self):
        """Décrémente le compteur de séances programmées (si RDV annulé)"""
        if self.nombre_seances_programmees > 0:
            self.nombre_seances_programmees -= 1
            self.save()

    def save(self, *args, **kwargs):
        # Auto-compléter nombre_seances_total depuis la prestation
        if not self.nombre_seances_total and self.prestation:
            self.nombre_seances_total = self.prestation.nombre_seances

        # Auto-compléter prix_total depuis la prestation
        if not self.prix_total and self.prestation:
            self.prix_total = self.prestation.prix

        super().save(*args, **kwargs)


class SeanceForfait(models.Model):
    """
    Représente une séance individuelle d'un forfait.
    Liée au forfait et potentiellement à un RDV.
    """
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),      # Pas encore programmée
        ('programmee', 'Programmée'),      # RDV planifié
        ('effectuee', 'Effectuée'),        # Séance réalisée
        ('annulee', 'Annulée'),            # RDV annulé, séance récupérée
    ]

    forfait = models.ForeignKey(
        ForfaitClient,
        on_delete=models.CASCADE,
        related_name='seances'
    )

    # Numéro de la séance (1, 2, 3, etc.)
    numero = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Numéro de la séance (1, 2, 3...)"
    )

    # Lien avec le RDV (optionnel tant que pas programmée)
    rendez_vous = models.OneToOneField(
        'RendezVous',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seance_forfait'
    )

    # Statut
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')

    # Dates
    date_programmation = models.DateTimeField(null=True, blank=True)
    date_realisation = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Séance de forfait"
        verbose_name_plural = "Séances de forfait"
        ordering = ['forfait', 'numero']
        unique_together = ['forfait', 'numero']

    def __str__(self):
        return f"{self.forfait.prestation.nom} - Séance {self.numero}/{self.forfait.nombre_seances_total}"

    def programmer(self, rendez_vous):
        """Associe cette séance à un RDV"""
        self.rendez_vous = rendez_vous
        self.statut = 'programmee'
        self.date_programmation = timezone.now()
        self.save()
        self.forfait.programmer_seance()

    def effectuer(self):
        """Marque la séance comme effectuée"""
        self.statut = 'effectuee'
        self.date_realisation = timezone.now()
        self.save()
        self.forfait.utiliser_seance()

    def annuler(self):
        """Annule la programmation de la séance"""
        self.rendez_vous = None
        self.statut = 'disponible'
        self.date_programmation = None
        self.save()
        self.forfait.deprogrammer_seance()


class ClotureCaisse(models.Model):
    """
    Clôture de caisse journalière par institut.
    """
    institut = models.ForeignKey(Institut, on_delete=models.CASCADE, related_name='clotures')
    date = models.DateField()

    # Montants calculés (depuis les paiements)
    total_especes_calcule = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_carte_calcule = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_cheque_calcule = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_om_calcule = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_wave_calcule = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_calcule = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    # Montant réel saisi par le manager
    montant_reel_especes = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    # Fond de caisse
    fond_caisse = models.IntegerField(
        default=30000,
        validators=[MinValueValidator(0)]
    )

    # Écart
    ecart = models.IntegerField(default=0)  # montant_reel - (total_especes_calcule + fond_caisse)

    # Métadonnées
    cloture_par = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True)
    date_cloture = models.DateTimeField(null=True, blank=True)
    cloture = models.BooleanField(default=False)  # True quand le manager a validé

    class Meta:
        verbose_name = "Clôture de caisse"
        verbose_name_plural = "Clôtures de caisse"
        ordering = ['-date', '-date_cloture']

    def __str__(self):
        if self.date_cloture:
            return f"{self.institut.nom} - {self.date} {self.date_cloture.strftime('%H:%M')}"
        return f"{self.institut.nom} - {self.date}"

    def calculer_totaux(self):
        """Calcule les totaux depuis les paiements du jour"""
        from django.db.models import Sum

        # Paiements des RDV validés
        paiements_rdv = Paiement.objects.filter(
            rendez_vous__institut=self.institut,
            rendez_vous__date=self.date,
            rendez_vous__statut='valide'
        )

        self.total_especes_calcule = paiements_rdv.filter(
            mode='especes'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        self.total_carte_calcule = paiements_rdv.filter(
            mode='carte'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        self.total_cheque_calcule = paiements_rdv.filter(
            mode='cheque'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        self.total_om_calcule = paiements_rdv.filter(
            mode='om'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        self.total_wave_calcule = paiements_rdv.filter(
            mode='wave'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        # Paiements par carte cadeau (prestations)
        total_carte_cadeau_prestations = paiements_rdv.filter(
            mode='carte_cadeau'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        # Ajouter les paiements de crédits du jour
        paiements_credit = PaiementCredit.objects.filter(
            credit__institut=self.institut,
            date__date=self.date
        )

        self.total_especes_calcule += paiements_credit.filter(
            mode='especes'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        self.total_carte_calcule += paiements_credit.filter(
            mode='carte'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        self.total_cheque_calcule += paiements_credit.filter(
            mode='cheque'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        self.total_om_calcule += paiements_credit.filter(
            mode='om'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        self.total_wave_calcule += paiements_credit.filter(
            mode='wave'
        ).aggregate(Sum('montant'))['montant__sum'] or 0

        # Ventes de cartes cadeaux du jour
        ventes_cartes = CarteCadeau.objects.filter(
            institut_achat=self.institut,
            date_achat__date=self.date,
        )
        ventes_cartes_especes = ventes_cartes.filter(
            mode_paiement_achat='especes'
        ).aggregate(Sum('montant_initial'))['montant_initial__sum'] or 0

        ventes_cartes_cb = ventes_cartes.filter(
            mode_paiement_achat='carte'
        ).aggregate(Sum('montant_initial'))['montant_initial__sum'] or 0

        ventes_cartes_cheque = ventes_cartes.filter(
            mode_paiement_achat='cheque'
        ).aggregate(Sum('montant_initial'))['montant_initial__sum'] or 0

        ventes_cartes_om = ventes_cartes.filter(
            mode_paiement_achat='om'
        ).aggregate(Sum('montant_initial'))['montant_initial__sum'] or 0

        ventes_cartes_wave = ventes_cartes.filter(
            mode_paiement_achat='wave'
        ).aggregate(Sum('montant_initial'))['montant_initial__sum'] or 0

        # Totaux généraux
        # Les espèces en caisse incluent les ventes de cartes cadeaux payées en espèces
        self.total_especes_calcule += ventes_cartes_especes
        self.total_carte_calcule += ventes_cartes_cb
        self.total_cheque_calcule += ventes_cartes_cheque
        self.total_om_calcule += ventes_cartes_om
        self.total_wave_calcule += ventes_cartes_wave

        # total_calcule = argent réellement encaissé (sans carte_cadeau car déjà compté à la vente)
        self.total_calcule = (
            self.total_especes_calcule
            + self.total_carte_calcule
            + self.total_cheque_calcule
            + self.total_om_calcule
            + self.total_wave_calcule
        )

        # Calculer l'écart si montant réel saisi
        if self.montant_reel_especes is not None:
            attendu = self.total_especes_calcule + self.fond_caisse
            self.ecart = self.montant_reel_especes - attendu

        self.save()

        # Retourner les détails cartes cadeaux pour l'affichage
        return {
            'total_carte_cadeau_prestations': total_carte_cadeau_prestations,
            'ventes_cartes_especes': ventes_cartes_especes,
            'ventes_cartes_cb': ventes_cartes_cb,
            'ventes_cartes_cheque': ventes_cartes_cheque,
            'ventes_cartes_om': ventes_cartes_om,
            'ventes_cartes_wave': ventes_cartes_wave,
            'ventes_cartes_total': ventes_cartes_especes + ventes_cartes_cb + ventes_cartes_cheque + ventes_cartes_om + ventes_cartes_wave,
            'nb_cartes_vendues': ventes_cartes.count(),
        }


class CarteCadeau(models.Model):
    """
    Carte cadeau achetée par un client pour un bénéficiaire.
    """
    STATUT_CHOICES = [
        ('active', 'Active'),
        ('expiree', 'Expirée'),
        ('soldee', 'Soldée'),
        ('annulee', 'Annulée'),
        ('supprimee', 'Supprimée'),
    ]

    code = models.CharField(max_length=20, unique=True, editable=False)

    acheteur = models.ForeignKey(
        'Client',
        on_delete=models.PROTECT,
        related_name='cartes_achetees',
    )
    beneficiaire = models.ForeignKey(
        'Client',
        on_delete=models.PROTECT,
        related_name='cartes_recues',
    )

    montant_initial = models.IntegerField(
        validators=[MinValueValidator(0)]
    )
    solde = models.IntegerField(
        validators=[MinValueValidator(0)]
    )

    institut_achat = models.ForeignKey(
        'Institut',
        on_delete=models.PROTECT,
        related_name='cartes_vendues',
    )

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='active')

    date_achat = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField(null=True, blank=True, help_text="Date d'expiration (6 mois après l'achat)")
    date_derniere_utilisation = models.DateTimeField(null=True, blank=True)

    mode_paiement_achat = models.CharField(
        max_length=20,
        choices=[
            ('especes', 'Espèces'),
            ('carte', 'Carte bancaire'),
            ('cheque', 'Chèque'),
            ('om', 'Orange Money'),
            ('wave', 'Wave'),
        ],
        default='especes',
    )

    # Double paiement
    montant_paiement_1 = models.IntegerField(null=True, blank=True,
        help_text="Montant payé avec le 1er moyen (= montant_initial si paiement simple)")
    moyen_paiement_2 = models.CharField(max_length=20, blank=True, null=True,
        choices=[
            ('especes', 'Espèces'),
            ('carte', 'Carte bancaire'),
            ('cheque', 'Chèque'),
            ('om', 'Orange Money'),
            ('wave', 'Wave'),
        ],
    )
    montant_paiement_2 = models.IntegerField(null=True, blank=True,
        help_text="Montant payé avec le 2ème moyen")

    vendue_par = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='cartes_vendues',
    )

    class Meta:
        verbose_name = "Carte cadeau"
        verbose_name_plural = "Cartes cadeaux"
        ordering = ['-date_achat']

    def __str__(self):
        return f"{self.code} - {self.beneficiaire} ({self.solde} CFA)"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generer_code()
        # Définir la date d'expiration à 6 mois après l'achat si non définie
        if not self.date_expiration and self.date_achat:
            self.date_expiration = self.date_achat + timedelta(days=180)
        if self.solde <= 0:
            self.solde = 0
            self.statut = 'soldee'
        super().save(*args, **kwargs)
        # Si c'est une nouvelle carte, définir l'expiration après la sauvegarde (date_achat sera rempli)
        if not self.date_expiration:
            self.date_expiration = self.date_achat + timedelta(days=180)
            super().save(update_fields=['date_expiration'])

    @staticmethod
    def generer_code():
        annee = timezone.now().year
        caracteres = string.ascii_uppercase + string.digits
        code_aleatoire = ''.join(random.choices(caracteres, k=6))
        code = f"CG-{annee}-{code_aleatoire}"
        while CarteCadeau.objects.filter(code=code).exists():
            code_aleatoire = ''.join(random.choices(caracteres, k=6))
            code = f"CG-{annee}-{code_aleatoire}"
        return code

    @property
    def est_expiree(self):
        """Vérifie si la carte est expirée (plus de 6 mois depuis l'achat)."""
        if self.date_expiration:
            return timezone.now() > self.date_expiration
        # Pour les anciennes cartes sans date d'expiration, vérifier 6 mois depuis l'achat
        if self.date_achat:
            return timezone.now() > (self.date_achat + timedelta(days=180))
        return False

    @property
    def jours_restants(self):
        """Retourne le nombre de jours restants avant expiration."""
        if self.date_expiration:
            delta = self.date_expiration - timezone.now()
            return max(0, delta.days)
        return 0

    @classmethod
    def marquer_cartes_expirees(cls):
        """Passe en statut 'expiree' toutes les cartes actives dont la date d'expiration est dépassée."""
        now = timezone.now()
        # Cartes avec date_expiration renseignée
        cls.objects.filter(
            statut='active',
            date_expiration__lt=now
        ).update(statut='expiree')
        # Anciennes cartes sans date_expiration (fallback 180 jours après achat)
        cls.objects.filter(
            statut='active',
            date_expiration__isnull=True,
            date_achat__lt=now - timedelta(days=180)
        ).update(statut='expiree')

    def utiliser(self, montant):
        """Utilise un montant de la carte. Retourne le montant réellement débité."""
        if self.est_expiree:
            self.statut = 'expiree'
            self.save(update_fields=['statut'])
            raise ValueError("Cette carte est expirée")
        if self.statut != 'active':
            raise ValueError("Cette carte n'est plus active")
        montant_debite = min(montant, self.solde)
        self.solde -= montant_debite
        self.date_derniere_utilisation = timezone.now()
        # Passer à soldée si le solde atteint 0
        if self.solde <= 0:
            self.statut = 'soldee'
        self.save()
        return montant_debite

    def get_total_utilise(self):
        return self.montant_initial - self.solde


class UtilisationCarteCadeau(models.Model):
    """
    Historique des utilisations d'une carte cadeau.
    """
    carte = models.ForeignKey(
        CarteCadeau,
        on_delete=models.CASCADE,
        related_name='utilisations',
    )
    rendez_vous = models.ForeignKey(
        'RendezVous',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_carte_cadeau',
    )
    montant = models.IntegerField(
        validators=[MinValueValidator(0)]
    )
    institut = models.ForeignKey(
        'Institut',
        on_delete=models.PROTECT,
        related_name='utilisations_cartes',
    )
    date = models.DateTimeField(auto_now_add=True)
    enregistre_par = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        verbose_name = "Utilisation carte cadeau"
        verbose_name_plural = "Utilisations cartes cadeaux"
        ordering = ['-date']

    def __str__(self):
        return f"{self.carte.code} - {self.montant} CFA - {self.date.strftime('%d/%m/%Y')}"


class ModificationLog(models.Model):
    """
    Journal des modifications de prix faites par les managers.
    Pour traçabilité et vérification par le patron.
    """
    TYPE_CHOICES = [
        ('prix_rdv', 'Modification prix RDV'),
        ('ajout_prestation', 'Ajout prestation'),
        ('modif_prestation', 'Modification prestation'),
        ('ajout_option', 'Ajout option'),
        ('modif_option', 'Modification option'),
    ]

    type_modification = models.CharField(max_length=50, choices=TYPE_CHOICES)
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True)
    institut = models.ForeignKey(Institut, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    # Détails
    description = models.TextField()
    valeur_avant = models.CharField(max_length=200, blank=True, null=True)
    valeur_apres = models.CharField(max_length=200, blank=True, null=True)

    # Référence optionnelle au RDV
    rendez_vous = models.ForeignKey(
        RendezVous,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Log de modification"
        verbose_name_plural = "Logs de modifications"
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_modification_display()} - {self.utilisateur} - {self.date}"
