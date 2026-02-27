import requests
import argparse
import sys

def test_api(url, target_url, format_type):
    api_url = f"{url}/api/download"
    payload = {"url": target_url, "format": format_type}
    
    print(f"Testing {api_url} with format {format_type}...")
    try:
        response = requests.post(api_url, json=payload, timeout=120)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
        
        if response.status_code == 200:
            print("Success! The server returned a valid response.")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Request failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://144.22.61.82:5000")
    parser.add_argument("--url", required=True)
    parser.add_argument("--format", default="mp3")
    args = parser.parse_args()
    
    success = test_api(args.server, args.url, args.format)
    sys.exit(0 if success else 1)
