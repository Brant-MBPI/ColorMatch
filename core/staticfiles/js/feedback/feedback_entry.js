document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('feedbackEntryForm');
    const saveBtn = document.querySelector('.btn-save-feedback');
    const currentStatusInput = document.getElementById('id_f_current_status');

    // 1. Initial Warning (Existing Logic)
    if (currentStatusInput && currentStatusInput.value.trim().toLowerCase() === 'pending') {
        Preline.confirm(
            'Entry Not Completed',
            'This record is still "Pending". Technical details and codes may be missing. Please ensure the tracking record is updated before saving feedback.',
            'warning'
        );
    }

    // 2. Hard Validation & Save Logic
    if (saveBtn && form) {
        saveBtn.addEventListener('click', function () {
            
            // Step A: Check standard validation (Comments, Storage, etc.)
            if (!form.reportValidity()) {
                return; // Stop if editable required fields are empty
            }

            // Step B: Manual check for Readonly Required fields
            // We look for any [required] field that is empty
            const emptyRequiredFields = Array.from(form.querySelectorAll('[required]'))
                .filter(input => !input.value.trim());

            if (emptyRequiredFields.length > 0) {
                // If readonly fields like Product Code or Lot No are empty
                Preline.confirm(
                    'Missing System Data',
                    'Cannot save feedback because this record is missing required tracking information. Please complete the "Pending/Completed" update for this record first.',
                    'danger',
                    () => { /* No action, just closes */ }
                );
                return; // Hard stop: Do not show the "Save" confirmation
            }

            // Step C: If everything (Editable + Readonly) has a value, show Save Confirmation
            Preline.confirm(
                'Save Feedback?',
                'Are you sure you want to update the feedback and monitoring details for this record?',
                'success',
                () => {
                    form.submit();
                }
            );
        });
    }
});