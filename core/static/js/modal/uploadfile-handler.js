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

        const myDropzone = new Dropzone("#dropzone-upload", {
            url: "/upload-endpoint/",
            autoProcessQueue: false,
            uploadMultiple: true,
            parallelUploads: 10,
            maxFiles: 10,
            addRemoveLinks: false, // our template already has its own remove link
            previewTemplate: previewTemplate,
            thumbnailWidth: 100,
            thumbnailHeight: 48,

            init: function() {
                const submitBtn = document.querySelector("#btn-upload-submit");
                const dzInstance = this;

                submitBtn.addEventListener("click", function() {
                    dzInstance.processQueue();
                });

                this.on("addedfile", function(file) {
                    // Tooltip for full filename
                    if (file.previewElement) {
                        const nameEl = file.previewElement.querySelector(".cz-filename");
                        if (nameEl) nameEl.setAttribute("title", file.name);
                    }

                    // filesize() returns an HTML string like "<strong>73.8</strong> KB"
                    // so it must be rendered with innerHTML, not textContent
                    const sizeEl = file.previewElement.querySelector(".cz-size");
                    if (sizeEl) {
                        sizeEl.innerHTML = dzInstance.filesize(file.size);
                    }

                    // Bootstrap Icon Injection for non-image files
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