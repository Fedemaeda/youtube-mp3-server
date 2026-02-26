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
        setStatus('Connecting to server...', 'info');

        try {
            // Step 1: Tell the server to start the download/conversion
            // We'll use the same API but we'll fetch it first to check for errors
            const response = await fetch(`${serverUrl}/api/download`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                let errorMessage = 'Server error';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    errorMessage = await response.text() || response.statusText;
                }
                throw new Error(errorMessage);
            }

            // Step 2: If successful, the server already processed it.
            // Now we trigger the actual file download.
            const getUrl = new URL(`${serverUrl}/api/download`);
            getUrl.searchParams.append('url', url);

            chrome.downloads.download({
                url: getUrl.toString(),
                saveAs: false
            }, () => {
                setStatus('Download started! Check folder.', 'success');
                setTimeout(() => {
                    window.close();
                }, 3000);
            });

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
