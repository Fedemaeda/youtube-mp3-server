import requests
import random
import concurrent.futures

def get_proxies(url):
    try:
        r = requests.get(url, timeout=5)
        return [p.strip() for p in r.text.splitlines() if p.strip()]
    except:
        return []

urls = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
]

all_proxies = []
for u in urls:
    pts = get_proxies(u)
    ptype = "socks5" if "socks5" in u else "http"
    all_proxies.extend([(ptype, p) for p in pts])

random.shuffle(all_proxies)
print(f"Testing {len(all_proxies)} total proxies...")

def check_proxy(proxy_info):
    ptype, p = proxy_info
    proxy_url = f"{ptype}://{p}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    try:
        # Check actual YouTube access instead of just a handshake
        r = requests.get('https://www.youtube.com', proxies=proxies, timeout=5)
        if r.status_code == 200:
            return proxy_url
    except Exception as e:
        pass
    return None

working = []
tested = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    # Only test the first 200 to save time
    futures = {executor.submit(check_proxy, p): p for p in all_proxies[:200]}
    for future in concurrent.futures.as_completed(futures):
        res = future.result()
        tested += 1
        if res:
            working.append(res)
            print(f"FOUND WORKING: {res}")
            if len(working) >= 3:
                break
        if tested % 50 == 0:
            print(f"Tested {tested}...")

print(f"Done. Found {len(working)} working: {working}")
