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

document.addEventListener('DOMContentLoaded', function () {
    // 1. Read data from the hidden HTML element
    const metadata = document.getElementById('formula-metadata');
    const isWrongType = metadata.dataset.isWrong === 'true';
    const actualType = metadata.dataset.actualType;

    // 2. Trigger Preline logic
    if (isWrongType) {
        Preline.confirm(
            'Incorrect Colorant Type', 
            `This CMF is categorized as '${actualType}', but you are accessing the MASTERBATCH matching form. Do you want to proceed anyway?`, 
            'warning', 
            () => {
                console.log("User proceeded.");
            },
            () => {
                // Use a regular string here or hardcode the back URL
                window.location.href = "/cmf/records/"; 
            }
        );
    }
});