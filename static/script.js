document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('download-form');
    const urlInput = document.getElementById('url-input');
    const submitBtn = document.getElementById('submit-btn');
    const mp4Btn = document.getElementById('mp4-btn');
    const statusMessage = document.getElementById('status-message');
    const cookieUploadBtn = document.getElementById('cookie-upload-btn');
    const cookiesFileInput = document.getElementById('cookies-file');
    const cookieStatus = document.getElementById('cookie-status');

    function setStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message show ${type}`;
    }

    function clearStatus() {
        statusMessage.className = 'status-message';
        statusMessage.textContent = '';
    }

    function setLoading(isLoading, btn, message = 'Downloading and converting... This may take a moment.') {
        const btnText = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.spinner');

        if (isLoading) {
            submitBtn.disabled = true;
            mp4Btn.disabled = true;
            btnText.style.display = 'none';
            spinner.style.display = 'block';
            setStatus(message, 'loading');
            return;
        }

        submitBtn.disabled = false;
        mp4Btn.disabled = false;
        btnText.style.display = 'block';
        spinner.style.display = 'none';
    }

    function getFilenameFromDisposition(contentDisposition, fallbackName) {
        if (!contentDisposition) {
            return fallbackName;
        }

        const utf8Match = contentDisposition.match(/filename\*\s*=\s*UTF-8''([^;]+)/i);
        if (utf8Match && utf8Match[1]) {
            return decodeURIComponent(utf8Match[1]).trim();
        }

        const quotedMatch = contentDisposition.match(/filename\s*=\s*"([^"]+)"/i);
        if (quotedMatch && quotedMatch[1]) {
            return quotedMatch[1].trim();
        }

        const plainMatch = contentDisposition.match(/filename\s*=\s*([^;]+)/i);
        if (plainMatch && plainMatch[1]) {
            return plainMatch[1].trim().replace(/^"|"$/g, '');
        }

        return fallbackName;
    }

    async function validateUrl(url) {
        const response = await fetch('/api/validate-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.error || 'Unsupported URL.');
        }
    }

    async function handleDownload(format, btn) {
        const url = urlInput.value.trim();
        if (!url) {
            setStatus('Paste a full YouTube, X/Twitter, or Instagram URL.', 'error');
            return;
        }

        try {
            clearStatus();
            setLoading(true, btn, `Processing ${format.toUpperCase()}... this may take up to a minute.`);

            await validateUrl(url);

            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url, format })
            });

            if (!response.ok) {
                let errorMessage = `Failed to download ${format}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (error) {
                    errorMessage = await response.text() || response.statusText;
                }
                throw new Error(errorMessage);
            }

            setStatus(`Streaming ${format.toUpperCase()} to browser...`, 'loading');

            const backendFilename = response.headers.get('X-Download-Filename');
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = (backendFilename && backendFilename.trim())
                ? backendFilename.trim()
                : getFilenameFromDisposition(contentDisposition, `file.${format}`);

            const blob = await response.blob();
            setStatus('Saving file...', 'loading');

            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.style.display = 'none';
            link.href = downloadUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

            setStatus('Download complete.', 'success');
            setTimeout(clearStatus, 3000);
            urlInput.value = '';
        } catch (error) {
            console.error('Download error:', error);
            setStatus(error.message, 'error');
        } finally {
            setLoading(false, btn);
        }
    }

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        handleDownload('mp3', submitBtn);
    });

    mp4Btn.addEventListener('click', () => {
        handleDownload('mp4', mp4Btn);
    });

    fetch('/api/cookies-status')
        .then((response) => response.json())
        .then((data) => {
            if (data.has_cookies) {
                cookieStatus.textContent = 'Cookies loaded. Authenticated as a real user.';
                cookieStatus.className = 'cookie-status ok';
                return;
            }

            cookieStatus.textContent = 'No cookies uploaded. Downloads may fail on cloud servers.';
            cookieStatus.className = 'cookie-status missing';
        })
        .catch(() => {
            cookieStatus.textContent = 'Could not check cookie status.';
            cookieStatus.className = 'cookie-status';
        });

    cookieUploadBtn.addEventListener('click', () => cookiesFileInput.click());

    cookiesFileInput.addEventListener('change', async () => {
        const file = cookiesFileInput.files[0];
        if (!file) {
            return;
        }

        const formData = new FormData();
        formData.append('cookies', file);
        cookieStatus.textContent = 'Uploading...';
        cookieStatus.className = 'cookie-status';

        try {
            const response = await fetch('/api/upload-cookies', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Upload failed.');
            }

            cookieStatus.textContent = 'Cookies uploaded successfully.';
            cookieStatus.className = 'cookie-status ok';
        } catch (error) {
            cookieStatus.textContent = `Error: ${error.message}`;
            cookieStatus.className = 'cookie-status';
        }
    });
});
