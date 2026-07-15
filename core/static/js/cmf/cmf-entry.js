// Use a function to ensure it runs even if content is dynamic
function initFormattingLogic() {
    console.log("Formatting Logic Initialized"); // Check your browser console (F12) for this!

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