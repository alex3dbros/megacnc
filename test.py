import json
import urllib.request

url = "http://192.168.1.127/api/get_chemistry"
body = json.dumps({"CiD": 0}).encode("utf-8")
req = urllib.request.Request(
    url,
    data=body,
    method="POST",
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=5) as r:
    data = r.read()
    print("status:", r.status, "len:", len(data))
    print("raw:", data[:80])  # primele bytes
    try:
        print("text:", data.decode("ascii"))
    except UnicodeDecodeError:
        print("not ascii (probabil msgpack)")

# opțional: decode msgpack
try:
    import msgpack
    print("msgpack:", msgpack.unpackb(data, raw=False))
except ImportError:
    print("pip install msgpack pentru decode")
except Exception as e:
    print("msgpack error:", e)