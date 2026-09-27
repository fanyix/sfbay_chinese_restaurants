# Turn discover_raw.json into map entries: filter to Chinese restaurants, drop closed/chains, dedupe, rate, merge.
import json, os, re, collections
H = os.path.dirname(os.path.abspath(__file__))
J = lambda f: json.load(open(os.path.join(H, f)))
CJK = re.compile(r'[一-鿿]')

# Google category (en or zh) -> (English cuisine, Chinese label, specificity)
CAT = {
 'Sichuan restaurant': ('Sichuan', '川菜'), 'Szechuan restaurant': ('Sichuan', '川菜'), '川菜馆': ('Sichuan', '川菜'),
 'Hunan restaurant': ('Hunan', '湘菜'), '湘菜馆': ('Hunan', '湘菜'),
 'Cantonese restaurant': ('Cantonese', '粤菜'), '粤菜馆': ('Cantonese', '粤菜'),
 'Dim sum restaurant': ('Cantonese dim sum', '粤式点心'), '中式点心餐馆': ('Cantonese dim sum', '粤式点心'),
 'Cha chaan teng (Hong Kong-style cafe)': ('Hong Kong cafe (cha chaan teng)', '港式茶餐厅'), '港式茶餐厅': ('Hong Kong cafe (cha chaan teng)', '港式茶餐厅'),
 'Hong Kong style fast food restaurant': ('Hong Kong style fast food', '港式快餐'), '港式快餐店': ('Hong Kong style fast food', '港式快餐'),
 'Hot pot restaurant': ('Hot pot', '火锅'), '火锅餐馆': ('Hot pot', '火锅'), '火锅店': ('Hot pot', '火锅'),
 'Shabu-shabu restaurant': ('Shabu hot pot', '涮涮锅'),
 'Taiwanese restaurant': ('Taiwanese', '台湾菜'), '台湾风味餐馆': ('Taiwanese', '台湾菜'), '台湾菜馆': ('Taiwanese', '台湾菜'),
 'Shanghainese restaurant': ('Shanghai', '上海菜'), '上海菜馆': ('Shanghai', '上海菜'),
 'Chinese noodle restaurant': ('Chinese noodles', '中式面馆'), '中国面馆': ('Chinese noodles', '中式面馆'),
 'Dumpling restaurant': ('Dumplings', '饺子'), '饺子馆': ('Dumplings', '饺子'),
 'Dongbei restaurant': ('Dongbei (northeast)', '东北菜'), '东北菜馆': ('Dongbei (northeast)', '东北菜'),
 'Beijing restaurant': ('Beijing', '北京菜'), 'Peking duck restaurant': ('Beijing/Peking duck', '北京烤鸭'), '北京烤鸭店': ('Beijing/Peking duck', '北京烤鸭'),
 'Xinjiang restaurant': ('Xinjiang', '新疆菜'), 'Uyghur cuisine restaurant': ('Uyghur', '维吾尔菜'), '维吾尔族风味餐馆': ('Uyghur', '维吾尔菜'), '新疆菜馆': ('Xinjiang', '新疆菜'),
 'Hakka restaurant': ('Hakka', '客家菜'), '客家菜馆': ('Hakka', '客家菜'),
 'Teochew restaurant': ('Teochew', '潮州菜'), '潮州菜馆': ('Teochew', '潮州菜'),
 'Fujian restaurant': ('Fujian', '闽菜'), 'Yunnan restaurant': ('Yunnan', '云南菜'), 'Shandong restaurant': ('Shandong', '鲁菜'),
 'Zhejiang restaurant': ('Zhejiang', '浙菜'), 'Jiangsu restaurant': ('Jiangsu', '苏菜'), 'Hainanese restaurant': ('Hainanese', '海南菜'),
 'Guizhou restaurant': ('Guizhou', '贵州菜'), 'Chongqing restaurant': ('Chongqing', '重庆菜'),
 'Mandarin restaurant': ('Northern Chinese', '北方菜'), 'Chinese takeaway': ('Chinese takeout', '中餐外卖'), '中餐外卖': ('Chinese takeout', '中餐外卖'),
 'Chinese restaurant': ('Chinese', '中餐'), '中餐馆': ('Chinese', '中餐'),
}
GENERIC = {'Chinese', 'Chinese takeout'}
# First category that means "not a Chinese restaurant" even if Chinese appears later.
NOT_REST = re.compile(r'bakery|bubble tea|tea house|tea store|dessert|grocery|supermarket|market|hospital|clinic|medical|store|shop$|'
                      r'bar$|cafe$|coffee|caterer|Japanese|Sushi|Ramen|Korean|Thai|Filipino|Indian|Mexican|Pizza|Burmese|Mongolian barbecue|'
                      r'面包|奶茶|甜品|超市|市场|医院|诊所|商店|日本|寿司|拉面|韩国|泰国|咖啡', re.I)
CHAINS = re.compile(r"panda express|p\.?f\.? chang|pei wei|pick up stix|huhot|genghis grill|bd'?s mongolian|flame broiler|"
                    r"leeann chin|manchu wok|chowking|teriyaki|sushi|99 ranch|chinese hospital|milk tea$|boba", re.I)
# Dish words that make a generically-categorised restaurant clearly Chinese.
DISH = [(r'dim ?sum|yum ?cha', 'Dim sum restaurant'), (r'hot ?pot|malatang|mala\b', 'Hot pot restaurant'),
        (r'dumpling|potsticker|xiao ?long|xlb|jiaozi', 'Dumpling restaurant'), (r'sichuan|szechuan|chongqing', 'Sichuan restaurant'),
        (r'hunan', 'Hunan restaurant'), (r'wonton|wun-?tun|congee|cantonese|\bcanton\b|hong kong|\bhk\b|roast duck|char siu', 'Cantonese restaurant'),
        (r'taiwan', 'Taiwanese restaurant'), (r'shang ?hai', 'Shanghainese restaurant'), (r'peking|beijing', 'Beijing restaurant'),
        (r'lanzhou|biang|xi.?an\b|hand.?pulled', 'Chinese noodle restaurant'), (r'uyghur|xinjiang', 'Uyghur cuisine restaurant')]
RESTISH = re.compile(r'^(Restaurant|Asian restaurant|Seafood restaurant|Noodle shop|Asian fusion restaurant|Soup shop|Takeout Restaurant|'
                     r'Family restaurant|Vegetarian restaurant|Delivery Restaurant|餐馆|亚洲风味餐馆|面馆|海鲜餐馆)$')

def eff_cats(r):
    """Google categories, plus a Chinese category implied by the name when Google only says 'Restaurant'/'Asian restaurant'."""
    cats = list(r['cats'] or [])
    if not chinese_cats(cats) and cats and RESTISH.match(cats[0]):
        for pat, c in DISH:
            if re.search(pat, r['name'], re.I): cats.append(c); break
    return cats
AMERICAN = re.compile(r"panda|wok|express|golden|dragon|jade|lotus|bamboo|china (king|express|garden|house|wok|palace|star|buffet|bistro|kitchen)|"
                      r"chinese (food|kitchen|cuisine|restaurant|bistro|cafe)|chop suey|buffet|mandarin|imperial|great wall|lucky|fortune|happy|"
                      r"hunan (garden|express|house|wok)|szechwan|szechuan (garden|house|express)", re.I)
REGION = {
 '旧金山': {'San Francisco'},
 '半岛': {'Daly City', 'Colma', 'South San Francisco', 'San Bruno', 'Pacifica', 'Millbrae', 'Burlingame', 'San Mateo', 'Foster City',
          'Belmont', 'San Carlos', 'Redwood City', 'Menlo Park', 'East Palo Alto', 'Brisbane', 'Half Moon Bay', 'Hillsborough',
          'Atherton', 'Woodside', 'Portola Valley', 'Montara', 'El Granada', 'Redwood Shores', 'North Fair Oaks'},
 '南湾': {'San Jose', 'Cupertino', 'Sunnyvale', 'Santa Clara', 'Mountain View', 'Palo Alto', 'Los Altos', 'Milpitas', 'Campbell',
          'Saratoga', 'Los Gatos', 'Morgan Hill', 'Gilroy', 'Los Altos Hills', 'Monte Sereno', 'Alviso', 'San Martin'},
 '东湾': {'Oakland', 'Alameda', 'Berkeley', 'Albany', 'El Cerrito', 'Richmond', 'San Pablo', 'Pinole', 'Hercules', 'Emeryville',
          'San Leandro', 'Castro Valley', 'Hayward', 'Union City', 'Fremont', 'Newark', 'Pleasanton', 'Dublin', 'Livermore', 'San Ramon',
          'Danville', 'Walnut Creek', 'Lafayette', 'Orinda', 'Moraga', 'Concord', 'Pleasant Hill', 'Martinez', 'Antioch', 'Pittsburg',
          'Brentwood', 'Oakley', 'Clayton', 'El Sobrante', 'Rodeo', 'Crockett', 'San Lorenzo', 'Piedmont', 'Kensington', 'Bay Point',
          'Discovery Bay', 'Alamo', 'Sunol', 'Pacheco'},
 '北湾': {'San Rafael', 'Novato', 'Mill Valley', 'Corte Madera', 'Larkspur', 'Sausalito', 'Tiburon', 'Greenbrae', 'Fairfax',
          'San Anselmo', 'Petaluma', 'Santa Rosa', 'Rohnert Park', 'Napa', 'Vallejo', 'Fairfield', 'Benicia', 'American Canyon',
          'Sonoma', 'Windsor', 'Cotati', 'Sebastopol', 'Healdsburg', 'Suisun City', 'Vacaville', 'Kentfield', 'Belvedere Tiburon', 'Calistoga'},
}
CITY2REG = {c: r for r, cs in REGION.items() for c in cs}

def city_of(addr):
    m = re.search(r',\s*([^,]+),\s*CA\s*\d{5}', addr or '')
    return m.group(1).strip() if m else None

def chinese_cats(cats):
    return [c for c in cats if c in CAT]

AMBIG = {'Dumpling restaurant', '饺子馆', 'Hot pot restaurant', '火锅餐馆', '火锅店', 'Shabu-shabu restaurant', 'Dim sum restaurant'}
NEUTRAL = re.compile(r'^(Restaurant|Asian restaurant|Asian fusion restaurant|Fusion restaurant|Seafood restaurant|Vegan restaurant|'
                     r'Vegetarian restaurant|Takeout Restaurant|Delivery Restaurant|Family restaurant|Noodle shop|Soup shop|Caterer|'
                     r'Catering food and drink supplier|Fast food restaurant|Barbecue restaurant|餐馆|亚洲风味餐馆|亚洲混合风味餐馆)$')

def is_candidate(r):
    cats = eff_cats(r); cc = chinese_cats(cats)
    if not cc and not (CJK.search(r['name']) and cats and re.search(r'restaurant|餐', cats[0], re.I)
                       and not any(re.search(r'tea|bakery|cafe|dessert|茶|甜品|面包', c, re.I) for c in cats)):
        return False, 'not-chinese'
    # e.g. Ukrainian/Nepalese dumplings, Korean/Vietnamese hot pot: another cuisine first, only an ambiguous "Chinese-ish" category
    if cc and set(cc) <= AMBIG and cats[0] not in CAT and not NEUTRAL.match(cats[0]) and not CJK.search(r['name']):
        return False, 'primary:' + cats[0]
    if cc and set(cc) <= AMBIG and not CJK.search(r['name']) and (
            any(re.search(r'Korean|Japanese|Sushi|Thai|Ukrainian|Nepal|Tibetan|Indian|Himalayan|Polish|Russian', c) for c in cats)
            or set(cc) == {'Shabu-shabu restaurant'}):
        return False, 'primary:other-cuisine hot pot/dumpling'
    if cats and cats[0] not in CAT and NOT_REST.search(cats[0]) and not CJK.search(r['name']):
        return False, 'primary:' + cats[0]
    if CHAINS.search(r['name']): return False, 'chain/non-restaurant name'
    if r.get('desc') == 'CLOSED' or r.get('p23') == 1: return False, 'closed'
    if not r['addr'] or city_of(r['addr']) not in CITY2REG: return False, 'outside:' + str(city_of(r['addr']))
    return True, ''

def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

# ---------------- rating / merge ----------------
SF_ZIP = {'94108': 'Chinatown', '94133': 'North Beach/Chinatown', '94121': 'Outer Richmond', '94118': 'Inner Richmond',
          '94122': 'Sunset', '94116': 'Parkside/Outer Sunset', '94112': 'Excelsior/Ingleside', '94134': 'Visitacion Valley/Portola',
          '94124': 'Bayview', '94110': 'Mission', '94103': 'SoMa', '94107': 'SoMa/Potrero', '94158': 'Mission Bay', '94102': 'Tenderloin/Civic Center',
          '94109': 'Nob Hill/Polk', '94111': 'Financial District', '94104': 'Financial District', '94105': 'Financial District',
          '94115': 'Western Addition', '94117': 'Haight', '94114': 'Castro/Noe Valley', '94131': 'Glen Park', '94127': 'West Portal',
          '94132': 'Lake Merced/Stonestown', '94123': 'Marina', '94129': 'Presidio', '94130': 'Treasure Island'}
CANTO = {'Cantonese', 'Cantonese dim sum', 'Hong Kong cafe (cha chaan teng)', 'Hong Kong style fast food'}
VIET = re.compile(r'Vietnamese|Pho|越南|Southeast Asian|Cambodian|Malaysian|Singaporean|Indonesian|Laotian', re.I)
FUSION = re.compile(r'Asian fusion|亚洲混合', re.I)

def cat_of(cuisine):
    c = cuisine.lower()
    for cat, kws in [('火锅/麻辣烫', ['hot pot', 'shabu', 'malatang']), ('美式中餐/越南华人', ['american', 'vietnamese', 'teochew', 'chiu chow']),
                     ('台湾菜', ['taiwan']), ('粤菜/港式', ['cantonese', 'hong kong', 'hk', 'dim sum', 'cha chaan']),
                     ('川湘/西南', ['sichuan', 'hunan', 'chongqing', 'guizhou', 'guangxi', 'yunnan']),
                     ('西北/新疆/清真', ['uyghur', 'xinjiang', 'halal', 'lanzhou', "xi'an", 'islamic', 'northwest']),
                     ('北方/东北/江浙', ['northern', 'dongbei', 'northeast', 'beijing', 'shandong', 'shanghai', 'mongolian', 'zhejiang', 'jiangsu']),
                     ('面食/饺子', ['noodle', 'dumpling', 'bun', 'xlb', 'huoshao'])]:
        if any(k in c for k in kws): return cat
    return '其他中餐'

def cjk_part(s):
    """Chinese part of a mixed name: first CJK run of 2+ chars (e.g. 'Home Eat汉家宴 - Santa Clara' -> '汉家宴')."""
    runs = [x.strip() for x in re.findall(r'[一-鿿][一-鿿·・]*', s or '')]
    return next((x for x in runs if len(x) >= 2), runs[0] if runs else '')

def zh_name(r, au):
    if CJK.search(r['name']): return cjk_part(r['name']), 'en'
    z = (au or {}).get('zh') or ''
    if CJK.search(z) and z != r['name']: return cjk_part(z), 'zh-CN'
    return '', None

def strip_zh(name):
    s = re.sub(r'[一-鿿（）()·・]+', ' ', name)
    s = re.sub(r'\s*[-|/]\s*$', '', re.sub(r'\s+', ' ', s)).strip(' -|/')
    return s or name

ZH_DISH = [(r'茶餐厅|茶餐廳|冰室', ('Hong Kong cafe (cha chaan teng)', '港式茶餐厅')), (r'烧腊|燒臘|烧味|燒味', ('Cantonese BBQ / roast meats', '粤式烧腊')),
           (r'酒家|酒樓|酒楼|点心|點心|海鲜|海鮮', ('Cantonese dim sum/seafood', '粤式点心/海鲜')), (r'粥', ('Cantonese congee', '粤式粥品')),
           (r'麻辣烫|火锅|火鍋|串串', ('Hot pot', '火锅')), (r'川|蜀|成都|重庆|重慶|乐山|樂山', ('Sichuan', '川菜')), (r'湘|湖南', ('Hunan', '湘菜')),
           (r'台湾|台灣|台式|士林', ('Taiwanese', '台湾菜')), (r'上海|阿拉|沪|滬|江南|杭州|苏州', ('Shanghai', '上海菜')),
           (r'兰州|蘭州|陕西|陝西|西安|秦', ('Northwest (Shaanxi/Lanzhou)', '西北菜')), (r'新疆|维吾尔|龟兹', ('Xinjiang', '新疆菜')),
           (r'东北|東北|奉天|哈尔滨', ('Dongbei (northeast)', '东北菜')), (r'北京|烤鸭|烤鴨|京', ('Beijing/Peking duck', '北京菜')),
           (r'云南|雲南|米线|米線', ('Yunnan rice noodles', '云南米线')), (r'贵州|貴州', ('Guizhou', '贵州菜')), (r'潮州|潮汕', ('Teochew', '潮州菜')),
           (r'客家', ('Hakka', '客家菜')), (r'山东|山東|鲁', ('Shandong', '鲁菜')), (r'饺|餃|包子', ('Dumplings', '饺子/包子')), (r'面|麵', ('Chinese noodles', '中式面馆')),
           (r'港|粤|粵|广州|廣州|台山', ('Cantonese', '粤菜'))]

def rate(r, au):
    cats = eff_cats(r); cc = chinese_cats(cats)
    desc = r.get('desc') or ''
    # desc can add a regional cuisine when categories are generic
    spec = []
    for c in cc:
        en, zh = CAT[c]
        if en not in GENERIC and (en, zh) not in spec: spec.append((en, zh))
    if not spec:   # generic "Chinese restaurant": take a regional cuisine from the name, then the description
        for text in (r['name'], desc):
            hit = next((CAT[c] for pat, c in DISH if re.search(pat, text, re.I)), None)
            if hit: spec.append(hit); break
    if ('Cantonese dim sum', '粤式点心') in spec and ('Cantonese', '粤菜') in spec: spec.remove(('Cantonese', '粤菜'))
    zh, zsrc = zh_name(r, au)
    if not spec and zh:
        hit = next((v for pat, v in ZH_DISH if re.search(pat, zh)), None)
        if hit: spec.append(hit)
    viet = bool(cats and VIET.search(cats[0])) or bool(re.search(r'vietnam|pho\b', desc, re.I))
    fusion = bool(cats and FUSION.search(cats[0]))
    american = not spec and bool(AMERICAN.search(r['name']) or re.search(r'american|chop suey|takeout|take-out|lunch special', desc, re.I))
    if spec: cuisine, cz = '/'.join(e for e, _ in spec[:2]), '/'.join(z for _, z in spec[:2])
    elif viet: cuisine, cz = 'Chinese-Vietnamese', '越南华人中餐'
    elif american: cuisine, cz = 'American Chinese', '美式中餐'
    elif fusion: cuisine, cz = 'Chinese/Asian fusion', '中餐/亚洲融合'
    else: cuisine, cz = 'Chinese', '中餐'
    if viet and spec: cuisine, cz = cuisine + '/Vietnamese', cz + '/越南菜'
    ev = []
    if zsrc == 'en': ev.append(f'Google 地图店名含中文「{zh}」')
    elif zsrc == 'zh-CN': ev.append(f'Google 地图中文版显示中文店名「{zh}」（商家自行登记）')
    ev.append('Google 分类：' + ' / '.join(c for c in cats[:3]))
    if desc != 'CLOSED' and len(desc.split()) >= 4: ev.append('简介：' + desc)
    if zsrc and not viet and not (american and zsrc == 'zh-CN'): conf = '高'
    elif zsrc: conf = '中'
    elif spec and not viet: conf = '中'
    else: conf = '低'
    if conf == '低':
        ev.append('无中文店名' + ('，越南华人风格' if viet else '，美式中餐风格' if american else '，仅泛称中餐') + '，弱推断')
    elif conf == '中' and not zsrc:
        ev.append('无中文店名，按地区菜系推断')
    sp = {e for e, _ in spec}
    city = city_of(r['addr']); reg = CITY2REG[city]
    if re.search(r'teochew|chiu ?chow', r['name'] + cuisine, re.I): lang = '粤语/潮州话'
    elif sp & {'Uyghur', 'Xinjiang'}: lang = '普通话 (维吾尔语)'
    elif viet: lang = '粤语'
    elif re.search(r'cantonese|hong kong|dim sum', cuisine + ' ' + desc, re.I): lang = '普通话/粤语'
    elif not spec and reg == '旧金山': lang = '普通话/粤语'
    else: lang = '普通话'
    z = re.search(r'CA (\d{5})', r['addr'])
    area = SF_ZIP.get(z.group(1), '') if (city == 'San Francisco' and z) else ''
    return {'conf': conf, 'direct': False, 'city': city, 'area': area, 'region': reg,
            'en': strip_zh(r['name']) if zsrc == 'en' else r['name'], 'zh': zh,
            'addr': r['addr'], 'cuisine': cuisine, 'cuisineZh': cz, 'cat': cat_of(cuisine), 'lang': lang, 'ev': '; '.join(ev),
            'lat': r['lat'], 'lng': r['lng'], 'approx': False, 'pid': r['pid']}

def load_raw():
    raw = {}
    for f in sorted(os.listdir(H)):
        if re.match(r'discover_raw(_\d+)?\.json$', f):
            for pid, r in J(f).items():
                if pid in raw: raw[pid]['found'] += r['found']
                else: raw[pid] = r
    return raw

def dist_m(a, b):
    import math
    dy = (a[0] - b[0]) * 111000; dx = (a[1] - b[1]) * 111000 * math.cos(math.radians(a[0]))
    return (dx * dx + dy * dy) ** .5

def existing():
    """Current South Bay entries, tagged with region + Google place id where the earlier closed-check found one."""
    d = J('data_southbay_backup.json'); g = J('gmaps_status.json')   # original 213 South Bay entries
    for x in d:
        x['region'] = '南湾'
        if x.get('pid'): continue
        best = None
        for v in g.values():
            if x['addr'] and x['addr'].split(',')[0] in v['q']:
                for rec in v['recs']:
                    if norm(rec['name'])[:5] == norm(x['en'])[:5] or norm(x['en'])[:6] in norm(rec['name']): best = rec['pid']; break
            if best: break
        x['pid'] = best
    return d

def similar(a, b):
    a, b = norm(a), norm(b)
    return a[:5] == b[:5] or (len(a) > 4 and a in b) or (len(b) > 4 and b in a)

def candidates():
    raw = load_raw(); ex = existing()
    expid = {x['pid'] for x in ex if x['pid']}
    out, drop = [], collections.Counter()
    for r in sorted(raw.values(), key=lambda r: -len(r['found'])):
        ok, w = is_candidate(r)
        if not ok: drop[w.split(':')[0]] += 1; continue
        if r['pid'] in expid or any(dist_m((r['lat'], r['lng']), (x['lat'], x['lng'])) < 80 and similar(r['name'], x['en']) for x in ex):
            drop['already in South Bay list'] += 1; continue
        if any(dist_m((r['lat'], r['lng']), (o['lat'], o['lng'])) < 40 and similar(r['name'], o['name']) for o in out):
            drop['duplicate listing'] += 1; continue
        out.append(r)
    return ex, out, drop

if __name__ == '__main__':
    import sys
    ex, cand, drop = candidates()
    if sys.argv[1:2] == ['audit-list']:   # 'audit-list all' also re-checks South Bay entries that already have a Chinese name
        items = [{'pid': r['pid'], 'name': r['name'], 'addr': r['addr']} for r in cand]
        items += [{'pid': x['pid'], 'name': x['en'], 'addr': x['addr']} for x in ex if x['pid'] and (not x['zh'] or sys.argv[2:] == ['all'])]
        json.dump(items, open(os.path.join(H, 'audit_items.json'), 'w'), ensure_ascii=False); print(len(items), 'to audit'); sys.exit()
    au = {}
    for f in sorted(os.listdir(H)):
        if re.match(r'zh_audit(_\d+)?\.json$', f): au.update({k: v for k, v in J(f).items() if k not in au or v})
    closed = []
    new = []
    for r in cand:
        a = au.get(r['pid'])
        if a and (a['p23'] == 1 or a['p88'] == 'CLOSED'):
            closed.append([strip_zh(r['name']), cjk_part(r['name']), city_of(r['addr']), r['addr'], 'Google Maps 复核显示 Permanently closed（未收录）']); continue
        new.append(rate(r, a))
    # existing entries: add Chinese names Google shows in zh-CN when we had none
    zh_added = 0
    for x in ex:
        a = au.get(x['pid'] or '')
        if a and not x['zh'] and CJK.search(a['zh'] or '') and a['zh'] != x['en']:
            x['zh'] = cjk_part(a['zh']); zh_added += 1
            x['ev'] = f"Google 地图中文版显示中文店名「{a['zh']}」; " + x['ev']
    # Chinese restaurants that discovery already saw as closed (would otherwise have passed the filter)
    for r in load_raw().values():
        if (r.get('desc') == 'CLOSED' or r.get('p23') == 1) and is_candidate(dict(r, desc=None, p23=None))[0]:
            closed.append([strip_zh(r['name']), cjk_part(r['name']), city_of(r['addr']), r['addr'], 'Google Maps 标注 Permanently closed（湾区扩展时剔除，未收录）'])
    keep = []
    for x in ex:
        a = au.get(x['pid'] or '')
        if a and (a['p23'] == 1 or a['p88'] == 'CLOSED'):
            closed.append([x['en'], x['zh'], x['city'], x['addr'], 'Google Maps 复核显示 Permanently closed（已从地图移除）'])
        else: keep.append(x)
    ex = keep
    allr = ex + new
    order = ['旧金山', '半岛', '东湾', '南湾', '北湾']
    allr.sort(key=lambda x: (order.index(x['region']), x['city'], '高中低'.index(x['conf']), x['en'].lower()))
    for i, x in enumerate(allr): x['id'] = i
    json.dump(allr, open(os.path.join(H, 'data.json'), 'w'), ensure_ascii=False, indent=0)
    json.dump(closed, open(os.path.join(H, 'closed_new.json'), 'w'), ensure_ascii=False, indent=0)
    print('dropped:', dict(drop)); print('closed, logged not included:', len(closed), '| zh names added to South Bay:', zh_added)
    print('total', len(allr), collections.Counter(x['region'] for x in allr), collections.Counter(x['conf'] for x in allr))
