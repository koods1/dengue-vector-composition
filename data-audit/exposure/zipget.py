"""Fetch named members from a remote zip via HTTP range requests."""
import urllib.request, struct, zlib, json, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

URL = 'https://ndownloader.figshare.com/files/34829370'   # SSP2.zip
WANT = sys.argv[1:] or ['SPP2/SSP2_2050.tif', 'SPP2/SSP2_2050.tfw']

def rng(start, end):
    req = urllib.request.Request(URL, headers={'Range': f'bytes={start}-{end}'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read()

ent = {e['name']: e for e in json.load(open('zip_entries.json'))}
os.makedirs('pop', exist_ok=True)
for name in WANT:
    if name not in ent:
        print(f'!! {name} not in archive'); continue
    e = ent[name]
    # local file header: 30 bytes fixed + name + extra
    hdr = rng(e['offset'], e['offset'] + 29)
    nlen, elen = struct.unpack('<HH', hdr[26:30])
    data_start = e['offset'] + 30 + nlen + elen
    blob = rng(data_start, data_start + e['csize'] - 1)
    raw = zlib.decompress(blob, -15) if e['comp'] == 8 else blob
    out = 'pop/' + os.path.basename(name)
    open(out, 'wb').write(raw)
    print(f"{name:<26} fetched {len(blob):,} -> wrote {len(raw):,} bytes to {out}")
