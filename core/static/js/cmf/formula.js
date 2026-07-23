document.querySelectorAll('.ts-select-table').forEach((el) => {
    new TomSelect(el, {
        selectOnTab: true,
        create: false, 
        placeholder: "Search material...",
        maxOptions: 50,
        dropdownParent: 'body',
        onItemAdd: function() {
            this.blur();
        }
    });
});

// --- 2. Reusable Hex Preview & Validation ---
const hexInput = document.querySelector('.hex-input');
const swatch = document.querySelector('.color-swatch');

if (hexInput && swatch) {
    const isValidHex = (value) => /^#([0-9A-Fa-f]{3}){1,2}$/.test(value);

    // Real-time preview
    hexInput.addEventListener('input', function () {
        let value = hexInput.value.trim();
        if (value && !value.startsWith('#')) {
            value = '#' + value;
        }
        if (isValidHex(value)) {
            swatch.style.backgroundColor = value;
        }
    });

    // Strict Validation on Unfocus
    hexInput.addEventListener('blur', function() {
        let value = hexInput.value.trim();
        
        if (value === "") {
            swatch.style.backgroundColor = "#FFFFFF";
            return;
        }

        if (!value.startsWith('#')) {
            value = '#' + value;
        }

        if (!isValidHex(value)) {
            hexInput.value = ""; 
            swatch.style.backgroundColor = "#FFFFFF";
        } else {
            hexInput.value = value;
        }
    });
}

// --- 3. Reusable Auto-Calculate Total Weight ---
// We attach the listener to the document to avoid needing a specific form ID
document.addEventListener('input', function(e) {
    if (e.target.classList.contains('weight-input')) {
        const totalWeightDisplay = document.querySelector('.total-weight-display');
        if (!totalWeightDisplay) return;

        let total = 0;
        const allWeightInputs = document.querySelectorAll('.weight-input');
        
        allWeightInputs.forEach(input => {
            const val = parseFloat(input.value);
            if (!isNaN(val)) {
                total += val;
            }
        });

        totalWeightDisplay.value = total.toFixed(4);
    }
});

// Select the form (works for both mb and dc as long as ID matches)
    const formulaForm = document.getElementById('formulaForm') || document.getElementById('formulaDcForm');
    
    const saveBtn = document.querySelector('.btn-save');
    const newBtn = document.querySelector('.btn-new');
    const printBtn = document.querySelector('.btn-print');

    // --- 1. SAVE / UPDATE LOGIC ---
    if (saveBtn && formulaForm) {
        saveBtn.addEventListener('click', function() {
            // Check HTML5 validation (required fields)
            if (formulaForm.reportValidity()) {
                // Determine if updating or saving new
                const formulaId = formulaForm.querySelector('[name="formula_id"]')?.value.trim();
                const isUpdate = formulaId && formulaId !== '';

                const title = isUpdate ? 'Update Formula?' : 'Save Formula?';
                const message = isUpdate 
                    ? 'Are you sure you want to update this existing formula? Existing data will be overwritten.' 
                    : 'Are you sure you want to save this new formula? Please verify all material weights before confirming.';

                Preline.confirm(
                    title, 
                    message, 
                    'success', 
                    () => {
                        formulaForm.submit(); 
                    }
                );
            }
        });
    }

    // --- 2. CREATE NEW LOGIC ---
    if (newBtn) {
        newBtn.addEventListener('click', function() {
            Preline.confirm(
                'Create New?', 
                'Any unsaved changes on this form will be lost and you will start a blank entry. Continue?', 
                'warning', 
                () => {
                    // Redirect to the base path without query parameters (clears ?no= and ?formula_id=)
                    window.location.href = window.location.pathname; 
                }
            );
        });
    }

    // --- 3. PRINT LOGIC ---
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }