# AUDIT DÉTAILLÉ - NOUVELLES FONCTIONNALITÉS
## Le Palais de la Beauté

**Date :** Février 2025  
**Objectif :** Recueillir les besoins précis pour implémenter les modules :
- Gestion des salaires et présences
- Gestion des stocks
- Gestion des dépenses et comptabilité

---

# 📋 SOMMAIRE

1. [Module Salaires & Présences](#1-module-salaires--présences)
2. [Module Stocks](#2-module-stocks)
3. [Module Dépenses & Comptabilité](#3-module-dépenses--comptabilité)
4. [Questions transversales](#4-questions-transversales)

---

# 1. MODULE SALAIRES & PRÉSENCES

## 1.1 Informations sur les employés

### Salaire de base

| # | Question | Réponse |
|---|----------|---------|
| 1.1.1 | Le salaire est-il **mensuel** ou **horaire** ? | ☐ Mensuel fixe ☐ Horaire ☐ Les deux selon l'employé |
| 1.1.2 | Y a-t-il des **catégories** d'employés avec des salaires différents ? (Ex: Manager, Esthéticienne senior, Junior, Stagiaire) | |
| 1.1.3 | Le salaire peut-il varier d'un mois à l'autre pour le même employé ? (Ex: heures sup, primes) | ☐ Oui ☐ Non |
| 1.1.4 | Y a-t-il des **primes** ? Si oui, lesquelles ? (Ex: prime d'assiduité, prime de performance, prime de fin d'année) | |
| 1.1.5 | Y a-t-il des **avances sur salaire** à gérer ? | ☐ Oui ☐ Non |
| 1.1.6 | Le salaire est-il le même pour les 3 instituts ou différent ? | ☐ Même ☐ Différent par institut |

### Contrat et horaires

| # | Question | Réponse |
|---|----------|---------|
| 1.1.7 | Quels sont les **jours de travail** habituels ? (Ex: Lundi-Samedi, 6j/7) | |
| 1.1.8 | Quels sont les **horaires** habituels ? (Ex: 8h-18h, 9h-19h) | |
| 1.1.9 | Les horaires sont-ils les mêmes pour tous les employés ? | ☐ Oui ☐ Non, variables |
| 1.1.10 | Y a-t-il des employés à **temps partiel** ? | ☐ Oui ☐ Non |
| 1.1.11 | Combien d'heures par semaine pour un temps plein ? | |
| 1.1.12 | Y a-t-il des **heures supplémentaires** ? Comment sont-elles rémunérées ? | |

---

## 1.2 Gestion des présences

### Pointage quotidien

| # | Question | Réponse |
|---|----------|---------|
| 1.2.1 | **Qui** saisit les présences ? | ☐ Le manager de chaque institut ☐ Un admin central ☐ L'employé lui-même |
| 1.2.2 | **Quand** les présences sont-elles saisies ? | ☐ En temps réel (arrivée/départ) ☐ À la fin de la journée ☐ À la fin de la semaine |
| 1.2.3 | Faut-il enregistrer **l'heure d'arrivée et de départ** exacte ? | ☐ Oui ☐ Non, juste présent/absent |
| 1.2.4 | Y a-t-il des **pauses** à comptabiliser ? (Ex: pause déjeuner) | ☐ Oui, durée : _____ ☐ Non |
| 1.2.5 | Un employé peut-il travailler dans **plusieurs instituts** le même jour ? | ☐ Oui ☐ Non |
| 1.2.6 | Faut-il un système de **validation** des présences par un supérieur ? | ☐ Oui ☐ Non |

### Types d'absences

| # | Question | Réponse |
|---|----------|---------|
| 1.2.7 | Quels sont les **types d'absences** à gérer ? | ☐ Absence justifiée ☐ Absence non justifiée ☐ Congé payé ☐ Congé maladie ☐ Congé maternité ☐ Permission ☐ Retard ☐ Autres : _______ |
| 1.2.8 | Quelles absences sont **payées** et lesquelles ne le sont pas ? | |
| 1.2.9 | Combien de jours de **congés payés** par an ? | |
| 1.2.10 | Comment sont gérés les **jours fériés** ? | ☐ Payés non travaillés ☐ Travaillés avec majoration ☐ Repos compensateur |
| 1.2.11 | Y a-t-il un **quota** de jours d'absence justifiée autorisés ? | |
| 1.2.12 | Faut-il joindre un **justificatif** pour les absences ? (Ex: certificat médical) | ☐ Oui ☐ Non |

### Retards

| # | Question | Réponse |
|---|----------|---------|
| 1.2.13 | Comment sont gérés les **retards** ? | ☐ Ignorés ☐ Cumulés en heures déduites ☐ Avertissement après X retards |
| 1.2.14 | À partir de combien de minutes est-ce considéré comme un retard ? | |
| 1.2.15 | Y a-t-il des **sanctions** pour les retards répétés ? | |

---

## 1.3 Calcul du salaire

### Formule de calcul

| # | Question | Réponse |
|---|----------|---------|
| 1.3.1 | Comment calculer la **retenue par jour** d'absence non justifiée ? | ☐ Salaire ÷ 30 jours ☐ Salaire ÷ nombre de jours travaillés du mois ☐ Autre : _______ |
| 1.3.2 | Les **demi-journées** d'absence sont-elles gérées ? | ☐ Oui ☐ Non |
| 1.3.3 | Y a-t-il des **cotisations sociales** à déduire ? | ☐ Oui, lesquelles : _______ ☐ Non |
| 1.3.4 | Y a-t-il un **impôt sur salaire** à déduire ? | ☐ Oui ☐ Non |
| 1.3.5 | Y a-t-il d'autres **retenues** possibles ? (Ex: prêt, casse, uniforme) | |

### Exemple de calcul souhaité

| # | Question | Réponse |
|---|----------|---------|
| 1.3.6 | Pouvez-vous donner un **exemple concret** de calcul de salaire avec absences ? | |
| 1.3.7 | Salaire brut - Retenues = Salaire net. Y a-t-il autre chose ? | |

---

## 1.4 Fiche de paie et historique

| # | Question | Réponse |
|---|----------|---------|
| 1.4.1 | Faut-il générer une **fiche de paie** imprimable ? | ☐ Oui ☐ Non |
| 1.4.2 | Quelles informations sur la fiche de paie ? | ☐ Salaire de base ☐ Jours travaillés ☐ Absences détaillées ☐ Retenues ☐ Primes ☐ Net à payer ☐ Autres : _______ |
| 1.4.3 | Faut-il un **historique** des salaires par employé ? | ☐ Oui ☐ Non |
| 1.4.4 | Sur combien de mois/années garder l'historique ? | |
| 1.4.5 | Le paiement du salaire est-il enregistré ? (date, mode de paiement) | ☐ Oui ☐ Non |

---

## 1.5 Tableau de bord et rapports

| # | Question | Réponse |
|---|----------|---------|
| 1.5.1 | Quels **indicateurs** voulez-vous voir ? | ☐ Total salaires du mois ☐ Taux d'absentéisme ☐ Heures travaillées ☐ Comparaison mois par mois ☐ Par institut ☐ Autres : _______ |
| 1.5.2 | Faut-il un **rapport mensuel** récapitulatif des salaires ? | ☐ Oui ☐ Non |
| 1.5.3 | Qui peut voir les salaires ? | ☐ Patron uniquement ☐ Patron + Managers ☐ Autres : _______ |

---

# 2. MODULE STOCKS

## 2.1 Types de produits

| # | Question | Réponse |
|---|----------|---------|
| 2.1.1 | Quels **types de produits** gérez-vous ? | ☐ Produits pour prestations (vernis, gel, crèmes...) ☐ Produits à vendre aux clients ☐ Consommables (coton, papier...) ☐ Équipements ☐ Autres : _______ |
| 2.1.2 | Combien de **références produits** approximativement ? | |
| 2.1.3 | Les produits sont-ils **partagés** entre les 3 instituts ou chaque institut a son stock propre ? | ☐ Stock commun ☐ Stock par institut |
| 2.1.4 | Y a-t-il des **transferts** de stock entre instituts ? | ☐ Oui ☐ Non |

## 2.2 Informations produit

| # | Question | Réponse |
|---|----------|---------|
| 2.2.1 | Quelles informations pour chaque produit ? | ☐ Nom ☐ Référence/Code ☐ Catégorie ☐ Prix d'achat ☐ Prix de vente ☐ Fournisseur ☐ Quantité min (alerte) ☐ Date de péremption ☐ Photo ☐ Autres : _______ |
| 2.2.2 | Les produits ont-ils des **variantes** ? (Ex: vernis rouge, vernis bleu) | ☐ Oui ☐ Non |
| 2.2.3 | Y a-t-il des **lots** avec dates de péremption différentes ? | ☐ Oui ☐ Non |

## 2.3 Mouvements de stock

### Entrées

| # | Question | Réponse |
|---|----------|---------|
| 2.3.1 | Comment sont enregistrées les **entrées** de stock ? | ☐ Réception commande fournisseur ☐ Transfert entre instituts ☐ Retour client ☐ Inventaire (ajustement) ☐ Autres : _______ |
| 2.3.2 | Faut-il enregistrer le **fournisseur** et le **prix d'achat** à chaque entrée ? | ☐ Oui ☐ Non |
| 2.3.3 | Y a-t-il un **bon de réception** à générer ? | ☐ Oui ☐ Non |

### Sorties

| # | Question | Réponse |
|---|----------|---------|
| 2.3.4 | Comment sont enregistrées les **sorties** de stock ? | ☐ Utilisation pour prestation ☐ Vente au client ☐ Perte/casse ☐ Péremption ☐ Transfert entre instituts ☐ Autres : _______ |
| 2.3.5 | La sortie de stock pour une prestation est-elle **automatique** ? (Ex: 1 pose gel = -1 pot de gel) | ☐ Oui, automatique ☐ Non, manuelle ☐ Les deux |
| 2.3.6 | Si automatique, comment définir la consommation par prestation ? | |

## 2.4 Inventaire

| # | Question | Réponse |
|---|----------|---------|
| 2.4.1 | À quelle **fréquence** faites-vous l'inventaire ? | ☐ Mensuel ☐ Trimestriel ☐ Annuel ☐ Jamais actuellement |
| 2.4.2 | Comment voulez-vous gérer les **écarts d'inventaire** ? | |
| 2.4.3 | Faut-il un **historique** des inventaires ? | ☐ Oui ☐ Non |

## 2.5 Alertes et seuils

| # | Question | Réponse |
|---|----------|---------|
| 2.5.1 | Faut-il une **alerte stock bas** ? | ☐ Oui ☐ Non |
| 2.5.2 | Comment définir le seuil minimum ? | ☐ Par produit ☐ Valeur par défaut pour tous |
| 2.5.3 | Comment recevoir l'alerte ? | ☐ Dans l'interface ☐ Par email ☐ Les deux |
| 2.5.4 | Faut-il une alerte pour les **produits bientôt périmés** ? | ☐ Oui ☐ Non |

## 2.6 Fournisseurs

| # | Question | Réponse |
|---|----------|---------|
| 2.6.1 | Faut-il gérer une **liste de fournisseurs** ? | ☐ Oui ☐ Non |
| 2.6.2 | Quelles informations pour un fournisseur ? | ☐ Nom ☐ Contact ☐ Téléphone ☐ Email ☐ Adresse ☐ Conditions de paiement ☐ Autres : _______ |
| 2.6.3 | Faut-il gérer les **commandes fournisseurs** ? | ☐ Oui ☐ Non |
| 2.6.4 | Un produit peut-il avoir **plusieurs fournisseurs** ? | ☐ Oui ☐ Non |

## 2.7 Rapports stock

| # | Question | Réponse |
|---|----------|---------|
| 2.7.1 | Quels **rapports** souhaitez-vous ? | ☐ État du stock actuel ☐ Mouvements du mois ☐ Valeur du stock ☐ Produits les plus utilisés ☐ Produits les plus vendus ☐ Autres : _______ |
| 2.7.2 | Faut-il pouvoir **exporter** les données ? (Excel, PDF) | ☐ Oui ☐ Non |

---

# 3. MODULE DÉPENSES & COMPTABILITÉ

## 3.1 Types de dépenses

| # | Question | Réponse |
|---|----------|---------|
| 3.1.1 | Quelles **catégories de dépenses** avez-vous ? | ☐ Achats produits/stock ☐ Salaires ☐ Loyer ☐ Électricité/Eau ☐ Internet/Téléphone ☐ Entretien/Réparations ☐ Marketing/Publicité ☐ Fournitures bureau ☐ Transport ☐ Impôts/Taxes ☐ Assurances ☐ Autres : _______ |
| 3.1.2 | Faut-il pouvoir **créer de nouvelles catégories** ? | ☐ Oui ☐ Non |
| 3.1.3 | Certaines dépenses sont-elles **récurrentes** ? (Ex: loyer tous les mois) | ☐ Oui ☐ Non |

## 3.2 Enregistrement des dépenses

| # | Question | Réponse |
|---|----------|---------|
| 3.2.1 | Quelles informations pour chaque dépense ? | ☐ Date ☐ Montant ☐ Catégorie ☐ Description ☐ Fournisseur/Bénéficiaire ☐ Mode de paiement ☐ Justificatif (photo/scan) ☐ Institut concerné ☐ Autres : _______ |
| 3.2.2 | **Qui** peut enregistrer les dépenses ? | ☐ Patron uniquement ☐ Managers ☐ Tous |
| 3.2.3 | Faut-il une **validation** des dépenses par le patron ? | ☐ Oui ☐ Non |
| 3.2.4 | Les dépenses sont-elles **par institut** ou globales ? | ☐ Par institut ☐ Globales ☐ Les deux |

## 3.3 Types de recettes (entrées d'argent)

| # | Question | Réponse |
|---|----------|---------|
| 3.3.1 | Les **recettes des prestations** sont déjà enregistrées via les paiements. Y a-t-il d'autres recettes ? | ☐ Vente de produits ☐ Location d'espace ☐ Autres : _______ |
| 3.3.2 | Faut-il un module séparé pour la **vente de produits** aux clients ? | ☐ Oui ☐ Non |

## 3.4 Caisse et trésorerie

| # | Question | Réponse |
|---|----------|---------|
| 3.4.1 | Avez-vous une **caisse physique** (espèces) par institut ? | ☐ Oui ☐ Non |
| 3.4.2 | Avez-vous un ou plusieurs **comptes bancaires** ? | ☐ Un compte ☐ Plusieurs (combien : ___) |
| 3.4.3 | Faut-il gérer les **comptes mobile money** (Orange Money, Wave) ? | ☐ Oui ☐ Non |
| 3.4.4 | Faut-il pouvoir enregistrer les **transferts** entre caisses/comptes ? | ☐ Oui ☐ Non |
| 3.4.5 | Faut-il un **rapprochement bancaire** ? | ☐ Oui ☐ Non |

## 3.5 Budget et prévisions

| # | Question | Réponse |
|---|----------|---------|
| 3.5.1 | Faut-il pouvoir définir un **budget mensuel** par catégorie ? | ☐ Oui ☐ Non |
| 3.5.2 | Faut-il une **alerte** si une catégorie dépasse le budget ? | ☐ Oui ☐ Non |
| 3.5.3 | Faut-il des **prévisions** de trésorerie ? | ☐ Oui ☐ Non |

## 3.6 Rapports financiers

| # | Question | Réponse |
|---|----------|---------|
| 3.6.1 | Quels **rapports** souhaitez-vous ? | ☐ Résumé mensuel (recettes - dépenses) ☐ Détail des dépenses par catégorie ☐ Comparaison mois par mois ☐ Comparaison année par année ☐ Par institut ☐ Graphiques d'évolution ☐ Autres : _______ |
| 3.6.2 | Faut-il un **tableau de bord** avec les chiffres clés ? | ☐ Oui ☐ Non |
| 3.6.3 | Quels indicateurs sur le tableau de bord ? | ☐ CA du mois ☐ Dépenses du mois ☐ Bénéfice ☐ CA vs mois précédent ☐ Top prestations ☐ Autres : _______ |
| 3.6.4 | Faut-il pouvoir **exporter** les rapports ? | ☐ Excel ☐ PDF ☐ Les deux |

---

# 4. QUESTIONS TRANSVERSALES

## 4.1 Droits d'accès

| # | Question | Réponse |
|---|----------|---------|
| 4.1.1 | Qui peut accéder au **module Salaires** ? | ☐ Patron uniquement ☐ Patron + Comptable ☐ Autres : _______ |
| 4.1.2 | Qui peut accéder au **module Stocks** ? | ☐ Patron ☐ Managers ☐ Tous les employés |
| 4.1.3 | Qui peut accéder au **module Dépenses** ? | ☐ Patron uniquement ☐ Patron + Managers ☐ Autres : _______ |
| 4.1.4 | Un employé peut-il voir **son propre** salaire/présences ? | ☐ Oui ☐ Non |

## 4.2 Multi-instituts

| # | Question | Réponse |
|---|----------|---------|
| 4.2.1 | Les données doivent-elles être **consolidées** (vue globale des 3 instituts) ? | ☐ Oui ☐ Non |
| 4.2.2 | Faut-il pouvoir **comparer** les performances des 3 instituts ? | ☐ Oui ☐ Non |

## 4.3 Période comptable

| # | Question | Réponse |
|---|----------|---------|
| 4.3.1 | L'**année fiscale** commence en janvier ou autre mois ? | |
| 4.3.2 | Faut-il pouvoir **clôturer** un mois/une année ? | ☐ Oui ☐ Non |
| 4.3.3 | Après clôture, peut-on encore modifier les données ? | ☐ Oui ☐ Non |

## 4.4 Priorités

| # | Question | Réponse |
|---|----------|---------|
| 4.4.1 | Quel module est le **plus urgent** ? | ☐ Salaires ☐ Stocks ☐ Dépenses |
| 4.4.2 | Par quel module voulez-vous **commencer** ? | |
| 4.4.3 | Y a-t-il des fonctionnalités **indispensables** vs **souhaitables** ? | |

## 4.5 Données existantes

| # | Question | Réponse |
|---|----------|---------|
| 4.5.1 | Avez-vous des **données existantes** à importer ? (Ex: liste produits Excel) | ☐ Oui ☐ Non |
| 4.5.2 | Utilisez-vous actuellement un autre logiciel pour ces fonctions ? | ☐ Oui, lequel : _______ ☐ Non |
| 4.5.3 | Comment gérez-vous ces aspects **actuellement** ? (Papier, Excel, autre) | |

---

# 5. RÉSUMÉ DES RÉPONSES À OBTENIR

## Priorité HAUTE (bloquant pour commencer)

| Module | Questions clés |
|--------|----------------|
| **Salaires** | Salaire mensuel ou horaire ? Formule de calcul retenue ? Types d'absences ? |
| **Présences** | Qui saisit ? Quand ? Niveau de détail (heures ou juste présent/absent) ? |
| **Stocks** | Stock par institut ou commun ? Sortie auto ou manuelle ? |
| **Dépenses** | Catégories de dépenses ? Par institut ou global ? |

## Priorité MOYENNE (pour affiner)

- Détails des primes et retenues
- Gestion des fournisseurs
- Alertes et seuils
- Format des rapports

## Priorité BASSE (peut être ajouté plus tard)

- Fiches de paie imprimables
- Budget et prévisions
- Rapprochement bancaire

---

# 6. PROCHAINES ÉTAPES

1. ☐ Envoyer ce questionnaire à la cliente
2. ☐ Organiser un appel ou une réunion pour parcourir les questions
3. ☐ Collecter toutes les réponses
4. ☐ Rédiger les PRD détaillés pour chaque module
5. ☐ Valider les PRD avec la cliente
6. ☐ Prioriser et planifier le développement

---

**Ce document est un questionnaire d'audit.**
**Les réponses permettront de créer des PRD précis et adaptés aux besoins réels.**
