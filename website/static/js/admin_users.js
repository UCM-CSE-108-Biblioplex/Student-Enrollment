document.addEventListener('DOMContentLoaded', function() {
    // Find all buttons with data-modal-trigger attribute
    const modalTriggers = document.querySelectorAll('[data-modal-trigger]');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            // Get the ID of the element to click (from the data attribute)
            const targetId = this.getAttribute('data-modal-trigger');
            // Find the actual trigger element and click it
            const actualTrigger = document.getElementById(targetId);
            if (actualTrigger) {
                actualTrigger.click();
            }
        });
    });
});