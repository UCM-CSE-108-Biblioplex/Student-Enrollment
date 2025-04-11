document.addEventListener('DOMContentLoaded', function() {
    // Global progress indicator
    htmx.config.globalIndicator = "#global-htmx-indicator";
    
    // Progress bar animation
    const progressBar = document.getElementById('global-htmx-indicator');
    
    htmx.on('htmx:beforeRequest', function() {
        progressBar.style.width = '0%';
        setTimeout(() => {
            progressBar.style.width = '30%';
        }, 50);
        setTimeout(() => {
            progressBar.style.width = '70%';
        }, 300);
    });
    
    htmx.on('htmx:beforeOnLoad', function() {
        progressBar.style.width = '90%';
    });
    
    htmx.on('htmx:afterOnLoad', function() {
        progressBar.style.width = '100%';
        setTimeout(() => {
            progressBar.style.width = '0%';
        }, 300);
    });
});

document.addEventListener("alpine:init", () => {
    Alpine.data("master", () => ({
        isDarkTheme: localStorage.getItem('theme') === 'dark' || 
                    (localStorage.getItem('theme') === null && 
                     window.matchMedia('(prefers-color-scheme: dark)').matches),
        
        toggleTheme() {
            this.isDarkTheme = !this.isDarkTheme;
            if (this.isDarkTheme) {
                document.documentElement.classList.add('dark-theme');
                document.documentElement.classList.remove('light-theme');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.classList.add('light-theme');
                document.documentElement.classList.remove('dark-theme');
                localStorage.setItem('theme', 'light');
            }
        },

        init() {
            // Set initial theme based on preference
            if (this.isDarkTheme) {
                document.documentElement.classList.add('dark-theme');
            } else {
                document.documentElement.classList.add('light-theme');
            }
        }
    }));
});
