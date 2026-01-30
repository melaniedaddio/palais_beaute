/**
 * Le Palais de la Beauté
 * Fichier JavaScript principal
 */

// Utilitaires
const App = {
    // Formater les montants en CFA
    formatCFA(montant) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'decimal',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(montant) + ' CFA';
    },

    // Formater les dates
    formatDate(date) {
        return new Intl.DateTimeFormat('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(new Date(date));
    },

    // Formater l'heure
    formatTime(time) {
        return time.substring(0, 5); // HH:MM
    },

    // Afficher un message
    showMessage(message, type = 'info') {
        const messagesContainer = document.querySelector('.messages') || this.createMessagesContainer();
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        messagesContainer.appendChild(messageDiv);

        // Auto-fermeture après 5 secondes
        setTimeout(() => {
            messageDiv.style.opacity = '0';
            setTimeout(() => messageDiv.remove(), 300);
        }, 5000);
    },

    // Créer le conteneur de messages s'il n'existe pas
    createMessagesContainer() {
        const container = document.createElement('div');
        container.className = 'messages';
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.insertBefore(container, mainContent.firstChild);
        }
        return container;
    },

    // Confirmation avant suppression
    confirmDelete(message = 'Êtes-vous sûr de vouloir supprimer cet élément ?') {
        return confirm(message);
    },

    // Loader
    showLoader() {
        const loader = document.createElement('div');
        loader.id = 'app-loader';
        loader.className = 'spinner';
        document.body.appendChild(loader);
    },

    hideLoader() {
        const loader = document.getElementById('app-loader');
        if (loader) loader.remove();
    },

    // AJAX helper
    async fetchJSON(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Fetch error:', error);
            this.showMessage('Une erreur est survenue', 'error');
            throw error;
        }
    },

    // Post form avec CSRF
    async postForm(url, formData) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        return await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        });
    }
};

// Modal utility
class Modal {
    constructor(content, options = {}) {
        this.options = {
            title: '',
            closeOnBackdrop: true,
            ...options
        };
        this.create(content);
    }

    create(content) {
        // Backdrop
        this.backdrop = document.createElement('div');
        this.backdrop.className = 'modal-backdrop';

        // Modal
        this.modal = document.createElement('div');
        this.modal.className = 'modal';

        // Header
        if (this.options.title) {
            const header = document.createElement('div');
            header.className = 'modal-header';

            const title = document.createElement('h2');
            title.className = 'modal-title';
            title.textContent = this.options.title;

            const closeBtn = document.createElement('button');
            closeBtn.className = 'modal-close';
            closeBtn.innerHTML = '×';
            closeBtn.onclick = () => this.close();

            header.appendChild(title);
            header.appendChild(closeBtn);
            this.modal.appendChild(header);
        }

        // Content
        const body = document.createElement('div');
        body.className = 'modal-body';
        if (typeof content === 'string') {
            body.innerHTML = content;
        } else {
            body.appendChild(content);
        }
        this.modal.appendChild(body);

        this.backdrop.appendChild(this.modal);

        // Event listeners
        if (this.options.closeOnBackdrop) {
            this.backdrop.addEventListener('click', (e) => {
                if (e.target === this.backdrop) {
                    this.close();
                }
            });
        }

        // Escape key
        this.escapeHandler = (e) => {
            if (e.key === 'Escape') this.close();
        };
        document.addEventListener('keydown', this.escapeHandler);

        document.body.appendChild(this.backdrop);
    }

    close() {
        document.removeEventListener('keydown', this.escapeHandler);
        this.backdrop.remove();
    }
}

// Autocomplete pour recherche clients
class ClientAutocomplete {
    constructor(inputElement, onSelect) {
        this.input = inputElement;
        this.onSelect = onSelect;
        this.results = null;
        this.selectedIndex = -1;
        this.init();
    }

    init() {
        // Créer le conteneur de résultats
        this.results = document.createElement('div');
        this.results.className = 'autocomplete-results';
        this.results.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        `;
        this.input.parentNode.style.position = 'relative';
        this.input.parentNode.appendChild(this.results);

        // Event listeners
        this.input.addEventListener('input', () => this.search());
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.results.contains(e.target)) {
                this.hide();
            }
        });
    }

    async search() {
        const query = this.input.value.trim();
        if (query.length < 2) {
            this.hide();
            return;
        }

        try {
            const data = await App.fetchJSON(`/api/clients/search/?q=${encodeURIComponent(query)}`);
            this.showResults(data.clients);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    showResults(clients) {
        if (clients.length === 0) {
            this.hide();
            return;
        }

        this.results.innerHTML = '';
        this.selectedIndex = -1;

        clients.forEach((client, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.style.cssText = `
                padding: 12px;
                cursor: pointer;
                border-bottom: 1px solid var(--border);
            `;
            item.innerHTML = `
                <div style="font-weight: 500;">${client.full_name}</div>
                <div style="font-size: 12px; color: var(--text-light);">${client.telephone}</div>
            `;

            item.addEventListener('mouseenter', () => {
                this.selectItem(index);
            });

            item.addEventListener('click', () => {
                this.onSelect(client);
                this.hide();
            });

            this.results.appendChild(item);
        });

        this.results.style.display = 'block';
    }

    handleKeydown(e) {
        const items = this.results.querySelectorAll('.autocomplete-item');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
            this.selectItem(this.selectedIndex);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
            this.selectItem(this.selectedIndex);
        } else if (e.key === 'Enter' && this.selectedIndex >= 0) {
            e.preventDefault();
            items[this.selectedIndex].click();
        } else if (e.key === 'Escape') {
            this.hide();
        }
    }

    selectItem(index) {
        const items = this.results.querySelectorAll('.autocomplete-item');
        items.forEach((item, i) => {
            if (i === index) {
                item.style.background = 'var(--bg-section)';
            } else {
                item.style.background = 'white';
            }
        });
        this.selectedIndex = index;
    }

    hide() {
        this.results.style.display = 'none';
        this.selectedIndex = -1;
    }
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    // Auto-focus sur le premier input de formulaire
    const firstInput = document.querySelector('form input:not([type=hidden])');
    if (firstInput) {
        firstInput.focus();
    }

    // Confirmation sur les liens/boutons de suppression
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', (e) => {
            const message = element.dataset.confirm || 'Êtes-vous sûr ?';
            if (!App.confirmDelete(message)) {
                e.preventDefault();
            }
        });
    });

    // Auto-fermeture des messages après 5 secondes
    document.querySelectorAll('.message').forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });

    console.log('✨ Le Palais de la Beauté - Application chargée');
});

// Export pour utilisation globale
window.App = App;
window.Modal = Modal;
window.ClientAutocomplete = ClientAutocomplete;
