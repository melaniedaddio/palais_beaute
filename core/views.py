import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Utilisateur, Client, Employe, Institut, CarteCadeau, UtilisationCarteCadeau, ForfaitClient, RendezVous
from .decorators import role_required


def login_view(request):
    """
    Page de connexion avec code PIN à 6 chiffres
    """
    if request.method == 'POST':
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
            messages.error(request, 'Code PIN incorrect')

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
    Liste de tous les clients avec recherche
    """
    search = request.GET.get('search', '')
    clients = Client.objects.all()

    if search:
        clients = clients.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(telephone__icontains=search)
        )

    clients = clients.order_by('nom', 'prenom')

    return render(request, 'clients/liste.html', {
        'clients': clients,
        'search': search
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
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        telephone = request.POST.get('telephone')
        sexe = request.POST.get('sexe', 'F')
        notes = request.POST.get('notes', '')

        # Vérifier que le téléphone n'existe pas déjà
        if Client.objects.filter(telephone=telephone).exists():
            messages.error(request, 'Ce numéro de téléphone existe déjà')
        else:
            client = Client.objects.create(
                nom=nom,
                prenom=prenom,
                telephone=telephone,
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

    if Client.objects.filter(telephone=telephone).exists():
        return JsonResponse({'success': False, 'message': 'Ce numéro de téléphone existe déjà'})

    client = Client.objects.create(
        nom=nom,
        prenom=prenom,
        telephone=telephone,
        email=email
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

    client.nom = nom
    client.prenom = prenom
    client.telephone = telephone
    client.email = email
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

    # Supprimer le client
    client.delete()

    return JsonResponse({
        'success': True,
        'message': f'Client {nom_client} supprimé avec succès'
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
    cartes = CarteCadeau.objects.select_related(
        'acheteur', 'beneficiaire', 'institut_achat'
    ).all()

    statut = request.GET.get('statut')
    if statut:
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

    return render(request, 'cartes_cadeaux/liste.html', {
        'cartes': cartes,
        'search': search,
        'statut_filtre': statut or '',
        'instituts': instituts,
    })


@login_required
@require_POST
def api_vendre_carte_cadeau(request):
    """API pour créer une nouvelle carte cadeau."""
    try:
        acheteur_id = request.POST.get('acheteur_id')
        beneficiaire_id = request.POST.get('beneficiaire_id')
        meme_personne = request.POST.get('meme_personne') == 'true'
        montant = int(request.POST.get('montant', 0))
        mode_paiement = request.POST.get('mode_paiement', 'especes')

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

        carte = CarteCadeau.objects.create(
            acheteur=acheteur,
            beneficiaire=beneficiaire,
            montant_initial=montant,
            solde=montant,
            institut_achat=institut,
            mode_paiement_achat=mode_paiement,
            vendue_par=utilisateur,
        )

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

    cartes = CarteCadeau.objects.filter(
        beneficiaire_id=client_id,
        statut='active',
        solde__gt=0,
    ).values('id', 'code', 'solde', 'montant_initial')

    return JsonResponse({'cartes': list(cartes)})


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
@role_required(['patron'])
@require_POST
def api_supprimer_carte_cadeau(request, carte_id):
    """API pour supprimer une carte cadeau (patron uniquement)"""
    try:
        carte = get_object_or_404(CarteCadeau, id=carte_id)

        # Vérifier s'il y a des utilisations
        nb_utilisations = carte.utilisations.count()

        if nb_utilisations > 0:
            return JsonResponse({
                'success': False,
                'message': f'Impossible de supprimer cette carte : {nb_utilisations} utilisation(s) enregistrée(s). Vous pouvez l\'annuler à la place.'
            }, status=400)

        code_carte = carte.code
        carte.delete()

        return JsonResponse({
            'success': True,
            'message': f'Carte cadeau {code_carte} supprimée avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
