import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Utilisateur, Client, Employe, Institut, CarteCadeau, UtilisationCarteCadeau, ForfaitClient, RendezVous, Credit, Prestation, Paiement
from .decorators import role_required
import re


def normaliser_telephone(telephone):
    """
    Normalise un numéro de téléphone en supprimant tous les caractères non numériques.
    Exemples :
        "77 123 45 67" -> "771234567"
        "+221 77-123-45-67" -> "221771234567"
        "77.123.45.67" -> "771234567"
    """
    if not telephone:
        return ""
    return re.sub(r'[^0-9]', '', telephone)


def normaliser_nom(nom):
    """
    Normalise un nom pour la comparaison (minuscules, sans accents, sans espaces multiples).
    """
    if not nom:
        return ""
    # Mettre en minuscules et supprimer les espaces en début/fin
    nom = nom.lower().strip()
    # Remplacer les espaces multiples par un seul espace
    nom = re.sub(r'\s+', ' ', nom)
    return nom


def trouver_client_existant(nom, prenom, telephone):
    """
    Recherche un client existant avec le même téléphone normalisé ET le même nom/prénom normalisé.
    Retourne le client existant ou None.
    """
    tel_normalise = normaliser_telephone(telephone)
    nom_normalise = normaliser_nom(nom)
    prenom_normalise = normaliser_nom(prenom)

    # Rechercher parmi tous les clients
    for client in Client.objects.all():
        client_tel = normaliser_telephone(client.telephone)
        client_nom = normaliser_nom(client.nom)
        client_prenom = normaliser_nom(client.prenom)

        # Vérifier si téléphone ET nom complet correspondent
        if client_tel == tel_normalise and client_nom == nom_normalise and client_prenom == prenom_normalise:
            return client

    return None


def trouver_doublon_nom(nom, prenom):
    """
    Recherche un client existant avec le même nom ET prénom normalisés (indépendamment du téléphone).
    Retourne le client existant ou None.
    """
    nom_normalise = normaliser_nom(nom)
    prenom_normalise = normaliser_nom(prenom)

    for client in Client.objects.all():
        if normaliser_nom(client.nom) == nom_normalise and normaliser_nom(client.prenom) == prenom_normalise:
            return client

    return None


def login_view(request):
    """
    Page de connexion avec code PIN à 6 chiffres
    """
    MAX_TENTATIVES = 5
    DUREE_BLOCAGE = 300  # 5 minutes en secondes

    if request.method == 'POST':
        # Rate limiting : vérifier les tentatives échouées
        tentatives = request.session.get('login_tentatives', 0)
        blocage_jusqu = request.session.get('login_blocage_jusqu', None)

        if blocage_jusqu:
            temps_restant = blocage_jusqu - timezone.now().timestamp()
            if temps_restant > 0:
                minutes = int(temps_restant // 60) + 1
                messages.error(request, f'Trop de tentatives. Réessayez dans {minutes} minute(s).')
                utilisateurs = Utilisateur.objects.filter(actif=True).select_related('user', 'institut').order_by('user__username')
                return render(request, 'login.html', {'utilisateurs': utilisateurs})
            else:
                # Blocage expiré, réinitialiser
                request.session['login_tentatives'] = 0
                request.session['login_blocage_jusqu'] = None
                tentatives = 0

        user_id = request.POST.get('user_id')
        pin = request.POST.get('pin')

        try:
            utilisateur = Utilisateur.objects.select_related('user', 'institut').get(
                id=user_id,
                actif=True
            )

            # Vérifier le PIN hashé
            if not utilisateur.check_pin(pin):
                raise Utilisateur.DoesNotExist

            # Connexion réussie : réinitialiser le compteur
            request.session['login_tentatives'] = 0
            request.session['login_blocage_jusqu'] = None

            # Connexion de l'utilisateur Django
            login(request, utilisateur.user)

            # Redirection selon le rôle
            if utilisateur.is_patron():
                return redirect('dashboard:index')
            elif utilisateur.institut.code == 'express':
                return redirect('express:index')
            else:
                # Palais ou Klinic
                return redirect('agenda:index', institut_code=utilisateur.institut.code)

        except Utilisateur.DoesNotExist:
            tentatives += 1
            request.session['login_tentatives'] = tentatives

            if tentatives >= MAX_TENTATIVES:
                request.session['login_blocage_jusqu'] = timezone.now().timestamp() + DUREE_BLOCAGE
                messages.error(request, f'Trop de tentatives ({MAX_TENTATIVES}). Compte bloqué pendant 5 minutes.')
            else:
                restantes = MAX_TENTATIVES - tentatives
                messages.error(request, f'Code PIN incorrect ({restantes} tentative(s) restante(s))')

    # Récupérer tous les utilisateurs actifs pour la liste déroulante
    utilisateurs = Utilisateur.objects.filter(actif=True).select_related('user', 'institut').order_by('user__username')

    return render(request, 'login.html', {
        'utilisateurs': utilisateurs
    })


def logout_view(request):
    """
    Déconnexion de l'utilisateur
    """
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès')
    return redirect('core:login')


@login_required
def clients_list(request):
    """
    Liste de tous les clients avec recherche et filtres
    """
    search = request.GET.get('search', '')
    filtre = request.GET.get('filtre', '')
    clients = Client.objects.all()

    if search:
        clients = clients.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(telephone__icontains=search)
        )

    if filtre == 'dettes':
        # Clients avec crédits non soldés
        clients_avec_dettes = Credit.objects.filter(solde=False).values_list('client_id', flat=True).distinct()
        clients = clients.filter(id__in=clients_avec_dettes)
    elif filtre == 'forfaits':
        # Clients avec forfaits actifs
        clients_avec_forfaits = ForfaitClient.objects.filter(statut='actif').values_list('client_id', flat=True).distinct()
        clients = clients.filter(id__in=clients_avec_forfaits)
    elif filtre == 'cartes':
        # Clients bénéficiaires d'une carte cadeau active
        clients_avec_cartes = CarteCadeau.objects.filter(statut='active').values_list('beneficiaire_id', flat=True).distinct()
        clients = clients.filter(id__in=clients_avec_cartes)

    clients = clients.order_by('-actif', 'nom', 'prenom')

    paginator = Paginator(clients, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'clients/liste.html', {
        'clients': page_obj,
        'page_obj': page_obj,
        'search': search,
        'filtre': filtre,
    })


@login_required
def client_detail(request, pk):
    """
    Fiche détaillée d'un client avec son historique
    """
    client = get_object_or_404(Client, pk=pk)

    # Historique des rendez-vous validés
    rendez_vous = RendezVous.objects.filter(
        client=client, statut='valide'
    ).select_related(
        'institut', 'prestation', 'employe'
    ).prefetch_related('paiements').order_by('-date', '-heure_debut')[:50]

    # Crédits du client
    credits = client.credits.all().order_by('-date_creation')

    # Forfaits du client (tous, actifs en premier)
    forfaits = ForfaitClient.objects.filter(
        client=client
    ).select_related('prestation', 'institut').prefetch_related('seances').order_by(
        '-statut',  # actif en premier
        '-date_achat'
    )

    return render(request, 'clients/fiche.html', {
        'client': client,
        'rendez_vous': rendez_vous,
        'credits': credits,
        'forfaits': forfaits,
        'total_depense': client.get_total_depense(),
        'nombre_visites': client.get_nombre_visites(),
        'credit_total': client.get_credit_total(),
    })


@login_required
def client_create(request):
    """
    Création d'un nouveau client
    """
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        sexe = request.POST.get('sexe', 'F')
        notes = request.POST.get('notes', '')

        # Normaliser le téléphone
        telephone_normalise = normaliser_telephone(telephone)

        # Vérifier si un client avec le même nom ET téléphone existe déjà
        client_existant = trouver_client_existant(nom, prenom, telephone)
        if client_existant:
            messages.warning(
                request,
                f'Ce client existe déjà : {client_existant.get_full_name()} ({client_existant.telephone}). '
                f'<a href="{client_existant.id}/" class="alert-link">Voir sa fiche</a>'
            )
        else:
            # Vérifier si le téléphone normalisé existe déjà
            doublon_telephone = None
            for c in Client.objects.all():
                if normaliser_telephone(c.telephone) == telephone_normalise:
                    doublon_telephone = c
                    break

            if doublon_telephone:
                messages.warning(
                    request,
                    f'Ce numéro de téléphone est déjà utilisé par : {doublon_telephone.get_full_name()}. '
                    f'<a href="{doublon_telephone.id}/" class="alert-link">Voir sa fiche</a>'
                )
            else:
                # Vérifier si un client avec le même nom+prénom existe (doublon potentiel)
                confirmer = request.POST.get('confirmer_doublon') == '1'
                doublon_nom = trouver_doublon_nom(nom, prenom)
                if doublon_nom and not confirmer:
                    messages.warning(
                        request,
                        f'Un client avec le même nom existe déjà : {doublon_nom.get_full_name()} ({doublon_nom.telephone}). '
                        f'<a href="{doublon_nom.id}/" class="alert-link">Voir sa fiche</a>. '
                        f'Si c\'est bien un nouveau client, cliquez à nouveau sur Enregistrer.'
                    )
                    return render(request, 'clients/create.html', {
                        'confirmer_doublon': True,
                        'form_data': {'nom': nom, 'prenom': prenom, 'telephone': telephone, 'sexe': sexe, 'notes': notes}
                    })
                client = Client.objects.create(
                    nom=nom,
                    prenom=prenom,
                    telephone=telephone_normalise if telephone_normalise else telephone,
                    sexe=sexe,
                    notes=notes
                )
                messages.success(request, f'Client {client.get_full_name()} créé avec succès')
                return redirect('core:client_detail', pk=client.pk)

    return render(request, 'clients/create.html')


@login_required
def client_search(request):
    """
    API de recherche de clients (pour autocomplete)
    """
    search = request.GET.get('q', '')
    if len(search) < 2:
        return JsonResponse({'clients': []})

    clients = Client.objects.filter(
        Q(nom__icontains=search) |
        Q(prenom__icontains=search) |
        Q(telephone__icontains=search)
    )[:10]

    results = [{
        'id': c.id,
        'nom': c.nom,
        'prenom': c.prenom,
        'telephone': c.telephone,
        'full_name': c.get_full_name(),
    } for c in clients]

    return JsonResponse({'clients': results})


@login_required
def api_client_creer(request):
    """API pour créer un nouveau client"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    nom = request.POST.get('nom', '').strip()
    prenom = request.POST.get('prenom', '').strip()
    telephone = request.POST.get('telephone', '').strip()
    email = request.POST.get('email', '').strip() or None

    if not all([nom, prenom, telephone]):
        return JsonResponse({'success': False, 'message': 'Nom, prénom et téléphone sont requis'})

    # Normaliser le téléphone pour le stockage
    telephone_normalise = normaliser_telephone(telephone)

    # Vérifier si un client avec le même nom ET téléphone existe déjà
    client_existant = trouver_client_existant(nom, prenom, telephone)
    if client_existant:
        return JsonResponse({
            'success': False,
            'duplicate': True,
            'message': f'Ce client existe déjà : {client_existant.get_full_name()} ({client_existant.telephone})',
            'existing_client': {
                'id': client_existant.id,
                'nom': client_existant.nom,
                'prenom': client_existant.prenom,
                'telephone': client_existant.telephone,
                'full_name': client_existant.get_full_name()
            }
        })

    # Vérifier si le téléphone normalisé existe déjà (même si nom différent)
    for c in Client.objects.all():
        if normaliser_telephone(c.telephone) == telephone_normalise:
            return JsonResponse({
                'success': False,
                'duplicate': True,
                'message': f'Ce numéro de téléphone est déjà utilisé par : {c.get_full_name()}',
                'existing_client': {
                    'id': c.id,
                    'nom': c.nom,
                    'prenom': c.prenom,
                    'telephone': c.telephone,
                    'full_name': c.get_full_name()
                }
            })

    # Vérifier si un client avec le même nom+prénom existe (doublon potentiel)
    confirmer = request.POST.get('confirmer_doublon') == '1'
    if not confirmer:
        doublon_nom = trouver_doublon_nom(nom, prenom)
        if doublon_nom:
            return JsonResponse({
                'success': False,
                'name_duplicate': True,
                'message': f'Un client avec le même nom existe déjà : {doublon_nom.get_full_name()} ({doublon_nom.telephone})',
                'existing_client': {
                    'id': doublon_nom.id,
                    'nom': doublon_nom.nom,
                    'prenom': doublon_nom.prenom,
                    'telephone': doublon_nom.telephone,
                    'full_name': doublon_nom.get_full_name()
                }
            })

    date_naissance_str = request.POST.get('date_naissance', '').strip()
    date_naissance = None
    if date_naissance_str:
        from datetime import date as date_type
        try:
            date_naissance = date_type.fromisoformat(date_naissance_str)
        except ValueError:
            pass
    notes = request.POST.get('notes', '').strip() or None

    client = Client.objects.create(
        nom=nom,
        prenom=prenom,
        telephone=telephone_normalise if telephone_normalise else telephone,
        email=email,
        date_naissance=date_naissance,
        notes=notes,
    )

    return JsonResponse({
        'success': True,
        'message': f'Client {client.get_full_name()} créé avec succès',
        'client_id': client.id
    })


@login_required
def api_client_modifier(request, pk):
    """API pour modifier un client existant (patron seulement)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    # Seul le patron peut modifier les clients
    if not request.user.utilisateur.is_patron:
        return JsonResponse({'success': False, 'message': 'Seul le patron peut modifier les clients'}, status=403)

    client = get_object_or_404(Client, pk=pk)

    nom = request.POST.get('nom', '').strip()
    prenom = request.POST.get('prenom', '').strip()
    telephone = request.POST.get('telephone', '').strip()
    email = request.POST.get('email', '').strip() or None

    if not all([nom, prenom, telephone]):
        return JsonResponse({'success': False, 'message': 'Nom, prénom et téléphone sont requis'})

    # Vérifier que le téléphone n'est pas déjà utilisé par un autre client
    if Client.objects.filter(telephone=telephone).exclude(pk=pk).exists():
        return JsonResponse({'success': False, 'message': 'Ce numéro de téléphone est déjà utilisé'})

    date_naissance_str = request.POST.get('date_naissance', '').strip()
    date_naissance = None
    if date_naissance_str:
        from datetime import date as date_type
        try:
            date_naissance = date_type.fromisoformat(date_naissance_str)
        except ValueError:
            pass
    notes = request.POST.get('notes', '').strip() or None

    client.nom = nom
    client.prenom = prenom
    client.telephone = telephone
    client.email = email
    client.date_naissance = date_naissance
    client.notes = notes
    client.save()

    return JsonResponse({
        'success': True,
        'message': f'Client {client.get_full_name()} modifié avec succès'
    })


@login_required
def api_client_supprimer(request, pk):
    """API pour supprimer un client (patron seulement)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    # Vérifier que l'utilisateur est patron
    if not request.user.utilisateur.is_patron:
        return JsonResponse({'success': False, 'message': 'Action non autorisée'}, status=403)

    client = get_object_or_404(Client, pk=pk)
    nom_client = client.get_full_name()

    # Vérifier si le client a des données liées
    nb_rdv = client.rendez_vous.count()
    nb_credits = client.credits.filter(solde=False).count()
    nb_forfaits = client.forfaits.filter(statut='actif').count()
    nb_cartes = client.cartes_achetees.filter(statut='active').count() + \
                client.cartes_recues.filter(statut='active').count()

    if nb_rdv > 0 or nb_credits > 0 or nb_forfaits > 0 or nb_cartes > 0:
        details = []
        if nb_rdv > 0:
            details.append(f'{nb_rdv} rendez-vous')
        if nb_credits > 0:
            details.append(f'{nb_credits} crédit(s) non soldé(s)')
        if nb_forfaits > 0:
            details.append(f'{nb_forfaits} forfait(s) actif(s)')
        if nb_cartes > 0:
            details.append(f'{nb_cartes} carte(s) cadeau active(s)')

        return JsonResponse({
            'success': False,
            'message': f'Impossible de supprimer {nom_client} : {", ".join(details)}. '
                       f'Vous pouvez désactiver ce client à la place.',
            'has_data': True
        })

    client.delete()

    return JsonResponse({
        'success': True,
        'message': f'Client {nom_client} supprimé avec succès'
    })


@login_required
def api_client_desactiver(request, pk):
    """API pour désactiver un client (patron seulement)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    if not request.user.utilisateur.is_patron:
        return JsonResponse({'success': False, 'message': 'Action non autorisée'}, status=403)

    client = get_object_or_404(Client, pk=pk)
    client.actif = not client.actif
    client.save()

    statut = 'activé' if client.actif else 'désactivé'
    return JsonResponse({
        'success': True,
        'message': f'Client {client.get_full_name()} {statut} avec succès'
    })


# ============================
# GESTION DES EMPLOYÉS
# ============================

@login_required
@role_required(['patron'])
def employes_list(request):
    """Liste de tous les employés groupés par institut (patron uniquement)"""
    # Récupérer tous les instituts
    instituts = Institut.objects.all().order_by('nom')

    # Récupérer les employés groupés par institut
    employes_par_institut = {}
    for institut in instituts:
        employes_par_institut[institut] = Employe.objects.filter(
            institut=institut
        ).order_by('ordre_affichage', 'nom')

    return render(request, 'employes/liste.html', {
        'instituts': instituts,
        'employes_par_institut': employes_par_institut
    })


@login_required
@role_required(['patron'])
def api_employe_creer(request):
    """API pour créer un nouvel employé (patron uniquement)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    try:
        nom = request.POST.get('nom', '').strip()
        institut_code = request.POST.get('institut', '').strip()

        if not all([nom, institut_code]):
            return JsonResponse({
                'success': False,
                'message': 'Nom et institut sont requis'
            })

        institut = get_object_or_404(Institut, code=institut_code)

        # Déterminer l'ordre d'affichage automatiquement (mettre à la fin)
        dernier = Employe.objects.filter(institut=institut).order_by('-ordre_affichage').first()
        ordre_affichage = (dernier.ordre_affichage + 1) if dernier else 1

        employe = Employe.objects.create(
            nom=nom,
            institut=institut,
            ordre_affichage=int(ordre_affichage),
            actif=True  # Toujours actif par défaut
        )

        return JsonResponse({
            'success': True,
            'message': f'Employé {employe.nom} créé avec succès',
            'employe': {
                'id': employe.id,
                'nom': employe.nom,
                'institut': employe.institut.nom,
                'ordre_affichage': employe.ordre_affichage,
                'actif': employe.actif
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@role_required(['patron'])
def api_employe_modifier(request, pk):
    """API pour modifier un employé existant (patron uniquement)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    try:
        employe = get_object_or_404(Employe, pk=pk)

        nom = request.POST.get('nom', '').strip()
        institut_code = request.POST.get('institut', '').strip()

        if not all([nom, institut_code]):
            return JsonResponse({
                'success': False,
                'message': 'Nom et institut sont requis'
            })

        institut = get_object_or_404(Institut, code=institut_code)

        employe.nom = nom
        employe.institut = institut
        # Conserver ordre_affichage et actif existants
        employe.save()

        return JsonResponse({
            'success': True,
            'message': f'Employé {employe.nom} modifié avec succès',
            'employe': {
                'id': employe.id,
                'nom': employe.nom,
                'institut': employe.institut.nom,
                'ordre_affichage': employe.ordre_affichage,
                'actif': employe.actif
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@role_required(['patron'])
def api_employe_supprimer(request, pk):
    """API pour supprimer un employé (patron uniquement)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    try:
        employe = get_object_or_404(Employe, pk=pk)

        # Vérifier si l'employé a des rendez-vous (related_name='rendez_vous')
        nb_rdv = employe.rendez_vous.count()
        if nb_rdv > 0:
            return JsonResponse({
                'success': False,
                'message': f'Impossible de supprimer {employe.nom} : {nb_rdv} rendez-vous associé(s). Vous pouvez le désactiver à la place.'
            }, status=400)

        nom_employe = employe.nom
        employe.delete()

        return JsonResponse({
            'success': True,
            'message': f'Employé {nom_employe} supprimé avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


# ============================
# CARTES CADEAUX
# ============================

@login_required
def cartes_cadeaux_list(request):
    """Liste des cartes cadeaux."""
    # Marquer automatiquement les cartes expirées
    CarteCadeau.marquer_cartes_expirees()

    cartes = CarteCadeau.objects.select_related(
        'acheteur', 'beneficiaire', 'institut_achat'
    ).all()

    # Par défaut, afficher les cartes actives
    statut = request.GET.get('statut', 'active')
    if statut:
        # Pour le filtre "annulee", inclure aussi les cartes supprimées
        if statut == 'annulee':
            cartes = cartes.filter(statut__in=['annulee', 'supprimee'])
        elif statut == 'toutes':
            # Afficher toutes les cartes sans filtre
            pass
        else:
            cartes = cartes.filter(statut=statut)

    search = request.GET.get('search', '')
    if search:
        cartes = cartes.filter(
            Q(code__icontains=search) |
            Q(beneficiaire__nom__icontains=search) |
            Q(beneficiaire__prenom__icontains=search) |
            Q(acheteur__nom__icontains=search) |
            Q(acheteur__prenom__icontains=search)
        )

    instituts = Institut.objects.all()

    paginator = Paginator(cartes, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'cartes_cadeaux/liste.html', {
        'cartes': page_obj,
        'page_obj': page_obj,
        'search': search,
        'statut_filtre': statut,
        'instituts': instituts,
    })


@login_required
@require_POST
def api_vendre_carte_cadeau(request):
    """API pour créer une nouvelle carte cadeau."""
    try:
        from decimal import Decimal, InvalidOperation
        from datetime import date, datetime

        acheteur_id = request.POST.get('acheteur_id')
        beneficiaire_id = request.POST.get('beneficiaire_id')
        meme_personne = request.POST.get('meme_personne') == 'true'
        montant = int(request.POST.get('montant', 0))
        mode_paiement = request.POST.get('mode_paiement', 'especes')

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

        if not acheteur_id:
            return JsonResponse({'success': False, 'message': 'Acheteur requis'})

        acheteur = Client.objects.get(id=acheteur_id)

        if meme_personne:
            beneficiaire = acheteur
        else:
            if not beneficiaire_id:
                return JsonResponse({'success': False, 'message': 'Bénéficiaire requis'})
            beneficiaire = Client.objects.get(id=beneficiaire_id)

        if montant <= 0:
            return JsonResponse({'success': False, 'message': 'Le montant doit être supérieur à 0'})

        utilisateur = request.user.utilisateur
        if utilisateur.is_patron():
            institut_id = request.POST.get('institut_id')
            if not institut_id:
                return JsonResponse({'success': False, 'message': 'Institut requis'})
            institut = Institut.objects.get(id=institut_id)
        else:
            institut = utilisateur.institut

        # Créer la carte cadeau avec les infos de paiement complètes
        carte_kwargs = dict(
            acheteur=acheteur,
            beneficiaire=beneficiaire,
            montant_initial=montant,
            solde=montant,
            institut_achat=institut,
            mode_paiement_achat=moyen_paiement_1,
            vendue_par=utilisateur,
        )

        if utilise_double_paiement and montant_paiement_2 > 0:
            carte_kwargs['montant_paiement_1'] = int(montant_paiement_1)
            carte_kwargs['moyen_paiement_2'] = moyen_paiement_2
            carte_kwargs['montant_paiement_2'] = int(montant_paiement_2)
        else:
            carte_kwargs['montant_paiement_1'] = montant

        carte = CarteCadeau.objects.create(**carte_kwargs)

        return JsonResponse({
            'success': True,
            'message': f'Carte cadeau {carte.code} créée avec succès',
            'carte': {
                'id': carte.id,
                'code': carte.code,
                'montant': carte.montant_initial,
                'beneficiaire': carte.beneficiaire.get_full_name(),
                'acheteur': carte.acheteur.get_full_name(),
            }
        })

    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Client non trouvé'})
    except Institut.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Institut non trouvé'})
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Montant invalide'})


@login_required
def api_verifier_carte_cadeau(request):
    """Vérifier le solde et l'historique d'une carte cadeau par son code."""
    code = request.GET.get('code', '').strip().upper()

    if not code:
        return JsonResponse({'found': False, 'message': 'Veuillez entrer un code'})

    try:
        carte = CarteCadeau.objects.select_related(
            'acheteur', 'beneficiaire', 'institut_achat'
        ).prefetch_related(
            'utilisations__institut',
            'utilisations__rendez_vous__prestation'
        ).get(code=code)

        # Basculer en expirée si nécessaire
        if carte.statut == 'active' and carte.est_expiree:
            carte.statut = 'expiree'
            carte.save(update_fields=['statut'])

        utilisations = []
        for u in carte.utilisations.all():
            util_data = {
                'date': u.date.strftime('%d/%m/%Y'),
                'institut': u.institut.nom,
                'montant': u.montant,
            }
            if u.rendez_vous and u.rendez_vous.prestation:
                util_data['prestation'] = u.rendez_vous.prestation.nom
            utilisations.append(util_data)

        return JsonResponse({
            'found': True,
            'carte': {
                'id': carte.id,
                'code': carte.code,
                'statut': carte.statut,
                'statut_display': carte.get_statut_display(),
                'beneficiaire': carte.beneficiaire.get_full_name(),
                'beneficiaire_tel': carte.beneficiaire.telephone,
                'acheteur': carte.acheteur.get_full_name(),
                'date_achat': carte.date_achat.strftime('%d/%m/%Y'),
                'institut_achat': carte.institut_achat.nom,
                'montant_initial': carte.montant_initial,
                'solde': carte.solde,
                'utilise': carte.get_total_utilise(),
                'utilisations': utilisations,
            }
        })

    except CarteCadeau.DoesNotExist:
        return JsonResponse({'found': False, 'message': 'Carte non trouvée'})


@login_required
def api_rechercher_cartes_client(request):
    """Rechercher les cartes cadeaux actives d'un client (bénéficiaire)."""
    client_id = request.GET.get('client_id')

    if not client_id:
        return JsonResponse({'cartes': []})

    try:
        now = timezone.now()

        # Marquer les cartes expirées avant la recherche
        CarteCadeau.marquer_cartes_expirees()

        # Récupérer les cartes actives avec solde > 0
        cartes_queryset = CarteCadeau.objects.filter(
            beneficiaire_id=client_id,
            statut='active',
            solde__gt=0,
        )

        cartes = []
        for carte in cartes_queryset:
            cartes.append({
                'id': carte.id,
                'code': carte.code,
                'solde': carte.solde,
                'montant_initial': carte.montant_initial,
                'date_expiration': carte.date_expiration.strftime('%d/%m/%Y') if carte.date_expiration else '',
                'jours_restants': carte.jours_restants,
            })

        return JsonResponse({'cartes': cartes})

    except Exception as e:
        import traceback
        print(f"Erreur API cartes cadeaux: {e}")
        print(traceback.format_exc())
        return JsonResponse({'cartes': [], 'error': str(e)}, status=500)


@login_required
def imprimer_carte_cadeau(request, carte_id):
    """Génère la page d'impression du bon cadeau."""
    carte = get_object_or_404(
        CarteCadeau.objects.select_related('acheteur', 'beneficiaire'),
        id=carte_id,
    )
    return render(request, 'cartes_cadeaux/bon_cadeau_print.html', {
        'carte': carte,
    })


@login_required
def api_carte_cadeau_whatsapp(request, carte_id, destinataire):
    """Génère un lien WhatsApp pour envoyer les infos d'une carte cadeau."""
    from .utils import generer_lien_whatsapp

    if destinataire not in ('beneficiaire', 'acheteur'):
        return JsonResponse({'success': False, 'message': 'Destinataire invalide'}, status=400)

    try:
        carte = CarteCadeau.objects.select_related(
            'beneficiaire', 'acheteur', 'institut_achat'
        ).get(id=carte_id)
    except CarteCadeau.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Carte non trouvée'}, status=404)

    if destinataire == 'beneficiaire':
        client = carte.beneficiaire
        message = (
            f"Bonjour {client.prenom} 😊\n\n"
            f"Vous avez reçu une carte cadeau de {carte.montant_initial:,} FCFA "
            f"au {carte.institut_achat.nom} !\n\n"
            f"🎁 Code : *{carte.code}*\n"
            f"💰 Solde : {carte.solde:,} FCFA\n"
        )
    else:
        client = carte.acheteur
        message = (
            f"Bonjour {client.prenom} 😊\n\n"
            f"Votre carte cadeau de {carte.montant_initial:,} FCFA "
            f"au {carte.institut_achat.nom} a bien été créée !\n\n"
            f"🎁 Code : *{carte.code}*\n"
            f"👤 Bénéficiaire : {carte.beneficiaire.get_full_name()}\n"
        )

    if carte.date_expiration:
        message += f"📅 Valable jusqu'au : {carte.date_expiration.strftime('%d/%m/%Y')}\n"

    message += f"\nÀ très bientôt ! 💖"

    lien = generer_lien_whatsapp(client.telephone, message)
    if not lien:
        return JsonResponse({
            'success': False,
            'message': f'Numéro de téléphone invalide pour {client.get_full_name()}'
        })

    return JsonResponse({'success': True, 'lien': lien})


@login_required
@role_required(['patron'])
@require_POST
def api_supprimer_carte_cadeau(request, carte_id):
    """API pour supprimer une carte cadeau (patron uniquement)"""
    try:
        carte = get_object_or_404(CarteCadeau, id=carte_id)

        # Vérifier si la carte est déjà supprimée
        if carte.statut == 'supprimee':
            return JsonResponse({
                'success': False,
                'message': 'Cette carte est déjà supprimée'
            }, status=400)

        code_carte = carte.code
        carte.statut = 'supprimee'
        carte.save()

        return JsonResponse({
            'success': True,
            'message': f'Carte cadeau {code_carte} supprimée avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
