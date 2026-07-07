Dropzone.autoDiscover = false;

document.addEventListener('DOMContentLoaded', function() {
    const uploadModal = document.getElementById('uploadModal');
    
    if (document.getElementById('dropzone-upload')) {
        const myDropzone = new Dropzone("#dropzone-upload", {
            url: "/upload-endpoint/", // Replace with your Django URL
            autoProcessQueue: false,
            uploadMultiple: true,
            parallelUploads: 10,
            maxFiles: 10,
            maxFilesize: 10, 
            addRemoveLinks: true,
            dictRemoveFile: "Remove",
            
            // UI sizing
            thumbnailWidth: 120,
            thumbnailHeight: 120,

            init: function() {
                const submitBtn = document.querySelector("#btn-upload-submit");
                const dzInstance = this;

                // Handle the Upload All button
                submitBtn.addEventListener("click", function() {
                    if (dzInstance.getQueuedFiles().length > 0) {
                        dzInstance.processQueue();
                    } else {
                        alert("Please select files first.");
                    }
                });

                // Set custom icons for non-image files (Excel, PDF, etc.)
                this.on("addedfile", function(file) {
                    if (!file.type.match(/image.*/)) {
                        // Using a standard document icon for non-images
                        dzInstance.emit("thumbnail", file, "https://cdn-icons-png.flaticon.com/512/2991/2991112.png");
                    }
                });

                this.on("queuecomplete", function() {
                    alert("Files uploaded successfully!");
                    bootstrap.Modal.getInstance(uploadModal).hide();
                    dzInstance.removeAllFiles();
                });
            }
        });
    }
});