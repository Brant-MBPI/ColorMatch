document.addEventListener('DOMContentLoaded', function () {
    const currentStatusInput = document.getElementById('id_f_current_status');
    const matchingNo = document.getElementById('id_f_matching_no')?.value || 'this record';

    if (currentStatusInput) {
        const statusValue = currentStatusInput.value.trim();

        // Check if status is Pending (case-insensitive)
        if (statusValue.toLowerCase() === 'pending') {
            
            // Using your established Preline.confirm wrapper for the notification
            Preline.confirm(
                'Entry Not Completed',
                `Warning: ${matchingNo} is still marked as Pending. Technical specifications and codes have not yet been finalized in the tracking system.`,
                'warning',
                () => {
                    // This is just an informative alert, so we do nothing on confirm
                }
            );
        }
    }
});