const sidebar = document.getElementById("sidebar");
const toggle = document.getElementById("toggleSidebar");

toggle.addEventListener("click", () => {

    if (window.innerWidth <= 992) {

        sidebar.classList.toggle("show");

    } else {

        sidebar.classList.toggle("collapsed");

    }

});