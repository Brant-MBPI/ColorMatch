const Preline = {
    // 1. CONFIRMATION MODAL
    // Usage: Preline.confirm('Delete?', 'This is permanent', 'danger', () => { doDelete(); });
    confirm: function(title, message, type, callback) {
        const modal = new bootstrap.Modal(document.getElementById('dynamicModal'));
        const iconContainer = document.getElementById('modalIcon');
        const icon = document.getElementById('modalIconClass');
        const confirmBtn = document.getElementById('modalConfirmBtn');

        document.getElementById('modalTitle').innerText = title;
        document.getElementById('modalMessage').innerText = message;

        // Set Icon and Color based on type
        iconContainer.className = 'modal-icon-circle icon-' + (type || 'success');
        icon.className = type === 'danger' ? 'bi bi-exclamation-triangle' : 'bi bi-check-lg';
        
        // Handle Confirmation
        confirmBtn.onclick = () => {
            callback();
            modal.hide();
        };

        modal.show();
    },

    // 2. TOAST NOTIFICATION
    // Usage: Preline.toast('Saved successfully!', 'success');
    toast: function(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `preline-toast border-${type}`;
        toast.innerHTML = `
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-circle'} text-${type}"></i>
            <span class="small text-white">${message}</span>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }
};