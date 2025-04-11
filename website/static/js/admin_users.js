document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener("htmx:afterSwap", (event) => {
        // Check if the swap targeted the users-content container
        if (event.detail.target.id === "users-content") {
            // Reinitialize Alpine for the newly swapped content
            Alpine.initTree(event.detail.target);
        }
    });
});