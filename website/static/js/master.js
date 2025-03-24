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
