Dropzone.autoDiscover = false;

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('dropzone-upload')) {

        const previewTemplate = `<div class="cz-preview">
<div class="cz-image"><img data-dz-thumbnail></div>
<div class="cz-details">
<div class="cz-filename" data-dz-name></div>
<div class="cz-size" data-dz-size></div>
</div>
<a class="cz-remove" href="javascript:void(0);" data-dz-remove>Remove</a>
</div>`.trim();

        // Exposed on window so entry.js can read its accepted files at
        // save-time — Dropzone no longer POSTs anywhere itself; we just
        // use it as a drag-and-drop file picker with previews.
        window.myDropzone = new Dropzone("#dropzone-upload", {
            url: "/upload-endpoint/",   // unused now — no processQueue() call happens anymore
            autoProcessQueue: false,
            uploadMultiple: true,
            parallelUploads: 10,
            maxFiles: 10,
            addRemoveLinks: false,
            previewTemplate: previewTemplate,
            thumbnailWidth: 100,
            thumbnailHeight: 48,

            init: function() {
                const dzInstance = this;

                // Removed: the old submitBtn -> processQueue() wiring.
                // Saving now happens through the main entry form's Save
                // button (entry.js), which pulls files from this
                // Dropzone instance directly instead of triggering a
                // separate upload request.

                this.on("addedfile", function(file) {
                    if (file.previewElement) {
                        const nameEl = file.previewElement.querySelector(".cz-filename");
                        if (nameEl) nameEl.setAttribute("title", file.name);
                    }

                    const sizeEl = file.previewElement.querySelector(".cz-size");
                    if (sizeEl) {
                        sizeEl.innerHTML = dzInstance.filesize(file.size);
                    }

                    if (!file.type.match(/image.*/)) {
                        const imageContainer = file.previewElement.querySelector(".cz-image");
                        imageContainer.innerHTML = '';

                        let iconClass = "bi-file-earmark-text";
                        if (file.name.endsWith('.pdf')) iconClass = "bi-file-earmark-pdf";
                        if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) iconClass = "bi-file-earmark-excel";
                        if (file.name.endsWith('.doc') || file.name.endsWith('.docx')) iconClass = "bi-file-earmark-word";

                        const iconHtml = document.createElement('i');
                        iconHtml.className = `bi ${iconClass}`;
                        imageContainer.appendChild(iconHtml);
                    }
                });
            }
        });
    }
});