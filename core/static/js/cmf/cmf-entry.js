/**
 * CMF Entry Form Logic
 * Handles input formatting, "Other" field toggling, and Button Listeners
 */

// Helper: Restrict input to numbers and decimal only
const restrictToNumbers = (e) => {
    const charCode = (e.which) ? e.which : e.keyCode;
    if (charCode !== 46 && charCode > 31 && (charCode < 48 || charCode > 57)) {
        e.preventDefault();
        return false;
    }
    if (charCode === 46 && e.target.value.indexOf('.') !== -1) {
        e.preventDefault();
        return false;
    }
    return true;
};

// --- 1. QTY RESIN LOGIC (KG Auto-concat) ---
document.querySelectorAll('.qty-resin-input').forEach(function(input) {
    input.addEventListener('keypress', restrictToNumbers);
    input.addEventListener('focus', function() {
        this.value = this.value.replace(/ KG/gi, '');
    });
    input.addEventListener('blur', function() {
        let val = this.value.trim();
        if (val !== "" && val !== "N/A") {
            let cleanVal = val.replace(/ KG/gi, "");
            this.value = cleanVal + " KG";
        }
    });
});

// --- 2. DOSAGE LOGIC (% Auto-concat) ---
document.querySelectorAll('.dosage-input').forEach(function(input) {
    input.addEventListener('keypress', restrictToNumbers);
    input.addEventListener('focus', function() {
        this.value = this.value.replace(/%/g, '');
    });
    input.addEventListener('blur', function() {
        let val = this.value.trim();
        if (val !== "" && val !== "N/A") {
            let cleanVal = val.replace(/%/g, "");
            this.value = cleanVal + "%";
        }
    });
});

// --- 3. TEMPERATURE LOGIC (N/A Default & Range with °C) ---
document.querySelectorAll('.temp-input').forEach(function(input) {
    input.addEventListener('keypress', (e) => {
        const charCode = (e.which) ? e.which : e.keyCode;
        if (charCode !== 46 && charCode !== 45 && charCode > 31 && (charCode < 48 || charCode > 57)) {
            e.preventDefault();
        }
    });
    input.addEventListener('focus', function() {
        if (this.value === "N/A") {
            this.value = "";
        } else {
            this.value = this.value.replace(/°C/g, '').trim();
        }
    });
    input.addEventListener('blur', function() {
        let val = this.value.trim();
        if (val === "" || val === "N/A") {
            this.value = "N/A";
            return;
        }
        let parts = val.split(/[-–—]| to /i);
        let formattedParts = parts.map(part => {
            let p = part.trim().replace(/[°C\s]/gi, "");
            return p !== "" ? p + "°C" : "";
        }).filter(p => p !== "");
        if (formattedParts.length >= 2) {
            this.value = formattedParts[0] + " - " + formattedParts[1];
        } else if (formattedParts.length === 1) {
            this.value = formattedParts[0];
        }
    });
});

// --- 4. REUSABLE "OTHERS" TOGGLE LOGIC ---
const updateOtherInputState = (trigger, input) => {
    if (trigger.checked) {
        input.disabled = false;
        input.required = true;
    } else {
        input.disabled = true;
        input.required = false;
        input.value = ""; 
    }
};

document.querySelectorAll('.js-other-container').forEach(container => {
    const trigger = container.querySelector('.js-other-trigger');
    const input = container.querySelector('.js-other-input');

    if (!trigger || !input) return;

    // Handle Checkboxes
    if (trigger.type === 'checkbox') {
        trigger.addEventListener('change', () => updateOtherInputState(trigger, input));
    } 
    // Handle Radios (listen to the whole group)
    else if (trigger.type === 'radio') {
        const groupName = trigger.name;
        document.querySelectorAll(`input[name="${groupName}"]`).forEach(radio => {
            radio.addEventListener('change', () => updateOtherInputState(trigger, input));
        });
    }
    // Initialize state on load
    updateOtherInputState(trigger, input);
});


// --- BUTTON LISTENERS ---
const cmfForm = document.querySelector('.cmf-entry-form');
const saveBtn = document.querySelector('.btn-save');
const newBtn = document.querySelector('.btn-new');
const printBtn = document.querySelector('.btn-dark-teal');


if (saveBtn && cmfForm) {
    saveBtn.addEventListener('click', function() {
        // 1. Check if the form is valid according to 'required' attributes
        if (cmfForm.reportValidity()) {
            // 2. Only show the modal if the form passes validation
            Preline.confirm(
                'Save Entry?', 
                'Are you sure you want to save this color matching entry? Please verify all technical specs before confirming.', 
                'success', 
                () => {
                    cmfForm.submit(); 
                }
            );
        }
    });
}

if (newBtn) {
    newBtn.addEventListener('click', function() {
        Preline.confirm(
            'Create New?', 
            'Any unsaved changes on this form will be lost. Do you want to continue?', 
            'warning', 
            () => {
                window.location.href = window.location.pathname; 
            }
        );
    });
}

if (printBtn) {
    printBtn.addEventListener('click', () => {
        window.print();
    });
}