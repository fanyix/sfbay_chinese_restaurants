# Look up each restaurant on Google Maps and record business-status signals.
import json, re, sys, time, os
sys.path.insert(0, '/tmp'); from gmaps import lookup, walk
D = json.load(open('map/data.json'))
OUT = 'map/gmaps_status.json'
res = json.load(open(OUT)) if os.path.exists(OUT) else {}
def place_records(data):
    out = []
    walk(data, lambda o, p: out.append(o) if isinstance(o, list) and len(o) > 100 and isinstance(o[11], str)
         and isinstance(o[78] if len(o) > 78 else None, str) and str(o[78]).startswith('ChIJ') else None)
    return out
for d in D:
    k = str(d['id'])
    if k in res and 'err' not in res[k]: continue
    q = f"{d['en']} {d['addr'] or d['city'] + ' CA'}"
    q = re.sub(r'\(.*?\)', '', q)
    try:
        txt, err = lookup(q)
        if err: res[k] = {'err': err}; continue
        recs = place_records(json.loads(txt[4:] if txt.startswith(")]}'") else txt))
        r = []
        for p in recs[:3]:
            r.append({'name': p[11], 'addr': p[39] if len(p) > 39 else None, 'p23': p[23],
                      'p88': (p[88][0] if isinstance(p[88], list) and p[88] and isinstance(p[88][0], str) else None) if len(p) > 88 else None,
                      'hours': bool(p[203]) if len(p) > 203 else None, 'pid': p[78]})
        res[k] = {'q': q, 'recs': r}
    except Exception as e:
        res[k] = {'err': repr(e)[:200]}
    json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=0)
    print(k, d['en'], '->', (res[k].get('recs') or [{}])[0].get('name') if 'recs' in res[k] else res[k], flush=True)
    time.sleep(1.2)
print('DONE', len(res))
