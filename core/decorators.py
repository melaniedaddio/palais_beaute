from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(roles):
    """
    Décorateur pour restreindre l'accès selon le rôle.
    Usage: @role_required(['patron']) ou @role_required(['patron', 'manager'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login')

            try:
                utilisateur = request.user.utilisateur
                if utilisateur.role not in roles:
                    messages.error(request, "Vous n'avez pas accès à cette page")
                    return redirect('core:login')
            except AttributeError:
                messages.error(request, "Utilisateur non configuré")
                return redirect('core:login')

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
            return redirect('core:login')

        try:
            utilisateur = request.user.utilisateur
            institut_code = kwargs.get('institut_code')

            # Le patron peut tout voir
            if utilisateur.is_patron():
                return view_func(request, *args, **kwargs)

            # Le manager ne peut voir que son institut
            if utilisateur.is_manager():
                if not utilisateur.institut:
                    messages.error(request, "Utilisateur manager sans institut assigné")
                    return redirect('core:login')

                if institut_code and utilisateur.institut.code != institut_code:
                    messages.error(request, "Vous n'avez pas accès à cet institut")
                    return redirect('core:login')

            return view_func(request, *args, **kwargs)
        except AttributeError as e:
            messages.error(request, f"Erreur de configuration utilisateur: {str(e)}")
            return redirect('core:login')
    return wrapper
