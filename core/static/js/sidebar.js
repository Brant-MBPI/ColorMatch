document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const toggleSidebar = document.getElementById("toggleSidebar");
    const mobileToggle = document.getElementById("mobileToggle");
    const logoTrigger = document.querySelector(".logo-icon-box");
    const body = document.body;

    // --- MOVE THESE TO THE TOP ---
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

            if (sidebar.classList.contains("collapsed")) {
                const appsMenu = document.getElementById('appsMenu');
                const cmfTrigger = document.querySelector('.cmf-nav-trigger');
                
                if (appsMenu && appsMenu.classList.contains('show')) {
                    const bsCollapse = bootstrap.Collapse.getInstance(appsMenu);
                    if (bsCollapse) {
                        bsCollapse.hide();
                    } else {
                        appsMenu.classList.remove('show');
                        if (cmfTrigger) cmfTrigger.setAttribute('aria-expanded', 'false');
                    }
                }
            }
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

    const cmfTrigger = document.querySelector('.cmf-nav-trigger');
    if (cmfTrigger) {
        cmfTrigger.addEventListener('click', function () {
            if (window.innerWidth >= 992 && sidebar.classList.contains('collapsed')) {
                sidebar.classList.remove('collapsed');
            }
        });
    }

    // --- 2. Theme Toggle Logic ---
    function updateThemeUI(isDark) {
        const text = isDark ? "Switch to Light Mode" : "Try Dark Mode";
        const iconClass = isDark ? "bi bi-sun me-2" : "bi bi-moon-stars me-2";
        
        // These now work because the variables are declared at the top
        if (themeToggleFooter) themeToggleFooter.textContent = text;
        if (sidebarThemeText) sidebarThemeText.textContent = text;
        if (sidebarThemeIcon) sidebarThemeIcon.className = iconClass;
    }

    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        body.classList.add("dark-mode");
        updateThemeUI(true);
    } else {
        updateThemeUI(false);
    }

    function toggleTheme(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        body.classList.toggle("dark-mode");
        const isDark = body.classList.contains("dark-mode");
        localStorage.setItem("theme", isDark ? "dark" : "light");
        updateThemeUI(isDark);
        document.dispatchEvent(new CustomEvent("themechange"));
    }

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

    // --- 4. Dynamic Navbar Logic ---
    const navbar = document.querySelector('.navbar');
    let lastScrollTop = 0;

    window.addEventListener('scroll', function() {
        let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        if (scrollTop > lastScrollTop && scrollTop > 50) {
            navbar.classList.add('nav-hidden');
        } else {
            navbar.classList.remove('nav-hidden');
        }
        lastScrollTop = scrollTop;
    });

    document.addEventListener('click', function(event) {
        if (navbar.classList.contains('nav-hidden')) {
            navbar.classList.remove('nav-hidden');
        }
    });

    navbar.addEventListener('click', function(e) {
        e.stopPropagation(); 
    });
});