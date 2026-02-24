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
            // Instead of downloading into the popup memory (which closes and kills the download),
            // we will instruct Chrome's download manager to download directly from the server API.
            // Since it's a POST request originally, we will append the url as a GET parameter.

            const getUrl = new URL(`${serverUrl}/api/download`);
            getUrl.searchParams.append('url', url);

            chrome.downloads.download({
                url: getUrl.toString(),
                saveAs: false
            }, () => {
                setStatus('Download started! Check your downloads.', 'success');
                setTimeout(() => {
                    window.close(); // Close popup
                }, 2000);
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
