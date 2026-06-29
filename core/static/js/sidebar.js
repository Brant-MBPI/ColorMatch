document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const toggleBtn = document.getElementById("toggleSidebar");
    const mobileToggleBtn = document.getElementById("mobileToggle");

    function toggleSidebar() {
        if (window.innerWidth <= 992) {
            sidebar.classList.toggle("show");
            // Remove collapsed class if switching to mobile view
            sidebar.classList.remove("collapsed");
        } else {
            sidebar.classList.toggle("collapsed");
            // Remove show class if switching to desktop view
            sidebar.classList.remove("show");
        }
    }

    if (toggleBtn) {
        toggleBtn.addEventListener("click", toggleSidebar);
    }

    if (mobileToggleBtn) {
        mobileToggleBtn.addEventListener("click", toggleSidebar);
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", (e) => {
        if (window.innerWidth <= 992) {
            if (!sidebar.contains(e.target) && 
                !toggleBtn.contains(e.target) && 
                (mobileToggleBtn && !mobileToggleBtn.contains(e.target)) &&
                sidebar.classList.contains("show")) {
                sidebar.classList.remove("show");
            }
        }
    });
});