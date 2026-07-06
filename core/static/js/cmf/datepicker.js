document.addEventListener('DOMContentLoaded', function() {

    // Sentinel date used internally to represent "ASAP"
    const ASAP_SENTINEL = new Date(8640000000000000);

    document.querySelectorAll('.flatpickr-container').forEach(container => {
        const input = container.querySelector('input');

        let options = {
            wrap: true,
            allowInput: true,
            dateFormat: "m/d/Y",
            disableMobile: true,
        };

        if (input.classList.contains('date-picker-multiple')) {
            options.mode = "multiple";
            options.conjunction = ", ";
        }

        if (input.classList.contains('date-picker-asap')) {
            // Teach Flatpickr that "ASAP" IS a valid parsed value
            options.parseDate = function(datestr, format) {
                if (datestr.trim().toUpperCase() === "ASAP") {
                    return ASAP_SENTINEL;
                }
                return flatpickr.parseDate(datestr, format);
            };

            // Teach Flatpickr to render the sentinel back out as "ASAP"
            options.formatDate = function(date, format) {
                if (date.getTime() === ASAP_SENTINEL.getTime()) {
                    return "ASAP";
                }
                return flatpickr.formatDate(date, format);
            };
        }

        flatpickr(container, options);
    });
});