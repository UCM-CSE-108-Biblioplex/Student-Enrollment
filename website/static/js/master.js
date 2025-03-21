document.addEventListener("alpine:init", () => {
    Alpine.data("master", () => ({
        mobileMenuOpen: false,
        theme: 'auto',
        
        init() {
        // Detect preferred color scheme
        this.detectColorScheme();
        
        // Add padding to body to prevent content from being hidden under fixed navbar
        // document.body.style.paddingTop = '70px';
        
        // Listen for OS theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (this.theme === 'auto') {
            this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
        },
        
        detectColorScheme() {
        // Check for saved user preference
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme) {
            this.theme = savedTheme;
            this.applyTheme(savedTheme);
        } else {
            // Use OS preference
            this.theme = 'auto';
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.applyTheme(prefersDark ? 'dark' : 'light');
        }
        },
        
        toggleTheme() {
        if (this.theme === 'light' || (this.theme === 'auto' && !window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            this.theme = 'dark';
        } else {
            this.theme = 'light';
        }
        
        localStorage.setItem('theme', this.theme);
        this.applyTheme(this.theme);
        },
        
        applyTheme(theme) {
        if (theme === 'auto') {
            theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        
        if (theme === 'dark') {
            document.documentElement.classList.add('dark-theme');
        } else {
            document.documentElement.classList.remove('dark-theme');
        }
        },
        
        toggleMobileMenu() {
        this.mobileMenuOpen = !this.mobileMenuOpen;
        
        if (this.mobileMenuOpen) {
            document.body.style.overflow = 'hidden'; // Prevent scrolling when menu is open
        } else {
            document.body.style.overflow = ''; // Restore scrolling
        }
        }
    }));
});  