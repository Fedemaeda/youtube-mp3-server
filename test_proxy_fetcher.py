import requests
import socket

def is_proxy_reachable(proxy_url):
    try:
        parts = proxy_url.split('://')[-1].split(':')
        host = parts[0]
        port = int(parts[1])
        with socket.create_connection((host, port), timeout=3):
            return True
    except Exception as e:
        return False

def get_residential_proxy():
    print("Testing Proxyscrape elite SOCKS5 list...")
    try:
        api_url = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=1000&country=all&ssl=all&anonymity=elite"
        resp = requests.get(api_url, timeout=10)
        proxies = [p.strip() for p in resp.text.splitlines() if p.strip()]
        print(f"Found {len(proxies)} candidates.")
        
        for p in proxies[:20]:
            proxy_candidate = f"socks5://{p}"
            reachable = is_proxy_reachable(proxy_candidate)
            print(f"Proxy {proxy_candidate}: {'REACHABLE' if reachable else 'FAILED'}")
            if reachable:
                return proxy_candidate
    except Exception as e:
        print(f"Error: {e}")
    return None

if __name__ == "__main__":
    result = get_residential_proxy()
    if result:
        print(f"\nWINNER: {result}")
    else:
        print("\nNO WORKING PROXIES FOUND.")
