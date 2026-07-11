document.addEventListener('DOMContentLoaded', function() {

    // --- Password visibility toggle ---
    document.querySelectorAll('.toggle-visibility').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    });

    // --- Login form submit (wire this up to your Django login view) ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // TODO: replace with real POST to your Django login endpoint
            console.log('Login submitted:', {
                username: document.getElementById('loginUsername').value,
                password: document.getElementById('loginPassword').value,
            });
        });
    }

});