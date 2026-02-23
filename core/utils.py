import re
from urllib.parse import quote


def normaliser_telephone_whatsapp(telephone):
    """
    Normalise un numéro de téléphone vers le format WhatsApp international.
    Supporte les formats ivoiriens (+225, 00225, ou 10 chiffres directs).
    Retourne None si le numéro est vide ou invalide.
    """
    if not telephone:
        return None

    # Supprimer tous les espaces, tirets, points, parenthèses
    tel = re.sub(r'[\s\-\.\(\)]', '', str(telephone))

    # Déjà au format international avec +
    if tel.startswith('+'):
        return tel[1:]  # Retirer le +

    # Format 00225XXXXXXXXXX
    if tel.startswith('00'):
        return tel[2:]

    # Numéro local ivoirien (10 chiffres, commence par 0x, 1x, 2x, 4x, 5x, 6x, 7x, 8x)
    if len(tel) == 10 and tel.isdigit():
        return '225' + tel

    # Numéro local ivoirien (8 chiffres)
    if len(tel) == 8 and tel.isdigit():
        return '225' + tel

    # Retourner tel quel si aucun pattern reconnu
    return tel if tel.isdigit() else None


def generer_lien_whatsapp(telephone, message):
    """
    Génère un lien WhatsApp avec le message pré-rempli.
    Retourne None si le téléphone est invalide.
    """
    numero = normaliser_telephone_whatsapp(telephone)
    if not numero:
        return None

    # Les caractères non-ASCII (emoji, accents) sont laissés bruts dans l'URL.
    # WhatsApp et les navigateurs modernes les gèrent nativement.
    # Encoder uniquement les caractères ASCII spéciaux (espace, &, =, +, etc.)
    safe_chars = ''.join(dict.fromkeys(c for c in message if ord(c) > 127))
    message_encode = quote(message, safe=safe_chars)
    return f'https://wa.me/{numero}?text={message_encode}'
