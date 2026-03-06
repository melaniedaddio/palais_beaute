from django.shortcuts import render, get_object_or_404, redirect
from core.decorators import login_required_json as login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Q
from datetime import datetime, date
from decimal import Decimal
import json

from core.decorators import institut_required
from core.models import Institut, Client, Credit, Paiement, PaiementCredit, CarteCadeau, UtilisationCarteCadeau


@login_required
@institut_required
def index(request, institut_code):
    """Vue principale des crédits - Liste des clients avec crédits"""
    institut = get_object_or_404(Institut, code=institut_code)

    # Vérifier que l'utilisateur a accès
    utilisateur = request.user.utilisateur
    if utilisateur.is_manager() and utilisateur.institut != institut:
        from django.contrib import messages
        messages.error(request, "Vous n'avez pas accès à cet institut")
        return redirect('core:login')

    # Filtre : tous les crédits ou seulement les non soldés
    filtre = request.GET.get('filtre', 'non_soldes')

    if filtre == 'tous':
        credits = Credit.objects.filter(institut=institut)
    else:
        credits = Credit.objects.filter(institut=institut, solde=False)

    credits = credits.select_related('client', 'rendez_vous').order_by('-date_creation')

    # Regrouper par client
    clients_credits = {}
    for credit in credits:
        client_id = credit.client.id
        if client_id not in clients_credits:
            clients_credits[client_id] = {
                'client': credit.client,
                'credits': [],
                'total_reste': 0
            }
        clients_credits[client_id]['credits'].append(credit)
        clients_credits[client_id]['total_reste'] += credit.reste_a_payer

    # Convertir en liste triée par montant restant décroissant
    clients_list = sorted(
        clients_credits.values(),
        key=lambda x: x['total_reste'],
        reverse=True
    )

    # Calculer les totaux globaux
    total_credits = sum(c['total_reste'] for c in clients_list)
    nb_clients = len(clients_list)

    context = {
        'institut': institut,
        'clients_credits': clients_list,
        'total_credits': total_credits,
        'nb_clients': nb_clients,
        'filtre': filtre,
    }

    return render(request, 'credits/index.html', context)


@login_required
@institut_required
def client_detail(request, institut_code, client_id):
    """Détails des crédits d'un client"""
    institut = get_object_or_404(Institut, code=institut_code)
    client = get_object_or_404(Client, id=client_id)

    # Récupérer tous les crédits du client pour cet institut
    credits = Credit.objects.filter(
        client=client,
        institut=institut
    ).select_related('rendez_vous').prefetch_related(
        'paiements'
    ).order_by('-date_creation')

    # Calculer les totaux
    total_reste = sum(c.reste_a_payer for c in credits if not c.solde)
    total_paye = sum(c.montant_paye for c in credits)

    context = {
        'institut': institut,
        'client': client,
        'credits': credits,
        'total_reste': total_reste,
        'total_paye': total_paye,
    }

    return render(request, 'credits/client_detail.html', context)


@login_required
@institut_required
@require_POST
def regler_credit(request, institut_code, credit_id):
    """Effectuer un règlement sur un crédit"""
    institut = get_object_or_404(Institut, code=institut_code)
    credit = get_object_or_404(Credit, id=credit_id, institut=institut)

    if credit.solde:
        return JsonResponse({
            'success': False,
            'message': 'Ce crédit est déjà soldé'
        }, status=400)

    try:
        # Récupérer les données
        montant = Decimal(request.POST.get('montant', 0))
        mode_paiement = request.POST.get('mode', 'especes')
        carte_cadeau_id = request.POST.get('carte_cadeau_id')

        # Validation
        if montant <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Le montant doit être supérieur à 0'
            }, status=400)

        if montant > credit.reste_a_payer:
            return JsonResponse({
                'success': False,
                'message': f'Le montant ne peut pas dépasser le reste à payer ({credit.reste_a_payer} CFA)'
            }, status=400)

        utilisation = None

        # Traitement spécial pour carte cadeau
        if mode_paiement == 'carte_cadeau':
            if not carte_cadeau_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Veuillez sélectionner une carte cadeau'
                }, status=400)

            # Récupérer et valider la carte cadeau
            carte = CarteCadeau.objects.filter(
                id=carte_cadeau_id,
                beneficiaire=credit.client,
                statut='active'
            ).first()

            if not carte:
                return JsonResponse({
                    'success': False,
                    'message': 'Carte cadeau non trouvée ou non valide pour ce client'
                }, status=400)

            if carte.solde < int(montant):
                return JsonResponse({
                    'success': False,
                    'message': f'Solde insuffisant sur la carte cadeau ({carte.solde} CFA disponibles)'
                }, status=400)

            # Créer l'utilisation de la carte cadeau
            utilisation = UtilisationCarteCadeau.objects.create(
                carte=carte,
                rendez_vous=credit.rendez_vous,
                montant=int(montant),
                institut=institut,
                enregistre_par=request.user.utilisateur,
            )

            # Débiter la carte
            carte.utiliser(int(montant))

        # Créer le paiement (le save() du modèle PaiementCredit met à jour automatiquement le crédit)
        paiement = PaiementCredit.objects.create(
            credit=credit,
            montant=int(montant),
            mode=mode_paiement,
            enregistre_par=request.user.utilisateur,
            utilisation_carte_cadeau=utilisation
        )

        # Recharger le crédit pour obtenir les valeurs à jour
        credit.refresh_from_db()

        return JsonResponse({
            'success': True,
            'message': 'Règlement enregistré avec succès',
            'reste_a_payer': credit.reste_a_payer,
            'solde': credit.solde
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@institut_required
def api_credit_details(request, institut_code, credit_id):
    """API : Récupérer les détails d'un crédit avec ses règlements"""
    institut = get_object_or_404(Institut, code=institut_code)
    credit = get_object_or_404(Credit, id=credit_id, institut=institut)

    paiements_credit = credit.paiements.select_related('enregistre_par').order_by('-date')

    data = {
        'id': credit.id,
        'client': credit.client.get_full_name(),
        'client_id': credit.client.id,
        'montant_total': credit.montant_total,
        'montant_paye': credit.montant_paye,
        'reste_a_payer': credit.reste_a_payer,
        'solde': credit.solde,
        'description': credit.description,
        'date_creation': credit.date_creation.strftime('%d/%m/%Y %H:%M'),
        'date_solde': credit.date_solde.strftime('%d/%m/%Y %H:%M') if credit.date_solde else None,
        'paiements': [{
            'id': p.id,
            'montant': p.montant,
            'mode': p.get_mode_display(),
            'date': p.date.strftime('%d/%m/%Y %H:%M'),
            'enregistre_par': p.enregistre_par.nom if p.enregistre_par else 'N/A'
        } for p in paiements_credit]
    }

    return JsonResponse(data)
