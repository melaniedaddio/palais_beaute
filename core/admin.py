from django.contrib import admin
from .models import (
    Institut, Utilisateur, Employe, Client, FamillePrestation, Prestation,
    Option, RendezVous, Paiement, Credit, PaiementCredit, ForfaitClient,
    SeanceForfait, ClotureCaisse, CarteCadeau, UtilisationCarteCadeau,
    ModificationLog
)


@admin.register(Institut)
class InstitutAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'actif', 'a_agenda')
    list_filter = ('actif',)


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'institut', 'actif')
    list_filter = ('role', 'actif', 'institut')


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'institut', 'actif', 'ordre_affichage')
    list_filter = ('institut', 'actif')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'telephone', 'actif', 'date_creation')
    list_filter = ('actif', 'sexe')
    search_fields = ('nom', 'prenom', 'telephone')


@admin.register(FamillePrestation)
class FamillePrestationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'institut', 'actif', 'ordre_affichage')
    list_filter = ('institut', 'actif')


@admin.register(Prestation)
class PrestationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'famille', 'prix', 'type_prestation', 'actif')
    list_filter = ('famille__institut', 'type_prestation', 'actif')
    search_fields = ('nom',)


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'institut', 'prix', 'actif')
    list_filter = ('institut', 'actif')


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('client', 'institut', 'prestation', 'date', 'heure_debut', 'statut', 'prix_total')
    list_filter = ('institut', 'statut', 'date')
    search_fields = ('client__nom', 'client__prenom', 'client__telephone')
    date_hierarchy = 'date'


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('rendez_vous', 'mode', 'montant', 'date')
    list_filter = ('mode', 'date')


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ('client', 'institut', 'montant_total', 'reste_a_payer', 'solde', 'date_creation')
    list_filter = ('institut', 'solde')
    search_fields = ('client__nom', 'client__prenom')


@admin.register(PaiementCredit)
class PaiementCreditAdmin(admin.ModelAdmin):
    list_display = ('credit', 'montant', 'mode', 'date')
    list_filter = ('mode',)


@admin.register(ForfaitClient)
class ForfaitClientAdmin(admin.ModelAdmin):
    list_display = ('client', 'prestation', 'institut', 'nombre_seances_total', 'nombre_seances_utilisees', 'statut')
    list_filter = ('institut', 'statut')
    search_fields = ('client__nom', 'client__prenom')


@admin.register(SeanceForfait)
class SeanceForfaitAdmin(admin.ModelAdmin):
    list_display = ('forfait', 'numero', 'statut')
    list_filter = ('statut',)


@admin.register(ClotureCaisse)
class ClotureCaisseAdmin(admin.ModelAdmin):
    list_display = ('institut', 'date', 'total_calcule', 'ecart', 'cloture')
    list_filter = ('institut', 'cloture')
    date_hierarchy = 'date'


@admin.register(CarteCadeau)
class CarteCadeauAdmin(admin.ModelAdmin):
    list_display = ('code', 'beneficiaire', 'montant_initial', 'solde', 'statut', 'date_achat')
    list_filter = ('statut', 'institut_achat')
    search_fields = ('code', 'beneficiaire__nom', 'acheteur__nom')


@admin.register(UtilisationCarteCadeau)
class UtilisationCarteCadeauAdmin(admin.ModelAdmin):
    list_display = ('carte', 'montant', 'institut', 'date')
    list_filter = ('institut',)


@admin.register(ModificationLog)
class ModificationLogAdmin(admin.ModelAdmin):
    list_display = ('type_modification', 'utilisateur', 'institut', 'date')
    list_filter = ('type_modification', 'institut')
    date_hierarchy = 'date'
    readonly_fields = ('type_modification', 'utilisateur', 'institut', 'date', 'description', 'valeur_avant', 'valeur_apres', 'rendez_vous')
