#!/usr/bin/env python
"""
Script pour créer les 4 utilisateurs du système.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'le_palais_beaute.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Utilisateur, Institut

print("=== CREATION DES UTILISATEURS ===\n")

# 1. Créer le Patron
print("1. Creation du Patron...")
user_patron, created = User.objects.get_or_create(
    username='patron',
    defaults={
        'first_name': 'Patron',
        'last_name': '',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    user_patron.set_password('temp123')  # Mot de passe temporaire
    user_patron.save()
    print("  - User Django cree")

util_patron, created = Utilisateur.objects.get_or_create(
    user=user_patron,
    defaults={
        'role': 'patron',
        'institut': None,
        'pin': '123456',  # A CHANGER en production !
        'actif': True
    }
)
if created:
    print("  - Utilisateur Patron cree (PIN: 123456)")
else:
    print("  - Patron existe deja")

# 2. Créer le Manager Le Palais
print("\n2. Creation du Manager Le Palais...")
palais = Institut.objects.get(code='palais')
user_palais, created = User.objects.get_or_create(
    username='manager_palais',
    defaults={
        'first_name': 'Manager',
        'last_name': 'Palais',
    }
)
if created:
    user_palais.set_password('temp123')
    user_palais.save()
    print("  - User Django cree")

util_palais, created = Utilisateur.objects.get_or_create(
    user=user_palais,
    defaults={
        'role': 'manager',
        'institut': palais,
        'pin': '234567',  # A CHANGER en production !
        'actif': True
    }
)
if created:
    print("  - Utilisateur Manager Palais cree (PIN: 234567)")
else:
    print("  - Manager Palais existe deja")

# 3. Créer le Manager La Klinic
print("\n3. Creation du Manager La Klinic...")
klinic = Institut.objects.get(code='klinic')
user_klinic, created = User.objects.get_or_create(
    username='manager_klinic',
    defaults={
        'first_name': 'Manager',
        'last_name': 'Klinic',
    }
)
if created:
    user_klinic.set_password('temp123')
    user_klinic.save()
    print("  - User Django cree")

util_klinic, created = Utilisateur.objects.get_or_create(
    user=user_klinic,
    defaults={
        'role': 'manager',
        'institut': klinic,
        'pin': '345678',  # A CHANGER en production !
        'actif': True
    }
)
if created:
    print("  - Utilisateur Manager Klinic cree (PIN: 345678)")
else:
    print("  - Manager Klinic existe deja")

# 4. Créer le Manager Express
print("\n4. Creation du Manager Express...")
express = Institut.objects.get(code='express')
user_express, created = User.objects.get_or_create(
    username='manager_express',
    defaults={
        'first_name': 'Manager',
        'last_name': 'Express',
    }
)
if created:
    user_express.set_password('temp123')
    user_express.save()
    print("  - User Django cree")

util_express, created = Utilisateur.objects.get_or_create(
    user=user_express,
    defaults={
        'role': 'manager',
        'institut': express,
        'pin': '456789',  # A CHANGER en production !
        'actif': True
    }
)
if created:
    print("  - Utilisateur Manager Express cree (PIN: 456789)")
else:
    print("  - Manager Express existe deja")

print("\n=== RESUME ===")
print(f"Total utilisateurs: {Utilisateur.objects.count()}")
print("\nCOMPTES CREES:")
print("1. Patron            - username: patron          - PIN: 123456")
print("2. Manager Palais    - username: manager_palais  - PIN: 234567")
print("3. Manager Klinic    - username: manager_klinic  - PIN: 345678")
print("4. Manager Express   - username: manager_express - PIN: 456789")
print("\nMot de passe temporaire pour tous: temp123")
print("\n⚠️  IMPORTANT: Changez les codes PIN en production!")
