from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse


def _is_ajax(request):
    """Détecte si la requête est un appel AJAX (fetch/XMLHttpRequest)."""
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Accept', '')
        or request.content_type == 'application/json'
        or '/api/' in request.path
    )


def _json_or_redirect(request, message='Session expirée, veuillez vous reconnecter'):
    """Renvoie du JSON pour les requêtes AJAX, sinon redirige vers le login."""
    if _is_ajax(request):
        return JsonResponse({
            'success': False,
            'message': message,
            'redirect': '/login/'
        }, status=401)
    messages.error(request, message)
    return redirect('core:login')


def login_required_json(view_func):
    """
    Remplace @login_required de Django pour les vues API.
    Renvoie du JSON (401) au lieu de rediriger vers le login HTML.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _json_or_redirect(request)
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(roles):
    """
    Décorateur pour restreindre l'accès selon le rôle.
    Usage: @role_required(['patron']) ou @role_required(['patron', 'manager'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _json_or_redirect(request)

            try:
                utilisateur = request.user.utilisateur
                if utilisateur.role not in roles:
                    return _json_or_redirect(request, "Vous n'avez pas accès à cette page")
            except AttributeError:
                return _json_or_redirect(request, "Utilisateur non configuré")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def institut_required(view_func):
    """
    Vérifie que le manager accède bien à son propre institut.
    Le patron peut accéder à tous les instituts.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _json_or_redirect(request)

        try:
            utilisateur = request.user.utilisateur
        except AttributeError:
            return _json_or_redirect(request, "Utilisateur non configuré")

        institut_code = kwargs.get('institut_code')

        # Le patron et les employés peuvent tout voir (institut NULL)
        if utilisateur.is_patron() or utilisateur.is_employe():
            return view_func(request, *args, **kwargs)

        # Le manager ne peut voir que son institut
        if utilisateur.is_manager():
            if not utilisateur.institut:
                return _json_or_redirect(request, "Utilisateur manager sans institut assigné")

            if institut_code and utilisateur.institut.code != institut_code:
                return _json_or_redirect(request, "Vous n'avez pas accès à cet institut")

        return view_func(request, *args, **kwargs)
    return wrapper
