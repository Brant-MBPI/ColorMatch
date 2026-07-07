Dropzone.autoDiscover = false;

document.addEventListener('DOMContentLoaded', function() {
    const uploadModal = document.getElementById('uploadModal');
    
    if (document.getElementById('dropzone-upload')) {
        const myDropzone = new Dropzone("#dropzone-upload", {
            url: "/upload-endpoint/", // Replace with your Django URL
            autoProcessQueue: false,  // Manual trigger
            uploadMultiple: true,
            parallelUploads: 10,
            maxFiles: 5,
            maxFilesize: 10, // MB
            addRemoveLinks: true,
            dictRemoveFile: "Remove",
            
            init: function() {
                const submitBtn = document.querySelector("#btn-upload-submit");
                const dzInstance = this;

                submitBtn.addEventListener("click", function() {
                    dzInstance.processQueue();
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