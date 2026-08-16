"""Is routine dengue vector surveillance species-resolved in the ten study
countries?

The projection says Ae. albopictus is displaced while Ae. aegypti is not. A
programme that reports only "Aedes spp." cannot observe that, so this asks two
separable questions per country:

  (a) is Ae. albopictus established and studied there at all?
  (b) does ROUTINE national surveillance distinguish the two species?

(a) is answerable from the literature. (b) mostly is not - published studies
are not evidence of routine practice - so this script establishes (a) and
flags what must be checked in national guidelines for (b).
"""
import urllib.request, urllib.parse, json, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
UA = {'User-Agent': 'dengue-vector-review (r.sundaram@northeastern.edu)'}

COUNTRIES = ['Singapore', 'Malaysia', 'Indonesia', 'Thailand', 'Philippines',
             'Vietnam', 'India', 'Bangladesh', 'Cambodia', 'Sri Lanka']

EPMC = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&pageSize={n}&resultType={rt}'

def q(query, n=1, rt='idlist'):
    u = EPMC.format(q=urllib.parse.quote(query), n=n, rt=rt)
    for a in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                        timeout=90) as r:
                return json.loads(r.read().decode('utf8'))
        except Exception:
            time.sleep(2 * (a + 1))
    return None

print(f"{'country':<13}{'albopictus':>11}{'+surveill':>11}{'+routine':>10}"
      f"{'aegypti':>9}{'ratio':>8}")
print('-' * 64)
res = {}
for c in COUNTRIES:
    a = q(f'"Aedes albopictus" AND "{c}"')
    s = q(f'"Aedes albopictus" AND "{c}" AND (surveillance OR monitoring)')
    r = q(f'"Aedes albopictus" AND "{c}" AND (surveillance OR monitoring) '
          f'AND (routine OR national OR programme OR program)')
    g = q(f'"Aedes aegypti" AND "{c}"')
    na = a['hitCount'] if a else None
    ns = s['hitCount'] if s else None
    nr = r['hitCount'] if r else None
    ng = g['hitCount'] if g else None
    ratio = (na / ng) if (na and ng) else float('nan')
    res[c] = dict(albopictus=na, surveillance=ns, routine=nr, aegypti=ng,
                  ratio=ratio)
    print(f'{c:<13}{na:>11}{ns:>11}{nr:>10}{ng:>9}{ratio:>8.2f}')
    time.sleep(0.4)

print('\nratio = albopictus literature / aegypti literature for that country.')
print('A low ratio suggests the secondary vector is comparatively understudied,')
print('which is a weak proxy for programme attention - not a measure of it.\n')

print('Titles mentioning routine or national albopictus surveillance:')
for c in COUNTRIES:
    d = q(f'"Aedes albopictus" AND "{c}" AND (surveillance OR monitoring) '
          f'AND (routine OR national OR programme OR program)', n=4, rt='core')
    if not d or not d.get('resultList', {}).get('result'):
        print(f'  {c}: none'); continue
    print(f'  {c}:')
    for x in d['resultList']['result'][:3]:
        print(f"      {x.get('pubYear','')}  {(x.get('title') or '')[:88]}")
    time.sleep(0.4)

json.dump(res, open('species_surveillance.json', 'w'), indent=1)
print('\nwrote species_surveillance.json')
