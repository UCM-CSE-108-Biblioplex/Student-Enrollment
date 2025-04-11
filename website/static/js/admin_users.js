document.addEventListener("alpine:init", () => {    
    // Form handling for user editing
    Alpine.data("editUserForm", (user) => ({
        userData: {
            user_id: user.user_id,
            first_name: user.first_name,
            middle_name: user.middle_name || "",
            last_name: user.last_name,
            username: user.username,
            email: user.email,
            is_admin: user.is_admin,
            password: ""
        },
        message: null,
        messageType: "",

        init() {console.log(this.submitting)},
        
        submitForm() {
            // Set submitting flag to true to show spinner
            this.submitting = true;
            this.message = null;

            // Create payload (omit password if empty)
            const payload = { ...this.userData };
            if (!payload.password) {
                delete payload.password;
            }
            
            // Send API request
            this.$dispatch(`submitting-${payload.user_id}`)
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
                window.location.reload();
            })
            .catch(error => {
                this.message = error.message || "An error occurred while updating the user.";
                this.messageType = "error";
                this.submitting = false;
            });
        }
    }));
});
