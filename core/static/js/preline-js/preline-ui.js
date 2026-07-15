const Preline = {
    // 1. TOAST SYSTEM
    toast: function(message, type = 'success') {
        let container = document.getElementById('preline-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'preline-toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        const cleanType = type.includes('error') ? 'danger' : type;
        toast.className = `preline-toast ${cleanType}`;
        
        let icon = 'check-circle-fill';
        if (cleanType === 'danger' || cleanType === 'error') icon = 'exclamation-triangle-fill';
        if (cleanType === 'warning') icon = 'exclamation-circle-fill';

        toast.innerHTML = `
            <i class="bi bi-${icon} fs-5"></i>
            <div class="flex-grow-1 mr-2">
                <span class="small fw-semibold d-block">${cleanType.toUpperCase()}</span>
                <span class="small opacity-75">${message}</span>
            </div>
            <button type="button" class="btn-close ms-2" style="font-size: 0.7rem" onclick="this.parentElement.remove()"></button>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(40px)';
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    },

    // 2. CONFIRMATION MODAL
    confirm: function(title, message, type, onConfirm) {
        const modalEl = document.getElementById('dynamicModal');
        const modal = new bootstrap.Modal(modalEl);
        
        document.getElementById('modalTitle').innerText = title;
        document.getElementById('modalMessage').innerText = message;
        
        const iconContainer = document.getElementById('modalIconContainer');
        const icon = document.getElementById('modalIcon');
        
        // Reset classes
        iconContainer.className = 'modal-icon-circle icon-' + (type || 'success');
        icon.className = 'bi ' + (type === 'danger' ? 'bi-exclamation-triangle' : 'bi-check-lg');

        const confirmBtn = document.getElementById('modalConfirmBtn');
        // Clear previous listeners
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

        newConfirmBtn.onclick = () => {
            onConfirm();
            modal.hide();
        };

        modal.show();
    }
};