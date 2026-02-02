from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Max
from django.views.decorators.http import require_POST
from core.decorators import role_required
from core.models import Institut, FamillePrestation, Prestation
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.utils import timezone
import json


@login_required
@role_required(['patron'])
def catalogue_view(request):
    """
    Vue principale du catalogue des prestations.
    """
    instituts = Institut.objects.all().order_by('nom')

    # Institut sélectionné (par défaut le premier)
    institut_code = request.GET.get('institut', 'palais')
    institut_actif = Institut.objects.filter(code=institut_code).first()

    if not institut_actif:
        institut_actif = instituts.first()

    # Familles avec prestations pour l'institut sélectionné
    familles = FamillePrestation.objects.filter(
        institut=institut_actif
    ).prefetch_related(
        'prestations'
    ).order_by('ordre_affichage', 'nom')

    # Recherche
    recherche = request.GET.get('q', '').strip()
    if recherche:
        familles = familles.filter(
            Q(nom__icontains=recherche) |
            Q(prestations__nom__icontains=recherche)
        ).distinct()

    return render(request, 'gestion/catalogue.html', {
        'instituts': instituts,
        'institut_actif': institut_actif,
        'familles': familles,
        'recherche': recherche,
    })


@login_required
@role_required(['patron'])
@require_POST
def creer_famille(request):
    """
    Créer une nouvelle famille de prestations.
    """
    try:
        data = json.loads(request.body)

        institut = Institut.objects.get(id=data['institut_id'])

        # Vérifier que le nom n'existe pas déjà dans cet institut
        if FamillePrestation.objects.filter(
            nom__iexact=data['nom'],
            institut=institut
        ).exists():
            return JsonResponse({
                'success': False,
                'error': 'Une famille avec ce nom existe déjà dans cet institut'
            })

        # Déterminer l'ordre (dernière position)
        dernier_ordre = FamillePrestation.objects.filter(
            institut=institut
        ).aggregate(Max('ordre_affichage'))['ordre_affichage__max'] or 0

        famille = FamillePrestation.objects.create(
            nom=data['nom'],
            institut=institut,
            couleur=data.get('couleur', '#3498db'),
            ordre_affichage=dernier_ordre + 1
        )

        return JsonResponse({
            'success': True,
            'famille': {
                'id': famille.id,
                'nom': famille.nom,
                'couleur': famille.couleur
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required(['patron'])
@require_POST
def modifier_famille(request, famille_id):
    """
    Modifier une famille existante.
    """
    try:
        data = json.loads(request.body)
        famille = get_object_or_404(FamillePrestation, id=famille_id)

        # Vérifier unicité du nom si changé
        if data.get('nom') and data['nom'].lower() != famille.nom.lower():
            if FamillePrestation.objects.filter(
                nom__iexact=data['nom'],
                institut=famille.institut
            ).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Une famille avec ce nom existe déjà'
                })

        # Mettre à jour
        if 'nom' in data:
            famille.nom = data['nom']
        if 'couleur' in data:
            famille.couleur = data['couleur']

        famille.save()

        return JsonResponse({
            'success': True,
            'famille': {
                'id': famille.id,
                'nom': famille.nom,
                'couleur': famille.couleur
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required(['patron'])
@require_POST
def supprimer_famille(request, famille_id):
    """
    Supprimer une famille et toutes ses prestations.
    """
    try:
        data = json.loads(request.body)
        famille = get_object_or_404(FamillePrestation, id=famille_id)

        # Vérifier la confirmation
        if data.get('confirmation') != 'SUPPRIMER':
            return JsonResponse({
                'success': False,
                'error': 'Veuillez taper "SUPPRIMER" pour confirmer'
            })

        nom_famille = famille.nom
        nb_prestations = famille.prestations.count()

        # Supprimer (cascade sur les prestations)
        famille.delete()

        return JsonResponse({
            'success': True,
            'message': f'Famille "{nom_famille}" et {nb_prestations} prestation(s) supprimées'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required(['patron'])
def famille_info_suppression(request, famille_id):
    """
    Récupère les informations avant suppression d'une famille.
    """
    famille = get_object_or_404(FamillePrestation, id=famille_id)
    nb_prestations = famille.prestations.count()

    return JsonResponse({
        'famille': {
            'id': famille.id,
            'nom': famille.nom,
        },
        'nb_prestations': nb_prestations
    })


@login_required
@role_required(['patron'])
@require_POST
def deplacer_famille(request, famille_id, direction):
    """
    Monter ou descendre une famille.
    direction: 'up' ou 'down'
    """
    try:
        famille = get_object_or_404(FamillePrestation, id=famille_id)

        if direction == 'up':
            # Trouver la famille au-dessus
            famille_dessus = FamillePrestation.objects.filter(
                institut=famille.institut,
                ordre_affichage__lt=famille.ordre_affichage
            ).order_by('-ordre_affichage').first()

            if famille_dessus:
                # Échanger les ordres
                famille.ordre_affichage, famille_dessus.ordre_affichage = (
                    famille_dessus.ordre_affichage, famille.ordre_affichage
                )
                famille.save()
                famille_dessus.save()

        elif direction == 'down':
            # Trouver la famille en-dessous
            famille_dessous = FamillePrestation.objects.filter(
                institut=famille.institut,
                ordre_affichage__gt=famille.ordre_affichage
            ).order_by('ordre_affichage').first()

            if famille_dessous:
                famille.ordre_affichage, famille_dessous.ordre_affichage = (
                    famille_dessous.ordre_affichage, famille.ordre_affichage
                )
                famille.save()
                famille_dessous.save()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# GESTION DES PRESTATIONS
# =============================================================================

@login_required
@role_required(['patron'])
@require_POST
def creer_prestation(request):
    """
    Créer une nouvelle prestation.
    """
    try:
        data = json.loads(request.body)

        famille = FamillePrestation.objects.get(id=data['famille_id'])

        # Vérifier que le nom n'existe pas déjà dans cette famille
        if Prestation.objects.filter(
            nom__iexact=data['nom'],
            famille=famille
        ).exists():
            return JsonResponse({
                'success': False,
                'error': 'Une prestation avec ce nom existe déjà dans cette famille'
            })

        # Déterminer l'ordre (dernière position)
        dernier_ordre = Prestation.objects.filter(
            famille=famille
        ).aggregate(Max('ordre_affichage'))['ordre_affichage__max'] or 0

        # Créer la prestation
        prestation = Prestation.objects.create(
            nom=data['nom'],
            famille=famille,
            type_prestation=data.get('type_prestation', 'normal'),
            prix=data.get('prix', 0),
            duree_minutes=data.get('duree_minutes'),
            unite=data.get('unite', ''),
            nombre_seances=data.get('nb_seances', 1),
            ordre_affichage=dernier_ordre + 1
        )

        # Associer les instituts
        if 'instituts' in data:
            prestation.instituts.set(data['instituts'])

        return JsonResponse({
            'success': True,
            'prestation': {
                'id': prestation.id,
                'nom': prestation.nom,
                'type_prestation': prestation.type_prestation,
                'prix': float(prestation.prix),
                'duree_minutes': prestation.duree_minutes,
                'unite': prestation.unite,
                'nb_seances': prestation.nb_seances,
                'actif': prestation.actif
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required(['patron'])
@require_POST
def modifier_prestation(request, prestation_id):
    """
    Modifier une prestation existante.
    """
    try:
        data = json.loads(request.body)
        prestation = get_object_or_404(Prestation, id=prestation_id)

        # Vérifier unicité du nom si changé
        if data.get('nom') and data['nom'].lower() != prestation.nom.lower():
            if Prestation.objects.filter(
                nom__iexact=data['nom'],
                famille=prestation.famille
            ).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Une prestation avec ce nom existe déjà dans cette famille'
                })

        # Mettre à jour les champs
        if 'nom' in data:
            prestation.nom = data['nom']
        if 'type_prestation' in data:
            prestation.type_prestation = data['type_prestation']
        if 'prix' in data:
            prestation.prix = data['prix']
        if 'duree_minutes' in data:
            prestation.duree_minutes = data['duree_minutes']
        if 'unite' in data:
            prestation.unite = data['unite']
        if 'nb_seances' in data:
            prestation.nombre_seances = data['nb_seances']

        prestation.save()

        # Mettre à jour les instituts
        if 'instituts' in data:
            prestation.instituts.set(data['instituts'])

        return JsonResponse({
            'success': True,
            'prestation': {
                'id': prestation.id,
                'nom': prestation.nom,
                'type_prestation': prestation.type_prestation,
                'prix': float(prestation.prix),
                'duree_minutes': prestation.duree_minutes,
                'unite': prestation.unite,
                'nb_seances': prestation.nb_seances,
                'actif': prestation.actif
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required(['patron'])
@require_POST
def supprimer_prestation(request, prestation_id):
    """
    Supprimer une prestation.
    """
    try:
        data = json.loads(request.body)
        prestation = get_object_or_404(Prestation, id=prestation_id)

        # Vérifier la confirmation
        if data.get('confirmation') != 'SUPPRIMER':
            return JsonResponse({
                'success': False,
                'error': 'Veuillez taper "SUPPRIMER" pour confirmer'
            })

        nom_prestation = prestation.nom

        # Supprimer
        prestation.delete()

        return JsonResponse({
            'success': True,
            'message': f'Prestation "{nom_prestation}" supprimée'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required(['patron'])
def prestation_info_suppression(request, prestation_id):
    """
    Récupère les informations avant suppression d'une prestation.
    """
    prestation = get_object_or_404(Prestation, id=prestation_id)

    # Vérifier si la prestation est utilisée dans des réservations ou paiements
    # Pour l'instant on retourne juste les infos de base
    return JsonResponse({
        'prestation': {
            'id': prestation.id,
            'nom': prestation.nom,
            'famille': prestation.famille.nom
        }
    })


@login_required
@role_required(['patron'])
def prestation_details(request, prestation_id):
    """
    Récupère toutes les informations d'une prestation pour l'édition.
    """
    prestation = get_object_or_404(Prestation, id=prestation_id)

    # Récupérer les IDs des instituts associés
    instituts_ids = list(prestation.instituts.values_list('id', flat=True))

    return JsonResponse({
        'success': True,
        'prestation': {
            'id': prestation.id,
            'nom': prestation.nom,
            'famille_id': prestation.famille.id,
            'type_prestation': prestation.type_prestation,
            'prix': prestation.prix,
            'duree_minutes': prestation.duree_minutes,
            'unite': prestation.unite or '',
            'nb_seances': prestation.nombre_seances,
            'instituts': instituts_ids,
            'actif': prestation.actif
        }
    })


@login_required
@role_required(['patron'])
@require_POST
def toggle_prestation_actif(request, prestation_id):
    """
    Activer/désactiver une prestation.
    """
    try:
        prestation = get_object_or_404(Prestation, id=prestation_id)
        prestation.actif = not prestation.actif
        prestation.save()

        return JsonResponse({
            'success': True,
            'actif': prestation.actif
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required(['patron'])
@require_POST
def deplacer_prestation(request, prestation_id, direction):
    """
    Monter ou descendre une prestation.
    direction: 'up' ou 'down'
    """
    try:
        prestation = get_object_or_404(Prestation, id=prestation_id)

        if direction == 'up':
            # Trouver la prestation au-dessus
            prestation_dessus = Prestation.objects.filter(
                famille=prestation.famille,
                ordre_affichage__lt=prestation.ordre_affichage
            ).order_by('-ordre_affichage').first()

            if prestation_dessus:
                # Échanger les ordres
                prestation.ordre_affichage, prestation_dessus.ordre_affichage = (
                    prestation_dessus.ordre_affichage, prestation.ordre_affichage
                )
                prestation.save()
                prestation_dessus.save()

        elif direction == 'down':
            # Trouver la prestation en-dessous
            prestation_dessous = Prestation.objects.filter(
                famille=prestation.famille,
                ordre_affichage__gt=prestation.ordre_affichage
            ).order_by('ordre_affichage').first()

            if prestation_dessous:
                prestation.ordre_affichage, prestation_dessous.ordre_affichage = (
                    prestation_dessous.ordre_affichage, prestation.ordre_affichage
                )
                prestation.save()
                prestation_dessous.save()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# RÉORDONNANCEMENT DRAG & DROP
# =============================================================================

@login_required
@role_required(['patron'])
@require_POST
def reordonner_familles(request, institut_id):
    """
    Réorganiser l'ordre des familles après drag & drop.
    Reçoit une liste d'IDs dans le nouvel ordre.
    """
    try:
        data = json.loads(request.body)
        famille_ids = data.get('famille_ids', [])

        # Vérifier que l'institut existe
        institut = get_object_or_404(Institut, id=institut_id)

        # Mettre à jour l'ordre d'affichage de chaque famille
        for index, famille_id in enumerate(famille_ids):
            FamillePrestation.objects.filter(
                id=famille_id,
                institut=institut
            ).update(ordre_affichage=index + 1)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@role_required(['patron'])
@require_POST
def reordonner_prestations(request, famille_id):
    """
    Réorganiser l'ordre des prestations dans une famille après drag & drop.
    Reçoit une liste d'IDs dans le nouvel ordre.
    """
    try:
        data = json.loads(request.body)
        prestation_ids = data.get('prestation_ids', [])

        # Vérifier que la famille existe
        famille = get_object_or_404(FamillePrestation, id=famille_id)

        # Mettre à jour l'ordre d'affichage de chaque prestation
        for index, prestation_id in enumerate(prestation_ids):
            Prestation.objects.filter(
                id=prestation_id,
                famille=famille
            ).update(ordre_affichage=index + 1)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# EXPORT EXCEL
# =============================================================================

@login_required
@role_required(['patron'])
def export_catalogue_excel(request):
    """
    Exporter le catalogue des prestations en Excel.
    """
    try:
        # Institut sélectionné
        institut_code = request.GET.get('institut', 'palais')
        institut = Institut.objects.filter(code=institut_code).first()

        if not institut:
            institut = Institut.objects.first()

        # Créer le workbook
        wb = Workbook()
        ws = wb.active
        ws.title = f"Catalogue {institut.nom}"

        # Styles
        header_fill = PatternFill(start_color="E8B4B8", end_color="E8B4B8", fill_type="solid")
        famille_fill = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
        header_font = Font(bold=True, size=12, color="FFFFFF")
        famille_font = Font(bold=True, size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # En-tête du document
        ws['A1'] = f"CATALOGUE DES PRESTATIONS - {institut.nom.upper()}"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = Alignment(horizontal='center')
        ws.merge_cells('A1:G1')

        ws['A2'] = f"Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}"
        ws['A2'].alignment = Alignment(horizontal='center')
        ws.merge_cells('A2:G2')

        # En-têtes des colonnes
        row = 4
        headers = ['Famille', 'Prestation', 'Type', 'Prix (CFA)', 'Durée', 'Unité', 'Statut']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border

        # Données
        row = 5
        familles = FamillePrestation.objects.filter(
            institut=institut,
            actif=True
        ).prefetch_related('prestations').order_by('ordre_affichage', 'nom')

        for famille in familles:
            prestations = famille.prestations.order_by('ordre_affichage', 'nom')

            if not prestations.exists():
                # Famille sans prestations
                ws.cell(row=row, column=1, value=famille.nom).font = famille_font
                ws.cell(row=row, column=1).fill = famille_fill
                ws.cell(row=row, column=2, value="(Aucune prestation)")
                for col in range(1, 8):
                    ws.cell(row=row, column=col).border = border
                row += 1
            else:
                # Prestations de la famille
                for idx, prestation in enumerate(prestations):
                    # Afficher le nom de la famille uniquement sur la première ligne
                    if idx == 0:
                        cell = ws.cell(row=row, column=1, value=famille.nom)
                        cell.font = famille_font
                        cell.fill = famille_fill
                    else:
                        cell = ws.cell(row=row, column=1, value="")
                        cell.fill = famille_fill

                    # Type de prestation
                    if prestation.type_prestation == 'forfait':
                        type_display = f"Forfait ({prestation.nombre_seances} séances)"
                    elif prestation.type_prestation == 'option':
                        type_display = "Option"
                    else:
                        type_display = "Normal"

                    # Données de la prestation
                    ws.cell(row=row, column=2, value=prestation.nom)
                    ws.cell(row=row, column=3, value=type_display)
                    ws.cell(row=row, column=4, value=prestation.prix)
                    ws.cell(row=row, column=5, value=prestation.get_duree_display())
                    ws.cell(row=row, column=6, value=prestation.unite or "-")
                    ws.cell(row=row, column=7, value="Actif" if prestation.actif else "Inactif")

                    # Bordures
                    for col in range(1, 8):
                        ws.cell(row=row, column=col).border = border

                    row += 1

        # Ajuster les largeurs de colonnes
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 20
        ws.column_dimensions['G'].width = 12

        # Générer la réponse
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'catalogue_{institut.code}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        wb.save(response)

        return response

    except Exception as e:
        return HttpResponse(f"Erreur lors de l'export: {str(e)}", status=500)
