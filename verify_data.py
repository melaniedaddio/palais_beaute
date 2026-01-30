#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'le_palais_beaute.settings')
django.setup()

from core.models import *

print("=== VERIFICATION DES DONNEES ===\n")

# Instituts
print("INSTITUTS:")
for institut in Institut.objects.all():
    print(f"  - {institut.nom} (code: {institut.code}, agenda: {institut.a_agenda})")

# Employés Express
print("\nEMPLOYES EXPRESS:")
express = Institut.objects.get(code='express')
for employe in Employe.objects.filter(institut=express):
    print(f"  - {employe.nom}")

# Prestations Express (quelques exemples)
print("\nPRESTATIONS EXPRESS (exemples):")
for famille in FamillePrestation.objects.filter(institut=express):
    print(f"\n  {famille.nom} ({famille.prestations.count()} prestations):")
    for p in famille.prestations.all()[:3]:
        unite = f" {p.unite}" if p.unite else ""
        print(f"    - {p.nom}: {p.prix} CFA ({p.get_duree_display()}){unite}")

# Options
print("\nOPTIONS:")
for institut in Institut.objects.all():
    options = Option.objects.filter(institut=institut)
    if options.exists():
        print(f"\n  {institut.nom}:")
        for opt in options:
            print(f"    - {opt.nom}: {opt.prix} CFA (quantite: {opt.a_quantite})")

print("\n=== TOTAUX ===")
print(f"Instituts: {Institut.objects.count()}")
print(f"Employes: {Employe.objects.count()}")
print(f"Familles de prestations: {FamillePrestation.objects.count()}")
print(f"Prestations: {Prestation.objects.count()}")
print(f"Options: {Option.objects.count()}")
