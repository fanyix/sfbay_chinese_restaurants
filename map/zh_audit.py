# For each candidate place, look it up on Google Maps in zh-CN to get its Chinese-locale name + fresh open/closed status.
import json, os, sys, time, urllib.parse
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from gmaps import get as _get, walk

def get(u):
    for i in range(4):
        try: return _get(u)
        except Exception as e:
            print('  net error, retrying:', e, flush=True); time.sleep(20 * (i + 1))
    return ''
TEMPLATE = open('/tmp/pb_url.txt').read().replace('hl=en', 'hl=zh-CN')
TQ = 'Chinese+restaurant+in+Daly+City%2C+CA'
OUT = os.path.join(H, 'zh_audit.json')

def recs(q):
    txt = get('https://www.google.com/' + TEMPLATE.replace(TQ, urllib.parse.quote_plus(q)))
    if not txt.startswith(")]}'"): return None
    out = []
    walk(json.loads(txt[4:]), lambda o, p: out.append(o) if isinstance(o, list) and len(o) > 100 and isinstance(o[11], str)
         and isinstance(o[78] if len(o) > 78 else None, str) and str(o[78]).startswith('ChIJ') else None)
    return out

def audit(items, delay=1.0):
    """items: list of {pid, name, addr}. Saves {pid: {zh, p23, p88, hours, n}} incrementally."""
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for i, it in enumerate(items):
        if it['pid'] in res: continue
        for attempt in range(3):
            rs = recs(f"{it['name']}, {it['addr']}")
            if rs is not None: break
            print('blocked? backing off', flush=True); time.sleep(90 * (attempt + 1))
        else: raise SystemExit('blocked; progress saved')
        hit = next((p for p in rs if p[78] == it['pid']), None)
        g = lambda p, k: p[k] if len(p) > k else None
        res[it['pid']] = None if hit is None else {
            'zh': hit[11], 'p23': g(hit, 23), 'hours': bool(g(hit, 203)), 'n': len(rs),
            'p88': g(hit, 88)[0] if isinstance(g(hit, 88), list) and g(hit, 88) and isinstance(g(hit, 88)[0], str) else None,
            'hood': g(hit, 14) if isinstance(g(hit, 14), str) else None}
        if i % 10 == 0:
            json.dump(res, open(OUT, 'w'), ensure_ascii=False); print(i, len(items), flush=True)
        time.sleep(delay)
    json.dump(res, open(OUT, 'w'), ensure_ascii=False)
    return res

if __name__ == '__main__':
    items = json.load(open(sys.argv[1]))
    if len(sys.argv) > 3:   # worker k of n: own output file, seeded with results so far
        k, n = int(sys.argv[2]), int(sys.argv[3])
        base = json.load(open(OUT)) if os.path.exists(OUT) else {}
        OUT = os.path.join(H, f'zh_audit_{k}.json')
        if not os.path.exists(OUT): json.dump(base, open(OUT, 'w'), ensure_ascii=False)
        items = items[k::n]
    audit(items)
