(function () {
    document.querySelectorAll('.ts-select-table').forEach((el) => {
        new TomSelect(el, {
            selectOnTab: true,
            create: false,
            placeholder: "Search material...",
            maxOptions: 50,
            dropdownParent: 'body',
            onItemAdd: function () {
                this.blur();
            }
        });
    });

    // --- 2. Reusable Hex Preview & Validation ---
    const hexInput = document.querySelector('.hex-input');
    const swatch = document.querySelector('.color-swatch');

    if (hexInput && swatch) {
        const isValidHex = (value) => /^#([0-9A-Fa-f]{3}){1,2}$/.test(value);

        hexInput.addEventListener('input', function () {
            let value = hexInput.value.trim();
            if (value && !value.startsWith('#')) {
                value = '#' + value;
            }
            if (isValidHex(value)) {
                swatch.style.backgroundColor = value;
            }
        });

        hexInput.addEventListener('blur', function () {
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
    document.addEventListener('input', function (e) {
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

    // --- 4. Save / New / Print button confirmations ---
    const saveBtn = document.querySelector('.btn-save');
    const newBtn = document.querySelector('.btn-new');
    const printBtn = document.querySelector('.btn-print');

    const form = saveBtn ? saveBtn.closest('form') : null;

    if (saveBtn && form) {
        saveBtn.addEventListener('click', function () {
            if (form.reportValidity()) {
                const formulaIdInput = form.querySelector('[name="formula_id"]');
                const isUpdate = formulaIdInput && formulaIdInput.value.trim() !== '';

                Preline.confirm(
                    isUpdate ? 'Update Formula?' : 'Save Formula?',
                    isUpdate
                        ? 'Are you sure you want to update this formula? Please verify all technical specs before confirming.'
                        : 'Are you sure you want to save this formula? Please verify all technical specs before confirming.',
                    'success',
                    () => {
                        form.submit();
                    }
                );
            }
        });
    }

    if (newBtn) {
        newBtn.addEventListener('click', function () {
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
})();