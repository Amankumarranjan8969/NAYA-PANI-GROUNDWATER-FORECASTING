import urllib.request
import re

url = 'https://free3d.com/3d-model/mountain-6839.html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print('HTTP 200, length:', len(html))
        m = re.search(r'<title>(.*?)</title>', html, re.I)
        if m:
            print('Title:', m.group(1))
        # Look for images and download buttons
        imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        print('Images found:', [img for img in imgs if 'mountain' in img.lower() or 'model' in img.lower()][:5])
        links = re.findall(r'href=["\']([^"\']+)["\']', html)
        print('Links found:', [l for l in links if 'download' in l.lower() or '.zip' in l.lower() or '.obj' in l.lower()][:5])
except Exception as e:
    print('Error:', e)
