document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const toggleSidebar = document.getElementById("toggleSidebar");
    const mobileToggle = document.getElementById("mobileToggle");
    const logoTrigger = document.querySelector(".logo-icon-box");
    const body = document.body;

    // Theme Toggles
    const themeToggleFooter = document.getElementById("themeToggle");       
    const themeToggleSidebar = document.getElementById("themeToggleSidebar"); 
    const sidebarThemeIcon = document.getElementById("sidebarThemeIcon");
    const sidebarThemeText = document.getElementById("sidebarThemeText");

    // --- 1. Sidebar Toggle Logic ---
    function toggleMenu() {
        if (window.innerWidth < 992) {
            sidebar.classList.toggle("show");
            overlay.classList.toggle("show");
        } else {
            sidebar.classList.toggle("collapsed");
        }
    }

    if (toggleSidebar) toggleSidebar.addEventListener("click", toggleMenu);
    if (mobileToggle) mobileToggle.addEventListener("click", toggleMenu);
    if (logoTrigger) logoTrigger.addEventListener("click", toggleMenu); 
    
    if (overlay) {
        overlay.addEventListener("click", () => {
            sidebar.classList.remove("show");
            overlay.classList.remove("show");
        });
    }

    // --- 2. Theme Toggle Logic (Synchronized) ---
    
    function updateThemeUI(isDark) {
        const text = isDark ? "Switch to Light Mode" : "Try Dark Mode";
        const iconClass = isDark ? "bi bi-sun me-2" : "bi bi-moon-stars me-2";
        
        // Update Footer Link (if it exists on current page)
        if (themeToggleFooter) {
            themeToggleFooter.textContent = text;
        }
        
        // Update Sidebar Dropdown (if it exists)
        if (sidebarThemeText) {
            sidebarThemeText.textContent = text;
        }
        if (sidebarThemeIcon) {
            sidebarThemeIcon.className = iconClass;
        }
    }

    // Initial Load - Check saved preference
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        body.classList.add("dark-mode");
        updateThemeUI(true);
    } else {
        updateThemeUI(false);
    }

    // Single function to handle the flip
    function toggleTheme(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation(); // Prevents Bootstrap from conflicting with the click
        }
        
        body.classList.toggle("dark-mode");
        const isDark = body.classList.contains("dark-mode");
        
        localStorage.setItem("theme", isDark ? "dark" : "light");
        updateThemeUI(isDark);
        
        // Notify other components
        document.dispatchEvent(new CustomEvent("themechange"));
    }

    // Attach listeners
    if (themeToggleFooter) themeToggleFooter.addEventListener("click", toggleTheme);
    if (themeToggleSidebar) themeToggleSidebar.addEventListener("click", toggleTheme);

    // --- 3. Datetime Logic ---
    const dtField = document.getElementById('datetimeFooter');
    if (dtField) {
        setInterval(() => {
            const now = new Date();
            dtField.textContent = now.toLocaleString();
        }, 1000);
    }


    const navbar = document.querySelector('.navbar');
    let lastScrollTop = 0;

    // --- 4. Dynamic Navbar Logic ---

    // A. Hide on Scroll Down, Show on Scroll Up
    window.addEventListener('scroll', function() {
        let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Only trigger after scrolling at least 50px
        if (scrollTop > lastScrollTop && scrollTop > 50) {
            // Scrolling Down - Hide Navbar
            navbar.classList.add('nav-hidden');
        } else {
            // Scrolling Up - Show Navbar
            navbar.classList.remove('nav-hidden');
        }
        lastScrollTop = scrollTop;
    });

    // B. Show Navbar when clicking anywhere on the screen
    document.addEventListener('click', function(event) {
        // We only care if the navbar is currently hidden
        if (navbar.classList.contains('nav-hidden')) {
            navbar.classList.remove('nav-hidden');
        }
    });

    // C. Prevent navbar from hiding if you are clicking the navbar itself 
    // (Optional: stops the "hide on next scroll" logic briefly)
    navbar.addEventListener('click', function(e) {
        e.stopPropagation(); 
    });
});