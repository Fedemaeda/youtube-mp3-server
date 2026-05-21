document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('youtube-url');
    const downloadBtn = document.getElementById('download-btn');
    const downloadMp4Btn = document.getElementById('download-mp4-btn');
    const btnText = document.querySelector('.btn-text');
    const spinner = document.querySelector('.spinner');
    const statusMessage = document.getElementById('status-message');
    const settingsBtn = document.getElementById('settings-btn');

    const DEFAULT_SERVER_URL = '';
    let serverUrl = DEFAULT_SERVER_URL;

    // Load server URL from storage
    chrome.storage.sync.get(['serverUrl'], (result) => {
        if (result.serverUrl) {
            serverUrl = result.serverUrl.replace(/\/$/, ""); // Remove trailing slash
        }
        console.log('Using server:', serverUrl);
        updateServerBadge();
    });

    const serverBadge = document.getElementById('server-badge');

    async function updateServerBadge() {
        if (!serverUrl) {
            setServerStatus('Set server URL', 'info');
            return;
        }
        try {
            const resp = await fetch(`${serverUrl}/api/cookies-status`);
            if (resp.ok) {
                const data = await resp.json();
                if (data.has_cookies) {
                    setServerStatus('Ready (Active)', 'success');
                } else {
                    setServerStatus('Online (Wait sync)', 'info');
                }
            }
        } catch (e) {
            console.warn('Server unreachable');
            setServerStatus('Offline', 'error');
        }
    }

    function setServerStatus(message, type) {
        serverBadge.textContent = message;
        serverBadge.className = `server-badge ${type}`;
    }

    function hasConfiguredServer() {
        return Boolean(serverUrl && /^https?:\/\//i.test(serverUrl));
    }

    // Get current active tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const activeTab = tabs[0];
        const currentUrl = activeTab?.url || '';
        const isYouTube = currentUrl.includes('youtube.com/watch') || currentUrl.includes('youtu.be/');
        const isX = currentUrl.includes('x.com/') || currentUrl.includes('twitter.com/');
        const isInstagram = currentUrl.includes('instagram.com/p/') ||
            currentUrl.includes('instagram.com/reels/') ||
            currentUrl.includes('instagram.com/reel/') ||
            currentUrl.includes('instagram.com/tv/');

        if (isYouTube || isX || isInstagram) {
            urlInput.value = currentUrl;
        } else {
            urlInput.value = '';
            urlInput.placeholder = 'No supported video found';
            downloadBtn.disabled = true;
            downloadMp4Btn.disabled = true;
            urlInput.classList.add('disabled');
        }
    });

    function setStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        
        // Add a subtle fade-in effect via class
        statusMessage.style.opacity = '0';
        setTimeout(() => {
            statusMessage.style.opacity = '1';
        }, 10);
    }

    // Open settings page
    settingsBtn.addEventListener('click', () => {
        chrome.runtime.openOptionsPage();
    });

    // Handle download clicks
    downloadBtn.addEventListener('click', () => handleDownload('mp3', downloadBtn));
    downloadMp4Btn.addEventListener('click', () => handleDownload('mp4', downloadMp4Btn));

    async function getCookiesForDomain(url) {
        const domain = new URL(url).hostname;
        // Get cookies for the main domain (e.g., .youtube.com)
        const baseDomain = domain.split('.').slice(-2).join('.');
        return new Promise((resolve) => {
            chrome.cookies.getAll({ domain: baseDomain }, (cookies) => {
                // Filter out some unnecessary cookies if needed, but let's send them all
                resolve(cookies);
            });
        });
    }

    async function syncCookies(url) {
        try {
            setStatus('Synchronizing session...', 'info');
            const cookies = await getCookiesForDomain(url);
            
            if (!cookies || cookies.length === 0) {
                console.log('No cookies found for domain');
                return false; 
            }

            const resp = await fetch(`${serverUrl}/api/sync-cookies-json`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookies: cookies })
            });
            
            if (!resp.ok) throw new Error('Sync failed server-side');
            
            const data = await resp.json();
            return data.success;
        } catch (error) {
            console.warn('Cookie sync failed:', error);
            return false;
        }
    }

    async function handleDownload(format, btn) {
        if (!hasConfiguredServer()) {
            setStatus('Please configure your online server URL first.', 'error');
            return;
        }
        const url = urlInput.value;
        if (!url) return;

        const btnText = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.spinner');

        // Disable both buttons during processing
        downloadBtn.disabled = true;
        downloadMp4Btn.disabled = true;

        btnText.style.display = 'none';
        spinner.style.display = 'block';
        
        try {
            const validateResp = await fetch(`${serverUrl}/api/validate-url`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            if (!validateResp.ok) {
                let message = 'Invalid URL';
                try {
                    const data = await validateResp.json();
                    message = data.error || message;
                } catch (e) {}
                setStatus(message, 'error');
                resetBtns();
                return;
            }

            // Step 1: Sync cookies (especially important for Instagram/YouTube)
            const syncSuccess = await syncCookies(url);
            if (!syncSuccess) {
                console.warn('Could not sync cookies. Server might use its own session.');
            }

            // Step 2: Trigger download
            setStatus(`Processing ${format.toUpperCase()}...`, 'info');
            
            const getUrl = new URL(`${serverUrl}/api/download`);
            getUrl.searchParams.append('url', url);
            getUrl.searchParams.append('format', format);

            chrome.downloads.download({
                url: getUrl.toString(),
                saveAs: false,
                // Add header to bypass some proxy warnings if any
                headers: [
                    { name: 'X-Client-Type', value: 'ZenRip-Extension' }
                ]
            }, (downloadId) => {
                if (chrome.runtime.lastError) {
                    console.error(chrome.runtime.lastError);
                    setStatus(chrome.runtime.lastError.message, 'error');
                    resetBtns();
                    return;
                }

                setStatus('Requesting file...', 'info');

                const listener = (delta) => {
                    if (delta.id === downloadId && delta.state) {
                        if (delta.state.current === 'complete') {
                            setStatus('Download complete!', 'success');
                            chrome.downloads.onChanged.removeListener(listener);
                            setTimeout(() => {
                                resetBtns();
                                window.close();
                            }, 2500);
                        } else if (delta.state.current === 'interrupted') {
                            setStatus('Download failed (Interrupted)', 'error');
                            chrome.downloads.onChanged.removeListener(listener);
                            resetBtns();
                        }
                    }
                };
                chrome.downloads.onChanged.addListener(listener);
            });

        } catch (error) {
            console.error(error);
            setStatus('Connection error. Is server up?', 'error');
            resetBtns();
        }
    }

    function resetBtns() {
        downloadBtn.disabled = false;
        downloadMp4Btn.disabled = false;

        const btns = [downloadBtn, downloadMp4Btn];
        btns.forEach(btn => {
            btn.querySelector('.btn-text') && (btn.querySelector('.btn-text').style.display = 'block');
            btn.querySelector('.spinner') && (btn.querySelector('.spinner').style.display = 'none');
        });
    }
});
