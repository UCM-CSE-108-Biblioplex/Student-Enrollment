document.addEventListener("alpine:init", () => {
    Alpine.data("signup_form", () => ({
        first_name_touched: false,
        last_name_touched: false,
        username_touched: false,
        email_touched: false,
        password1_touched: false,
        password2_touched: false,

        username_checking: false,
        username_taken: false,
        username_valid: false,
        username_timer: null,
        username: "",
        email: "",
        password1: "",
        password2: "",
        passwords_match () {
            if (!this.password1_touched || !this.password2_touched) {
                return;
            }
            validity = this.password1 != this.password2 || !this.password1_touched || !this.password2_touched;
            if(!validity) {
                this.$refs.password1.validity.valid = false;
                this.$refs.password2.validity.valid = false;
            }
            return(validity);
        },
        check_username() {
            this.username_touched = true;
            this.username_valid = false;
            this.username_taken = false;
            
            // Clear any existing timer
            if (this.username_timer) {
                clearTimeout(this.username_timer);
            }
            
            // Don't check if username is less than 4 characters
            if (this.username.length < 4) {
                this.username_checking = false;
                return;
            }
            
            // Set checking state and debounce API call
            this.username_checking = true;
            
            // Debounce for 500ms to avoid excessive API calls
            this.username_timer = setTimeout(() => {
                fetch(`/api/v1/username?username=${encodeURIComponent(this.username)}`)
                    .then(response => response.json())
                    .then(data => {
                        this.username_checking = false;
                        if (data.valid) {
                            this.username_valid = true;
                            this.username_taken = false;
                        } else {
                            this.$refs.username.setCustomValidity ("Username already taken.");
                            this.username_valid = false;
                            this.username_taken = true;
                        }
                    })
                    .catch(error => {
                        console.error("Error checking username:", error);
                        this.username_checking = false;
                    });
            }, 2000);
        },
        update_password_strength() {
            const password = this.password1;
            let strength = 0;
      
            if (password.length > 5) {
              strength += 20;
            }
            if (password.length > 15) {
              strength += 20;
            }
            if (/[A-Z]/.test(password)) {
              strength += 20;
            }
            if (/[0-9]/.test(password)) {
              strength += 20;
            }
            if (/[^a-zA-Z0-9\s]/.test(password)) {
              strength += 20;
            }
      
            this.password_strength = strength;
      
            if (strength <= 40) {
                this.password_strength_label = "Weak";
                this.password_strength_class = "weak";
            } else if (strength <= 60) {
                this.password_strength_label = "Medium";
                this.password_strength_class = "medium";
            } else if (strength <= 80) {
                this.password_strength_label = "Strong";
                this.password_strength_class = "strong";
            } else {
                this.password_strength_label = "Very Strong";
                this.password_strength_class = "very-strong";
            }
          },
    }));
});
