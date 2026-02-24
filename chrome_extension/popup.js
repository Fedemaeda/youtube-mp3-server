document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('youtube-url');
    const downloadBtn = document.getElementById('download-btn');
    const btnText = document.querySelector('.btn-text');
    const spinner = document.querySelector('.spinner');
    const statusMessage = document.getElementById('status-message');
    const settingsBtn = document.getElementById('settings-btn');

    let serverUrl = '';

    // Load server URL from storage
    chrome.storage.sync.get(['serverUrl'], (result) => {
        if (result.serverUrl) {
            serverUrl = result.serverUrl.replace(/\/$/, ""); // Remove trailing slash
        } else {
            setStatus('Please configure your server URL first!', 'error');
            downloadBtn.disabled = true;
        }
    });

    // Get current active tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const currentUrl = tabs[0].url;
        if (currentUrl.includes('youtube.com/watch') || currentUrl.includes('youtu.be/')) {
            urlInput.value = currentUrl;
        } else {
            urlInput.value = 'Not a YouTube video';
            downloadBtn.disabled = true;
        }
    });

    function setStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
    }

    // Open settings page
    settingsBtn.addEventListener('click', () => {
        chrome.runtime.openOptionsPage();
    });

    // Handle download click
    downloadBtn.addEventListener('click', async () => {
        if (!serverUrl) return;
        const url = urlInput.value;

        downloadBtn.disabled = true;
        btnText.style.display = 'none';
        spinner.style.display = 'block';
        setStatus('Sending request to server...', 'info');

        try {
            const response = await fetch(`${serverUrl}/api/download`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Server Error: ${response.status}`);
            }

            // Get filename
            let filename = 'audio.mp3';
            const contentDisposition = response.headers.get('Content-Disposition');
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?(.+)"?/);
                if (match && match.length === 2) filename = match[1];
            }

            // Download file via Chrome downloads API
            const blob = await response.blob();
            const reader = new FileReader();
            reader.readAsDataURL(blob);
            reader.onloadend = () => {
                const base64data = reader.result;
                chrome.downloads.download({
                    url: base64data,
                    filename: filename,
                    saveAs: true
                }, () => {
                    setStatus('Download ready!', 'success');
                    setTimeout(() => {
                        window.close(); // Close popup
                    }, 2000);
                });
            };

        } catch (error) {
            console.error(error);
            setStatus(error.message, 'error');
        } finally {
            downloadBtn.disabled = false;
            btnText.style.display = 'block';
            spinner.style.display = 'none';
        }
    });
});
