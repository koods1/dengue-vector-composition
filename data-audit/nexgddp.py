"""D. Which NEX-GDDP-CMIP6 models carry the variables we need across all
three SSPs plus historical? Enumerated from the public S3 bucket so the
model list is a stated criterion rather than a selection."""
import urllib.request, urllib.parse, sys, re, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
B = 'https://nex-gddp-cmip6.s3.amazonaws.com/'
NS = '{http://s3.amazonaws.com/doc/2006-03-01/}'
import xml.etree.ElementTree as ET

def ls(prefix, delim='/'):
    out, tok = [], None
    while True:
        q = {'list-type': '2', 'prefix': prefix, 'max-keys': '1000'}
        if delim: q['delimiter'] = delim
        if tok: q['continuation-token'] = tok
        with urllib.request.urlopen(B + '?' + urllib.parse.urlencode(q), timeout=90) as r:
            x = ET.fromstring(r.read())
        out += [p.find(NS + 'Prefix').text for p in x.findall(NS + 'CommonPrefixes')]
        out += [k.find(NS + 'Key').text for k in x.findall(NS + 'Contents')]
        t = x.find(NS + 'NextContinuationToken')
        if t is None or not t.text: break
        tok = t.text
    return out

root = 'NEX-GDDP-CMIP6/'
models = [p[len(root):].strip('/') for p in ls(root) if p.endswith('/')]
print(f'models in bucket: {len(models)}\n')

WANT_SCEN = ['historical', 'ssp126', 'ssp245', 'ssp585']
WANT_VAR = ['tas', 'pr']
rows = []
for i, m in enumerate(models, 1):
    scens = [p.rstrip('/').split('/')[-1] for p in ls(f'{root}{m}/') if p.endswith('/')]
    ok = {}
    for sc in WANT_SCEN:
        if sc not in scens:
            ok[sc] = None; continue
        # one ensemble member dir under the scenario
        ens = [p.rstrip('/').split('/')[-1] for p in ls(f'{root}{m}/{sc}/') if p.endswith('/')]
        if not ens:
            ok[sc] = None; continue
        vars_ = [p.rstrip('/').split('/')[-1] for p in ls(f'{root}{m}/{sc}/{ens[0]}/') if p.endswith('/')]
        ok[sc] = (ens[0], [v for v in WANT_VAR if v in vars_])
    complete = all(ok[s] and len(ok[s][1]) == 2 for s in WANT_SCEN)
    rows.append((m, ok, complete))
    mark = 'COMPLETE' if complete else 'incomplete'
    ensname = ok['historical'][0] if ok['historical'] else '-'
    miss = [s for s in WANT_SCEN if not ok[s] or len(ok[s][1]) < 2]
    print(f'{i:>3}. {m:<22} {ensname:<12} {mark:<11}'
          + ('' if complete else 'missing: ' + ','.join(miss)))

comp = [r[0] for r in rows if r[2]]
print(f'\n{len(comp)} of {len(models)} models have tas and pr for historical + all three SSPs:')
for c in comp: print('   ', c)
json.dump({'models_all': models, 'models_complete': comp},
          open('nexgddp_models.json', 'w'), indent=1)
print('\nwrote nexgddp_models.json')
