document.addEventListener("alpine:init", () => {
    // Global variable for search debouncing
    window.searchDebounceTimeout = null;
    
    // Form handling for user editing
    Alpine.data("editUserForm", (user) => ({
        userData: {
            user_id: user.id,
            first_name: user.first_name,
            middle_name: user.middle_name || "",
            last_name: user.last_name,
            username: user.username,
            email: user.email,
            is_admin: user.is_admin,
            password: ""
        },
        message: "",
        messageType: "",
        
        submitForm() {
            // Clear previous messages
            this.message = "";
            this.messageType = "";
            
            // Create payload (omit password if empty)
            const payload = {...this.userData};
            if (!payload.password) {
                delete payload.password;
            }
            
            // Send API request
            fetch('/api/v1/users', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(text || 'Failed to update user');
                    });
                }
                return response.json();
            })
            .then(data => {
                this.message = "User updated successfully!";
                this.messageType = "success";
                
                // Refresh the table after successful update
                setTimeout(() => {
                    htmx.trigger('#user-search', 'search');
                    // Close modal after a delay
                    setTimeout(() => {
                        this.$dispatch('close-modal');
                    }, 1000);
                }, 1500);
            })
            .catch(error => {
                this.message = error.message || "An error occurred while updating the user.";
                this.messageType = "error";
            });
        }
    }));
});
