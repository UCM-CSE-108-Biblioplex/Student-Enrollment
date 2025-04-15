document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener("htmx:afterSwap", (event) => {
        // Check if the swap targeted the users-content container
        if (event.detail.target.id === "courses-content") {
            // Reinitialize Alpine for the newly swapped content
            Alpine.initTree(event.detail.target);
        }
        if (event.detail.target.id === "terms-content") {
            // Reinitialize Alpine for the newly swapped content
            Alpine.initTree(event.detail.target);
        }
        if (event.detail.target.id === "users-content") {
            // Reinitialize Alpine for the newly swapped content
            Alpine.initTree(event.detail.target);
        }
        if (event.detail.target.id === "departments-content") {
            // Reinitialize Alpine for the newly swapped content
            Alpine.initTree(event.detail.target);
        }
    });
});

document.addEventListener('alpine:init', () => {
    Alpine.data("param", () => ({
        updateURLParam (param, value) {
            const url = new URL (window.location.href);
            url.searchParams.set(param, value);
            window.history.pushState ({}, '', url);
        }
    }))
})