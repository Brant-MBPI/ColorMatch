document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const toggleBtn = document.getElementById("toggleSidebar"); // Button inside sidebar
    const mobileToggle = document.getElementById("mobileToggle"); // Button in top navbar
    const themeToggle = document.getElementById("themeToggle");
    const body = document.body;

    // Function to toggle sidebar based on screen size
    function handleToggle() {
        if (window.innerWidth < 992) {
            // Mobile: Slide in/out and show overlay
            sidebar.classList.toggle("show");
            overlay.classList.toggle("show");
        } else {
            // Desktop: Collapse/Expand
            sidebar.classList.toggle("collapsed");
        }
    }

    if (toggleBtn) toggleBtn.addEventListener("click", handleToggle);
    if (mobileToggle) mobileToggle.addEventListener("click", handleToggle);
    
    // Close sidebar when clicking overlay (mobile)
    if (overlay) {
        overlay.addEventListener("click", () => {
            sidebar.classList.remove("show");
            overlay.classList.remove("show");
        });
    }

    // --- Theme Logic ---
    const currentTheme = localStorage.getItem("theme");
    if (currentTheme === "dark") {
        body.classList.add("dark-mode");
        if(themeToggle) themeToggle.textContent = "Switch to Light Mode";
    }

    if (themeToggle) {
        themeToggle.addEventListener("click", (e) => {
            e.preventDefault();
            body.classList.toggle("dark-mode");
            const isDark = body.classList.contains("dark-mode");
            localStorage.setItem("theme", isDark ? "dark" : "light");
            themeToggle.textContent = isDark ? "Switch to Light Mode" : "Try Dark Mode";
        });
    }
});