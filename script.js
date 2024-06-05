    const uploadButton = document.getElementById('uploadButton');
    const virusTotalButton = document.getElementById('VTButton');
    const fileInput = document.getElementById('fileInput');
    const resultDisplay = document.getElementById('resultText');
    const statusText = document.getElementById('statusText');
    const VTinfoElements = document.querySelectorAll('.VTinfo');
    const reader = new FileReader();

    fileInput.addEventListener('change', typeCheck);
    uploadButton.addEventListener('click', function() {
        fileInput.click();
    });
    setupReader();


    function setupReader() {
        reader.onload = checkFileSignature;
        reader.onerror = () => {
            console.error('File reading failed');
            resultDisplay.textContent = 'Error: Failed to read file.';
        };
    }

    function checkFileSignature(eventObj) {
        const signature = new DataView(eventObj.target.result).getUint16(0, false);
        if (signature === 0x4D5A) // 0x4D5A is 'MZ' in hexadecimal (PE file signature)
            uploadFile();
        else
            invalidFileScheme(); //allows VirusTotal verification despite file not being a PE

    }

    function uploadFile() {
        if (!fileInput.files[0])
            return;

        var formData = new FormData();
        formData.append('file', fileInput.files[0]);

        startUploadScheme();

        fetch('http://localhost:5000/upload', {
                method: 'POST',
                body: formData,
            })
            .then(response => {
                if (response.ok)
                    return response.json();
                else
                    return response.json().then(errorData => {
                        throw errorData.error;
                    });
            })
            .then(data => {
                if (data.result === 1) { //malware
                    resultDisplay.style.color = 'red'
                    resultDisplay.textContent = 'MALWARE DETECTED!'
                } else { //benign
                    resultDisplay.style.color = '#0ADD08'
                    resultDisplay.textContent = 'FILE IS BENIGN!'
                }
                successUploadScheme(); //UI and active buttons
            })
            .catch(error => {
                failedUploadScheme();
                if (error instanceof TypeError)
                    resultDisplay.textContent = 'Network error, Could not complete the request.'
                else
                    resultDisplay.textContent = error;
            });
    }


virusTotalButton.addEventListener('click', function() {
    if (!fileInput.files[0])
        return;
    var formData = new FormData();
    formData.append('file', fileInput.files[0]);
    startVtScheme();
    fetch('http://localhost:5000/virusTotal', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (response.ok)
                return response.json();
            else
                return response.json().then(errorData => {
                    throw errorData.error;
                });
        })
        .then(data => {
            if('hash' in data){ //file report by md5 hash
                updateStats(data);
                successVtScheme();
            }
            else{ //file report by upload
                startVtUploadScheme();
                pollStatus(data.file_id);
            }
        })
        .catch(error => {
            failedVtScheme();
            if (error instanceof TypeError)
                statusText.textContent = 'Network error, Could not complete the request.';
            else
                statusText.textContent = error;
        });
});


//recursive polling until completed status.
function pollStatus(file_id) {
    setTimeout(() => {
        fetch(`http://localhost:5000/status/${file_id}`)
            .then(response => {
                if (response.ok)
                    return response.json();
                else
                    return response.json().then(errorData => {
                        throw errorData.error;
                    });
            })
            .then(data => {
                if (data.data.attributes.status === 'completed') {
                    updateStats(data);
                    successVtScheme();
                } else {
                    pollStatus(file_id);
                }
            })
            .catch(error => {
                failedVtScheme();
                if (error instanceof TypeError)
                    statusText.textContent = 'Network error, Could not complete the request.';
                else
                    statusText.textContent = error;
            });
    }, 15000);  // Poll every 15 seconds
}


    function typeCheck() {
        reader.readAsArrayBuffer(fileInput.files[0].slice(0, 2));
    }

    function startUploadScheme() {
        uploadButton.disabled = true;
        resultDisplay.style.color = 'white';
        resultDisplay.textContent = 'Loading...';
        virusTotalButton.style.display = 'none';
        statusText.textContent = '';
        for (var i = 0; i < VTinfoElements.length; i++)
            VTinfoElements[i].innerText = '';
    }

    function successUploadScheme() {
        virusTotalButton.style.display = 'block';
        uploadButton.disabled = false;
        virusTotalButton.disabled = false; 
    }

    function failedUploadScheme() {
        resultDisplay.style.color = 'white';
        uploadButton.disabled = false;
        virusTotalButton.disabled = false;
    }

    function invalidFileScheme() {
        resultDisplay.style.color = 'white';
        resultDisplay.textContent = 'Invalid file type!';
        virusTotalButton.style.display = 'block';
        virusTotalButton.disabled = false;
        for (var i = 0; i < VTinfoElements.length; i++)
            VTinfoElements[i].innerText = '';
    }

    function startVtUploadScheme() {
        statusText.textContent = 'Actively scanning with multiple anti-malware engines. this may take a few minutes...';
    }

        function startVtScheme() {
        virusTotalButton.disabled = true;
        uploadButton.disabled = true;
        statusText.textContent = 'Just a moment...';
        statusText.style.display = 'block';
    }

    function successVtScheme() {
        statusText.style.display = 'none';
        uploadButton.disabled = false;
    }

    function failedVtScheme() {
        uploadButton.disabled = false;
        virusTotalButton.disabled = false;
    }


        function updateStats(data) {
        let stats
        let meta
        if('hash' in data) //through file md5 hash
        {
            stats = data.hash.attributes.last_analysis_stats;
            meta = data.hash.attributes
        }
        else //through file upload
        {
            stats = data.data.attributes.stats;
            meta = data.meta.file_info;
        }

        let totalChecks = parseInt(stats.malicious) + parseInt(stats.suspicious) + parseInt(stats.undetected) + parseInt(stats.harmless);

        var mapping = [
            "Detection Rate: " + stats.malicious + "/" + totalChecks,
            "Suspicious: " + stats.suspicious,
            "File Size: " + meta.size + " bytes",
            "MD5: " + meta.md5,
            "SHA-1: " + meta.sha1,
            "SHA-256: " + meta.sha256
        ];

        for (var i = 0; i < VTinfoElements.length; i++) {
            VTinfoElements[i].innerText = mapping[i];
        }
    }