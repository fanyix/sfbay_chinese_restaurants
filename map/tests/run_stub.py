# Smoke-test index.html without a browser: run its inline script under JXA (osascript) against a DOM/Leaflet stub,
# in desktop and mobile mode, and exercise the filters. Prints PASS/FAIL lines; exit code 1 on any failure.
import os, re, subprocess, sys
T = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(os.path.dirname(T))
js = re.findall(r'<script>(.*?)</script>', open(os.path.join(R, 'index.html')).read(), re.S)[-1]
stub = open(os.path.join(T, 'stub.js')).read()
TEST = r'''
 const out = [], ok = (name, c) => out.push((c ? 'PASS ' : 'FAIL ') + name);
 const n = () => +$('shown').textContent.match(/显示 (\d+)/)[1];
 ok('init shows all ' + DATA.length, n() === DATA.length);
 ok('ids equal index', DATA.every((d, i) => d.id === i));
 ok('coords in Bay Area', DATA.every(d => d.lat > 36.8 && d.lat < 38.9 && d.lng > -123.3 && d.lng < -121.2));
 ok('required fields', DATA.every(d => d.en && d.conf && d.lang && d.cat && d.cuisineZh && d.region && d.city));
 fRegion.children.forEach((b, i) => {
   b.onclick(); ok('region ' + REGIONS[i] + ' = ' + n(), n() === DATA.filter(d => d.region === REGIONS[i]).length); b.onclick();
 });
 const r0 = fRegion.children[0]; r0.onclick();
 const c = DATA.find(d => d.region === REGIONS[0]).city;
 citySel.onchange({ target: { value: c } }); ok('city ' + c, n() === DATA.filter(d => d.city === c).length);
 r0.onclick(); fRegion.children[1].onclick(); ok('city cleared when region changes', state.city === '');
 $('reset').onclick(); ok('reset', n() === DATA.length && state.region.size === 0);
 $('q').oninput({ target: { value: '点心' } }); ok('search 点心 > 0', n() > 0);
 ok('popups render', DATA.every(d => popup(d).length > 200));
 return out.join('\n');'''
fail = False
for mobile in ('false', 'true'):
    p = f'/tmp/run_stub_{mobile}.js'
    open(p, 'w').write(f'var MOBILE={mobile};\n{stub}\n(function(){{{js}\n{TEST}\n}})()')   # function scope: JXA reserves global $
    r = subprocess.run(['osascript', '-l', 'JavaScript', p], capture_output=True, text=True)
    print(f'--- {"mobile" if mobile == "true" else "desktop"}'); print(r.stdout.strip() or r.stderr.strip())
    fail |= r.returncode != 0 or 'FAIL' in r.stdout or not r.stdout.strip()
sys.exit(1 if fail else 0)
