import math
from django.shortcuts import render, get_object_or_404, redirect
from core.decorators import login_required_json as login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, date, time, timedelta
from decimal import Decimal, InvalidOperation
import json

from core.decorators import institut_required, role_required
from core.models import (
    Institut, Employe, Client, Prestation, Option, RendezVous,
    RendezVousOption, Paiement, Credit, FamillePrestation, ClotureCaisse,
    PaiementCredit, ModificationLog, CarteCadeau, UtilisationCarteCadeau,
    ForfaitClient, SeanceForfait, GroupeRDV, Depense, MouvementStock
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
    ).select_related('client', 'employe', 'prestation', 'prestation__famille', 'groupe').prefetch_related('options_selectionnees__option')

    # Dates de validation (dernier paiement) par RDV validé
    from django.db.models import Max as DBMax
    validation_dates = dict(
        Paiement.objects.filter(
            rendez_vous__in=rendez_vous.filter(statut='valide')
        ).values('rendez_vous_id').annotate(last=DBMax('date')).values_list('rendez_vous_id', 'last')
    )

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
                'client_id': rdv.client.id,
                'employe': rdv.employe.prenom or rdv.employe.nom,
                'employe_id': rdv.employe.id,
                'prestation': rdv.prestation.nom,
                'date': rdv.date.strftime('%Y-%m-%d'),
                'heure_debut': rdv.heure_debut.strftime('%H:%M'),
                'heure_fin': rdv.heure_fin.strftime('%H:%M'),
                'duree_creneaux': int((datetime.combine(date.today(), rdv.heure_fin) -
                                      datetime.combine(date.today(), rdv.heure_debut)).total_seconds() / 900),
                'prix_total': float(rdv.prix_total),
                'remise_pourcent': rdv.remise_pourcent or 0,
                'statut': rdv.statut,
                'couleur': rdv.prestation.famille.couleur,
                'options': [opt.option.nom for opt in rdv.options_selectionnees.all()],
                'est_seance_forfait': rdv.est_seance_forfait,
                'groupe_id': rdv.groupe_id,
                'groupe_duree_personnalisee': rdv.groupe.duree_personnalisee if rdv.groupe else None,
                'prestation_id': rdv.prestation.id,
                'famille_id': rdv.famille_id,
                'prix_base': float(rdv.prix_base),
                'groupe_prix_total': rdv.groupe.prix_total if rdv.groupe else None,
                'validation_datetime': validation_dates[rdv.id].isoformat() if rdv.id in validation_dates else None,
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
    clotures_du_jour = list(ClotureCaisse.objects.filter(
        institut=institut,
        date=date_selectionnee,
        cloture=True
    ).values_list('date_cloture', flat=True).order_by('date_cloture'))

    caisse_cloturee = bool(clotures_du_jour)

    # Timestamps ISO des clôtures du jour (pour le JS)
    clotures_timestamps_json = json.dumps([c.isoformat() for c in clotures_du_jour])

    # Compter séparément les RDV annulés/absents pour les stats
    rdv_annules_absents_count = RendezVous.objects.filter(
        institut=institut,
        date=date_selectionnee,
        statut__in=['annule', 'annule_client', 'absent']
    ).count()

    # CA encaissé : paiements RDV du jour
    # Exclure carte_cadeau (déjà compté lors de la vente de la carte)
    ca_paiements_rdv = Paiement.objects.filter(
        rendez_vous__institut=institut,
        rendez_vous__date=date_selectionnee,
        rendez_vous__statut='valide'
    ).exclude(mode__in=['carte_cadeau', 'forfait', 'offert']).aggregate(total=Sum('montant'))['total'] or 0

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
    rdv_par_employe_json = json.dumps(rdv_par_employe)

    utilisateur = request.user.utilisateur
    context = {
        'institut': institut,
        'date_selectionnee': date_selectionnee,
        'employes': employes,
        'creneaux': creneaux,
        'rdv_par_employe': rdv_par_employe_json,
        'familles': familles,
        'options': options,
        'caisse_cloturee': caisse_cloturee,
        'clotures_timestamps_json': clotures_timestamps_json,
        'rdv_annules_absents_count': rdv_annules_absents_count,
        'ca_encaisse': ca_encaisse,
        'credits_encaisses': credits_encaisses,
        'ca_forfaits_reel': ca_forfaits_reel,
        'ca_forfaits_encaisse': ca_forfaits_encaisse,
        'is_employe': utilisateur.is_employe(),
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
@require_GET
def api_verifier_conflit(request, institut_code):
    """API : Vérifie si un créneau est libre pour un employé (chevauchement avec RDV existants)"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)

    employe_id      = request.GET.get('employe_id')
    date_str        = request.GET.get('date')
    heure_debut_str = request.GET.get('heure_debut')
    heure_fin_str   = request.GET.get('heure_fin')
    rdv_exclude_id  = request.GET.get('rdv_exclude_id')

    if not all([employe_id, date_str, heure_debut_str, heure_fin_str]):
        return JsonResponse({'conflit': False})

    try:
        heure_debut = datetime.strptime(heure_debut_str, '%H:%M').time()
        heure_fin   = datetime.strptime(heure_fin_str,   '%H:%M').time()
    except ValueError:
        return JsonResponse({'conflit': False})

    rdvs = RendezVous.objects.filter(
        institut=institut,
        employe_id=employe_id,
        date=date_str,
        heure_debut__lt=heure_fin,
        heure_fin__gt=heure_debut,
    ).exclude(statut__in=['annule', 'annule_client', 'absent'])

    if rdv_exclude_id:
        rdvs = rdvs.exclude(id=rdv_exclude_id)
        # Exclure aussi tous les RDVs du même groupe que le RDV exclu
        try:
            rdv_exclu = RendezVous.objects.only('groupe_id').get(id=rdv_exclude_id)
            if rdv_exclu.groupe_id:
                rdvs = rdvs.exclude(groupe_id=rdv_exclu.groupe_id)
        except RendezVous.DoesNotExist:
            pass

    # Pour les groupes avec duree_personnalisee, recalculer la fin effective
    # afin d'éviter les faux conflits avec des RDVs "hors durée"
    rdvs_candidats = list(rdvs.select_related('client', 'prestation', 'groupe'))

    rdv_conflit = None
    for rdv_c in rdvs_candidats:
        if rdv_c.groupe_id and rdv_c.groupe and rdv_c.groupe.duree_personnalisee:
            from django.db.models import Min as _Min
            debut_groupe = RendezVous.objects.filter(
                groupe_id=rdv_c.groupe_id,
            ).exclude(
                statut__in=['annule', 'annule_client', 'absent']
            ).aggregate(debut=_Min('heure_debut'))['debut']
            if debut_groupe:
                dt_fin_eff = datetime.combine(date.today(), debut_groupe) + timedelta(
                    minutes=rdv_c.groupe.duree_personnalisee
                )
                heure_fin_eff = dt_fin_eff.time()
                # Pas de chevauchement réel si la fin effective est <= heure_debut demandée
                if heure_fin_eff <= heure_debut:
                    continue
        rdv_conflit = rdv_c
        break

    if rdv_conflit:
        return JsonResponse({
            'conflit': True,
            'rdv': {
                'id': rdv_conflit.id,
                'client': str(rdv_conflit.client),
                'prestation': rdv_conflit.prestation.nom,
                'heure_debut': rdv_conflit.heure_debut.strftime('%H:%M'),
                'heure_fin':   rdv_conflit.heure_fin.strftime('%H:%M'),
            }
        })

    return JsonResponse({'conflit': False})


@login_required
@role_required(['patron', 'manager'])
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

        # Récupérer les options avec leurs quantités
        import json
        options_data_str = request.POST.get('options_data', '[]')
        options_data = json.loads(options_data_str) if options_data_str else []

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
        if options_data:
            # options_data est une liste de dict: [{'id': '1', 'quantite': 2}, ...]
            option_ids = [opt['id'] for opt in options_data]
            options = Option.objects.filter(id__in=option_ids)
            # Créer un dict pour accès rapide aux quantités
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
@role_required(['patron', 'manager'])
@institut_required
@require_POST
def api_rdv_creer_groupe(request, institut_code):
    """API : Créer un groupe de rendez-vous (réservation multi-prestations en une fois)"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)

    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')
        date_str = data.get('date')
        prestations_data = data.get('prestations', [])
        duree_personnalisee = data.get('duree_personnalisee')  # en minutes, optionnel

        if not client_id:
            return JsonResponse({'success': False, 'message': 'Client requis'}, status=400)
        if not date_str:
            return JsonResponse({'success': False, 'message': 'Date requise'}, status=400)
        if not prestations_data:
            return JsonResponse({'success': False, 'message': 'Au moins une prestation requise'}, status=400)

        client = get_object_or_404(Client, id=client_id)
        date_rdv = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Valider la durée personnalisée si fournie
        duree_perso_int = None
        if duree_personnalisee is not None:
            try:
                duree_perso_int = int(duree_personnalisee)
                if duree_perso_int < 1:
                    duree_perso_int = None
            except (ValueError, TypeError):
                duree_perso_int = None

        # Créer le groupe (conteneur)
        groupe = GroupeRDV.objects.create(
            client=client,
            institut=institut,
            date=date_rdv,
            cree_par=request.user.utilisateur,
            nombre_rdv=len(prestations_data),
            duree_personnalisee=duree_perso_int,
        )

        rdvs_crees = []

        for prest_data in prestations_data:
            employe_id    = prest_data.get('employe_id')
            heure_str     = prest_data.get('heure_debut')
            prestation_id = prest_data.get('prestation_id')
            prix_base     = Decimal(str(prest_data.get('prix_base', 0)))
            options_list  = prest_data.get('options', [])
            seance_forfait_id = prest_data.get('seance_forfait_id')

            if not employe_id or not heure_str or not prestation_id:
                groupe.delete()
                return JsonResponse(
                    {'success': False, 'message': 'Employé, heure et prestation requis pour chaque RDV'},
                    status=400
                )

            employe    = get_object_or_404(Employe, id=employe_id, institut=institut)
            prestation = get_object_or_404(Prestation, id=prestation_id)
            heure_debut = datetime.strptime(heure_str, '%H:%M').time()
            heure_fin_str = prest_data.get('heure_fin')
            heure_fin_obj = datetime.strptime(heure_fin_str, '%H:%M').time() if heure_fin_str else None

            # Gérer la séance de forfait (Klinic)
            seance_forfait  = None
            forfait_client  = None
            est_seance_forfait = False

            if seance_forfait_id:
                if '_' in str(seance_forfait_id):
                    forfait_id, numero = str(seance_forfait_id).split('_')
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
            options_objs = []
            quantites = {}
            if options_list:
                option_ids  = [o['option_id'] for o in options_list]
                options_objs = list(Option.objects.filter(id__in=option_ids))
                quantites   = {o['option_id']: int(o['quantite']) for o in options_list}
                for opt in options_objs:
                    qte = quantites.get(opt.id, 1)
                    prix_options += opt.prix * qte

            # Créer le RDV lié au groupe
            rdv = RendezVous.objects.create(
                institut=institut,
                client=client,
                employe=employe,
                prestation=prestation,
                famille=prestation.famille,
                date=date_rdv,
                heure_debut=heure_debut,
                heure_fin=heure_fin_obj,
                prix_base=prix_base,
                prix_options=prix_options,
                statut='planifie',
                cree_par=request.user.utilisateur,
                groupe=groupe,
                est_seance_forfait=est_seance_forfait,
                forfait=forfait_client,
                numero_seance=seance_forfait.numero if seance_forfait else None,
            )

            # Programmer la séance forfait
            if seance_forfait:
                seance_forfait.programmer(rdv)

            # Attacher les options
            for opt in options_objs:
                qte = quantites.get(opt.id, 1)
                RendezVousOption.objects.create(
                    rendez_vous=rdv,
                    option=opt,
                    prix_unitaire=opt.prix,
                    quantite=qte,
                    prix_total=opt.prix * qte,
                )

            rdvs_crees.append(rdv)

        # Mettre à jour les totaux du groupe
        groupe.recalculer_totaux()

        return JsonResponse({
            'success': True,
            'message': f'{len(rdvs_crees)} rendez-vous créé(s) avec succès',
            'nombre_rdv': len(rdvs_crees),
            'groupe_id': groupe.id,
            'rdv_ids': [rdv.id for rdv in rdvs_crees],
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


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
        'employe': rdv.employe.prenom or rdv.employe.nom,
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
        'remise_pourcent': rdv.remise_pourcent or 0,
        'statut': rdv.statut,
        'est_seance_forfait': rdv.est_seance_forfait,
        'groupe_id': rdv.groupe_id,
        'groupe_prix_total': float(rdv.groupe.prix_total) if rdv.groupe else None,
        'nombre_rdv_groupe': rdv.groupe.rendez_vous.exclude(statut__in=['annule', 'annule_client']).count() if rdv.groupe else 0,
        'options': [{'id': opt.option.id, 'nom': opt.option.nom, 'prix': float(opt.prix_unitaire), 'quantite': opt.quantite} for opt in options]
    }

    return JsonResponse(data)


@login_required
@role_required(['patron', 'manager'])
@institut_required
@require_POST
def api_rdv_ajouter_prestation(request, institut_code, rdv_id):
    """API : Ajouter une prestation à un RDV existant (même employé, lié au même groupe)"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv_existant = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    if rdv_existant.statut == 'valide':
        return JsonResponse({'success': False, 'message': 'Impossible de modifier un RDV déjà validé'}, status=400)

    try:
        data = json.loads(request.body)
        prestation_id     = data.get('prestation_id')
        heure_str         = data.get('heure_debut')
        prix_base         = Decimal(str(data.get('prix_base', 0)))
        options_list      = data.get('options', [])
        seance_forfait_id = data.get('seance_forfait_id')
        employe_id_param  = data.get('employe_id')

        if not prestation_id or not heure_str:
            return JsonResponse({'success': False, 'message': 'Prestation et heure requises'}, status=400)

        prestation  = get_object_or_404(Prestation, id=prestation_id)
        heure_debut = datetime.strptime(heure_str, '%H:%M').time()

        # Déterminer l'employé (peut être différent du RDV d'origine)
        if employe_id_param and str(employe_id_param) != str(rdv_existant.employe_id):
            employe = get_object_or_404(Employe, id=employe_id_param, institut=institut)
            # Vérifier conflit pour ce nouvel employé
            duree_min = prestation.duree_minutes if prestation.duree_minutes else (
                int(float(prestation.duree) * 60) if prestation.duree else 0
            )
            heure_fin_new = (datetime.combine(rdv_existant.date, heure_debut) + timedelta(
                minutes=duree_min
            )).time()
            conflits = RendezVous.objects.filter(
                institut=institut,
                employe=employe,
                date=rdv_existant.date,
                heure_debut__lt=heure_fin_new,
                heure_fin__gt=heure_debut,
            ).exclude(statut__in=['annule', 'annule_client', 'absent'])
            if conflits.exists():
                rdv_conflit = conflits.first()
                return JsonResponse({
                    'success': False,
                    'message': f'Conflit : {employe.prenom or employe.nom} a déjà un RDV ({rdv_conflit.client} - {rdv_conflit.heure_debut.strftime("%H:%M")})',
                }, status=400)
        else:
            employe = rdv_existant.employe

        # Gérer la séance de forfait
        seance_forfait  = None
        forfait_client  = None
        est_seance_forfait = False

        if seance_forfait_id:
            if '_' in str(seance_forfait_id):
                forfait_id, numero = str(seance_forfait_id).split('_')
                seance_forfait = get_object_or_404(
                    SeanceForfait,
                    forfait_id=forfait_id,
                    numero=int(numero),
                    forfait__client=rdv_existant.client,
                    forfait__institut=institut,
                    statut='disponible'
                )
            else:
                seance_forfait = get_object_or_404(
                    SeanceForfait,
                    id=seance_forfait_id,
                    forfait__client=rdv_existant.client,
                    forfait__institut=institut,
                    statut='disponible'
                )
            forfait_client = seance_forfait.forfait
            est_seance_forfait = True
            prix_base = Decimal('0')
            prestation = forfait_client.prestation

        # Créer ou récupérer le groupe
        groupe = rdv_existant.groupe
        if not groupe:
            groupe = GroupeRDV.objects.create(
                client=rdv_existant.client,
                institut=institut,
                date=rdv_existant.date,
                cree_par=request.user.utilisateur,
                nombre_rdv=1,
            )
            rdv_existant.groupe = groupe
            rdv_existant.save(update_fields=['groupe'])

        # Calculer le prix des options
        prix_options = Decimal('0')
        options_objs = []
        quantites = {}
        if options_list:
            option_ids  = [o['option_id'] for o in options_list]
            options_objs = list(Option.objects.filter(id__in=option_ids))
            quantites   = {o['option_id']: int(o['quantite']) for o in options_list}
            for opt in options_objs:
                prix_options += opt.prix * quantites.get(opt.id, 1)

        # Créer le nouveau RDV (même client, même date, même groupe, employé potentiellement différent)
        nouveau_rdv = RendezVous.objects.create(
            institut=institut,
            client=rdv_existant.client,
            employe=employe,
            prestation=prestation,
            famille=prestation.famille,
            date=rdv_existant.date,
            heure_debut=heure_debut,
            prix_base=prix_base,
            prix_options=prix_options,
            statut='planifie',
            cree_par=request.user.utilisateur,
            groupe=groupe,
            est_seance_forfait=est_seance_forfait,
            forfait=forfait_client,
            numero_seance=seance_forfait.numero if seance_forfait else None,
        )

        # Programmer la séance forfait
        if seance_forfait:
            seance_forfait.programmer(nouveau_rdv)

        # Attacher les options
        for opt in options_objs:
            qte = quantites.get(opt.id, 1)
            RendezVousOption.objects.create(
                rendez_vous=nouveau_rdv,
                option=opt,
                prix_unitaire=opt.prix,
                quantite=qte,
                prix_total=opt.prix * qte,
            )

        groupe.recalculer_totaux()

        # Durée personnalisée : s'applique uniquement au nouveau RDV (pas au groupe entier)
        # pour ne pas modifier l'affichage des autres RDVs du groupe
        duree_personnalisee = data.get('duree_personnalisee')
        if duree_personnalisee is not None:
            try:
                duree_int = int(duree_personnalisee)
                if duree_int > 0:
                    fin_custom = (datetime.combine(rdv_existant.date, heure_debut) + timedelta(minutes=duree_int)).time()
                    RendezVous.objects.filter(id=nouveau_rdv.id).update(heure_fin=fin_custom)
            except (ValueError, TypeError):
                pass

        message = f'Prestation "{prestation.nom}" ajoutée avec succès'
        if est_seance_forfait:
            message = f'Séance {seance_forfait.numero}/{forfait_client.nombre_seances_total} du forfait programmée'

        return JsonResponse({
            'success': True,
            'message': message,
            'rdv_id': nouveau_rdv.id,
            'groupe_id': groupe.id,
            'est_seance_forfait': est_seance_forfait,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@role_required(['patron', 'manager'])
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
        raison_modification = request.POST.get('raison_modification', '')

        # Récupérer les options avec leurs quantités
        import json
        options_data_str = request.POST.get('options_data', '[]')
        options_data = json.loads(options_data_str) if options_data_str else []

        # Sauvegarder l'ancien prix pour la traçabilité
        ancien_prix_base = rdv.prix_base
        ancien_prix_total = rdv.prix_total

        # Mettre à jour le RDV
        employe_id = request.POST.get('employe_id')
        if employe_id:
            rdv.employe = get_object_or_404(Employe, id=employe_id, institut=institut)
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
        if options_data:
            # options_data est une liste de dict: [{'id': '1', 'quantite': 2}, ...]
            option_ids = [opt['id'] for opt in options_data]
            options = Option.objects.filter(id__in=option_ids)
            # Créer un dict pour accès rapide aux quantités
            quantites = {str(opt['id']): int(opt['quantite']) for opt in options_data}
            for option in options:
                qte = quantites.get(str(option.id), 1)
                RendezVousOption.objects.create(
                    rendez_vous=rdv,
                    option=option,
                    prix_unitaire=option.prix,
                    quantite=qte,
                    prix_total=option.prix * qte
                )
                prix_options += option.prix * qte

        rdv.prix_options = prix_options

        # Si le prix a été modifié, marquer le RDV et créer un log
        if prix_modifie:
            if not rdv.prix_modifie:
                rdv.prix_original = ancien_prix_base
            rdv.prix_modifie = True
            rdv.raison_modification = raison_modification

        rdv.save()

        # Durée personnalisée : modifier heure_fin de CE RDV uniquement, sans toucher au groupe
        duree_personnalisee = request.POST.get('duree_personnalisee')
        if duree_personnalisee:
            try:
                duree_int = int(duree_personnalisee)
                if duree_int > 0:
                    fin_custom = (datetime.combine(rdv.date, rdv.heure_debut) + timedelta(minutes=duree_int)).time()
                    RendezVous.objects.filter(id=rdv.id).update(heure_fin=fin_custom)
            except (ValueError, TypeError):
                pass

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

        # Prix total groupe forcé manuellement
        groupe_prix_total = request.POST.get('groupe_prix_total')
        if groupe_prix_total and rdv.groupe:
            try:
                rdv.groupe.prix_total = int(Decimal(groupe_prix_total))
                rdv.groupe.save(update_fields=['prix_total'])
            except Exception:
                pass

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
@role_required(['patron', 'manager'])
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
@role_required(['patron', 'manager'])
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
                'employe': rdv.employe.prenom or rdv.employe.nom
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@role_required(['patron', 'manager'])
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
@role_required(['patron', 'manager'])
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
@role_required(['patron', 'manager'])
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

    if rdv.statut in ('absent', 'annule_client'):
        return JsonResponse({
            'success': False,
            'message': f'Impossible : ce rendez-vous est déjà {rdv.get_statut_display().lower()}'
        }, status=400)

    # RDV validé : vérifier qu'il n'est pas passé en clôture
    if rdv.statut == 'valide':
        # Utiliser la date du dernier paiement (= heure de validation réelle)
        from django.db.models import Max as DBMax
        last_paiement_date = rdv.paiements.aggregate(last=DBMax('date'))['last']
        if last_paiement_date is None:
            last_paiement_date = timezone.make_aware(datetime.combine(rdv.date, rdv.heure_debut))
        est_cloture = ClotureCaisse.objects.filter(
            institut=rdv.institut,
            date=rdv.date,
            cloture=True,
            date_cloture__gt=last_paiement_date
        ).exists()
        if est_cloture:
            return JsonResponse({
                'success': False,
                'message': 'Impossible : ce rendez-vous a déjà été comptabilisé dans une clôture de caisse'
            }, status=400)

    try:
        annuler_groupe = request.POST.get('annuler_groupe') == 'true'

        if annuler_groupe and rdv.groupe_id:
            # Annuler tous les RDVs du groupe (planifiés ou validés non-clôturés)
            rdvs_groupe = RendezVous.objects.filter(
                groupe_id=rdv.groupe_id,
                institut=institut,
            ).exclude(statut__in=['absent', 'annule_client'])
            nb = rdvs_groupe.count()
            rdvs_groupe.update(statut='annule_client')
            return JsonResponse({
                'success': True,
                'message': f'{nb} prestation(s) du groupe annulée(s)'
            })
        else:
            rdv.statut = 'annule_client'
            rdv.save()
            return JsonResponse({
                'success': True,
                'message': 'Rendez-vous annulé'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
def api_rdv_client_jour(request, institut_code, rdv_id):
    """API : Récupérer tous les RDV d'un client pour une journée donnée"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv_actuel = get_object_or_404(RendezVous, id=rdv_id, institut=institut)

    # Récupérer tous les RDV du même client pour la même journée (sauf annulés)
    rdvs_client = RendezVous.objects.filter(
        client=rdv_actuel.client,
        date=rdv_actuel.date,
        institut=institut
    ).exclude(
        statut__in=['annule', 'annule_client', 'valide']  # Exclure les annulés et déjà validés
    ).select_related('prestation', 'employe').prefetch_related('options_selectionnees__option')

    rdvs_data = []
    prix_total_global = 0

    for rdv in rdvs_client:
        options = rdv.options_selectionnees.select_related('option')
        rdv_data = {
            'id': rdv.id,
            'client': rdv.client.get_full_name(),
            'employe': rdv.employe.prenom or rdv.employe.nom,
            'prestation': rdv.prestation.nom,
            'heure_debut': rdv.heure_debut.strftime('%H:%M'),
            'heure_fin': rdv.heure_fin.strftime('%H:%M'),
            'prix_base': float(rdv.prix_base),
            'prix_options': float(rdv.prix_options),
            'prix_total': float(rdv.prix_total),
            'est_seance_forfait': rdv.est_seance_forfait,
            'options': [{'nom': opt.option.nom, 'prix': float(opt.prix_total)} for opt in options]
        }
        rdvs_data.append(rdv_data)
        prix_total_global += rdv.prix_total

    # Si tous les RDV ont un groupe avec un prix personnalisé, l'utiliser comme base
    groupe_prix_custom = None
    if rdvs_data:
        premier_rdv = rdvs_client.first()
        if premier_rdv and premier_rdv.groupe and premier_rdv.groupe.prix_total:
            groupe_prix_custom = float(premier_rdv.groupe.prix_total)

    return JsonResponse({
        'success': True,
        'rdvs': rdvs_data,
        'prix_total_global': groupe_prix_custom if groupe_prix_custom else float(prix_total_global),
        'client': rdv_actuel.client.get_full_name(),
        'date': rdv_actuel.date.strftime('%d/%m/%Y'),
        'nb_rdvs': len(rdvs_data)
    })


@login_required
@role_required(['patron', 'manager'])
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
        moyen_paiement_1 = request.POST.get('moyen_paiement_1', request.POST.get('moyen_paiement', 'especes'))

        # Remise
        remise_pourcent = max(0, min(99, int(request.POST.get('remise_pourcent', 0) or 0)))
        prix_effectif = math.ceil(rdv.prix_total * (100 - remise_pourcent) / 100 / 1000) * 1000
        rdv.remise_pourcent = remise_pourcent
        rdv.save()

        # Double paiement
        utilise_double_paiement = request.POST.get('utilise_double_paiement') == 'true'
        moyen_paiement_2 = request.POST.get('moyen_paiement_2', '')
        try:
            montant_paiement_2 = Decimal(request.POST.get('montant_paiement_2', '0') or '0')
        except (ValueError, InvalidOperation):
            montant_paiement_2 = Decimal('0')

        # 1. Traiter les cartes cadeaux sur le prix effectif (après remise)
        cartes_json = request.POST.get('cartes_cadeaux', '')
        montant_total_cartes = 0
        montant_restant_prix = prix_effectif
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
                    montant_restant_prix,
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
                    montant_restant_prix -= montant_a_utiliser

        # 2. Déterminer le montant cash (après déduction des cartes cadeaux)
        if type_paiement == 'complet':
            montant_restant = montant_restant_prix
        elif type_paiement == 'differe':
            montant_restant = 0
        else:  # partiel
            montant_paye = int(Decimal(request.POST.get('montant', 0)))
            montant_restant = min(montant_paye, montant_restant_prix)

        # 3. Créer le(s) paiement(s) pour le cash
        if utilise_double_paiement and montant_paiement_2 > 0:
            montant_paiement_1 = montant_restant - int(montant_paiement_2)
            if montant_paiement_1 > 0:
                Paiement.objects.create(
                    rendez_vous=rdv,
                    mode=moyen_paiement_1,
                    montant=montant_paiement_1,
                )
            if montant_paiement_2 > 0:
                Paiement.objects.create(
                    rendez_vous=rdv,
                    mode=moyen_paiement_2,
                    montant=int(montant_paiement_2),
                )
        else:
            if montant_restant > 0:
                Paiement.objects.create(
                    rendez_vous=rdv,
                    mode=moyen_paiement_1,
                    montant=montant_restant,
                )

        # 4. Si paiement partiel ou différé, créer un crédit
        montant_effectif = montant_total_cartes + montant_restant
        if montant_effectif < prix_effectif:
            Credit.objects.create(
                client=rdv.client,
                institut=institut,
                rendez_vous=rdv,
                montant_total=prix_effectif,
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
@role_required(['patron', 'manager'])
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
    ventes_cartes_especes = 0
    ventes_cartes_cb = 0
    ventes_cartes_cheque = 0
    ventes_cartes_om = 0
    ventes_cartes_wave = 0
    for _carte in ventes_cartes:
        _m1 = _carte.mode_paiement_achat
        _mt1 = _carte.montant_paiement_1 if _carte.montant_paiement_1 else _carte.montant_initial
        if _m1 == 'especes': ventes_cartes_especes += _mt1
        elif _m1 == 'carte': ventes_cartes_cb += _mt1
        elif _m1 == 'cheque': ventes_cartes_cheque += _mt1
        elif _m1 == 'om': ventes_cartes_om += _mt1
        elif _m1 == 'wave': ventes_cartes_wave += _mt1
        if _carte.moyen_paiement_2 and _carte.montant_paiement_2:
            _m2 = _carte.moyen_paiement_2
            _mt2 = _carte.montant_paiement_2
            if _m2 == 'especes': ventes_cartes_especes += _mt2
            elif _m2 == 'carte': ventes_cartes_cb += _mt2
            elif _m2 == 'cheque': ventes_cartes_cheque += _mt2
            elif _m2 == 'om': ventes_cartes_om += _mt2
            elif _m2 == 'wave': ventes_cartes_wave += _mt2

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
    totaux_clotures = clotures_existantes.aggregate(
        especes=models.Sum('total_especes_calcule'),
        carte=models.Sum('total_carte_calcule'),
        cheque=models.Sum('total_cheque_calcule'),
        om=models.Sum('total_om_calcule'),
        wave=models.Sum('total_wave_calcule'),
    )
    total_jour = (
        (totaux_clotures['especes'] or 0) + total_especes_encours
        + (totaux_clotures['carte'] or 0) + total_carte_encours
        + (totaux_clotures['cheque'] or 0) + total_cheque_encours
        + (totaux_clotures['om'] or 0) + total_om_encours
        + (totaux_clotures['wave'] or 0) + total_wave_encours
    )
    total_jour_especes = (totaux_clotures['especes'] or 0) + total_especes_encours
    total_jour_carte = (totaux_clotures['carte'] or 0) + total_carte_encours

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

    # Dépenses en espèces depuis la dernière clôture (ou début de journée)
    depenses_especes = Depense.objects.filter(
        institut=institut,
        date=date_selectionnee,
        mode_paiement='especes',
        date_creation__gte=heure_debut
    ).aggregate(total=models.Sum('montant'))['total'] or 0

    # Sorties de stock depuis la dernière clôture (quantité × prix_achat produit)
    sorties_stock_qs = MouvementStock.objects.filter(
        institut=institut,
        type_mouvement='sortie',
        date_creation__date=date_selectionnee,
        date_creation__gte=heure_debut
    ).select_related('produit')
    total_sorties_stock = sum(m.quantite * m.produit.prix_achat for m in sorties_stock_qs)

    # Montant espèces attendu = total espèces en cours - dépenses espèces - sorties stock + fond de caisse
    montant_attendu = total_especes_encours - depenses_especes - total_sorties_stock + institut.fond_caisse

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
        'depenses_especes': depenses_especes,
        'total_sorties_stock': total_sorties_stock,
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
@role_required(['patron', 'manager'])
@institut_required
@require_POST
def api_cloturer_caisse(request, institut_code):
    """API : Valider la clôture de caisse - supporte plusieurs clôtures par jour"""
    from django.db import models

    institut = get_object_or_404(Institut, code=institut_code)

    try:
        date_str = request.POST.get('date')
        montant_reel = request.POST.get('montant_reel')
        montant_retrait = max(0, int(request.POST.get('montant_retrait', 0) or 0))

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

        total_cheque_rdv = paiements_rdv.filter(mode='cheque').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        total_om_rdv = paiements_rdv.filter(mode='om').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        total_wave_rdv = paiements_rdv.filter(mode='wave').aggregate(
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

        total_cheque_credit = paiements_credit.filter(mode='cheque').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        total_om_credit = paiements_credit.filter(mode='om').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        total_wave_credit = paiements_credit.filter(mode='wave').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        # Ventes de cartes cadeaux depuis la dernière clôture
        ventes_cartes = CarteCadeau.objects.filter(
            institut_achat=institut,
            date_achat__date=date_cloture,
            date_achat__gte=heure_debut,
        )
        ventes_cartes_par_mode = {'especes': 0, 'carte': 0, 'cheque': 0, 'om': 0, 'wave': 0}
        for carte in ventes_cartes:
            mode1 = carte.mode_paiement_achat
            montant1 = carte.montant_paiement_1 if carte.montant_paiement_1 else carte.montant_initial
            ventes_cartes_par_mode[mode1] += montant1
            if carte.moyen_paiement_2 and carte.montant_paiement_2:
                ventes_cartes_par_mode[carte.moyen_paiement_2] += carte.montant_paiement_2

        total_especes = total_especes_rdv + total_especes_credit + ventes_cartes_par_mode['especes']
        total_carte = total_carte_rdv + total_carte_credit + ventes_cartes_par_mode['carte']
        total_cheque = total_cheque_rdv + total_cheque_credit + ventes_cartes_par_mode['cheque']
        total_om = total_om_rdv + total_om_credit + ventes_cartes_par_mode['om']
        total_wave = total_wave_rdv + total_wave_credit + ventes_cartes_par_mode['wave']

        # Valider le retrait : ne peut pas laisser moins de 30 000 CFA dans la caisse
        # On se base sur le montant réel saisi, pas le calculé
        fond_caisse_min = 30000
        especes_disponibles_retrait = max(0, int(montant_reel) - fond_caisse_min)
        if montant_retrait > especes_disponibles_retrait:
            return JsonResponse({
                'success': False,
                'message': f'Le retrait ne peut pas dépasser {especes_disponibles_retrait:,} CFA (fond de caisse minimum de 30 000 CFA conservé)'
            }, status=400)

        # Créer une NOUVELLE clôture (plus de get_or_create)
        cloture = ClotureCaisse.objects.create(
            institut=institut,
            date=date_cloture,
            fond_caisse=institut.fond_caisse,
            montant_reel_especes=int(montant_reel),
            total_especes_calcule=total_especes,
            total_carte_calcule=total_carte,
            total_cheque_calcule=total_cheque,
            total_om_calcule=total_om,
            total_wave_calcule=total_wave,
            total_calcule=total_especes + total_carte + total_cheque + total_om + total_wave,
            montant_retrait=montant_retrait,
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
@role_required(['patron', 'manager'])
@institut_required
@require_POST
def api_groupe_modifier(request, institut_code, groupe_id):
    """API : Modifier l'heure de début et/ou la durée personnalisée d'un groupe de RDVs"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    groupe   = get_object_or_404(GroupeRDV, id=groupe_id, institut=institut)

    try:
        data = json.loads(request.body)
        nouvelle_heure_str   = data.get('heure_debut')
        duree_personnalisee  = data.get('duree_personnalisee')

        rdvs_actifs = list(
            RendezVous.objects.filter(groupe=groupe)
            .exclude(statut__in=['annule', 'annule_client', 'absent'])
            .order_by('heure_debut')
        )

        if not rdvs_actifs:
            return JsonResponse({'success': False, 'message': 'Aucun RDV actif dans ce groupe'}, status=400)

        # --- Mises à jour individuelles par RDV (heure_debut + heure_fin + prestation) ---
        rdv_mises_a_jour = data.get('rdv_mises_a_jour', [])
        for item in rdv_mises_a_jour:
            try:
                rdv_obj = RendezVous.objects.get(id=item['id'], groupe=groupe)
                rdv_obj.heure_debut = datetime.strptime(item['heure_debut'], '%H:%M').time()
                rdv_obj.heure_fin   = datetime.strptime(item['heure_fin'],   '%H:%M').time()
                date_str_item = item.get('date')
                if date_str_item:
                    rdv_obj.date = datetime.strptime(date_str_item, '%Y-%m-%d').date()
                employe_id = item.get('employe_id')
                if employe_id:
                    from core.models import Employe as _Employe
                    try:
                        rdv_obj.employe = _Employe.objects.get(id=employe_id, institut=institut)
                    except _Employe.DoesNotExist:
                        pass
                prestation_id = item.get('prestation_id')
                if prestation_id:
                    from core.models import Prestation as _Prestation
                    new_prest = _Prestation.objects.get(id=prestation_id, famille__institut=institut)
                    rdv_obj.prestation = new_prest
                    rdv_obj.famille = new_prest.famille
                    prix_base_val = item.get('prix_base')
                    rdv_obj.prix_base = int(Decimal(str(prix_base_val))) if prix_base_val is not None else int(new_prest.prix)
                    rdv_obj.prix_total = rdv_obj.prix_base + rdv_obj.prix_options
                rdv_obj.save()
            except (RendezVous.DoesNotExist, KeyError, ValueError):
                pass

        # --- Prix total groupe forcé ---
        groupe_prix_total = data.get('groupe_prix_total')
        if groupe_prix_total is not None:
            try:
                groupe.prix_total = int(Decimal(str(groupe_prix_total)))
                groupe.save(update_fields=['prix_total'])
            except Exception:
                pass

        # --- Décaler l'heure de début de tous les RDVs (compatibilité ancienne API) ---
        if nouvelle_heure_str and not rdv_mises_a_jour:
            nouvelle_heure = datetime.strptime(nouvelle_heure_str, '%H:%M').time()
            ancienne_heure = rdvs_actifs[0].heure_debut
            decalage_min = int(
                (datetime.combine(date.today(), nouvelle_heure) -
                 datetime.combine(date.today(), ancienne_heure)).total_seconds() / 60
            )
            if decalage_min != 0:
                for rdv_obj in rdvs_actifs:
                    nouvelle_dt = datetime.combine(date.today(), rdv_obj.heure_debut) + timedelta(minutes=decalage_min)
                    rdv_obj.heure_debut = nouvelle_dt.time()
                    rdv_obj.save(update_fields=['heure_debut'])

        # --- Durée personnalisée (compatibilité ancienne API) ---
        if duree_personnalisee is not None and not rdv_mises_a_jour:
            try:
                duree_int = int(duree_personnalisee)
                groupe.duree_personnalisee = duree_int if duree_int > 0 else None
                groupe.save(update_fields=['duree_personnalisee'])
            except (ValueError, TypeError):
                pass

        return JsonResponse({'success': True, 'message': 'Groupe modifié avec succès'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


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
@role_required(['patron', 'manager'])
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

        # Double paiement
        utilise_double_paiement = request.POST.get('utilise_double_paiement') == 'true'
        moyen_paiement_1 = request.POST.get('moyen_paiement_1', mode_paiement)
        moyen_paiement_2 = request.POST.get('moyen_paiement_2', '')

        try:
            montant_paiement_1_str = request.POST.get('montant_paiement_1', '0')
            montant_paiement_1 = Decimal(montant_paiement_1_str) if montant_paiement_1_str else Decimal('0')
        except (ValueError, InvalidOperation):
            montant_paiement_1 = Decimal('0')

        try:
            montant_paiement_2_str = request.POST.get('montant_paiement_2', '0')
            montant_paiement_2 = Decimal(montant_paiement_2_str) if montant_paiement_2_str else Decimal('0')
        except (ValueError, InvalidOperation):
            montant_paiement_2 = Decimal('0')

        # Validation
        client = get_object_or_404(Client, id=client_id)
        prestation = get_object_or_404(Prestation, id=prestation_id, est_forfait=True)

        prix_forfait = prestation.prix
        utilisateur = request.user.utilisateur

        # Créer le forfait client (utiliser comme RDV fictif pour les paiements)
        from datetime import date, datetime
        rdv_forfait = RendezVous.objects.create(
            institut=institut,
            client=client,
            employe=institut.employes.first(),
            prestation=prestation,
            famille=prestation.famille,
            date=date.today(),
            heure_debut=datetime.now().time(),
            heure_fin=datetime.now().time(),
            prix_base=prix_forfait,
            prix_options=0,
            prix_total=prix_forfait,
            statut='valide',
            cree_par=utilisateur,
            valide_par=utilisateur,
            est_seance_forfait=False,
        )

        # 1. Traiter les cartes cadeaux sur le prix total
        cartes_json = request.POST.get('cartes_cadeaux', '')
        montant_total_cartes = 0
        montant_restant_prix = int(prix_forfait)
        if cartes_json:
            cartes_data = json.loads(cartes_json)
            for carte_item in cartes_data:
                carte = CarteCadeau.objects.get(
                    id=carte_item['carte_id'],
                    beneficiaire=client,
                    statut='active',
                )
                montant_a_utiliser = min(
                    int(carte_item['montant']),
                    carte.solde,
                    montant_restant_prix,
                )
                if montant_a_utiliser > 0:
                    utilisation = UtilisationCarteCadeau.objects.create(
                        carte=carte,
                        rendez_vous=rdv_forfait,
                        montant=montant_a_utiliser,
                        institut=institut,
                        enregistre_par=utilisateur,
                    )
                    carte.utiliser(montant_a_utiliser)
                    Paiement.objects.create(
                        rendez_vous=rdv_forfait,
                        mode='carte_cadeau',
                        montant=montant_a_utiliser,
                        utilisation_carte_cadeau=utilisation,
                    )
                    montant_total_cartes += montant_a_utiliser
                    montant_restant_prix -= montant_a_utiliser

        # 2. Déterminer le montant cash
        if type_paiement == 'complet':
            montant_restant = montant_restant_prix
        elif type_paiement == 'differe':
            montant_restant = 0
        else:  # partiel
            montant_restant = min(int(montant_paye), montant_restant_prix)

        montant_effectif = montant_total_cartes + montant_restant

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

        # 3. Créer les paiements cash
        if montant_restant > 0:
            if utilise_double_paiement and montant_paiement_2 > 0:
                montant_cash_1 = montant_restant - int(montant_paiement_2)
                if montant_cash_1 > 0:
                    Paiement.objects.create(
                        rendez_vous=rdv_forfait,
                        mode=moyen_paiement_1,
                        montant=montant_cash_1,
                    )
                if montant_paiement_2 > 0:
                    Paiement.objects.create(
                        rendez_vous=rdv_forfait,
                        mode=moyen_paiement_2,
                        montant=int(montant_paiement_2),
                    )
            else:
                Paiement.objects.create(
                    rendez_vous=rdv_forfait,
                    mode=moyen_paiement_1,
                    montant=montant_restant,
                )

        # 4. Si paiement partiel ou différé, créer un crédit
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
@role_required(['patron', 'manager'])
@institut_required
@require_POST
def api_rdv_valider_groupe(request, institut_code):
    """API : Valider plusieurs rendez-vous d'un même client en une seule fois"""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)

    try:
        # Récupérer la liste des IDs de RDV à valider
        rdv_ids = request.POST.getlist('rdv_ids[]')
        if not rdv_ids:
            return JsonResponse({
                'success': False,
                'message': 'Aucun rendez-vous à valider'
            }, status=400)

        # Récupérer les données de paiement
        type_paiement = request.POST.get('type_paiement', 'complet')
        moyen_paiement_1 = request.POST.get('moyen_paiement_1', 'especes')

        # Convertir les montants en Decimal de manière sécurisée
        try:
            montant_paiement_1_str = request.POST.get('montant_paiement_1', '0')
            montant_paiement_1 = Decimal(montant_paiement_1_str) if montant_paiement_1_str else Decimal('0')
        except (ValueError, InvalidOperation):
            montant_paiement_1 = Decimal('0')

        # Paiement avec 2 moyens
        utilise_double_paiement = request.POST.get('utilise_double_paiement') == 'true'
        moyen_paiement_2 = request.POST.get('moyen_paiement_2', '')

        try:
            montant_paiement_2_str = request.POST.get('montant_paiement_2', '0')
            montant_paiement_2 = Decimal(montant_paiement_2_str) if montant_paiement_2_str else Decimal('0')
        except (ValueError, InvalidOperation):
            montant_paiement_2 = Decimal('0')

        # Cartes cadeaux
        cartes_json = request.POST.get('cartes_cadeaux', '')

        # Récupérer tous les RDV à valider
        rdvs = RendezVous.objects.filter(
            id__in=rdv_ids,
            institut=institut
        ).exclude(statut='valide')

        if not rdvs.exists():
            return JsonResponse({
                'success': False,
                'message': 'Aucun rendez-vous trouvé'
            }, status=400)

        # Vérifier que tous les RDV sont du même client
        clients = set(rdv.client_id for rdv in rdvs)
        if len(clients) > 1:
            return JsonResponse({
                'success': False,
                'message': 'Tous les rendez-vous doivent être du même client'
            }, status=400)

        client = rdvs.first().client
        utilisateur = request.user.utilisateur

        # Calculer le prix total de tous les RDV (pour la répartition proportionnelle)
        prix_total_global = sum(rdv.prix_total for rdv in rdvs)

        # Utiliser le prix personnalisé du groupe si défini (pour la base de calcul du montant total)
        premier_rdv = rdvs.first()
        groupe_obj = premier_rdv.groupe if premier_rdv else None
        prix_base_global = float(groupe_obj.prix_total) if (groupe_obj and groupe_obj.prix_total) else prix_total_global

        # Remise globale sur le groupe
        remise_pourcent = max(0, min(99, int(request.POST.get('remise_pourcent', 0) or 0)))
        prix_effectif_global = math.ceil(prix_base_global * (100 - remise_pourcent) / 100 / 1000) * 1000

        # 1. Traiter les cartes cadeaux sur le prix effectif (après remise)
        montant_total_cartes = 0
        montant_restant_prix = prix_effectif_global
        if cartes_json:
            cartes_data = json.loads(cartes_json)
            for carte_item in cartes_data:
                carte = CarteCadeau.objects.get(
                    id=carte_item['carte_id'],
                    beneficiaire=client,
                    statut='active',
                )
                montant_a_utiliser = min(
                    int(carte_item['montant']),
                    carte.solde,
                    montant_restant_prix,
                )
                if montant_a_utiliser > 0:
                    # Créer une utilisation pour chaque RDV proportionnellement
                    rdvs_list = list(rdvs)
                    total_carte_distribue = 0
                    for idx_carte, rdv in enumerate(rdvs_list):
                        if idx_carte == len(rdvs_list) - 1:
                            # Dernier RDV : attribuer le reste pour éviter les erreurs d'arrondi
                            montant_rdv = montant_a_utiliser - total_carte_distribue
                        else:
                            proportion = Decimal(str(rdv.prix_total)) / Decimal(str(prix_total_global))
                            montant_rdv = int(montant_a_utiliser * proportion)
                        if montant_rdv > 0:
                            utilisation = UtilisationCarteCadeau.objects.create(
                                carte=carte,
                                rendez_vous=rdv,
                                montant=montant_rdv,
                                institut=institut,
                                enregistre_par=utilisateur,
                            )
                            Paiement.objects.create(
                                rendez_vous=rdv,
                                mode='carte_cadeau',
                                montant=montant_rdv,
                                utilisation_carte_cadeau=utilisation,
                            )
                            total_carte_distribue += montant_rdv
                    carte.utiliser(montant_a_utiliser)
                    montant_total_cartes += montant_a_utiliser
                    montant_restant_prix -= montant_a_utiliser

        # Déterminer le montant cash (après déduction des cartes cadeaux)
        if type_paiement == 'complet':
            montant_cash_total = montant_restant_prix
        elif type_paiement == 'differe':
            montant_cash_total = 0
        else:  # partiel
            montant_cash_total = min(int(montant_paiement_1 + montant_paiement_2), montant_restant_prix)

        # 2. Valider chaque RDV et créer les paiements
        # Filtrer les RDV non-forfait pour la répartition proportionnelle
        rdvs_normaux = [rdv for rdv in rdvs if not rdv.est_seance_forfait]
        total_distribue_1 = 0
        total_distribue_2 = 0

        for idx, rdv in enumerate(rdvs):
            rdv.statut = 'valide'
            rdv.remise_pourcent = remise_pourcent
            rdv.save()

            # Si c'est une séance de forfait, la marquer comme effectuée
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

                # ✅ CORRECTION : Payer les options si présentes (non incluses dans le forfait)
                if rdv.prix_options > 0 and prix_total_global > 0:
                    if montant_paiement_1 > 0:
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

            # Dernier RDV normal : attribuer le reste pour éviter les erreurs d'arrondi
            est_dernier = (rdv == rdvs_normaux[-1])

            # Créer les paiements proportionnels
            if montant_paiement_1 > 0:
                if est_dernier:
                    montant_rdv_1 = int(montant_paiement_1) - total_distribue_1
                else:
                    proportion = Decimal(str(rdv.prix_total)) / Decimal(str(prix_total_global))
                    montant_rdv_1 = int(montant_paiement_1 * proportion)
                if montant_rdv_1 > 0:
                    Paiement.objects.create(
                        rendez_vous=rdv,
                        mode=moyen_paiement_1,
                        montant=montant_rdv_1,
                    )
                    total_distribue_1 += montant_rdv_1

            if utilise_double_paiement and montant_paiement_2 > 0:
                if est_dernier:
                    montant_rdv_2 = int(montant_paiement_2) - total_distribue_2
                else:
                    proportion = Decimal(str(rdv.prix_total)) / Decimal(str(prix_total_global))
                    montant_rdv_2 = int(montant_paiement_2 * proportion)
                if montant_rdv_2 > 0:
                    Paiement.objects.create(
                        rendez_vous=rdv,
                        mode=moyen_paiement_2,
                        montant=montant_rdv_2,
                    )
                    total_distribue_2 += montant_rdv_2

        # 3. Si paiement partiel ou différé, créer un crédit global
        montant_effectif = montant_total_cartes + montant_cash_total
        if montant_effectif < prix_effectif_global:
            # Créer la description avec la liste des prestations
            prestations_liste = ", ".join([rdv.prestation.nom for rdv in rdvs])
            Credit.objects.create(
                client=client,
                institut=institut,
                montant_total=prix_effectif_global,
                montant_paye=int(montant_effectif),
                description=f"Groupe de {len(rdvs)} prestations - {prestations_liste}",
            )

        return JsonResponse({
            'success': True,
            'message': f'{len(rdvs)} rendez-vous validés avec succès',
            'nb_rdvs': len(rdvs)
        })

    except CarteCadeau.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Carte cadeau non trouvée ou non valide'
        }, status=400)
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


@login_required
@role_required(['patron', 'manager'])
@institut_required
def page_rappels(request, institut_code):
    """Page de rappels : affiche les RDVs du lendemain groupés par employé."""
    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)

    demain = date.today() + timedelta(days=1)

    employes = Employe.objects.filter(
        institut=institut,
        actif=True
    ).order_by('ordre_affichage', 'nom')

    rdvs_demain = RendezVous.objects.filter(
        institut=institut,
        date=demain,
    ).exclude(
        statut__in=['annule', 'annule_client']
    ).select_related('client', 'employe', 'prestation').order_by('employe__ordre_affichage', 'heure_debut')

    # Grouper par employé, en dédupliquant les groupes
    # On passe une liste de dicts pour éviter les attributs underscore inaccessibles en template
    rdvs_par_employe = {}
    for employe in employes:
        rdvs_employe_bruts = [rdv for rdv in rdvs_demain if rdv.employe_id == employe.id]
        items_employe = []
        groupes_vus = set()

        for rdv in rdvs_employe_bruts:
            if rdv.groupe_id:
                if rdv.groupe_id in groupes_vus:
                    # Déjà traité → ignorer
                    continue
                groupes_vus.add(rdv.groupe_id)
                # Récupérer toutes les prestations du groupe pour cet employé
                rdvs_du_groupe = [r for r in rdvs_employe_bruts if r.groupe_id == rdv.groupe_id]
                prestations_groupe = ', '.join(r.prestation.nom for r in rdvs_du_groupe)
                items_employe.append({
                    'rdv': rdv,
                    'prestations_groupe': prestations_groupe,
                    'nb_prestations': len(rdvs_du_groupe),
                    'rappel_envoye': rdv.rappel_envoye,
                })
            else:
                items_employe.append({
                    'rdv': rdv,
                    'prestations_groupe': None,
                    'nb_prestations': 1,
                    'rappel_envoye': rdv.rappel_envoye,
                })

        if items_employe:
            rdvs_par_employe[employe] = items_employe

    return render(request, 'agenda/rappels.html', {
        'institut': institut,
        'demain': demain,
        'rdvs_par_employe': rdvs_par_employe,
    })


@login_required
@role_required(['patron', 'manager'])
@institut_required
def api_rdv_whatsapp_rappel(request, institut_code, rdv_id):
    """API : Génère un lien WhatsApp de rappel RDV pour le lendemain."""
    from core.utils import generer_lien_whatsapp

    institut = get_object_or_404(Institut, code=institut_code, a_agenda=True)
    rdv = get_object_or_404(
        RendezVous.objects.select_related('client', 'prestation', 'employe'),
        id=rdv_id,
        institut=institut
    )

    telephone = rdv.client.telephone
    prenom = rdv.client.prenom
    heure = rdv.heure_debut.strftime('%Hh%M')

    # Si le RDV fait partie d'un groupe, lister toutes les prestations
    if rdv.groupe_id:
        rdvs_groupe = RendezVous.objects.filter(
            groupe_id=rdv.groupe_id
        ).exclude(
            statut__in=['annule', 'annule_client']
        ).select_related('prestation').order_by('heure_debut')
        prestations_str = ', '.join(r.prestation.nom for r in rdvs_groupe)
    else:
        prestations_str = rdv.prestation.nom

    message = (
        f"Bonjour {prenom},\n\n"
        f"Nous vous rappelons votre rendez-vous demain au {institut.nom} :\n\n"
        f"- Heure : {heure}\n"
        f"- Prestation(s) : {prestations_str}\n\n"
        f"Nous avons hâte de vous accueillir.\n\n"
        f"En cas d'empêchement, merci de nous prévenir à l'avance.\n"
        f"À demain !"
    )

    lien = generer_lien_whatsapp(telephone, message)
    if not lien:
        return JsonResponse({
            'success': False,
            'message': f'Numéro de téléphone invalide pour {rdv.client.get_full_name()}'
        })

    rdv.rappel_envoye = True
    rdv.save(update_fields=['rappel_envoye'])

    return JsonResponse({'success': True, 'lien': lien})
