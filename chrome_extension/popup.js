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
        setStatus('Processing video... this may take a moment.', 'info');

        try {
            const getUrl = new URL(`${serverUrl}/api/download`);
            getUrl.searchParams.append('url', url);

            chrome.downloads.download({
                url: getUrl.toString(),
                saveAs: false,
                headers: [
                    { name: 'ngrok-skip-browser-warning', value: '69420' }
                ]
            }, (downloadId) => {
                if (chrome.runtime.lastError) {
                    console.error(chrome.runtime.lastError);
                    setStatus(chrome.runtime.lastError.message, 'error');
                    resetBtn();
                    return;
                }

                setStatus('Downloading to folder...', 'info');

                // Listener to track when the download is actually finished
                const listener = (delta) => {
                    if (delta.id === downloadId && delta.state) {
                        if (delta.state.current === 'complete') {
                            setStatus('Download complete!', 'success');
                            chrome.downloads.onChanged.removeListener(listener);
                            setTimeout(() => {
                                resetBtn();
                                window.close();
                            }, 2000);
                        } else if (delta.state.current === 'interrupted') {
                            setStatus('Download failed or cancelled.', 'error');
                            chrome.downloads.onChanged.removeListener(listener);
                            resetBtn();
                        }
                    }
                };
                chrome.downloads.onChanged.addListener(listener);
            });

        } catch (error) {
            console.error(error);
            setStatus(error.message, 'error');
            resetBtn();
        }
    });

    function resetBtn() {
        downloadBtn.disabled = false;
        btnText.style.display = 'block';
        spinner.style.display = 'none';
    }
});
