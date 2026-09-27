# Discover Chinese restaurants across the Bay Area via Google Maps search (paginated), saving raw place records.
import json, os, re, sys, time, urllib.parse
sys.path.insert(0, os.path.dirname(__file__)); from gmaps import get as _get, walk, pb_template

def get(u):
    for i in range(4):
        try: return _get(u)
        except Exception as e:
            print('  net error, retrying:', e, flush=True); time.sleep(20 * (i + 1))
    return ''

SF = ['Chinatown', 'Financial District', 'SoMa', 'Mission District', 'Inner Richmond', 'Outer Richmond', 'Inner Sunset',
      'Outer Sunset', 'Parkside', 'Excelsior', 'Visitacion Valley', 'Bayview', 'Portola', 'Ingleside', 'Nob Hill',
      'Tenderloin', 'Marina District', 'Noe Valley', 'Castro', 'Haight-Ashbury', 'Western Addition', 'Potrero Hill', 'North Beach']
AREAS = ([f'{n}, San Francisco' for n in SF] +
  # Peninsula
  ['Daly City', 'Colma', 'South San Francisco', 'San Bruno', 'Pacifica', 'Millbrae', 'Burlingame', 'San Mateo', 'Foster City',
   'Belmont', 'San Carlos', 'Redwood City', 'Menlo Park', 'East Palo Alto', 'Brisbane', 'Half Moon Bay'] +
  # East Bay
  ['Chinatown, Oakland', 'Oakland', 'Alameda', 'Berkeley', 'Albany', 'El Cerrito', 'Richmond', 'San Pablo', 'Pinole', 'Hercules',
   'Emeryville', 'San Leandro', 'Castro Valley', 'Hayward', 'Union City', 'Fremont', 'Newark', 'Pleasanton', 'Dublin', 'Livermore',
   'San Ramon', 'Danville', 'Walnut Creek', 'Lafayette', 'Orinda', 'Concord', 'Pleasant Hill', 'Martinez', 'Antioch', 'Pittsburg', 'Brentwood'] +
  # North Bay
  ['San Rafael', 'Novato', 'Mill Valley', 'Corte Madera', 'Petaluma', 'Santa Rosa', 'Napa', 'Vallejo', 'Fairfield', 'Benicia'] +
  # South Bay (re-sweep to fill gaps)
  ['Downtown San Jose', 'Berryessa, San Jose', 'Evergreen, San Jose', 'West San Jose', 'Almaden, San Jose', 'Blossom Valley, San Jose',
   'North San Jose', 'Cupertino', 'Sunnyvale', 'Santa Clara', 'Mountain View', 'Palo Alto', 'Los Altos', 'Milpitas', 'Campbell',
   'Saratoga', 'Los Gatos', 'Morgan Hill', 'Gilroy'])
QUERIES = [('Chinese restaurant', 6), ('dim sum', 2), ('hot pot', 2), ('Taiwanese restaurant', 2),
           ('Sichuan Hunan restaurant', 2), ('Chinese noodles dumplings', 2)]
K, N = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
SUF = f'_{K}' if N > 1 else ''
OUT = os.path.join(os.path.dirname(__file__), f'discover_raw{SUF}.json')
DONE = os.path.join(os.path.dirname(__file__), f'discover_done{SUF}.json')
BASE_DONE = os.path.join(os.path.dirname(__file__), 'discover_done.json')
raw = json.load(open(OUT)) if os.path.exists(OUT) else {}
done = set(json.load(open(DONE))) if os.path.exists(DONE) else set()
if N > 1 and os.path.exists(BASE_DONE): done |= set(json.load(open(BASE_DONE)))
AREAS = AREAS[K::N]

TEMPLATE = pb_template(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pb_template.txt'))   # query swapped per request
TQ = 'Chinese+restaurant+in+Daly+City%2C+CA'
assert TEMPLATE.count(TQ) >= 1, 'template query not found'

def fetch(query, off):
    qq = urllib.parse.quote_plus(query)
    u = TEMPLATE.replace(TQ, qq).replace('%217i20', '%217i20%218i' + str(off))
    for attempt in range(3):
        txt = get('https://www.google.com/' + u)
        if txt.startswith(")]}'"): return json.loads(txt[4:])
        print('  blocked? backing off', flush=True); time.sleep(90 * (attempt + 1))
    raise SystemExit('blocked by Google; progress saved')

def records(data):
    out = []
    walk(data, lambda o, p: out.append(o) if isinstance(o, list) and len(o) > 100 and isinstance(o[11], str)
         and isinstance(o[78] if len(o) > 78 else None, str) and str(o[78]).startswith('ChIJ') else None)
    return out

def slim(p):
    g = lambda i: p[i] if len(p) > i else None
    ll = g(9)
    return {'name': p[11], 'addr': g(39), 'lat': ll[2] if isinstance(ll, list) else None, 'lng': ll[3] if isinstance(ll, list) else None,
            'cats': g(13) or [], 'desc': (g(88)[0] if isinstance(g(88), list) and g(88) and isinstance(g(88)[0], str) else None),
            'p23': g(23), 'hours': bool(g(203)), 'pid': p[78],
            'rating': (g(4)[7] if isinstance(g(4), list) and len(g(4)) > 8 else None),
            'reviews': (g(4)[8] if isinstance(g(4), list) and len(g(4)) > 8 else None)}

total_req = 0
for area in AREAS:
    for q, pages in QUERIES:
        key = f'{q} | {area}'
        if key in done: continue
        query = f'{q} in {area}, CA'
        for pg in range(pages):
            recs = records(fetch(query, pg * 20)); total_req += 1
            new = 0
            for p in recs:
                s = slim(p)
                if s['pid'] not in raw: raw[s['pid']] = {**s, 'found': [key]}; new += 1
                elif key not in raw[s['pid']]['found']: raw[s['pid']]['found'].append(key)
            time.sleep(1.0)
            if len(recs) < 20 or new == 0: break
        done.add(key)
        json.dump(raw, open(OUT, 'w'), ensure_ascii=False)
        json.dump(sorted(done), open(DONE, 'w'), ensure_ascii=False)
    print(f'{area}: total places {len(raw)}, requests {total_req}', flush=True)
print('DONE', len(raw))
