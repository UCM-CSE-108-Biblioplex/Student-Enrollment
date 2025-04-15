// Simple Alpine component to manage modal state and fetch content
document.addEventListener('alpine:init', () => {
    Alpine.data('userRolesPage', () => ({
        openModalId: null, // Which user's modal is open
        modalContent: '<div class=\"p-4 text-center\">Loading...</div>', // Placeholder

        fetchModalContent(userId) {
            // Use HTMX utility function to fetch content
            htmx.ajax('GET', `/api/v1/users/${userId}/roles/modal`, '#user-roles-modal-content')
                .then(response => {
                    // Alpine doesn't automatically re-init HTMX-loaded content.
                    // We need to manually tell Alpine to scan the new content.
                    // Ensure the modal content div exists before trying to init.
                    const modalContentDiv = document.getElementById('user-roles-modal-content');
                    if (modalContentDiv) {
                         // Replace content first
                        modalContentDiv.innerHTML = response;
                        // Then initialize Alpine within that specific container
                        Alpine.initTree(modalContentDiv);
                    }
                })
                .catch(error => {
                    console.error("Error fetching modal content:", error);
                    const modalContentDiv = document.getElementById('user-roles-modal-content');
                     if (modalContentDiv) {
                        modalContentDiv.innerHTML = '<div class=\"p-4 text-red-500 text-center\">Error loading content.</div>';
                     }
                });
        },

        closeModal() {
            this.openModalId = null;
            this.modalContent = '<div class=\"p-4 text-center\">Loading...</div>'; // Reset placeholder
        }
    }));

    // Ensure Alpine re-initializes after main table pagination swaps
    Alpine.data("param", () => ({
        updateURLParam (param, value) {
            const url = new URL (window.location.href);
            url.searchParams.set(param, value);
            window.history.pushState ({}, '', url);
        }
    }));

    // Listener to re-init Alpine within the modal after HTMX swaps *inside* the modal
    document.body.addEventListener('htmx:afterSwap', function(event) {
        if (event.detail.target.id === 'user-roles-modal-content') {
            // Re-initialize Alpine for the swapped modal content
             Alpine.initTree(event.detail.target);
        }
         if (event.detail.target.id === 'user-roles-table-container') {
            // Re-initialize Alpine for the main table container if needed
             Alpine.initTree(event.detail.target);
        }
    });
});