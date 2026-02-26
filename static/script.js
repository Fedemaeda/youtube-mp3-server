document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('download-form');
    const urlInput = document.getElementById('url-input');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.querySelector('.btn-text');
    const spinner = document.querySelector('.spinner');
    const statusMessage = document.getElementById('status-message');

    function setStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message show ${type}`;
    }

    function clearStatus() {
        statusMessage.className = 'status-message';
        statusMessage.textContent = '';
    }

    function setLoading(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            spinner.style.display = 'block';
            setStatus('Downloading and converting... This may take a moment.', 'loading');
        } else {
            submitBtn.disabled = false;
            btnText.style.display = 'block';
            spinner.style.display = 'none';
        }
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const url = urlInput.value.trim();
        if (!url) return;

        setLoading(true);
        clearStatus();

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                let errorMessage = 'Failed to download audio';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    // If response is not JSON, use the status text
                    errorMessage = await response.text() || response.statusText;
                }
                throw new Error(errorMessage);
            }

            // Get the filename from the Content-Disposition header if available
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'audio.mp3';
            if (contentDisposition && contentDisposition.includes('attachment')) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
                if (filenameMatch && filenameMatch.length === 2) {
                    filename = filenameMatch[1];
                }
            }

            // Create a blob from the response and trigger download
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();

            // Clean up
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);

            setStatus('Download complete!', 'success');
            setTimeout(clearStatus, 3000);
            urlInput.value = '';

        } catch (error) {
            console.error('Download error:', error);
            setStatus(error.message, 'error');
        } finally {
            setLoading(false);
        }
    });

    // --- Cookie Upload Logic ---
    const cookieUploadBtn = document.getElementById('cookie-upload-btn');
    const cookiesFileInput = document.getElementById('cookies-file');
    const cookieStatus = document.getElementById('cookie-status');

    // Check current cookie status on load
    fetch('/api/cookies-status')
        .then(r => r.json())
        .then(data => {
            if (data.has_cookies) {
                cookieStatus.textContent = '✅ Cookies loaded — authenticated as a real user.';
                cookieStatus.className = 'cookie-status ok';
            } else {
                cookieStatus.textContent = '⚠️ No cookies uploaded. May fail on cloud servers.';
                cookieStatus.className = 'cookie-status missing';
            }
        });

    cookieUploadBtn.addEventListener('click', () => cookiesFileInput.click());

    cookiesFileInput.addEventListener('change', async () => {
        const file = cookiesFileInput.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('cookies', file);
        cookieStatus.textContent = 'Uploading...';
        cookieStatus.className = 'cookie-status';
        try {
            const res = await fetch('/api/upload-cookies', { method: 'POST', body: formData });
            const data = await res.json();
            if (res.ok) {
                cookieStatus.textContent = '✅ Cookies uploaded successfully!';
                cookieStatus.className = 'cookie-status ok';
            } else {
                cookieStatus.textContent = `❌ Error: ${data.error}`;
                cookieStatus.className = 'cookie-status';
            }
        } catch (e) {
            cookieStatus.textContent = '❌ Upload failed.';
            cookieStatus.className = 'cookie-status';
        }
    });
});
