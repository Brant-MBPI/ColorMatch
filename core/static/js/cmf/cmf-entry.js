/**
 * CMF Entry Form Logic
 * Handles input formatting (Dosage, Temp, Qty Resin) and Button Listeners
 */

    
// Helper: Restrict input to numbers and decimal only
const restrictToNumbers = (e) => {
    const charCode = (e.which) ? e.which : e.keyCode;
    // Allow: 0-9, dot (.), and backspace/tab/arrows
    if (charCode !== 46 && charCode > 31 && (charCode < 48 || charCode > 57)) {
        e.preventDefault();
        return false;
    }
    // Prevent multiple decimals
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
        // Remove " KG" so user can edit the raw number
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
        // Remove "%" so user can edit the raw number
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
    
    // Allow numbers, dots, and hyphens (-) for ranges like 180-200
    input.addEventListener('keypress', (e) => {
        const charCode = (e.which) ? e.which : e.keyCode;
        if (charCode !== 46 && charCode !== 45 && charCode > 31 && (charCode < 48 || charCode > 57)) {
            e.preventDefault();
        }
    });

    // Clear "N/A" or remove "°C" when user clicks in to type
    input.addEventListener('focus', function() {
        if (this.value === "N/A") {
            this.value = "";
        } else {
            this.value = this.value.replace(/°C/g, '').trim();
        }
    });

    // If user leaves it empty, put "N/A" back, otherwise format range with °C
    input.addEventListener('blur', function() {
        let val = this.value.trim();

        if (val === "" || val === "N/A") {
            this.value = "N/A";
            return;
        }

        // Split by dash, em-dash, or the word "to"
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



// --- BUTTON LISTENERS ---
document.addEventListener('DOMContentLoaded', function() {
    const cmfForm = document.querySelector('.cmf-entry-form');
    const saveBtn = document.querySelector('.btn-save');
    const newBtn = document.querySelector('.btn-new');
    const printBtn = document.querySelector('.btn-dark-teal');

    // 1. SAVE FUNCTION LISTENER
    if (saveBtn && cmfForm) {
        saveBtn.addEventListener('click', function() {
            Preline.confirm(
                'Save Entry?', 
                'Are you sure you want to save this color matching entry? Please verify all technical specs before confirming.', 
                'success', 
                () => {
                    cmfForm.submit(); 
                }
            );
        });
    }

    // 2. NEW FUNCTION LISTENER (Clear Form Confirmation)
    if (newBtn) {
        newBtn.addEventListener('click', function() {
            Preline.confirm(
                'Create New?', 
                'Any unsaved changes on this form will be lost. Do you want to continue?', 
                'warning', 
                () => {
                    window.location.reload(); 
                }
            );
        });
    }

    // 3. PRINT FUNCTION (Simple Print)
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }
});