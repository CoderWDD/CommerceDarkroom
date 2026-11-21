import json
import time
import requests

def test_sse():
    url = "http://127.0.0.1:3000/api/v1/studio/render-batch"
    payload = {
        "session_id": "sess_1795246787_init",
        "aspect_ratio": "1:1",
        "concurrency": 1,
        "perspective_ids": ["01_white_bg"]
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    t0 = time.time()
    print(f"[{time.strftime('%X')}] Sending POST to {url}...")
    with requests.post(url, json=payload, headers=headers, stream=True, timeout=120) as resp:
        print(f"[{time.strftime('%X')}] HTTP Response: {resp.status_code}, headers: {dict(resp.headers)}")
        for line in resp.iter_lines():
            if line:
                decoded = line.decode('utf-8', errors='replace')
                elapsed = time.time() - t0
                print(f"[{time.strftime('%X')}] (+{elapsed:.2f}s) SSE line: {decoded}")
            else:
                elapsed = time.time() - t0
                print(f"[{time.strftime('%X')}] (+{elapsed:.2f}s) SSE empty line (event delimiter)")

if __name__ == "__main__":
    test_sse()
