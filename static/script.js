document.addEventListener('DOMContentLoaded', () => {
    // --- Mouse Follower Logic ---
    const glow = document.getElementById('cursor-glow');
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let currentX = mouseX;
    let currentY = mouseY;

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function animate() {
        // Smooth interpolation (laziness)
        currentX += (mouseX - currentX) * 0.1;
        currentY += (mouseY - currentY) * 0.1;

        if (glow) {
            glow.style.transform = `translate(calc(${currentX}px - 50%), calc(${currentY}px - 50%))`;
        }
        requestAnimationFrame(animate);
    }
    animate();

    const form = document.getElementById('download-form');
    const urlInput = document.getElementById('url-input');
    const submitBtn = document.getElementById('submit-btn');
    const mp4Btn = document.getElementById('mp4-btn');
    const statusMessage = document.getElementById('status-message');

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
        } else {
            submitBtn.disabled = false;
            mp4Btn.disabled = false;
            btnText.style.display = 'block';
            spinner.style.display = 'none';
        }
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        handleDownload('mp3', submitBtn);
    });

    mp4Btn.addEventListener('click', () => {
        handleDownload('mp4', mp4Btn);
    });

    async function handleDownload(format, btn) {
        const url = urlInput.value.trim();
        if (!url) return;

        setLoading(true, btn, `Processing ${format.toUpperCase()}... this may take up to a minute.`);
        clearStatus();

        try {
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
                } catch (e) {
                    errorMessage = await response.text() || response.statusText;
                }
                throw new Error(errorMessage);
            }

            // Update status for streaming phase
            setStatus(`Streaming ${format.toUpperCase()} to browser...`, 'loading');

            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `file.${format}`;
            if (contentDisposition && contentDisposition.includes('attachment')) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
                if (filenameMatch && filenameMatch.length === 2) {
                    filename = filenameMatch[1];
                }
            }

            const blob = await response.blob();

            // Final phase: saving file
            setStatus('Saving file...', 'loading');

            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();

            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);

            setStatus('Download complete!', 'success');
            setTimeout(clearStatus, 3000);
            urlInput.value = '';

        } catch (error) {
            console.error('Download error:', error);
            setStatus(error.message, 'error');
        } finally {
            setLoading(false, btn);
        }
    }

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
