from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import json

from core.decorators import institut_required, role_required
from core.models import (
    Institut, Employe, Client, Prestation, Option, RendezVous,
    RendezVousOption, Paiement, Credit, FamillePrestation, ClotureCaisse,
    PaiementCredit, ModificationLog, CarteCadeau, UtilisationCarteCadeau,
    ForfaitClient, SeanceForfait
)

@login_required
@institut_required
def index(request, institut_code):
    """Vue principale de l'agenda avec grille horaire"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)

    # Date sélectionnée (par défaut aujourd'hui)
    date_str = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        date_selectionnee = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        date_selectionnee = date.today()

    # Récupérer les employés de cet institut
    employes = Employe.objects.filter(
        institut=institut,
        actif=True
    ).order_by('ordre_affichage', 'nom')

    # Récupérer les rendez-vous du jour (exclure les annulés pour libérer les créneaux)
    rendez_vous = RendezVous.objects.filter(
        institut=institut,
        date=date_selectionnee
    ).exclude(
        statut__in=['annule', 'annule_client']
    ).select_related('client', 'employe', 'prestation').prefetch_related('options_selectionnees__option')

    # Créer la grille horaire (7h à 23h, créneaux de 15min)
    debut_journee = time(7, 0)
    fin_journee = time(23, 0)
    creneaux = []
    heure_actuelle = datetime.combine(date.today(), debut_journee)
    heure_fin = datetime.combine(date.today(), fin_journee)

    while heure_actuelle <= heure_fin:
        creneaux.append(heure_actuelle.time())
        heure_actuelle += timedelta(minutes=15)

    # Organiser les RDV par employé et créneau
    rdv_par_employe = {}
    for employe in employes:
        rdv_par_employe[employe.id] = []
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
                'couleur': rdv.get_couleur(),  # Utiliser la méthode qui gère le statut
                'options': [opt.option.nom for opt in rdv.options_selectionnees.all()],
                'est_seance_forfait': rdv.est_seance_forfait,
            }
            # Ajouter les infos forfait si applicable
            if rdv.est_seance_forfait and rdv.forfait:
                rdv_data['label_forfait'] = f"Séance {rdv.numero_seance}/{rdv.forfait.nombre_seances_total}"
            rdv_par_employe[employe.id].append(rdv_data)

    # Récupérer toutes les familles de prestations et options
    # Ne récupérer que les familles qui ont au moins une prestation active
    familles = FamillePrestation.objects.filter(
        institut=institut,
        prestations__actif=True
    ).distinct().order_by('ordre_affichage', 'nom')
    options = Option.objects.filter(institut=institut, actif=True).order_by('nom')

    # Vérifier si la caisse est clôturée pour ce jour
    caisse_cloturee = ClotureCaisse.objects.filter(
        institut=institut,
        date=date_selectionnee,
        cloture=True
    ).exists()

    # Compter séparément les RDV annulés/absents pour les stats
    rdv_annules_absents_count = RendezVous.objects.filter(
        institut=institut,
        date=date_selectionnee,
        statut__in=['annule', 'annule_client', 'absent']
    ).count()

    # CA encaissé : paiements RDV du jour
    ca_paiements_rdv = Paiement.objects.filter(
        rendez_vous__institut=institut,
        rendez_vous__date=date_selectionnee,
        rendez_vous__statut='valide'
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Crédits encaissés ce jour pour cet institut
    credits_encaisses = PaiementCredit.objects.filter(
        credit__institut=institut,
        date__date=date_selectionnee
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Forfaits vendus ce jour pour cet institut
    forfaits_du_jour = ForfaitClient.objects.filter(
        institut=institut,
        date_achat__date=date_selectionnee
    )
    ca_forfaits_reel = forfaits_du_jour.aggregate(total=Sum('prix_total'))['total'] or 0
    ca_forfaits_encaisse = forfaits_du_jour.aggregate(total=Sum('montant_paye_initial'))['total'] or 0

    ca_encaisse = ca_paiements_rdv + credits_encaisses + ca_forfaits_encaisse

    # Convertir rdv_par_employe en JSON pour le template
    import json
    rdv_par_employe_json = json.dumps(rdv_par_employe)

    context = {
        'institut': institut,
        'date_selectionnee': date_selectionnee,
        'employes': employes,
        'creneaux': creneaux,
        'rdv_par_employe': rdv_par_employe_json,
        'familles': familles,
        'options': options,
        'caisse_cloturee': caisse_cloturee,
        'rdv_annules_absents_count': rdv_annules_absents_count,
        'ca_encaisse': ca_encaisse,
        'credits_encaisses': credits_encaisses,
        'ca_forfaits_reel': ca_forfaits_reel,
        'ca_forfaits_encaisse': ca_forfaits_encaisse,
    }

    return render(request, 'agenda/agenda.html', context)


@login_required
@institut_required
def api_prestations(request, institut_code):
    """API : Récupérer toutes les prestations d'un institut"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)

    prestations = Prestation.objects.filter(
        famille__institut=institut,
        actif=True
    ).select_related('famille').values(
        'id', 'nom', 'prix', 'duree', 'famille_id', 'famille__nom', 'type_prestation', 'nombre_seances'
    )

    return JsonResponse(list(prestations), safe=False)


@login_required
@institut_required
@require_POST
def api_rdv_creer(request, institut_code):
    """API : Créer un nouveau rendez-vous"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)

    try:
        # Récupérer les données du formulaire
        client_id = request.POST.get('client_id')
        employe_id = request.POST.get('employe_id')
        prestation_id = request.POST.get('prestation_id')
        date_str = request.POST.get('date')
        heure_str = request.POST.get('heure')
        prix_base = Decimal(request.POST.get('prix_base', 0))
        options_ids = request.POST.getlist('options')

        # Paramètre pour utiliser une séance de forfait
        seance_forfait_id = request.POST.get('seance_forfait_id')

        # Validation
        client = get_object_or_404(Client, id=client_id)
        employe = get_object_or_404(Employe, id=employe_id, institut=institut)
        prestation = get_object_or_404(Prestation, id=prestation_id)
        date_rdv = datetime.strptime(date_str, '%Y-%m-%d').date()
        heure_debut = datetime.strptime(heure_str, '%H:%M').time()

        # Vérifier si c'est une séance de forfait
        seance_forfait = None
        forfait_client = None
        est_seance_forfait = False

        if seance_forfait_id:
            # Format: forfait_id_numero (ex: "5_2" = forfait 5, séance 2)
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
            # Pour une séance forfait, le prix de base est 0
            prix_base = Decimal('0')
            # Utiliser la prestation du forfait
            prestation = forfait_client.prestation

        # Calculer le prix des options
        prix_options = Decimal('0')
        if options_ids:
            options = Option.objects.filter(id__in=options_ids)
            prix_options = sum(opt.prix for opt in options)

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
            cree_par=request.user.utilisateur,
            # Champs forfait
            est_seance_forfait=est_seance_forfait,
            forfait=forfait_client,
            numero_seance=seance_forfait.numero if seance_forfait else None
        )

        # Programmer la séance forfait si applicable
        if seance_forfait:
            seance_forfait.programmer(rdv)

        # Ajouter les options
        if options_ids:
            for option in options:
                RendezVousOption.objects.create(
                    rendez_vous=rdv,
                    option=option,
                    prix_unitaire=option.prix,
                    quantite=1
                )

        message = 'Rendez-vous créé avec succès'
        if est_seance_forfait:
            message = f'Séance {seance_forfait.numero}/{forfait_client.nombre_seances_total} du forfait programmée'

        return JsonResponse({
            'success': True,
            'message': message,
            'rdv_id': rdv.id,
            'est_seance_forfait': est_seance_forfait
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
def api_rdv_details(request, institut_code, rdv_id):
    """API : Récupérer les détails d'un RDV"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    options = rdv.options_selectionnees.select_related('option')

    data = {
        'id': rdv.id,
        'client': rdv.client.get_full_name(),
        'client_id': rdv.client.id,
        'employe': rdv.employe.nom,
        'employe_id': rdv.employe.id,
        'prestation': rdv.prestation.nom,
        'prestation_id': rdv.prestation.id,
        'famille_id': rdv.prestation.famille.id,
        'date': rdv.date.strftime('%Y-%m-%d'),
        'heure_debut': rdv.heure_debut.strftime('%H:%M'),
        'heure_fin': rdv.heure_fin.strftime('%H:%M'),
        'prix_base': float(rdv.prix_base),
        'prix_options': float(rdv.prix_options),
        'prix_total': float(rdv.prix_total),
        'statut': rdv.statut,
        'est_seance_forfait': rdv.est_seance_forfait,
        'options': [{'id': opt.option.id, 'nom': opt.option.nom, 'prix': float(opt.prix)} for opt in options]
    }

    return JsonResponse(data)


@login_required
@institut_required
@require_POST
def api_rdv_modifier(request, institut_code, rdv_id):
    """API : Modifier un rendez-vous existant"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    # Ne pas modifier un RDV validé (sauf pour le patron)
    if rdv.statut == 'valide' and request.user.utilisateur.role != 'patron':
        return JsonResponse({
            'success': False,
            'message': 'Impossible de modifier un rendez-vous validé'
        }, status=403)

    try:
        # Récupérer les données
        prestation_id = request.POST.get('prestation_id')
        date_str = request.POST.get('date')
        heure_str = request.POST.get('heure')
        prix_base = Decimal(request.POST.get('prix_base', 0))
        options_ids = request.POST.getlist('options')
        raison_modification = request.POST.get('raison_modification', '')

        # Sauvegarder l'ancien prix pour la traçabilité
        ancien_prix_base = rdv.prix_base
        ancien_prix_total = rdv.prix_total

        # Mettre à jour le RDV
        if prestation_id:
            rdv.prestation = get_object_or_404(Prestation, id=prestation_id)
        if date_str:
            rdv.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if heure_str:
            rdv.heure_debut = datetime.strptime(heure_str, '%H:%M').time()

        # Détecter si le prix a changé
        prix_modifie = (prix_base != ancien_prix_base)

        rdv.prix_base = prix_base

        # Recalculer le prix des options
        rdv.options_selectionnees.all().delete()
        prix_options = Decimal('0')
        if options_ids:
            options = Option.objects.filter(id__in=options_ids)
            for option in options:
                RendezVousOption.objects.create(
                    rendez_vous=rdv,
                    option=option,
                    prix_unitaire=option.prix,
                    quantite=1
                )
                prix_options += option.prix

        rdv.prix_options = prix_options

        # Si le prix a été modifié, marquer le RDV et créer un log
        if prix_modifie:
            if not rdv.prix_modifie:
                rdv.prix_original = ancien_prix_base
            rdv.prix_modifie = True
            rdv.raison_modification = raison_modification

        rdv.save()

        # Créer un log de modification de prix
        if prix_modifie:
            nouveau_prix_total = rdv.prix_total

            ModificationLog.objects.create(
                type_modification='prix_rdv',
                utilisateur=request.user.utilisateur,
                institut=institut,
                description=f"Modification prix RDV #{rdv.id} - Client: {rdv.client.get_full_name()} - Prestation: {rdv.prestation.nom}",
                valeur_avant=f"{ancien_prix_base} CFA (Total: {ancien_prix_total} CFA)",
                valeur_apres=f"{prix_base} CFA (Total: {nouveau_prix_total} CFA)",
                rendez_vous=rdv
            )

        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous modifié avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
@require_POST
def api_rdv_supprimer(request, institut_code, rdv_id):
    """API : Supprimer un rendez-vous"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    # Ne pas supprimer un RDV validé (sauf pour le patron)
    if rdv.statut == 'valide' and request.user.utilisateur.role != 'patron':
        return JsonResponse({
            'success': False,
            'message': 'Impossible de supprimer un rendez-vous validé'
        }, status=403)

    try:
        rdv.delete()
        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous supprimé avec succès'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
@require_POST
def api_rdv_deplacer(request, institut_code, rdv_id):
    """API : Déplacer un rendez-vous (drag & drop dans l'agenda)"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    # Ne pas déplacer un RDV validé (sauf pour le patron)
    if rdv.statut == 'valide' and request.user.utilisateur.role != 'patron':
        return JsonResponse({
            'success': False,
            'message': 'Impossible de déplacer un rendez-vous validé'
        }, status=403)

    try:
        # Récupérer les nouvelles coordonnées
        nouvelle_date = request.POST.get('date')
        nouvelle_heure = request.POST.get('heure')
        nouvel_employe_id = request.POST.get('employe_id')

        if nouvelle_date:
            rdv.date = datetime.strptime(nouvelle_date, '%Y-%m-%d').date()

        if nouvelle_heure:
            rdv.heure_debut = datetime.strptime(nouvelle_heure, '%H:%M').time()

        if nouvel_employe_id:
            rdv.employe = get_object_or_404(Employe, id=nouvel_employe_id, institut=institut)

        rdv.save()

        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous déplacé avec succès',
            'rdv': {
                'id': rdv.id,
                'date': rdv.date.strftime('%Y-%m-%d'),
                'heure_debut': rdv.heure_debut.strftime('%H:%M'),
                'heure_fin': rdv.heure_fin.strftime('%H:%M'),
                'employe': rdv.employe.nom
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
@require_POST
def api_rdv_annuler(request, institut_code, rdv_id):
    """API : Annuler un rendez-vous (change le statut au lieu de supprimer)"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    if rdv.statut == 'annule':
        return JsonResponse({
            'success': False,
            'message': 'Ce rendez-vous est déjà annulé'
        }, status=400)

    # Ne pas annuler un RDV validé (sauf pour le patron)
    if rdv.statut == 'valide' and request.user.utilisateur.role != 'patron':
        return JsonResponse({
            'success': False,
            'message': 'Impossible d\'annuler un rendez-vous validé'
        }, status=403)

    try:
        rdv.statut = 'annule'
        rdv.save()

        # Si c'est une séance de forfait, la remettre disponible
        if rdv.est_seance_forfait:
            try:
                seance = SeanceForfait.objects.get(rendez_vous=rdv)
                seance.annuler()
                return JsonResponse({
                    'success': True,
                    'message': 'Rendez-vous annulé - Séance forfait remise disponible'
                })
            except SeanceForfait.DoesNotExist:
                pass

        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous annulé avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
@require_POST
def api_rdv_absent(request, institut_code, rdv_id):
    """API : Marquer un RDV comme absent (client ne s'est pas présenté) - Patron uniquement"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    # Vérifier que l'utilisateur est patron
    if request.user.utilisateur.role != 'patron':
        return JsonResponse({
            'success': False,
            'message': 'Seul le patron peut marquer un RDV comme absent'
        }, status=403)

    if rdv.statut in ('valide', 'absent', 'annule_client'):
        return JsonResponse({
            'success': False,
            'message': f'Impossible : ce rendez-vous est déjà {rdv.get_statut_display().lower()}'
        }, status=400)

    try:
        rdv.statut = 'absent'
        rdv.save()
        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous marqué comme absent'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
@require_POST
def api_rdv_annule_client(request, institut_code, rdv_id):
    """API : Marquer un RDV comme annulé par le client - Patron uniquement"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    # Vérifier que l'utilisateur est patron
    if request.user.utilisateur.role != 'patron':
        return JsonResponse({
            'success': False,
            'message': 'Seul le patron peut marquer un RDV comme annulé par le client'
        }, status=403)

    if rdv.statut in ('valide', 'absent', 'annule_client'):
        return JsonResponse({
            'success': False,
            'message': f'Impossible : ce rendez-vous est déjà {rdv.get_statut_display().lower()}'
        }, status=400)

    try:
        rdv.statut = 'annule_client'
        rdv.save()
        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous marqué comme annulé par le client'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
@require_POST
def api_rdv_valider(request, institut_code, rdv_id):
    """API : Valider un rendez-vous et créer le paiement"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    if rdv.statut == 'valide':
        return JsonResponse({
            'success': False,
            'message': 'Ce rendez-vous est déjà validé'
        }, status=400)

    try:
        # Valider le RDV
        rdv.statut = 'valide'
        rdv.save()

        utilisateur = request.user.utilisateur

        # === CAS SPÉCIAL : Séance de forfait ===
        if rdv.est_seance_forfait:
            # Marquer la séance comme effectuée
            try:
                seance = SeanceForfait.objects.get(rendez_vous=rdv)
                seance.effectuer()
            except SeanceForfait.DoesNotExist:
                pass

            # Créer le paiement forfait (0 CFA pour la prestation)
            Paiement.objects.create(
                rendez_vous=rdv,
                mode='forfait',
                montant=0,
            )

            # Si des options sont ajoutées, créer un paiement séparé
            if rdv.prix_options > 0:
                moyen_paiement = request.POST.get('moyen_paiement', 'especes')
                Paiement.objects.create(
                    rendez_vous=rdv,
                    mode=moyen_paiement,
                    montant=int(rdv.prix_options),
                )

            return JsonResponse({
                'success': True,
                'message': f'Séance {rdv.numero_seance} du forfait validée'
            })

        # === CAS NORMAL : RDV standard ===
        # Récupérer les données de paiement
        type_paiement = request.POST.get('type_paiement', 'complet')
        moyen_paiement = request.POST.get('moyen_paiement', 'especes')

        # Déterminer le montant payé
        if type_paiement == 'complet':
            montant_paye = rdv.prix_total
        elif type_paiement == 'differe':
            montant_paye = Decimal('0')
        else:  # partiel
            montant_paye = Decimal(request.POST.get('montant', 0))

        montant_restant = int(montant_paye)

        # 1. Traiter les cartes cadeaux si présentes
        cartes_json = request.POST.get('cartes_cadeaux', '')
        montant_total_cartes = 0
        if cartes_json:
            cartes_data = json.loads(cartes_json)
            for carte_item in cartes_data:
                carte = CarteCadeau.objects.get(
                    id=carte_item['carte_id'],
                    beneficiaire=rdv.client,
                    statut='active',
                )
                montant_a_utiliser = min(
                    int(carte_item['montant']),
                    carte.solde,
                    montant_restant,
                )
                if montant_a_utiliser > 0:
                    utilisation = UtilisationCarteCadeau.objects.create(
                        carte=carte,
                        rendez_vous=rdv,
                        montant=montant_a_utiliser,
                        institut=institut,
                        enregistre_par=utilisateur,
                    )
                    carte.utiliser(montant_a_utiliser)
                    Paiement.objects.create(
                        rendez_vous=rdv,
                        mode='carte_cadeau',
                        montant=montant_a_utiliser,
                        utilisation_carte_cadeau=utilisation,
                    )
                    montant_total_cartes += montant_a_utiliser
                    montant_restant -= montant_a_utiliser

        # 2. Créer le paiement pour le reste (espèces/carte bancaire)
        if montant_restant > 0:
            Paiement.objects.create(
                rendez_vous=rdv,
                mode=moyen_paiement,
                montant=montant_restant,
            )

        # 3. Si paiement partiel ou différé, créer un crédit
        montant_effectif = montant_total_cartes + montant_restant
        if montant_effectif < rdv.prix_total:
            Credit.objects.create(
                client=rdv.client,
                institut=institut,
                rendez_vous=rdv,
                montant_total=int(rdv.prix_total),
                montant_paye=int(montant_effectif),
                description=f"{rdv.prestation.nom} - {rdv.date.strftime('%d/%m/%Y')}",
            )

        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous validé avec succès'
        })

    except CarteCadeau.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Carte cadeau non trouvée ou non valide pour ce client'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
def cloture_caisse(request, institut_code):
    """Vue de clôture de caisse journalière - supporte plusieurs clôtures par jour"""
    from django.db import models

    institut = get_object_or_404(Institut, code=institut_code)

    # Date sélectionnée (par défaut aujourd'hui)
    date_str = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        date_selectionnee = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        date_selectionnee = date.today()

    # Récupérer toutes les clôtures déjà effectuées pour cette date
    clotures_existantes = ClotureCaisse.objects.filter(
        institut=institut,
        date=date_selectionnee,
        cloture=True
    ).order_by('date_cloture')

    # Trouver la dernière clôture effectuée
    derniere_cloture = clotures_existantes.last()

    # Déterminer l'heure de début pour le calcul (soit dernière clôture, soit début de journée)
    if derniere_cloture and derniere_cloture.date_cloture:
        heure_debut = derniere_cloture.date_cloture
        # Gérer les anciennes clôtures avec datetime naïf
        if timezone.is_naive(heure_debut):
            heure_debut = timezone.make_aware(heure_debut)
    else:
        # Début de la journée (avec timezone pour compatibilité avec les DateTimeField)
        heure_debut = timezone.make_aware(datetime.combine(date_selectionnee, datetime.min.time()))

    # Calculer les totaux depuis la dernière clôture (ou début de journée)
    # Paiements des RDV validés
    paiements_rdv = Paiement.objects.filter(
        rendez_vous__institut=institut,
        rendez_vous__date=date_selectionnee,
        rendez_vous__statut='valide',
        date__gte=heure_debut
    )

    total_especes_rdv = paiements_rdv.filter(mode='especes').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_carte_rdv = paiements_rdv.filter(mode='carte').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_cheque_rdv = paiements_rdv.filter(mode='cheque').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_om_rdv = paiements_rdv.filter(mode='om').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_wave_rdv = paiements_rdv.filter(mode='wave').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    # Paiements par carte cadeau (prestations) depuis la dernière clôture
    total_carte_cadeau_prestations = paiements_rdv.filter(mode='carte_cadeau').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    # Ventes de cartes cadeaux depuis la dernière clôture
    from django.utils import timezone as tz
    ventes_cartes = CarteCadeau.objects.filter(
        institut_achat=institut,
        date_achat__date=date_selectionnee,
        date_achat__gte=heure_debut,
    )
    nb_cartes_vendues = ventes_cartes.count()
    ventes_cartes_especes = ventes_cartes.filter(
        mode_paiement_achat='especes'
    ).aggregate(total=models.Sum('montant_initial'))['total'] or 0
    ventes_cartes_cb = ventes_cartes.filter(
        mode_paiement_achat='carte'
    ).aggregate(total=models.Sum('montant_initial'))['total'] or 0
    ventes_cartes_cheque = ventes_cartes.filter(
        mode_paiement_achat='cheque'
    ).aggregate(total=models.Sum('montant_initial'))['total'] or 0
    ventes_cartes_om = ventes_cartes.filter(
        mode_paiement_achat='om'
    ).aggregate(total=models.Sum('montant_initial'))['total'] or 0
    ventes_cartes_wave = ventes_cartes.filter(
        mode_paiement_achat='wave'
    ).aggregate(total=models.Sum('montant_initial'))['total'] or 0

    # Paiements de crédits depuis la dernière clôture
    paiements_credit = PaiementCredit.objects.filter(
        credit__institut=institut,
        date__date=date_selectionnee,
        date__gte=heure_debut
    )

    total_especes_credit = paiements_credit.filter(mode='especes').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_carte_credit = paiements_credit.filter(mode='carte').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_cheque_credit = paiements_credit.filter(mode='cheque').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_om_credit = paiements_credit.filter(mode='om').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_wave_credit = paiements_credit.filter(mode='wave').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    # Totaux en attente de clôture
    total_especes_encours = total_especes_rdv + total_especes_credit + ventes_cartes_especes
    total_carte_encours = total_carte_rdv + total_carte_credit + ventes_cartes_cb
    total_cheque_encours = total_cheque_rdv + total_cheque_credit + ventes_cartes_cheque
    total_om_encours = total_om_rdv + total_om_credit + ventes_cartes_om
    total_wave_encours = total_wave_rdv + total_wave_credit + ventes_cartes_wave
    total_encours = total_especes_encours + total_carte_encours + total_cheque_encours + total_om_encours + total_wave_encours + total_carte_cadeau_prestations

    # Calculer le total cumulé du jour (toutes les clôtures + en cours)
    total_jour_especes = clotures_existantes.aggregate(
        total=models.Sum('total_especes_calcule')
    )['total'] or 0
    total_jour_especes += total_especes_encours

    total_jour_carte = clotures_existantes.aggregate(
        total=models.Sum('total_carte_calcule')
    )['total'] or 0
    total_jour_carte += total_carte_encours

    total_jour = total_jour_especes + total_jour_carte + total_cheque_encours + total_om_encours + total_wave_encours

    # Compter les RDV validés et non validés
    rdv_valides = RendezVous.objects.filter(
        institut=institut,
        date=date_selectionnee,
        statut='valide'
    ).count()

    rdv_non_valides = RendezVous.objects.filter(
        institut=institut,
        date=date_selectionnee,
        statut='planifie'
    ).count()

    # Montant espèces attendu = total espèces en cours + fond de caisse
    montant_attendu = total_especes_encours + institut.fond_caisse

    # Forfaits (uniquement pour La Klinic)
    nb_forfaits_vendus = 0
    total_forfaits_vendus = 0
    nb_seances_forfait = 0

    if institut.code == 'klinic':
        # Forfaits vendus depuis la dernière clôture
        forfaits_vendus = ForfaitClient.objects.filter(
            institut=institut,
            date_achat__date=date_selectionnee,
            date_achat__gte=heure_debut,
        )
        nb_forfaits_vendus = forfaits_vendus.count()
        total_forfaits_vendus = forfaits_vendus.aggregate(
            total=models.Sum('prix_total')
        )['total'] or 0

        # Séances de forfait validées (paiements forfait)
        nb_seances_forfait = paiements_rdv.filter(mode='forfait').count()

    context = {
        'institut': institut,
        'date_selectionnee': date_selectionnee,
        'clotures_existantes': clotures_existantes,
        'total_especes': total_especes_encours,
        'total_carte': total_carte_encours,
        'total_cheque': total_cheque_encours,
        'total_om': total_om_encours,
        'total_wave': total_wave_encours,
        'total_encours': total_encours,
        'total_jour': total_jour,
        'total_jour_especes': total_jour_especes,
        'total_jour_carte': total_jour_carte,
        'total_especes_rdv': total_especes_rdv,
        'total_carte_rdv': total_carte_rdv,
        'total_cheque_rdv': total_cheque_rdv,
        'total_om_rdv': total_om_rdv,
        'total_wave_rdv': total_wave_rdv,
        'total_especes_credit': total_especes_credit,
        'total_carte_credit': total_carte_credit,
        'total_cheque_credit': total_cheque_credit,
        'total_om_credit': total_om_credit,
        'total_wave_credit': total_wave_credit,
        'total_carte_cadeau_prestations': total_carte_cadeau_prestations,
        'nb_cartes_vendues': nb_cartes_vendues,
        'ventes_cartes_especes': ventes_cartes_especes,
        'ventes_cartes_cb': ventes_cartes_cb,
        'ventes_cartes_cheque': ventes_cartes_cheque,
        'ventes_cartes_om': ventes_cartes_om,
        'ventes_cartes_wave': ventes_cartes_wave,
        'rdv_valides': rdv_valides,
        'rdv_non_valides': rdv_non_valides,
        'fond_caisse': institut.fond_caisse,
        'montant_attendu': montant_attendu,
        'nb_clotures': clotures_existantes.count(),
        # Forfaits (La Klinic uniquement)
        'nb_forfaits_vendus': nb_forfaits_vendus,
        'total_forfaits_vendus': total_forfaits_vendus,
        'nb_seances_forfait': nb_seances_forfait,
    }

    return render(request, 'agenda/cloture_caisse.html', context)


@login_required
@institut_required
@require_POST
def api_cloturer_caisse(request, institut_code):
    """API : Valider la clôture de caisse - supporte plusieurs clôtures par jour"""
    from django.db import models

    institut = get_object_or_404(Institut, code=institut_code)

    try:
        date_str = request.POST.get('date')
        montant_reel = request.POST.get('montant_reel')

        date_cloture = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Vérifier qu'il n'y a plus de RDV non validés
        rdv_non_valides = RendezVous.objects.filter(
            institut=institut,
            date=date_cloture,
            statut='planifie'
        ).count()

        if rdv_non_valides > 0:
            return JsonResponse({
                'success': False,
                'message': f'Il reste {rdv_non_valides} rendez-vous non validés. Veuillez les valider ou les annuler avant de clôturer.'
            }, status=400)

        # Trouver la dernière clôture effectuée pour cette date
        derniere_cloture = ClotureCaisse.objects.filter(
            institut=institut,
            date=date_cloture,
            cloture=True
        ).order_by('-date_cloture').first()

        # Déterminer l'heure de début pour le calcul (avec timezone)
        if derniere_cloture and derniere_cloture.date_cloture:
            heure_debut = derniere_cloture.date_cloture
            # Gérer les anciennes clôtures avec datetime naïf
            if timezone.is_naive(heure_debut):
                heure_debut = timezone.make_aware(heure_debut)
        else:
            heure_debut = timezone.make_aware(datetime.combine(date_cloture, datetime.min.time()))

        # Calculer les totaux depuis la dernière clôture
        paiements_rdv = Paiement.objects.filter(
            rendez_vous__institut=institut,
            rendez_vous__date=date_cloture,
            rendez_vous__statut='valide',
            date__gte=heure_debut
        )

        total_especes_rdv = paiements_rdv.filter(mode='especes').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        total_carte_rdv = paiements_rdv.filter(mode='carte').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        paiements_credit = PaiementCredit.objects.filter(
            credit__institut=institut,
            date__date=date_cloture,
            date__gte=heure_debut
        )

        total_especes_credit = paiements_credit.filter(mode='especes').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        total_carte_credit = paiements_credit.filter(mode='carte').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        total_especes = total_especes_rdv + total_especes_credit
        total_carte = total_carte_rdv + total_carte_credit

        # Créer une NOUVELLE clôture (plus de get_or_create)
        cloture = ClotureCaisse.objects.create(
            institut=institut,
            date=date_cloture,
            fond_caisse=institut.fond_caisse,
            montant_reel_especes=int(montant_reel),
            total_especes_calcule=total_especes,
            total_carte_calcule=total_carte,
            total_calcule=total_especes + total_carte,
            cloture=True,
            cloture_par=request.user.utilisateur,
            date_cloture=timezone.now()
        )

        # Calculer l'écart
        montant_attendu = total_especes + cloture.fond_caisse
        cloture.ecart = cloture.montant_reel_especes - montant_attendu
        cloture.save()

        return JsonResponse({
            'success': True,
            'message': f'Caisse clôturée avec succès à {cloture.date_cloture.strftime("%H:%M")}',
            'ecart': cloture.ecart
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


# ============================
# FORFAITS MULTI-SÉANCES
# ============================

@login_required
@institut_required
def api_forfaits_disponibles(request, institut_code):
    """API : Récupérer les forfaits disponibles pour un institut (Klinic uniquement)"""
    institut = get_object_or_404(Institut, code=institut_code)

    # Les forfaits sont uniquement pour La Klinic
    if institut.code != 'klinic':
        return JsonResponse({'forfaits': []})

    forfaits = Prestation.objects.filter(
        famille__institut=institut,
        actif=True,
        est_forfait=True
    ).select_related('famille').values(
        'id', 'nom', 'prix', 'duree', 'nombre_seances', 'famille_id', 'famille__nom'
    )

    return JsonResponse({'forfaits': list(forfaits)})


@login_required
@institut_required
def api_forfaits_client(request, institut_code, client_id):
    """API : Récupérer les forfaits actifs d'un client"""
    institut = get_object_or_404(Institut, code=institut_code)
    client = get_object_or_404(Client, id=client_id)

    forfaits = ForfaitClient.objects.filter(
        client=client,
        institut=institut,
        statut='actif'
    ).select_related('prestation', 'prestation__famille')

    forfaits_data = []
    for f in forfaits:
        # Récupérer les séances disponibles
        seances_disponibles = f.seances.filter(statut='disponible').values_list('numero', flat=True)

        forfaits_data.append({
            'id': f.id,
            'prestation_id': f.prestation.id,
            'prestation_nom': f.prestation.nom,
            'famille_nom': f.prestation.famille.nom,
            'nombre_seances_total': f.nombre_seances_total,
            'nombre_seances_utilisees': f.nombre_seances_utilisees,
            'seances_restantes': f.get_seances_restantes(),
            'seances_a_programmer': f.get_seances_a_programmer(),
            'seances_disponibles': list(seances_disponibles),
            'prix_total': f.prix_total,
            'date_achat': f.date_achat.strftime('%d/%m/%Y'),
        })

    return JsonResponse({'forfaits': forfaits_data})


@login_required
@institut_required
@require_POST
def api_forfait_acheter(request, institut_code):
    """API : Achat d'un forfait pour un client"""
    institut = get_object_or_404(Institut, code=institut_code)

    # Les forfaits sont uniquement pour La Klinic
    if institut.code != 'klinic':
        return JsonResponse({
            'success': False,
            'message': 'Les forfaits ne sont disponibles que pour La Klinic'
        }, status=400)

    try:
        client_id = request.POST.get('client_id')
        prestation_id = request.POST.get('prestation_id')
        type_paiement = request.POST.get('type_paiement', 'complet')  # complet, partiel, differe
        mode_paiement = request.POST.get('mode_paiement', 'especes')
        montant_paye = Decimal(request.POST.get('montant', 0))

        # Validation
        client = get_object_or_404(Client, id=client_id)
        prestation = get_object_or_404(Prestation, id=prestation_id, est_forfait=True)

        # Déterminer le montant payé
        prix_forfait = prestation.prix
        if type_paiement == 'complet':
            montant_effectif = prix_forfait
        elif type_paiement == 'differe':
            montant_effectif = 0
        else:  # partiel
            montant_effectif = int(montant_paye)

        utilisateur = request.user.utilisateur

        # Créer le forfait client
        forfait = ForfaitClient.objects.create(
            client=client,
            prestation=prestation,
            institut=institut,
            nombre_seances_total=prestation.nombre_seances,
            prix_total=prix_forfait,
            montant_paye_initial=montant_effectif,
            vendu_par=utilisateur,
        )

        # Créer les séances individuelles
        for i in range(1, prestation.nombre_seances + 1):
            SeanceForfait.objects.create(
                forfait=forfait,
                numero=i,
                statut='disponible'
            )

        # Si paiement partiel ou différé, créer un crédit
        if montant_effectif < prix_forfait:
            Credit.objects.create(
                client=client,
                institut=institut,
                montant_total=prix_forfait,
                montant_paye=montant_effectif,
                description=f"Forfait {prestation.nom} - {prestation.nombre_seances} séances"
            )

        return JsonResponse({
            'success': True,
            'message': f'Forfait {prestation.nom} acheté avec succès',
            'forfait': {
                'id': forfait.id,
                'prestation': prestation.nom,
                'nombre_seances': forfait.nombre_seances_total,
                'prix_total': forfait.prix_total,
                'montant_paye': montant_effectif,
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@role_required(['patron'])
@require_POST
def api_forfait_supprimer(request, institut_code, forfait_id):
    """API pour supprimer un forfait (patron uniquement)"""
    try:
        forfait = get_object_or_404(ForfaitClient, id=forfait_id)

        # Vérifier s'il y a des séances effectuées
        nb_seances_effectuees = forfait.seances.filter(statut='effectuee').count()

        if nb_seances_effectuees > 0:
            return JsonResponse({
                'success': False,
                'message': f'Impossible de supprimer ce forfait : {nb_seances_effectuees} séance(s) déjà effectuée(s). Vous pouvez l\'annuler à la place.'
            }, status=400)

        # Vérifier s'il y a des séances programmées avec RDV
        nb_seances_programmees = forfait.seances.filter(statut='programmee', rendez_vous__isnull=False).count()

        if nb_seances_programmees > 0:
            return JsonResponse({
                'success': False,
                'message': f'Impossible de supprimer ce forfait : {nb_seances_programmees} séance(s) programmée(s) avec rendez-vous. Annulez les RDV d\'abord.'
            }, status=400)

        prestation_nom = forfait.prestation.nom
        client_nom = forfait.client.get_full_name()

        # Supprimer le forfait (les séances seront supprimées en cascade)
        forfait.delete()

        return JsonResponse({
            'success': True,
            'message': f'Forfait {prestation_nom} de {client_nom} supprimé avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
