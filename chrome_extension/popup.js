document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('youtube-url');
    const downloadBtn = document.getElementById('download-btn');
    const downloadMp4Btn = document.getElementById('download-mp4-btn');
    const btnText = document.querySelector('.btn-text');
    const spinner = document.querySelector('.spinner');
    const statusMessage = document.getElementById('status-message');
    const settingsBtn = document.getElementById('settings-btn');

    const DEFAULT_SERVER_URL = 'http://144.22.61.82:5000';
    let serverUrl = DEFAULT_SERVER_URL;

    // Load server URL from storage
    chrome.storage.sync.get(['serverUrl'], (result) => {
        if (result.serverUrl) {
            serverUrl = result.serverUrl.replace(/\/$/, ""); // Remove trailing slash
        }
        // If not set, we keep the hardcoded default
        console.log('Using server:', serverUrl);
    });

    // Get current active tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const currentUrl = tabs[0].url;
        const isYouTube = currentUrl.includes('youtube.com/watch') || currentUrl.includes('youtu.be/');
        const isX = currentUrl.includes('x.com/') || currentUrl.includes('twitter.com/');

        if (isYouTube || isX) {
            urlInput.value = currentUrl;
        } else {
            urlInput.value = 'No supported video found';
            downloadBtn.disabled = true;
            downloadMp4Btn.disabled = true;
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

    // Handle download clicks
    downloadBtn.addEventListener('click', () => handleDownload('mp3', downloadBtn));
    downloadMp4Btn.addEventListener('click', () => handleDownload('mp4', downloadMp4Btn));

    async function handleDownload(format, btn) {
        if (!serverUrl) return;
        const url = urlInput.value;
        const btnText = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.spinner');

        // Disable both buttons during processing
        downloadBtn.disabled = true;
        downloadMp4Btn.disabled = true;

        btnText.style.display = 'none';
        spinner.style.display = 'block';
        setStatus(`Processing ${format.toUpperCase()}... this may take a moment.`, 'info');

        try {
            const getUrl = new URL(`${serverUrl}/api/download`);
            getUrl.searchParams.append('url', url);
            getUrl.searchParams.append('format', format);

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
                    resetBtns();
                    return;
                }

                setStatus('Downloading to folder...', 'info');

                const listener = (delta) => {
                    if (delta.id === downloadId && delta.state) {
                        if (delta.state.current === 'complete') {
                            setStatus('Download complete!', 'success');
                            chrome.downloads.onChanged.removeListener(listener);
                            setTimeout(() => {
                                resetBtns();
                                window.close();
                            }, 2000);
                        } else if (delta.state.current === 'interrupted') {
                            setStatus('Download failed or cancelled.', 'error');
                            chrome.downloads.onChanged.removeListener(listener);
                            resetBtns();
                        }
                    }
                };
                chrome.downloads.onChanged.addListener(listener);
            });

        } catch (error) {
            console.error(error);
            setStatus(error.message, 'error');
            resetBtns();
        }
    }

    function resetBtns() {
        downloadBtn.disabled = false;
        downloadMp4Btn.disabled = false;

        const btns = [downloadBtn, downloadMp4Btn];
        btns.forEach(btn => {
            btn.querySelector('.btn-text').style.display = 'block';
            btn.querySelector('.spinner').style.display = 'none';
        });
    }
});
