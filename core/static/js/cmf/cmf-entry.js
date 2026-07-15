// Use a function to ensure it runs even if content is dynamic
function initFormattingLogic() {

    // --- DOSAGE LOGIC ---
    document.querySelectorAll('.dosage-input').forEach(function(input) {
        input.addEventListener('blur', function() {
            let val = this.value.trim();
            if (val !== "" && val !== "N/A") {
                // Strip everything except numbers, dots, and dashes
                let cleanVal = val.replace(/[%\s]/g, "");
                this.value = cleanVal + "%";
            }
        });
    });

    // --- TEMPERATURE LOGIC ---
    document.querySelectorAll('.temp-input').forEach(function(input) {
        // Clear N/A on focus
        input.addEventListener('focus', function() {
            if (this.value === "N/A") { this.value = ""; }
        });

        input.addEventListener('blur', function() {
            let val = this.value.trim();

            if (val === "" || val === "N/A") {
                this.value = "N/A";
                return;
            }

            // Split by dash, em-dash, or the word "to"
            let parts = val.split(/[-–—]| to /i);

            let formattedParts = parts.map(part => {
                // Remove spaces, degree symbols, and 'C'
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
}

// Run on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFormattingLogic);
} else {
    initFormattingLogic();
}

const cmfForm = document.querySelector('.cmf-entry-form');
const saveBtn = document.querySelector('.btn-save');
const newBtn = document.querySelector('.btn-new');

// 1. SAVE FUNCTION LISTENER
if (saveBtn) {
    saveBtn.addEventListener('click', function() {
        // Use our Preline confirmation system
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
                window.location.reload(); // Refresh page to clear
            }
        );
    });
}

// 3. PRINT FUNCTION (Simple Print)
const printBtn = document.querySelector('.btn-dark-teal');
if (printBtn) {
    printBtn.addEventListener('click', () => {
        window.print();
    });
}