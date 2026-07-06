document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Standard Single Date Pickers (Created & Due)
    flatpickr(".date-picker-single", {
        dateFormat: "d/m/Y",
        allowInput: true,
        disableMobile: true
    });

    // 2. Multiple Date Picker (Received)
    flatpickr(".date-picker-multiple", {
        mode: "multiple",
        dateFormat: "d/m/Y",
        conjunction: ", ",
        allowInput: true,
        disableMobile: true
    });

    // 3. ASAP Logic (Required Date)
    const asapPicker = flatpickr(".date-picker-asap", {
        dateFormat: "d/m/Y",
        allowInput: true,
        disableMobile: true,
        onClose: function(selectedDates, dateStr, instance) {
            const val = instance.input.value.toUpperCase();
            if (val === "ASAP") {
                instance.input.value = "ASAP";
            }
        }
    });

    // Handle manual typing of "ASAP"
    document.querySelector('.date-picker-asap').addEventListener('blur', function() {
        const val = this.value.toUpperCase();
        if (val.includes("ASAP")) {
            this.value = "ASAP";
        } else {
            // If it's not ASAP and not a valid date, Flatpickr usually clears it
            // but we ensure it remains strict here if needed.
        }
    });

    // Global: Make the calendar icon trigger the picker
    document.querySelectorAll('.input-group-text').forEach(icon => {
        icon.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            if (input._flatpickr) {
                input._flatpickr.open();
            }
        });
    });
});