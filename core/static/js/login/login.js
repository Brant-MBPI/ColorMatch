document.addEventListener('DOMContentLoaded', function() {

    // --- Password visibility toggle (used on both login and signup) ---
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

    // --- Signup: confirm password match check ---
    const signupPassword = document.getElementById('signupPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    const matchHint = document.getElementById('matchHint');

    if (signupPassword && confirmPassword && matchHint) {
        function checkMatch() {
            if (!confirmPassword.value) {
                matchHint.textContent = '';
                matchHint.classList.remove('error', 'success');
                return;
            }
            if (confirmPassword.value === signupPassword.value) {
                matchHint.textContent = 'Passwords match.';
                matchHint.classList.remove('error');
                matchHint.classList.add('success');
            } else {
                matchHint.textContent = 'Passwords do not match.';
                matchHint.classList.remove('success');
                matchHint.classList.add('error');
            }
        }
        signupPassword.addEventListener('input', checkMatch);
        confirmPassword.addEventListener('input', checkMatch);
    }

    // --- Signup form submit (wire this up to your Django registration view) ---
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (signupPassword.value !== confirmPassword.value) {
                matchHint.textContent = 'Passwords do not match.';
                matchHint.classList.remove('success');
                matchHint.classList.add('error');
                return;
            }
            // TODO: replace with real POST to your Django registration endpoint
            console.log('Signup submitted:', {
                username: document.getElementById('signupUsername').value,
                email: document.getElementById('signupEmail').value,
                first_name: document.getElementById('firstName').value,
                last_name: document.getElementById('lastName').value,
                password: signupPassword.value,
            });
        });
    }

});