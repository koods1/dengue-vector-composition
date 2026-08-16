"""Read a remote zip's central directory via HTTP range requests, so we can
fetch only the members we need instead of 2.5 GB."""
import urllib.request, struct, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://ndownloader.figshare.com/files/34829370'

def rng(url, start, end):
    req = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()

def tail(url, n):
    req = urllib.request.Request(url, headers={'Range': f'bytes=-{n}'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()

d = tail(URL, 4000)
i = d.rfind(b'PK\x05\x06')
n_ent, cd_size, cd_off = (struct.unpack('<H', d[i + 10:i + 12])[0],
                          struct.unpack('<I', d[i + 12:i + 16])[0],
                          struct.unpack('<I', d[i + 16:i + 20])[0])
print(f'{n_ent} entries, central directory {cd_size:,} B at {cd_off:,}')
cd = rng(URL, cd_off, cd_off + cd_size - 1)

entries, p = [], 0
while p < len(cd) and cd[p:p + 4] == b'PK\x01\x02':
    comp, = struct.unpack('<H', cd[p + 10:p + 12])
    csz, usz = struct.unpack('<II', cd[p + 20:p + 28])
    nlen, elen, clen = struct.unpack('<HHH', cd[p + 28:p + 34])
    lho, = struct.unpack('<I', cd[p + 42:p + 46])
    name = cd[p + 46:p + 46 + nlen].decode('utf8', 'replace')
    entries.append(dict(name=name, comp=comp, csize=csz, usize=usz, offset=lho))
    p += 46 + nlen + elen + clen

print(f'parsed {len(entries)} entries\n')
for e in entries[:12]:
    print(f"  {e['usize']:>14,} u / {e['csize']:>14,} c  method={e['comp']}  {e['name']}")
if len(entries) > 12:
    print(f'  ... and {len(entries) - 12} more')
json.dump(entries, open('zip_entries.json', 'w'), indent=1)
print('\nwrote zip_entries.json')
