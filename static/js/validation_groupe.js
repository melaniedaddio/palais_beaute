/**
 * Fichier JavaScript pour la validation groupée et le double paiement
 * À inclure dans le template agenda.html
 */

// Fonction pour activer/désactiver le double paiement
function toggleDoublePaiement() {
    const checkbox = document.getElementById('utilise-double-paiement');
    const montant1Group = document.getElementById('montant-moyen-1-group');
    const moyen2Section = document.getElementById('section-moyen-paiement-2');
    const label1 = document.getElementById('label-moyen-paiement-1');

    if (checkbox.checked) {
        // Activer le double paiement
        montant1Group.style.display = 'block';
        moyen2Section.style.display = 'block';
        label1.textContent = '1er moyen de paiement';

        // Initialiser le montant du premier moyen à 0
        document.getElementById('montant-paiement-1').value = '';
        calculerMontant2();
    } else {
        // Désactiver le double paiement
        montant1Group.style.display = 'none';
        moyen2Section.style.display = 'none';
        label1.textContent = 'Moyen de paiement';
    }
}

// Fonction pour calculer automatiquement le montant du 2ème moyen
function calculerMontant2() {
    const montant1 = parseFloat(document.getElementById('montant-paiement-1').value) || 0;

    // Récupérer le total des cartes cadeaux s'il y en a
    const checks = document.querySelectorAll('.carte-cadeau-check:checked');
    let totalCartes = 0;
    checks.forEach(check => {
        const carteId = check.dataset.carteId;
        const montantInput = document.querySelector(`.carte-cadeau-montant[data-carte-id="${carteId}"]`);
        totalCartes += parseInt(montantInput.value) || 0;
    });

    const montant2 = Math.max(0, validationPrixTotal - totalCartes - montant1);
    document.getElementById('montant-paiement-2-text').textContent = montant2.toLocaleString('fr-FR') + ' CFA';
}

// Fonction modifiée pour charger la validation (détection multi-RDV)
function ouvrirModalValidationAvecDetection(rdvId) {
    showPageLoader('Chargement...');

    // D'abord, vérifier s'il y a plusieurs RDV pour ce client ce jour
    fetch('/agenda/{{ institut.code }}/api/rdv/' + rdvId + '/client-jour/')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.nb_rdvs > 1) {
                // Validation groupée
                afficherValidationGroupee(data);
            } else {
                // Validation unique (appeler la fonction originale)
                chargerRdvUniqueOriginal(rdvId);
            }
        })
        .catch(error => {
            // En cas d'erreur, utiliser la validation unique
            console.warn('Impossible de charger les RDV du client, validation unique', error);
            chargerRdvUniqueOriginal(rdvId);
        });
}

function afficherValidationGroupee(data) {
    rdvsAValider = data.rdvs;

    // Masquer RDV unique, afficher RDV groupé
    document.getElementById('rdv-unique-info').style.display = 'none';
    document.getElementById('rdv-groupe-info').style.display = 'block';
    document.getElementById('validation-mode-groupe').value = 'true';

    // Remplir les infos
    document.getElementById('rdv-groupe-count').textContent = data.nb_rdvs;
    document.getElementById('rdv-groupe-client').textContent = data.client;
    document.getElementById('validation-prix-total-groupe').textContent = data.prix_total_global.toLocaleString('fr-FR') + ' CFA';

    // Construire la liste des RDV
    let listeHtml = '';
    data.rdvs.forEach((rdv, index) => {
        listeHtml += `<div style="background: #fff; border-left: 4px solid #c9a86a; padding: 12px; margin-bottom: 8px; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <strong>${rdv.prestation}</strong>
                <span style="color: #c9a86a; font-weight: 600;">${rdv.prix_total.toLocaleString('fr-FR')} CFA</span>
            </div>
            <div style="font-size: 13px; color: #666;">
                ${rdv.heure_debut} - ${rdv.heure_fin} • ${rdv.employe}
                ${rdv.options.length > 0 ? '<br>Options : ' + rdv.options.map(o => o.nom).join(', ') : ''}
            </div>
        </div>`;
    });
    document.getElementById('rdv-groupe-liste').innerHTML = listeHtml;

    validationPrixTotal = data.prix_total_global;
    validationClientId = data.rdvs[0].client_id || null;

    // Réinitialiser le formulaire
    document.getElementById('validation-type-paiement').value = 'complet';
    document.getElementById('utilise-double-paiement').checked = false;
    toggleDoublePaiement();

    // Afficher le modal
    hidePageLoader();
    document.getElementById('modal-validation').style.display = 'flex';

    // Charger les cartes cadeaux
    // Note: cette fonction existe déjà dans le template
    if (validationClientId) {
        chargerCartesCadeaux(validationClientId);
    }
}

function chargerRdvUniqueOriginal(rdvId) {
    // Cette fonction correspond au code original de ouvrirModalValidation
    // Elle sera appelée si un seul RDV existe
    fetch('/agenda/{{ institut.code }}/api/rdv/' + rdvId + '/')
        .then(response => response.json())
        .then(rdv => {
            rdvsAValider = []; // Pas de mode groupe

            // Afficher RDV unique, masquer RDV groupé
            document.getElementById('rdv-unique-info').style.display = 'block';
            document.getElementById('rdv-groupe-info').style.display = 'none';
            document.getElementById('validation-mode-groupe').value = 'false';

            document.getElementById('validation-rdv-id').value = rdv.id;
            document.getElementById('validation-client').textContent = rdv.client;
            document.getElementById('validation-prestation').textContent = rdv.prestation;
            document.getElementById('validation-date').textContent = rdv.date;
            document.getElementById('validation-heure').textContent = rdv.heure_debut;
            document.getElementById('validation-prix-total').textContent = rdv.prix_total.toLocaleString('fr-FR') + ' CFA';

            validationPrixTotal = rdv.prix_total;
            validationClientId = rdv.client_id;
            document.getElementById('validation-montant').value = rdv.prix_total;

            // Réinitialiser le formulaire
            document.getElementById('validation-type-paiement').value = 'complet';
            document.getElementById('utilise-double-paiement').checked = false;
            toggleDoublePaiement();

            hidePageLoader();
            document.getElementById('modal-validation').style.display = 'flex';

            // Charger les cartes cadeaux du client
            chargerCartesCadeaux(rdv.client_id);
        })
        .catch(error => {
            hidePageLoader();
            showError('Erreur lors du chargement: ' + error);
        });
}
