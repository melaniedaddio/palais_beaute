from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, date, time
from decimal import Decimal
import json

from core.decorators import role_required
from core.models import (
    Institut, Employe, Client, Prestation, FamillePrestation,
    RendezVous, VenteExpressPrestation, Paiement, Credit, ClotureCaisse,
    PaiementCredit, CarteCadeau, UtilisationCarteCadeau
)


@login_required
@role_required(['patron', 'manager'])
def index(request):
    """Vue principale de la caisse Express"""
    # Récupérer l'institut Express
    institut = get_object_or_404(Institut, code='express')

    # Vérifier que l'utilisateur a accès (patron ou manager express)
    utilisateur = request.user.utilisateur
    if utilisateur.is_manager() and utilisateur.institut != institut:
        from django.contrib import messages
        messages.error(request, "Vous n'avez pas accès à Express")
        return redirect('core:login')

    # Date sélectionnée (par défaut aujourd'hui)
    date_str = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        date_selectionnee = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        date_selectionnee = date.today()

    # Récupérer les employés Express
    employes = Employe.objects.filter(
        institut=institut,
        actif=True
    ).order_by('ordre_affichage', 'nom')

    # Récupérer les familles de prestations Express
    familles = FamillePrestation.objects.filter(
        institut=institut
    ).prefetch_related('prestations').order_by('ordre_affichage', 'nom')

    # Récupérer les ventes du jour
    ventes = RendezVous.objects.filter(
        institut=institut,
        date=date_selectionnee,
        statut='valide'
    ).select_related('client', 'employe').prefetch_related(
        'prestations_express__prestation', 'paiements'
    ).order_by('-date_creation')

    # Calculer les totaux du jour
    totaux = ventes.aggregate(
        total=Sum('prix_total')
    )

    paiements_especes = Paiement.objects.filter(
        rendez_vous__in=ventes,
        mode='especes'
    ).aggregate(Sum('montant'))['montant__sum'] or 0

    paiements_carte = Paiement.objects.filter(
        rendez_vous__in=ventes,
        mode='carte'
    ).aggregate(Sum('montant'))['montant__sum'] or 0

    # Préparer les données des ventes pour l'affichage
    ventes_list = []
    for vente in ventes:
        # Récupérer les prestations de cette vente
        prestations_list = []
        for vep in vente.prestations_express.all():
            prestations_list.append({
                'nom': vep.prestation.nom,
                'quantite': vep.quantite,
                'prix': vep.prix_total
            })

        # Récupérer le mode de paiement
        paiement = vente.paiements.first()
        mode_paiement = paiement.mode if paiement else 'non_paye'

        ventes_list.append({
            'id': vente.id,
            'heure': vente.date_creation.strftime('%H:%M'),
            'client': vente.client.get_full_name(),
            'employe': vente.employe.nom,
            'prestations': prestations_list,
            'total': vente.prix_total,
            'mode': mode_paiement
        })

    # Vérifier si la caisse est clôturée pour ce jour
    caisse_cloturee = ClotureCaisse.objects.filter(
        institut=institut,
        date=date_selectionnee,
        cloture=True
    ).exists()

    # CA encaissé : paiements RDV + crédits encaissés ce jour
    # Exclure carte_cadeau (déjà compté lors de la vente de la carte)
    ca_paiements_rdv = Paiement.objects.filter(
        rendez_vous__in=ventes
    ).exclude(mode__in=['carte_cadeau', 'forfait', 'offert']).aggregate(total=Sum('montant'))['total'] or 0

    credits_encaisses = PaiementCredit.objects.filter(
        credit__institut=institut,
        date__date=date_selectionnee
    ).aggregate(total=Sum('montant'))['total'] or 0

    ca_encaisse = ca_paiements_rdv + credits_encaisses

    context = {
        'institut': institut,
        'date_selectionnee': date_selectionnee,
        'employes': employes,
        'familles': familles,
        'ventes': ventes_list,
        'total_jour': totaux['total'] or 0,
        'total_especes': paiements_especes,
        'total_carte': paiements_carte,
        'ca_encaisse': ca_encaisse,
        'credits_encaisses': credits_encaisses,
        'caisse_cloturee': caisse_cloturee,
    }

    return render(request, 'express/express.html', context)


@login_required
@require_POST
def creer_vente(request):
    """Créer une nouvelle vente Express"""
    try:
        institut = get_object_or_404(Institut, code='express')

        # Récupérer les données
        client_id = request.POST.get('client_id')
        employe_id = request.POST.get('employe_id')
        prestations_data = json.loads(request.POST.get('prestations', '[]'))
        type_paiement = request.POST.get('type_paiement', 'complet')
        moyen_paiement = request.POST.get('moyen_paiement', 'especes')
        montant_paye = request.POST.get('montant_paye', 0)

        # Validation
        if not client_id or not employe_id or not prestations_data:
            return JsonResponse({
                'success': False,
                'message': 'Données incomplètes'
            }, status=400)

        client = get_object_or_404(Client, id=client_id)
        employe = get_object_or_404(Employe, id=employe_id, institut=institut)

        # Calculer le prix total
        prix_total = 0
        for prest_data in prestations_data:
            prestation = get_object_or_404(Prestation, id=prest_data['id'])
            quantite = int(prest_data.get('quantite', 1))
            prix_total += prestation.prix * quantite

        # Créer le RDV (utilisé comme vente Express)
        # On met une prestation fictive (la première) juste pour respecter le schéma
        premiere_prestation = get_object_or_404(Prestation, id=prestations_data[0]['id'])

        rdv = RendezVous.objects.create(
            institut=institut,
            client=client,
            employe=employe,
            prestation=premiere_prestation,
            famille=premiere_prestation.famille,
            date=date.today(),
            heure_debut=datetime.now().time(),
            heure_fin=datetime.now().time(),
            prix_base=prix_total,
            prix_options=0,
            prix_total=prix_total,
            statut='valide',  # Direct validé pour Express
            cree_par=request.user.utilisateur,
            valide_par=request.user.utilisateur
        )

        # Ajouter toutes les prestations
        for prest_data in prestations_data:
            prestation = get_object_or_404(Prestation, id=prest_data['id'])
            quantite = int(prest_data.get('quantite', 1))

            VenteExpressPrestation.objects.create(
                rendez_vous=rdv,
                prestation=prestation,
                quantite=quantite,
                prix_unitaire=prestation.prix
            )

        # Gestion du paiement
        if type_paiement == 'complet':
            montant_paye = prix_total
        elif type_paiement == 'differe':
            montant_paye = Decimal('0')
        else:  # partiel
            montant_paye = Decimal(montant_paye)

        montant_restant = int(montant_paye)

        # 1. Traiter les cartes cadeaux si présentes (comme dans l'agenda)
        cartes_json = request.POST.get('cartes_cadeaux', '')
        montant_total_cartes = 0
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
                    montant_restant,
                )
                if montant_a_utiliser > 0:
                    utilisation = UtilisationCarteCadeau.objects.create(
                        carte=carte,
                        rendez_vous=rdv,
                        montant=montant_a_utiliser,
                        institut=institut,
                        enregistre_par=request.user.utilisateur,
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

        # 2. Créer le paiement pour le reste (espèces/carte bancaire/etc.)
        if montant_restant > 0:
            Paiement.objects.create(
                rendez_vous=rdv,
                mode=moyen_paiement,
                montant=montant_restant,
            )

        # 3. Si paiement partiel ou différé, créer un crédit
        montant_effectif = montant_total_cartes + montant_restant
        if montant_effectif < prix_total:
            description = ", ".join([p['nom'] for p in prestations_data])
            if len(description) > 200:
                description = description[:197] + "..."

            Credit.objects.create(
                client=client,
                institut=institut,
                rendez_vous=rdv,
                montant_total=int(prix_total),
                montant_paye=int(montant_effectif),
                description=description
            )

        return JsonResponse({
            'success': True,
            'message': 'Vente enregistrée avec succès',
            'vente_id': rdv.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@role_required(['patron', 'manager'])
def cloture_caisse(request):
    """Vue de clôture de caisse journalière pour Express - supporte plusieurs clôtures par jour"""
    from django.db import models

    institut = get_object_or_404(Institut, code='express')

    # Vérifier l'accès
    utilisateur = request.user.utilisateur
    if utilisateur.is_manager() and utilisateur.institut != institut:
        from django.contrib import messages
        messages.error(request, "Vous n'avez pas accès à Express")
        return redirect('core:login')

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

    # Déterminer l'heure de début pour le calcul (avec timezone)
    if derniere_cloture and derniere_cloture.date_cloture:
        heure_debut = derniere_cloture.date_cloture
    else:
        heure_debut = timezone.make_aware(datetime.combine(date_selectionnee, datetime.min.time()))

    # Calculer les totaux depuis la dernière clôture
    paiements_ventes = Paiement.objects.filter(
        rendez_vous__institut=institut,
        rendez_vous__date=date_selectionnee,
        rendez_vous__statut='valide',
        date__gte=heure_debut
    )

    total_especes_ventes = paiements_ventes.filter(mode='especes').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_carte_ventes = paiements_ventes.filter(mode='carte').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_cheque_ventes = paiements_ventes.filter(mode='cheque').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_om_ventes = paiements_ventes.filter(mode='om').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    total_wave_ventes = paiements_ventes.filter(mode='wave').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    # Paiements par carte cadeau (prestations)
    total_carte_cadeau_prestations = paiements_ventes.filter(mode='carte_cadeau').aggregate(
        total=models.Sum('montant')
    )['total'] or 0

    # Ventes de cartes cadeaux depuis la dernière clôture
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
    total_especes_encours = total_especes_ventes + total_especes_credit + ventes_cartes_especes
    total_carte_encours = total_carte_ventes + total_carte_credit + ventes_cartes_cb
    total_cheque_encours = total_cheque_ventes + total_cheque_credit + ventes_cartes_cheque
    total_om_encours = total_om_ventes + total_om_credit + ventes_cartes_om
    total_wave_encours = total_wave_ventes + total_wave_credit + ventes_cartes_wave
    # total_encours = argent réellement encaissé (sans carte_cadeau car déjà compté à la vente)
    total_encours = total_especes_encours + total_carte_encours + total_cheque_encours + total_om_encours + total_wave_encours

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

    # Compter les ventes validées et non validées
    ventes_validees = RendezVous.objects.filter(
        institut=institut,
        date=date_selectionnee,
        statut='valide'
    ).count()

    ventes_non_validees = RendezVous.objects.filter(
        institut=institut,
        date=date_selectionnee,
        statut='planifie'
    ).count()

    # Montant espèces attendu = total espèces en cours + fond de caisse
    montant_attendu = total_especes_encours + institut.fond_caisse

    context = {
        'institut': institut,
        'date_selectionnee': date_selectionnee,
        'clotures_existantes': clotures_existantes,
        'ventes_validees': ventes_validees,
        'ventes_non_validees': ventes_non_validees,
        'total_especes': total_especes_encours,
        'total_carte': total_carte_encours,
        'total_cheque': total_cheque_encours,
        'total_om': total_om_encours,
        'total_wave': total_wave_encours,
        'total_encours': total_encours,
        'total_jour': total_jour,
        'total_jour_especes': total_jour_especes,
        'total_jour_carte': total_jour_carte,
        'fond_caisse': institut.fond_caisse,
        'montant_attendu': montant_attendu,
        'nb_clotures': clotures_existantes.count(),
        # Détails pour le template
        'total_especes_ventes': total_especes_ventes,
        'total_carte_ventes': total_carte_ventes,
        'total_cheque_ventes': total_cheque_ventes,
        'total_om_ventes': total_om_ventes,
        'total_wave_ventes': total_wave_ventes,
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
    }

    return render(request, 'express/cloture.html', context)


@login_required
@role_required(['patron', 'manager'])
@require_POST
def api_cloturer_caisse(request):
    """API : Clôturer la caisse Express"""
    from django.db import models

    institut = get_object_or_404(Institut, code='express')

    # Vérifier l'accès
    utilisateur = request.user.utilisateur
    if utilisateur.is_manager() and utilisateur.institut != institut:
        return JsonResponse({
            'success': False,
            'message': "Vous n'avez pas accès à Express"
        }, status=403)

    try:
        date_str = request.POST.get('date')
        montant_reel = request.POST.get('montant_reel')

        date_cloture = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Vérifier qu'il n'y a plus de ventes non validées
        ventes_non_validees = RendezVous.objects.filter(
            institut=institut,
            date=date_cloture,
            statut='planifie'
        ).count()

        if ventes_non_validees > 0:
            return JsonResponse({
                'success': False,
                'message': f'Il reste {ventes_non_validees} ventes non validées. Veuillez les valider ou les annuler avant de clôturer.'
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
        else:
            heure_debut = timezone.make_aware(datetime.combine(date_cloture, datetime.min.time()))

        # Calculer les totaux depuis la dernière clôture
        paiements_ventes = Paiement.objects.filter(
            rendez_vous__institut=institut,
            rendez_vous__date=date_cloture,
            rendez_vous__statut='valide',
            date__gte=heure_debut
        )

        total_especes_ventes = paiements_ventes.filter(mode='especes').aggregate(
            total=models.Sum('montant')
        )['total'] or 0

        total_carte_ventes = paiements_ventes.filter(mode='carte').aggregate(
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

        total_especes = total_especes_ventes + total_especes_credit
        total_carte = total_carte_ventes + total_carte_credit

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
            cloture_par=utilisateur,
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
