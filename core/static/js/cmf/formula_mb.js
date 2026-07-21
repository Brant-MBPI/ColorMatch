
// Initialize TomSelect for Table Materials
document.querySelectorAll('.ts-select-table').forEach((el) => {
    new TomSelect(el, {
        selectOnTab: true,
        create: false, // Forces selection from the list ONLY
        placeholder: "Search material...",
        maxOptions: 50, // Helps with performance if the list is huge
        dropdownParent: 'body', // Fixes overflow issues in scrolling tables
        onItemAdd: function() {
            this.blur(); // Close dropdown after selection
        }
    });
});

var hexInput = document.getElementById('id_srgb_hex');
var swatch = document.getElementById('id_color_swatch');

function isValidHex(value) {
    // Checks for # followed by 3 or 6 hex characters
    return /^#([0-9A-Fa-f]{3}){1,2}$/.test(value);
}

// Real-time preview (remains for UX)
hexInput.addEventListener('input', function () {
    var value = hexInput.value.trim();
    if (value && !value.startsWith('#')) {
        value = '#' + value;
    }
    if (isValidHex(value)) {
        swatch.style.backgroundColor = value;
    }
});

// Strict Validation on Unfocus (Blur)
hexInput.addEventListener('blur', function() {
    var value = hexInput.value.trim();
    
    // Accept none/no entry (keep null/blank)
    if (value === "") {
        swatch.style.backgroundColor = "#FFFFFF";
        return;
    }

    // Auto-append # if missing
    if (!value.startsWith('#')) {
        value = '#' + value;
    }

    // Check validity
    if (!isValidHex(value)) {
        hexInput.value = ""; // Clear invalid input
        swatch.style.backgroundColor = "#FFFFFF"; // Reset swatch
    } else {
        hexInput.value = value; // Update input with # prefix if valid
    }
});

// --- 2. Auto-Calculate Total Weight ---
const formulaForm = document.getElementById('formulaForm');
const totalWeightInput = document.getElementById('total_weight');

formulaForm.addEventListener('input', function(e) {
    if (e.target.classList.contains('weight-input')) {
        let total = 0;
        const weightInputs = document.querySelectorAll('.weight-input');
        
        weightInputs.forEach(input => {
            const val = parseFloat(input.value);
            if (!isNaN(val)) {
                total += val;
            }
        });

        totalWeightInput.value = total.toFixed(4);
    }
});
